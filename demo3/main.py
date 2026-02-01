from utils import *
import copy
import faulthandler
faulthandler.disable()

def main():
    STYLE_DB_ROOT = "./faiss/style"
    TPO_DB_ROOT   = "./faiss/tpo"
    CATEGORY_ORDER = ["상의", "아우터", "바지", "신발", "가방"]

    model = load_embedding_model()

    persona = pick_persona()
    user_gender = GENDER_MAP[persona]
    negatives = get_negatives()

    tpo_raw = get_tpo()
    parsed_tpo = parse_tpo(tpo_raw)

    db_cache = load_all_dbs(STYLE_DB_ROOT, TPO_DB_ROOT, CATEGORY_ORDER)

    base_style_query = safe_join(PERSONA_MOOD[persona])
    base_tpo_query   = safe_join(parsed_tpo)

    print("\n==============================")
    print("SESSION START")
    print(f"persona: {persona}")
    print(f"parsed_tpo: {parsed_tpo}")
    print(f"base_style_query: {base_style_query}")
    print(f"base_tpo_query: {base_tpo_query}")
    print("==============================\n")

    conflict = judge_conflict(persona, parsed_tpo)
    print(f"⚠️ conflict: {conflict}\n") # 한 번만 파악

    selected_items = {} # 유저가 선택한 아이템들
    selected_context_text = "" # main_cat, sub_cat, description: reason
    
    # main 카테고리별로 sub_cat, color, fit, pattern을 []으로 initialize
    hard_constraints_by_category = {
        cat: init_hard_constraints() # preferred factor
        for cat in CATEGORY_ORDER
    }
    
    style_query = base_style_query
    tpo_query = base_tpo_query

    print(f"style_query: {style_query}")
    print(f"tpo_query:   {tpo_query}")

    for category in CATEGORY_ORDER:
        print(f"\n===== [{category}] =====")
        hard_constraints = hard_constraints_by_category[category] 
        rerun_category = True
        all_top_items = []
        all_reasons = []
        cnt = 0
        
        while rerun_category: 
            rerun_category = False

            style_items, tpo_items = retrieve_candidates_by_category(
                persona=persona,
                category=category,
                style_query=style_query,
                tpo_query=tpo_query,
                db_cache=db_cache,
                model=model,
                negatives=negatives,
                user_gender=user_gender,
                hard_constraints=hard_constraints,
                topk=5
            )
            
            if not style_items and not tpo_items: # 하나라도 있으면 False, 둘 다 없어야 True
                print(f"\n❌ [{category}] 조건을 만족하는 아이템을 찾을 수 없습니다. 마지막으로 추천된 아이템들로부터 변경을 시도할게요!\n")
                           
            else: # style_items or tpo_items인 경우
                print_candidates("STYLE_DB", style_items)
                print_candidates("TPO_DB", tpo_items)

                fused_candidates = fuse_candidates(style_items, tpo_items, conflict, topk=5)
                print("\n[Stage 1] Style/TPO score-based fusion 완료")
                print_fused_candidates(fused_candidates)

                if not selected_items:
                    print("ℹ️ 아직 선택된 아이템 없음 → 단일 아이템 기준 조화 판단")
                else:
                    print(f"🧩 이미 선택된 아이템 {len(selected_items)}개 기준으로 조화 판단")

                top_item_ids = rerank_with_llm(
                    persona=persona,
                    parsed_tpo=parsed_tpo,
                    conflict=conflict,
                    fused_candidates=fused_candidates,
                    selected_items=selected_items,
                    topk=3)

                print("\n[Stage 2] Harmony-based LLM reranking 시작")
                print("\n추천 결과:")
                reason_query = build_reason_query(persona, parsed_tpo)

                for pid in top_item_ids:
                    cnt += 1
                    item = lookup_item_by_id(pid, fused_candidates)
                    if item is None:
                        continue

                    reason = generate_reason(
                        reason_query=reason_query,
                        selected_context_text=selected_context_text,
                        item_desc = f"{item.get('main_cat_name')}({item.get('sub_cat_name')}): {item.get('description')}"
                    )
                    
                    all_reasons.append(reason)
                    all_top_items.append(item)
                    print_results(cnt, item, reason) # 새롭게 추가된 번호와 아이템만 출력
                    

            # 추천될 때까지 반복
            pref_list = []
            while True:
                if category in ["상의", "바지", "아우터"]:
                    user_input = input(f"""\n마음에 드는 아이템 번호(1~{cnt}) 또는 추가 요청을 입력해주세요. 혹시 추천된 아이템이 마음에 들지 않으신가요? 아래 보기에서 수정할 사항을 입력해주세요. (sub_cat_name / color / fit / pattern / texture) """).strip()
                elif category == "신발":
                    user_input = input(f"""\n마음에 드는 아이템 번호(1~{cnt}) 또는 추가 요청을 입력해주세요. 혹시 추천된 아이템이 마음에 들지 않으신가요? 아래 보기에서 수정할 사항을 입력해주세요. (sub_cat_name / color/ texture) """).strip()
                elif category == "가방":
                    user_input = input(f"""\n마음에 드는 아이템 번호(1~{cnt}) 또는 추가 요청을 입력해주세요. 혹시 추천된 아이템이 마음에 들지 않으신가요? 아래 보기에서 수정할 사항을 입력해주세요. (sub_cat_name / color / pattern / texture) """).strip()
                
                if user_input.isdigit():
                    sel = int(user_input)
                    if 1 <= sel <= len(all_top_items):
                        chosen = all_top_items[sel - 1]

                        add_selected_item(category, selected_items, chosen) # main_cat를 key로 해서 내용을 value로 업데이트
                        selected_context_text = append_selected_context(selected_context_text, chosen)

                        print(f"✅ 선택 완료: {chosen.get('product_id')}")
                        break
                    else:
                        print(f"⚠️ 1~{cnt} 사이의 번호를 입력해주세요.")

                elif user_input in ["sub_cat_name", "color", "fit", "pattern", "texture"]:
                    details = DETAIL_MAP[user_input]
                    options = details[category]
                    options_to_text = ", ".join(options)
                    preference = input(f"""어떻게 변경해드릴까요? 아래 옵션에서 선택해주세요.
                                        {options_to_text}""")
                    pref_list.append(preference) # 리스트로 만들기
                    if user_input == "color":
                        alter = []
                        if preference == "화이트":
                            alter = ["크림", "아이보리", "베이지"]
                        if preference == "그린":
                            alter = ["카키"]
                        if preference == "버건디":
                            alter = ["와인", "레드"]
                        if preference == "그레이":
                            alter = ["실버", "회색"]
                        if alter:
                            pref_list.extend(alter)
                    
                    feedback = {"intent": user_input,
                                "include": pref_list}
                    
                    apply_feedback_to_constraints(feedback, hard_constraints) # update constraints
                    print("🔄 피드백 반영 완료")
                    print(f"현재 hard constraints: {hard_constraints}")
                    rerun_category = True
                    break

                else:
                    print("⚠️ 번호 또는 요청을 입력해주세요.")

    print("\n🎉 최종 코디 완성!")
    refined_tpo = refine_tpo_text(tpo_raw)
    print(f"💬 TPO: {refined_tpo}\n\n")
    for key, value in selected_items.items():
        print(f"📌 Main Category: {key}")
        print(f"👉 Product Name: {value['product_name']}")
        print(f"💍 Brand: {value['brand']}")
        print(f"💰 Price: {value['price']}")
        print(f"🔗 Item Link: {value['item_url']}")
        print(f"🔗 Image Link: {value['img_url']}")
        print("\n\n")

if __name__ == "__main__":
    import multiprocessing as mp
    mp.set_start_method("spawn", force=True)
    main()
