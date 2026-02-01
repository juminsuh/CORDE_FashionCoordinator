import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
os.environ['OMP_NUM_THREADS'] = '1'

import json
import faiss
import torch
from openai import OpenAI
from dotenv import load_dotenv
from prompt import *
from sentence_transformers import SentenceTransformer

load_dotenv('.env', override=True)
API_KEY = os.getenv("OPENAI_API_KEY")

PERSONA_MAP = {
    1: "pme",
    2: "nowon",
    3: "ob",
    4: "moyeon",
    5: "seoksa",
    6: "promie"
}


NEGATIVE_MAP = {
    "fit": {
        1: "오버사이즈",
        2: "슬림",
        3: ""
    },
    "pattern": {
        1: "로고",
        2: "스트라이프",
        3: "체크",
        4: ""
    },
    "price": {
        1: 100000,
        2: 200000,
        3: 300000,
        4: 500000,
        5: 500000
    }
}

GENDER_MAP = {
    "pme": "남자",
    "nowon": "남자",
    "ob": "남자",
    "moyeon": "여자",
    "seoksa": "여자",
    "promie": "여자"
}

PERSONA_MOOD = {
    "pme": ["캐주얼", "단정", "프레피","남친룩"],
    "moyeon": ["스트릿"],
    "seoksa": ["캐주얼", "편함"],
    "promie": ["여성스러움", "시크", "단정"],
    "nowon": ["미니멀", "캐주얼"],
    "ob": ["스트릿", "워크웨어"],
}

DETAIL_MAP = {
    "sub_cat_name": {
        "상의": ['긴소매 티셔츠', '니트/스웨터', '후드 티셔츠', '셔츠/블라우스', '피케/카라 티셔츠', '맨투맨/스웨트'],
        "바지": ['데님 팬츠', '코튼 팬츠', '슈트 팬츠/슬랙스', '트레이닝/조거 팬츠'],
        "아우터": ['롱패딩/헤비 아우터', '무스탕/퍼', '플리스/뽀글이', '겨울 싱글 코트', '숏패딩/헤비 아우터', '슈트/블레이저 재킷', '카디건', '후드 집업'],
        "신발": ['스니커즈', '부츠/워커', '구두', '패딩/퍼 신발'],
        "가방": ['백팩', '메신저/크로스 백', '에코백', '숄더백']
    },
    "color": {
        "상의": ['블랙', '화이트', '차콜', '그린', '그레이', '네이비', '브라운', '핑크', '블루', '버건디'],
        "바지": ['블랙', '화이트', '차콜', '그레이', '네이비', '브라운', '블루'],
        "아우터": ['블랙', '화이트', '차콜', '그린', '그레이', '네이비', '브라운', '핑크', '블루', '버건디'],
        "신발": ['블랙', '화이트', '차콜', '그레이', '네이비', '브라운', '블루'],
        "가방": ['블랙', '화이트', '차콜', '그린', '그레이', '네이비', '브라운', '블루', '버건디']
    },
    "fit": {
        "상의": ['슬림', '레귤러', '오버사이즈'],
        "바지": ['레귤러', '오버사이즈'],
        "아우터": ['레귤러']
    },
    "pattern": {
        "상의": ['단색', '로고/그래픽', '스트라이프', '체크'],
        "바지": ['단색', '로고/그래픽'],
        "아우터": ['단색', '로고/그래픽'],
        "가방": ['로고/그래픽', '기타패턴', '단색']
    },
    "texture": {
        "상의": ['면', '니트', '폴리에스테르'],
        "바지": ['폴리에스테르', '면', '나일론'],
        "아우터": ['나일론', '울', '니트', '면', '폴리에스테르'],
        "신발": ['천연가죽', '스웨이드', '폴리에스테르', '인조가죽'],
        "가방": ['나일론', '면', '폴리에스테르']
    }
    
}

# ===============================
# 0. Utils
# ===============================

from openai import OpenAI
import os, json, faiss, torch
import numpy as np
from sentence_transformers import SentenceTransformer

def tpo_to_text(tpo_val):
    """tpo가 list/str/None 섞여 들어와도 검색쿼리에 안전하게 넣기"""
    if tpo_val is None:
        return ""
    if isinstance(tpo_val, list):
        return ", ".join([str(x) for x in tpo_val if x])
    return str(tpo_val)

def safe_join(parts):
    # "", None 제거 + 중복 제거
    cleaned = []
    for p in parts:
        if not p:
            continue
        p = str(p).strip()
        if not p:
            continue
        cleaned.append(p)
    return ", ".join(list(dict.fromkeys(cleaned)))

# ===============================
# 1. Load Model & DB
# ===============================

def load_embedding_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"➡️ DEVICE: {device}")
    print("👉 Embedding model is loading...")
    model = SentenceTransformer("upskyy/bge-m3-korean", device=device)
    model.eval()
    return model

def embed_text(text: str, model):
    with torch.no_grad():
        vec = model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
    return vec.astype("float32")


def load_db(db_dir):
    index_path = os.path.join(db_dir, "index.faiss")
    # index = faiss.read_index(index_path)
    index = faiss.read_index(index_path, faiss.IO_FLAG_MMAP | faiss.IO_FLAG_READ_ONLY)
    metas = [json.loads(l) for l in open(os.path.join(db_dir, "metadata.jsonl"), encoding="utf-8")]
    return index, metas


def load_all_dbs(style_root, tpo_root, categories):
    db_cache = {"style": {}, "tpo": {}}
    print("👉 DB cache is loading...")
    for cat in categories:
        # tpo DB는 항상 존재
        db_cache["tpo"][cat] = {}
        db_cache["tpo"][cat]["index"], db_cache["tpo"][cat]["meta"] = load_db(
            os.path.join(tpo_root, cat)
        )

        # style DB는 있는 경우만
        style_cat_dir = os.path.join(style_root, cat)
        if os.path.exists(style_cat_dir):
            db_cache["style"][cat] = {}
            db_cache["style"][cat]["index"], db_cache["style"][cat]["meta"] = load_db(
                style_cat_dir
            )
        else:
            db_cache["style"][cat] = None  # 🔥 중요

    return db_cache

# ===============================
# 2. Input
# ===============================

def pick_persona():
    persona_input = int(input(PERSONA))
    return PERSONA_MAP[persona_input]


def get_tpo():
    return input("\nTPO를 입력해주세요: ").strip()


def get_negatives():
    print("비선호 요소를 조사하겠습니다.\n")
    fit_input = int(input("[비선호 요소 1] fit\n 다음 중 비선호하는 요소를 번호로 입력해주세요.\n1. 오버사이즈  2. 슬림  3. 없음\n"))
    fit_info = NEGATIVE_MAP["fit"][fit_input]

    pattern_input = int(input("[비선호 요소 2] pattern\n다음 중 비선호하는 요소를 번호로 입력해주세요.\n1. 로고  2. 스트라이프  3. 체크  4. 없음\n"))
    pattern_info = NEGATIVE_MAP["pattern"][pattern_input]

    price_input = int(input("[비선호 요소 3] price\n 다음 중 평소 옷 한 벌에 소비 가능한 최대 금액을 골라주세요.\n1. 10만원  2. 20만원  3. 30만원  4. 50만원  5. 그 이상 소비 가능\n"))
    price_info = NEGATIVE_MAP["price"][price_input] # threshold로 사용됨

    return {
            "fit": [fit_info] if fit_info else [],
            "pattern": [pattern_info] if pattern_info else [],
            "price_raw": price_info
            }


# =============================================================================================
# 3. OpenAI API: parse_tpo, judge_conflict, rerank_with_llm, generate_reason, update_query
# =============================================================================================

def get_client():
    # 환경변수 OPENAI_API_KEY 사용
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def parse_tpo(tpo_text: str):
    print("👉 Parsing the tpo...")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    res = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": TPO_PARSE_PROMPT},
            {
        "role": "user",
        "content": "1월에 회사 면접을 보러 가서 단정하고 깔끔한 면접룩을 추천받고 싶어."
    },
    {
        "role": "assistant",
        "content": json.dumps(
            {
                "parsed_keywords": ["1월에 회사 면접", "단정하고 깔끔한 면접룩"]
            },
            ensure_ascii=False
        )
    },

    # shot 2
    {
        "role": "user",
        "content": "남자친구와 2박 3일 부산으로 여행 가는데 편하면서도 예쁜 스타일 추천받고 싶어."
    },
    {
        "role": "assistant",
        "content": json.dumps(
            {
                "parsed_keywords": ["남자친구와 여행", "편안한 스타일", "예쁜 여친룩"]
            },
            ensure_ascii=False
        )
    },

            {"role": "user", "content": tpo_text},
        ]
    )
    parsed = json.loads(res.choices[0].message.content)
    return parsed.get("parsed_keywords", [])

def judge_conflict(persona: str, parsed_tpo: list) -> bool:
    print("👉 Judging tpo and style conflict...")
    client = get_client()

    payload = {
        "persona": persona,
        "persona_mood": PERSONA_MOOD[persona],
        "tpo": parsed_tpo
    }

    res = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        response_format={"type":"json_object"},
        messages=[
            {"role":"system", "content": MATCH_CLASSIFY_PROMPT},
            {"role":"user", "content": json.dumps(payload, ensure_ascii=False)}
        ]
    )

    obj = json.loads(res.choices[0].message.content)
    return bool(obj["conflict"])

def rerank_with_llm(
    persona,
    parsed_tpo,
    conflict,
    fused_candidates,
    selected_items,
    topk=3
):
    print("👉 Items are reranking with llm...")
    client = get_client()

    def summarize(item):
        return {
            "product_id": str(item.get("product_id")),
            "sub_category": item.get("sub_cat_name"),
            "style": item.get("style"),
            "fit": item.get("fit"),
            "pattern": item.get("pattern"),
            "texture": item.get("texture"),
            "color": item.get("color"),
            "tpo": item.get("tpo"),
            "description": item.get("description"),
            "img_url": item.get("img_url")
        }

    payload = {
        "persona": persona,
        "persona_mood": PERSONA_MOOD[persona],
        "parsed_tpo": parsed_tpo,
        "conflict": conflict,
        "selected_items": selected_items,          # 🔥 조화 anchor
        "candidates": [summarize(x) for x in fused_candidates]
    }

    res = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": HARMONY_RERANK_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
        ]
    )

    obj = json.loads(res.choices[0].message.content)
    return obj["top_items"][:topk]

def build_reason_query(persona, parsed_tpo):
    tpo_text = ", ".join(parsed_tpo)
    persona_text = ", ".join(PERSONA_MOOD[persona])
    return f"추천상황(TPO): {tpo_text}\n페르소나 스타일: {persona_text}"

def generate_reason(reason_query: str, selected_context_text: str, item_desc: str):
    print("👉 Reason for recommendation is generating...")
    client = get_client()

    reason_input = f"""
[TPO & PERSONA]
{reason_query}

[이미 선택된 아이템]
{selected_context_text if selected_context_text else "없음"}

[현재 추천 아이템]
{item_desc}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.0,
        messages=[
            {"role":"system", "content": REASON_GENERATE_PROMPT},
            # few-shot
            {"role":"user", "content": """
[TPO & PERSONA]
추천상황(TPO): 회사 면접, 단정하고 깔끔한 면접룩
페르소나 스타일: 포멀, 단정, 프레피

[이미 선택된 아이템]
- 상의(셔츠): 부드럽고 탄탄한 코튼 소재의 쿨한 셔츠

[현재 추천 아이템]
바지(슬랙스): 다크 네이비 색상의 단정하고 깔끔한 슬랙스
""".strip()},
            {"role":"assistant", "content": "다크 네이비 슬랙스는 첫인상을 차분하게 잡아주면서도 실루엣이 깔끔해 면접 자리에서 신뢰감을 줍니다. 앞서 고른 코튼 셔츠와 톤온톤으로 이어져 전체 룩이 정돈돼 보이고, 오래 앉아 있어도 흐트러짐이 덜해요."},
            {"role":"user", "content": reason_input},
        ]
    )
    return response.choices[0].message.content.strip()

def refine_tpo_text(tpo_raw: str):
    print("👉 Refining TPO text...")
    client = get_client()

    # TPO 추출을 위한 시스템 프롬프트 (별도 정의 필요)
    TPO_REFINE_PROMPT = """
당신은 사용자의 요청에서 핵심 TPO(상황, 장소, 목적)만 추출하여 짧고 간결한 키워드로 변환하는 전문가입니다.
- 불필요한 서술어(~해줘, ~하고 싶어 등)를 제거하세요.
- '~룩', '~상황' 등의 명사형 키워드로 요약하세요.
- 출력은 반드시 정제된 텍스트만 반환하세요.
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.0,  # 일관성을 위해 0으로 설정
        messages=[
            {"role": "system", "content": TPO_REFINE_PROMPT},
            # Few-shot 예시로 가이드 제공
            {"role": "user", "content": "남자친구와 데이트할 때 입을 옷 추천해줘"},
            {"role": "assistant", "content": "남자친구와 데이트룩"},
            {"role": "user", "content": "결혼식 하객으로 가는데 깔끔하게 입고 싶어"},
            {"role": "assistant", "content": "결혼식 하객룩"},
            {"role": "user", "content": "회사 면접 보러 갈 때 신뢰감을 주는 복장"},
            {"role": "assistant", "content": "회사 면접룩"},
            # 실제 입력값
            {"role": "user", "content": tpo_raw},
        ]
    )
    return response.choices[0].message.content.strip()

def update_query_with_feedback(prev_query: str, feedback_text: str):
    print("👉 Query is being updated with feedback...")
    client = get_client()
    payload = {
        "PERSONA_SUMMARY": prev_query,   # ✅ 프롬프트 문구에 맞춤
        "user_feedback": feedback_text   # ✅ 프롬프트 문구에 맞춤
    }
    res = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        response_format={"type":"json_object"},
        messages=[
            {"role":"system", "content": UPDATE_QUERY_PROMPT},
            {"role":"user", "content": json.dumps(payload, ensure_ascii=False)}
        ]
    )
    return json.loads(res.choices[0].message.content)["updated_query"]

# -------------------------------
# 4. Retrieve
# -------------------------------

def retrieve_from_faiss(persona, model, index, metas, query_text, negatives, user_gender, hard_constraints=None, topk=5):
    # dense search (faiss)
    qvec = embed_text(query_text, model).reshape(1, -1)
    faiss.normalize_L2(qvec)

    search_k = min(len(metas), topk * 30) # 10개
    D, I = index.search(qvec, search_k)
    print(f"DEBUG: {len(I[0])} items found in FAISS") # 1. 검색된 개수 확인

    results = []
    for rank_i, idx in enumerate(I[0]):
        if idx < 0:
            continue
        meta = metas[idx].copy()

        # gender filter
        if user_gender == "남자" and meta.get("gender") == "여":
            continue
        if user_gender == "여자" and meta.get("gender") == "남":
            continue

        # persona filter
        if persona == "pme" or persona == "promie":
            if meta.get("style") == "스트릿":
                continue
            
        # ---------- sub category ----------
        if hard_constraints["forced_sub_categories"]:
            sub_cat = meta.get("sub_cat_name")
            if sub_cat != hard_constraints["forced_sub_categories"][-1]: # 여러 개가 있을 수 있는데 마지막 걸로 
                continue
        
        # ---------- color ----------
        if hard_constraints["preferred_colors"]:
            color = meta.get("color")
            main_color = color.split(", ")[0] # 주요 색상
            print(f"main_color: {main_color}")
            
            if not any(pref in main_color for pref in hard_constraints['preferred_colors']): # preferred colors의 요소가 color에 포함돼 있지 않으면 continue
                continue

        # ---------- fit ----------
        if hard_constraints["preferred_fits"]:
            fit = meta.get("fit")
            if fit != hard_constraints["preferred_fits"][-1]: # 여러 개가 있을 수 있는데 마지막 걸로 
                continue

        # ---------- pattern ----------
        if hard_constraints["preferred_patterns"]:
            pattern = meta.get("pattern")
            if pattern != hard_constraints["preferred_patterns"][-1]: # 여러 개가 있을 수 있는데 마지막 걸로 
                continue

        # ---------- texture ----------
        if hard_constraints["preferred_textures"]:
            texture = meta.get("texture")
            if texture != hard_constraints["preferred_textures"][-1]: # 여러 개가 있을 수 있는데 마지막 걸로 
                continue

        # negative filter
        if meta.get("fit") in negatives["fit"]:
            continue
        if meta.get("pattern") in negatives["pattern"]:
            continue
        if meta.get("price_raw", 0) > negatives["price_raw"]:
            continue

        meta["score"] = float(D[0][rank_i])
        results.append(meta)
        if len(results) >= topk:
            break
        
    print(f"DEBUG: {len(results)} items are left") # 최종 검색된 개수 확인
    return results

def retrieve_candidates_by_category(persona, category, style_query, tpo_query, db_cache, model, negatives, user_gender, hard_constraints=None, topk=5):
    print("👉 Retrieve items...")

    style_items = []
    if db_cache["style"][category] is not None:
        style_items = retrieve_from_faiss(
            persona,
            model,
            db_cache["style"][category]["index"],
            db_cache["style"][category]["meta"],
            style_query,
            negatives,
            user_gender,
            hard_constraints,
            topk
        )

    tpo_items = retrieve_from_faiss(
        persona,
        model,
        db_cache["tpo"][category]["index"],
        db_cache["tpo"][category]["meta"],
        tpo_query,
        negatives,
        user_gender,
        hard_constraints,
        topk
    )

    return style_items, tpo_items

def print_candidates(title, items, limit=5):
    print(f"\n--- {title} (n={len(items)}) ---")
    for i, x in enumerate(items[:limit], 1):
        print(
            f"[{i}] product_id={x.get('product_id')} | "
            f"gender={x.get('gender')} | "
            f"price={x.get('price')} | "
            f"tpo={x.get('tpo')} | "
            f"style={x.get('style')} | "
            f"fit={x.get('fit')} | "
            f"pattern={x.get('pattern')} | "
            f"score={x.get('score', 0):.4f}"
        )

def print_results(i, item, reason):
    print(f"\n[{i}] product_id={item.get('product_id')}")
    print(f"sub_cat={item.get('sub_cat_name')}")
    print(f"color={item.get('color')}")
    print(f"image={item.get('img_url')}")
    print(f"price={item.get('price')}")
    print(f"fit={item.get('fit')}")
    print(f"pattern={item.get('pattern')}")
    print(f"description={item.get('description')}")
    print(f"👉 이유: {reason}")

def fuse_candidates(style_items, tpo_items, conflict, topk=5):
    merged = {}

    # 1) score 수집 (item 단위로)
    for item in style_items:
        pid = str(item["product_id"])
        merged.setdefault(pid, {"item": item, "style_sim": 0.0, "tpo_sim": 0.0})
        merged[pid]["style_sim"] = item["score"] # normalize + IndexFlatP이므로 D는 거리가 아니라 코사인 유사도

    for item in tpo_items:
        pid = str(item["product_id"])
        merged.setdefault(pid, {"item": item, "style_sim": 0.0, "tpo_sim": 0.0})
        merged[pid]["tpo_sim"] = item["score"]

    candidates = list(merged.values())
    if not candidates:
        return []

    # 3) normalize 함수
    def normalize(vals):
        mx, mn = max(vals), min(vals)
        if mx - mn < 1e-6:
            return [0.5 for _ in vals]  # 전부 비슷하면 중립값
        return [(v - mn) / (mx - mn) for v in vals]

    style_vals = [v["style_sim"] for v in merged.values()]
    tpo_vals   = [v["tpo_sim"]   for v in merged.values()]

    style_norm = normalize(style_vals)
    tpo_norm   = normalize(tpo_vals)

    # 4) 가중치 (conflict-aware)
    alpha, beta = (0.0, 1.0) if conflict else (0.5, 0.5)

    # 5) fused score 계산
    fused = []
    for (pid, v), s, t in zip(merged.items(), style_norm, tpo_norm):
        fused_score = alpha * s + beta * t
        fused.append((fused_score, v["item"]))

    fused.sort(key=lambda x: x[0], reverse=True)

    # 6) TOP-K item만 반환
    return [item for _, item in fused[:topk]]


def print_fused_candidates(items, title="FUSED_CANDIDATES"):
    print(f"\n=== {title} (n={len(items)}) ===")
    for i, x in enumerate(items, 1):
        print(
            f"[{i}] product_id={x.get('product_id')} | "
            f"sub_category={x.get('sub_cat_name')} | "
            f"img={x.get('img_url')} |"
            f"style={x.get('style')} | "
            f"tpo={x.get('tpo')} | "
            f"fit={x.get('fit')} | "
            f"pattern={x.get('pattern')} | "
            f"price={x.get('price')} | "
            f"score={x.get('score', 'N/A')}"
        )

def lookup_item_by_id(product_id, candidates):
    pid = str(product_id)
    for item in candidates:
        if str(item.get("product_id")) == pid:
            return item
    print(f"⚠️ lookup_item_by_id: product_id={product_id} not found")
    return None


# --------------------------------------------------------------
# 5. build context: add selected item, context, summary
# --------------------------------------------------------------
def add_selected_item(category, selected_items: list, chosen_item: dict):
    """
    selected_items: 유저가 '확정'한 아이템들만 저장
    조화 기반 reranking의 기준(anchor)
    """
    selected_items[category] = {
        "product_id": str(chosen_item.get("product_id")),
        "product_name": chosen_item.get("product_name"),
        "category": chosen_item.get("main_cat_name"),
        "sub_category": chosen_item.get("sub_cat_name"),
        "brand": chosen_item.get("brand"),
        "price": chosen_item.get("price"),
        "item_url": chosen_item.get("item_url"),
        "img_url": chosen_item.get("img_url"),
        "style": chosen_item.get("style_name"),
        "fit": chosen_item.get("fit"),
        "texture": chosen_item.get("texture"),
        "pattern": chosen_item.get("pattern"),
        "color": chosen_item.get("color"),      # 있으면
        "tpo": chosen_item.get("tpo"),
        "description": chosen_item.get("description")
    }

def append_selected_context(selected_context_text: str, chosen_item: dict) -> str:
    # 사람이 읽을 컨텍스트(이유 생성/리랭크에서 쓰기)
    line = f"- {chosen_item.get('main_cat_name')}({chosen_item.get('sub_cat_name')}): {chosen_item.get('description')}"
    return (selected_context_text + "\n" + line).strip()


# -----------------------
# 6. update feedback 
# -----------------------

def init_hard_constraints():
    return {
        "forced_sub_categories": [],

        "preferred_colors": [],

        "preferred_fits": [],

        "preferred_patterns": [],

        "preferred_textures": [],
    }


def apply_feedback_to_constraints(feedback_obj, hard_constraints):
    intent = feedback_obj["intent"]

    if intent == "sub_cat_name":
        hard_constraints["forced_sub_categories"].extend(
            feedback_obj.get("include", [])
        )

    elif intent == "color":
        hard_constraints["preferred_colors"].extend(
            feedback_obj.get("include", [])
        )
    elif intent == "fit":
        hard_constraints["preferred_fits"].extend(
            feedback_obj.get("include", [])
        )

    elif intent == "pattern":
        hard_constraints["preferred_patterns"].extend(
            feedback_obj.get("include", [])
        )

    elif intent == "texture":
        hard_constraints["preferred_textures"].extend(
            feedback_obj.get("include", [])
        )

