import requests
import json
from typing import Dict, List, Any
from utils import DETAIL_MAP, extract_category_from_input, refine_tpo_text

BASE_URL = "http://127.0.0.1:8000"

class DemoClient:
    """데모데이용 멀티 세션 클라이언트 (test_client.py의 모든 기능 포함)"""
    
    def __init__(self):
        self.session_id = None
        self.base_url = BASE_URL
        self.user_tpo = None
    
    def print_separator(self, title="", char="=", length=60):
        """구분선 출력"""
        if title:
            print(f"\n{char * length}")
            print(f" {title}")
            print(f"{char * length}\n")
        else:
            print(f"\n{char * length}\n")
    
    def print_response(self, response: requests.Response, show_full=False):
        """응답 결과 출력"""
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if show_full:
                print(f"Response:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
            else:
                print(f"Response: {json.dumps(data, ensure_ascii=False)}")
        else:
            print(f"Error: {response.text}")
    
    def get_headers(self):
        """API 호출용 헤더 반환"""
        if not self.session_id:
            raise Exception("Session not created. Call create_session() first.")
        return {"X-Session-ID": self.session_id}
    
    def health_check(self):
        """헬스 체크"""
        self.print_separator("헬스 체크")
        
        try:
            response = requests.get(self.base_url, timeout=5)
            self.print_response(response)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ 서버 정상 작동")
                print(f"   - 메시지: {data['message']}")
                print(f"   - 활성 세션 수: {data.get('active_sessions', 'N/A')}")
                return True
        except requests.exceptions.ConnectionError:
            print("❌ 서버 연결 실패")
            print("   서버가 실행 중인지 확인하세요: http://127.0.0.1:8000")
            return False
        
        return False
    
    def create_session(self):
        """1. 세션 생성 (멀티 세션 지원)"""
        self.print_separator("TEST 1: 세션 생성")
        
        print("⏳ 세션 생성 중...")
        try:
            response = requests.post(f"{self.base_url}/session/create", timeout=10)
            self.print_response(response)
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data["session_id"]
                print(f"\n✅ 세션 생성 성공!")
                print(f"   - Session ID: {self.session_id[:8]}...")
                return True
            else:
                print(f"\n❌ 세션 생성 실패")
                return False
        except Exception as e:
            print(f"❌ 세션 생성 중 오류: {str(e)}")
            return False
    
    def persona(self):
        """2. 페르소나 선택 테스트"""
        self.print_separator("TEST 2: 페르소나 선택")
        
        print("사용 가능한 페르소나:")
        print("  1. pme     - 김프메 (남, 24) - 프레피/단정")
        print("  2. nowon   - 정노원 (남, 27) - 캐주얼")
        print("  3. ob      - 최오비 (남, 26) - 스트릿")
        print("  4. moyon  - 이모연 (여, 24) - 힙한/보이시")
        print("  5. seoksa  - 주석사 (여, 25) - 캐주얼")
        print("  6. promi  - 정프로미 (여, 23) - 페미닌")
        
        persona = input("\n✨ 당신의 페르소나를 선택해주세요 (예: pme): ").strip().lower()
        
        if persona not in ["pme", "nowon", "ob", "moyon", "seoksa", "promi"]:
            print(f"⚠️ 잘못된 페르소나입니다. 기본값 'pme'를 사용합니다.")
            persona = "pme"
        
        print(f"✨ 선택한 페르소나: {persona}")
        
        try:
            response = requests.post(
                f"{self.base_url}/session/persona",
                json={"persona": persona},
                headers=self.get_headers(),
                timeout=10
            )
            self.print_response(response)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ 페르소나 설정 성공!")
                print(f"   - 페르소나: {data['persona']}")
                print(f"   - 성별: {data['user_gender']}")
                return True, persona
            return False, None
        except Exception as e:
            print(f"❌ 페르소나 설정 중 오류: {str(e)}")
            return False, None
    
    def tpo(self, persona):
        """3. TPO 설정 테스트"""
        self.print_separator("TEST 3: TPO 설정")
        
        print("TPO(Time, Place, Occasion)를 입력하세요.")
        print("예시:")
        print("  - 대학교 수업 듣고 친구랑 저녁 약속")
        print("  - 친구 생일파티")
        print("  - 회사 면접")
        print("  - 데이트")
        
        tpo = input("\n💁‍♀️ 오늘의 TPO는 무엇인가요?: ").strip()
        
        while not tpo:
            print("⚠️ TPO는 필수 입력입니다.")
            tpo = input("💁‍♀️ 오늘의 TPO는 무엇인가요?: ").strip()
        
        print(f"💁‍♀️ 입력한 TPO: {tpo}")
        self.user_tpo = tpo
        
        try:
            response = requests.post(
                f"{self.base_url}/session/tpo",
                json={"tpo": tpo, "persona": persona},
                headers=self.get_headers(),
                timeout=30
            )
            self.print_response(response)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ TPO 설정 성공!")
                print(f"   - 파싱된 키워드: {', '.join(data['parsed_tpo'])}")
                print(f"   - 충돌 여부: {data['conflict']}")
                return True
            return False
        except Exception as e:
            print(f"❌ TPO 설정 중 오류: {str(e)}")
            return False
    
    def negatives(self):
        """4. 비선호 요소 조사 테스트"""
        self.print_separator("TEST 4: 비선호 요소 조사")
        
        print("비선호하는 요소를 설정하세요 (없으면 Enter)")
        
        # Fit
        fit_input = input("\n[핏] 비선호하는 핏을 입력해주세요! [ 오버사이즈 | 슬림 | 없음 ]")
        if "오버사이즈" in fit_input or "오버 사이즈" in fit_input:
            fit = "오버사이즈"
        elif "슬림" in fit_input:
            fit = "슬림"
        else:
            fit = ""
        if fit not in ["오버사이즈", "슬림", ""]:
            print(f"⚠️ 잘못된 입력입니다. 비선호 핏을 설정하지 않습니다.")
            fit = ""
        fit = fit if fit else None
        
        # Pattern  
        pattern_input = input("\n[패턴] 비선호하는 패턴을 입력해주세요! [ 로고 | 스트라이프 | 체크 ]")
        if "로고" in pattern_input:
            pattern = "로고"
        elif "스트라이프" in pattern_input or "줄무늬" in pattern_input:
            pattern = "스트라이프"
        elif "체크" in pattern_input:
            pattern = "체크"
        else:
            pattern = ""
        if pattern not in ["로고", "스트라이프", "체크", ""]:
            print(f"⚠️ 잘못된 입력입니다. 비선호 패턴을 설정하지 않습니다.")
            pattern = ""
        pattern = pattern if pattern else None
        
        # Price
        price_input = input("\n[가격] 옷 한 벌에 최대 얼마까지 사용하시나요? [ 10만원 | 20만원 | 30만원 | 50만원 | 그 이상 ]")
        if "10" in price_input or "십만원" in price_input or "십 만원" in price_input:
            price_threshold = 100000
        elif "20" in price_input or "이십만원" in price_input or "이십 만원" in price_input:
            price_threshold = 200000
        elif "30" in price_input or "삼십만원" in price_input or "삼십 만원" in price_input:
            price_threshold = 300000
        elif "50" in price_input or "오십만원" in price_input or "오십 만원" in price_input:
            price_threshold = 500000
        elif "이상" in price_input or "무제한" in price_input or "제한없" in price_input:
            price_threshold = 999999999  # 사실상 제한 없음
        else:
            price_threshold = 999999999  # 기본값: 제한 없음          
        
        negatives = {
            "fit": fit,
            "pattern": pattern,
            "price_threshold": price_threshold
        }
        
        print(f"\n설정된 비선호 요소:")
        print(f"   - 핏: {negatives['fit'] if negatives['fit'] else '없음'}")
        print(f"   - 패턴: {negatives['pattern'] if negatives['pattern'] else '없음'}")
        print(f"   - 가격 상한: {negatives['price_threshold']:,}원")
        
        try:
            response = requests.post(
                f"{self.base_url}/session/negatives",
                json=negatives,
                headers=self.get_headers(),
                timeout=10
            )
            self.print_response(response)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ 비선호 설정 성공!")
                print(f"   - 필터링 적용: {data['negatives']}")
                return True
            return False
        except Exception as e:
            print(f"❌ 비선호 설정 중 오류: {str(e)}")
            return False
    
    def session_status(self):
        """5. 세션 상태 확인 테스트"""
        self.print_separator("TEST 5: 세션 상태 확인")
        
        try:
            response = requests.get(
                f"{self.base_url}/session/status",
                headers=self.get_headers(),
                timeout=10
            )
            self.print_response(response, show_full=True)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ 세션 상태:")
                print(f"   - 초기화 완료: {data['initialized']}")
                print(f"   - 현재 카테고리: {data['current_category']}")
                print(f"   - 진행도: {data['category_index']}/{data['total_categories']}")
                print(f"   - 완료 여부: {data['is_complete']}")
                return True
            return False
        except Exception as e:
            print(f"❌ 세션 상태 확인 중 오류: {str(e)}")
            return False
    
    def recommend_and_select(self):
        """6. 순차적 추천 및 선택 (사용자 입력) - 이전 추천 선택 옵션 추가"""
        self.print_separator("TEST 6: 순차적 추천 및 선택")
        
        categories_completed = 0
        previous_candidates = None  # 이전 추천 캐싱
        
        while True:
            # 현재 상태 확인
            try:
                status_response = requests.get(
                    f"{self.base_url}/session/status",
                    headers=self.get_headers(),
                    timeout=10
                )
                if status_response.status_code != 200:
                    print("❌ 상태 확인 실패")
                    break
                
                status = status_response.json()
                
                if status["is_complete"]:
                    print("\n🎉 모든 카테고리 완료!")
                    break
                
                current_category = status["current_category"]
                progress = f"({status['category_index'] + 1}/{status['total_categories']})"
                
                self.print_separator(f"카테고리: {current_category} {progress}", char="-", length=60)
                
                # 추천 받기
                print(f"📦 {current_category} 추천 중... (20-30초 소요)")
                rec_response = requests.post(
                    f"{self.base_url}/recommend/next",
                    headers=self.get_headers(),
                    timeout=120
                )
                
                if rec_response.status_code != 200:
                    print(f"❌ 추천 실패: {rec_response.text}")
                    break
                
                rec_data = rec_response.json()
                new_candidates = rec_data["candidates"]  # 새로운 추천
                
                # 복구 또는 빈 결과 메시지 확인
                if rec_data.get("message"):
                    print(f"\n💬 {rec_data['message']}")
                
                if rec_data.get("recovered_from_previous"):
                    print("⚠️ 이전 추천이 복구되었습니다.")
                
                # 추천 결과가 없는 경우 처리
                if not new_candidates:
                    print(f"\n⚠️ {current_category}에 추천 아이템이 없습니다.")
                    
                    # 이전 추천이 있는 경우 복구 옵션 제공
                    if previous_candidates:
                        print("\n💡 이전에 추천된 아이템 목록이 있습니다.")
                        print("\n옵션:")
                        print("  1. 이전 추천 목록에서 선택하기")
                        print("  2. 피드백으로 조건 완화하기")
                        
                        choice = input("\n선택 (1/2): ").strip()
                        
                        if choice == "1":
                            # 이전 추천 목록 복원
                            new_candidates = previous_candidates
                            print(f"\n🔄 이전 추천 목록을 복원했습니다. ({len(new_candidates)}개)")
                            
                        elif choice == "2":
                            # 피드백으로 조건 완화
                            print("\n📝 조건을 완화하기 위한 피드백을 입력하세요.")
                            print("\n어떤 조건을 바꾸고 싶나요? [ 세부 카테고리 / 색상 / 소재 ] 중에서 하나를 골라주세요.")
                            
                            fb_type_input = input("\n피드백 타입: ").strip()
                            
                            if "세부 카테고리" in fb_type_input or "세부카테고리" in fb_type_input:
                                fb_type = "sub_cat_name"
                                fb_type_text = "세부 카테고리"
                            elif "색상" in fb_type_input or "색" in fb_type_input:
                                fb_type = "color"
                                fb_type_text = "색상"
                            elif "소재" in fb_type_input:
                                fb_type = "texture"
                                fb_type_text = "소재"
                            else:
                                print("이런! 잘못된 피드백 타입을 입력하셨습니다. 다시 시도해주세요.")    
                                continue
                            
                            if fb_type not in ["sub_cat_name", "color", "texture"]:
                                print("⚠️ 잘못된 피드백 타입입니다. 다시 시도하세요.")
                                continue
                            
                            print(f"{fb_type_input} 조건을 수정한 {current_category}를 다시 추천합니다...")
                            options = DETAIL_MAP[fb_type][current_category]
                            options_text = " | ".join(options)
                            feedback = input(f"어떤 {fb_type_text}을 추천받고 싶으신가요? 아래 보기 중에서 하나를 골라주세요!\n{options_text}: ")
                            fb_value = extract_category_from_input(feedback, options) # list
                            
                            if not fb_value:
                                print("⚠️ 값을 입력하지 않았습니다.")
                                continue
                            
                            # 피드백 API 호출
                            fb_response = requests.post(
                                f"{self.base_url}/feedback",
                                json={"type": fb_type, "value": fb_value},
                                headers=self.get_headers(),
                                timeout=10
                            )
                            
                            if fb_response.status_code == 200:
                                print(f"\n✅ 피드백 반영 완료!")
                                print(f"   타입: {fb_type}")
                                print(f"   값: {', '.join(fb_value)}")
                                print("\n🔄 재추천을 받습니다...")
                                continue  # 다시 추천 루프로
                            else:
                                print(f"❌ 피드백 실패: {fb_response.text}")
                                continue
                            
                        else:
                            # 종료
                            return False
                    
                    else:
                        # 이전 추천이 없는 경우
                        print("\n옵션:")
                        print("  1. 비선호 조건 완화하기")
                        
                        choice = input("\n선택 (1/종료): ").strip()

                        if choice == "1":
                            self.negatives()
                            continue
                        else:
                            return False
                        
                if new_candidates and previous_candidates:
                    print(f"\n✨ 새로운 추천 아이템 {len(new_candidates)}개를 받았습니다!")
                    print(f"💡 이전 추천 아이템 {len(previous_candidates)}개도 함께 보여드립니다.\n")
                    
                    # 새로운 추천 + 이전 추천을 하나의 리스트로 결합
                    # 각 아이템에 출처 표시를 위한 정보 추가
                    candidates = []
                    
                    # 새로운 추천 추가 (앞부분)
                    for item in new_candidates:
                        item_copy = item.copy()
                        item_copy['_source'] = 'new'
                        candidates.append(item_copy)
                    
                    # 이전 추천 추가 (뒷부분)
                    for item in previous_candidates:
                        item_copy = item.copy()
                        item_copy['_source'] = 'previous'
                        candidates.append(item_copy)
                    
                else:
                    # 이전 추천이 없거나 새 추천이 없으면 그대로 사용
                    candidates = new_candidates
                    for item in candidates:
                        item['_source'] = 'new'
                
                # 현재 사용 중인 새로운 추천을 이전 추천으로 백업
                if new_candidates:
                    previous_candidates = new_candidates
                
                # 추천 결과 출력 (출처 표시 포함)
                print(f"\n✨ 총 추천 아이템 {len(candidates)}개:\n")
                for i, item in enumerate(candidates, 1):
                    source_label = "🆕 [새로운 추천]" if item.get('_source') == 'new' else "📌 [이전 추천]"
                    
                    print(f"{source_label} [{i}] {item['product_name']}")
                    print(f"    브랜드: {item['brand']}")
                    print(f"    가격: {item['price']}")
                    print(f"    색상: {item.get('color', 'N/A')}")
                    print(f"    핏: {item.get('fit', 'N/A')}")
                    print(f"    패턴: {item.get('pattern', 'N/A')}")
                    print(f"    추천 이유: {item['reason']}")
                    print(f"    item_url: {item.get('item_url')}")
                    print()
                
                # 현재 사용 중인 추천을 이전 추천으로 백업
                if new_candidates:
                    previous_candidates = new_candidates
                
                # 사용자 입력 받기 (선택 또는 피드백)
                while True:
                    print("\n원하는 작업을 선택하세요:")
                    print(f"  [1-{len(candidates)}]: 해당 번호의 아이템 선택")
                    print("  [f]: 피드백하여 재추천 받기")
                    
                    user_input = input("\n입력: ").strip().lower()
                    
                    # 아이템 선택
                    if user_input.isdigit():
                        idx = int(user_input) - 1
                        if 0 <= idx < len(candidates):
                            selected_item = candidates[idx]
                            
                            print(f"\n🔘 선택: [{idx+1}] {selected_item['product_name']}")
                            confirm = input("이 아이템을 선택하시겠습니까? (y/n): ").strip().lower()
                            
                            if confirm != 'y':
                                print("선택을 취소합니다.")
                                continue
                            
                            # 아이템 선택 API 호출
                            select_response = requests.post(
                                f"{self.base_url}/select",
                                json={"product_id": selected_item["product_id"]},
                                headers=self.get_headers(),
                                timeout=10
                            )
                            
                            if select_response.status_code != 200:
                                print(f"❌ 선택 실패: {select_response.text}")
                                continue
                            
                            select_data = select_response.json()
                            print(f"\n✅ {current_category} 선택 완료: {selected_item['product_name']}")
                            
                            if select_data["next_category"]:
                                print(f"➡️  다음 카테고리: {select_data['next_category']}")
                            
                            categories_completed += 1
                            previous_candidates = None  # 다음 카테고리로 넘어가면 캐시 초기화
                            break  # 다음 카테고리로
                        else:
                            print(f"⚠️ 1~{len(candidates)} 사이의 숫자를 입력하세요.")
                    
                    # 피드백
                    elif user_input == "f":
                        print("\n어떤 조건을 바꾸고 싶나요? [ 세부 카테고리 / 색상 / 소재 ] 중에서 하나를 골라주세요.")
                        
                        fb_type_input = input("\n피드백 타입: ").strip()
                        
                        if "세부 카테고리" in fb_type_input or "세부카테고리" in fb_type_input:
                            fb_type = "sub_cat_name"
                            fb_type_text = "세부 카테고리"
                        elif "색상" in fb_type_input or "색" in fb_type_input:
                            fb_type = "color"
                            fb_type_text = "색상"
                        elif "소재" in fb_type_input:
                            fb_type = "texture"
                            fb_type_text = "소재"
                        else:
                            print("이런! 잘못된 피드백 타입을 입력하셨습니다. 다시 시도해주세요.")    
                            continue
                        
                        if fb_type not in ["sub_cat_name", "color", "texture"]:
                            print("⚠️ 잘못된 피드백 타입입니다. 다시 시도하세요.")
                            continue
                        
                        print(f"{fb_type_text} 조건을 수정한 {current_category}를 다시 추천합니다...")
                        options = DETAIL_MAP[fb_type][current_category]
                        options_text = " | ".join(options)
                        feedback = input(f"어떤 {fb_type_input}을 추천받고 싶으신가요? 아래 보기 중에서 하나를 골라주세요!\n{options_text}: ")
                        fb_value = extract_category_from_input(feedback, options) # list
                        
                        if not fb_value:
                            print("⚠️ 값을 입력하지 않았습니다.")
                            continue
                        
                        # 피드백 API 호출
                        fb_response = requests.post(
                            f"{self.base_url}/feedback",
                            json={"type": fb_type, "value": fb_value},
                            headers=self.get_headers(),
                            timeout=10
                        )
                        
                        if fb_response.status_code == 200:
                            print(f"\n✅ 피드백 반영 완료!")
                            print(f"   타입: {fb_type}")
                            print(f"   값: {', '.join(fb_value)}")
                            print("\n🔄 재추천을 받습니다...")
                            break  # 다시 추천 루프로
                        else:
                            print(f"❌ 피드백 실패: {fb_response.text}")
                    
                    else:
                        print("⚠️ 올바른 입력이 아닙니다.")
            
            except Exception as e:
                print(f"❌ 추천 과정 중 오류: {str(e)}")
                break
        
        return categories_completed == 5
    
    def test_7_show_all(self):
        """7. 최종 결과 조회 테스트"""
        self.print_separator("TEST 7: 최종 결과 조회")
        
        try:
            response = requests.get(
                f"{self.base_url}/show_all",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                refined_tpo = refine_tpo_text(self.user_tpo)
                print(f"✅ 최종 코디 완성!\n")
                print(f"📍 TPO: {refined_tpo}")
                print(f"📦 선택된 아이템: {data['total_count']}개\n")
                
                for category, item in data["selected_items"].items():
                    print(f"{'='*60}")
                    print(f"[{category}]")
                    print(f"  • 상품명: {item['product_name']}")
                    print(f"  • 브랜드: {item['brand']}")
                    print(f"  • 가격: {item['price']}")
                    print(f"  • 상품 URL: {item['item_url']}")
                    print(f"  • 이미지 URL: {item['img_url']}")
                    print()
                
                print("="*60)
                return True
            elif response.status_code == 400:
                print("⚠️ 아직 모든 카테고리를 완료하지 않았습니다.")
                print(f"   {response.json()['detail']}")
                return False
            else:
                print(f"❌ 최종 결과 조회 실패: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 최종 결과 조회 중 오류: {str(e)}")
            return False
    
    def delete_session(self):
        """세션 삭제"""
        if self.session_id:
            try:
                requests.delete(
                    f"{self.base_url}/session/delete",
                    headers=self.get_headers(),
                    timeout=5
                )
                print(f"\n🗑️ 세션 삭제 완료")
            except:
                pass  # 세션 삭제 실패는 무시
            finally:
                self.session_id = None
    
    def run_full_test(self):
        """전체 테스트 실행 (대화형) - test_client.py와 동일"""
        self.print_separator("👗 Fashion Recommendation API - 대화형 테스트 (멀티 세션)", char="=", length=70)
        print("페르소나와 TPO를 입력하여 맞춤 코디를 추천받으세요!")
        print("각 카테고리마다 아이템을 직접 선택하거나 피드백할 수 있습니다.")
        self.print_separator(char="=", length=70)
        
        # 헬스 체크
        if not self.health_check():
            print("\n❌ 서버가 실행되지 않았습니다. 테스트를 종료합니다.")
            return False
        
        # 1. 세션 생성 (멀티 세션 지원!)
        if not self.create_session():
            return False
        
        try:
            # 2. 페르소나 선택
            persona_success, persona = self.persona()
            if not persona_success or not persona:
                print("\n❌ 페르소나 선택 실패. 테스트를 종료합니다.")
                return False
            
            # 3. TPO 설정
            if not self.tpo(persona):
                return False
            
            # 4. 비선호 요소 설정
            if not self.negatives():
                return False
            
            # 5. 세션 상태 확인
            self.session_status()
            
            # 6. 추천 및 선택 (대화형)
            if not self.recommend_and_select():
                print("\n⚠️ 추천 프로세스가 중단되었습니다.")
                return False
            
            # 7. 최종 결과
            self.test_7_show_all()
            
            self.print_separator("🎉 코디 추천이 완료되었습니다!", char="=", length=70)
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️ 사용자가 중단했습니다.")
            return False
        except Exception as e:
            print(f"\n❌ 예상치 못한 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 세션 삭제
            self.delete_session()

def main_menu():
    """메인 메뉴 - 반복 실행 가능"""
    print("\n" + "="*70)
    print("    👗 Fashion Recommendation System - 데모데이 버전 (멀티 세션)")
    print("="*70)
    
    while True:
        print("\n메뉴:")
        print("  1. 새로운 코디 추천 받기")
        print("  2. 서버 상태 확인")
        print("  3. 종료")
        
        choice = input("\n선택 (1/2/3): ").strip()
        
        if choice == "1":
            client = DemoClient()
            client.run_full_test()
            
            # 다시 실행 여부 확인
            print("\n" + "-"*70)
            again = input("다른 코디를 추천받으시겠습니까? (y/n): ").strip().lower()
            if again != 'y':
                print("\n감사합니다! 👋")
                break
        
        elif choice == "2":
            client = DemoClient()
            client.health_check()
        
        elif choice == "3":
            print("\n감사합니다! 👋")
            break
        
        else:
            print("⚠️ 올바른 선택이 아닙니다.")

if __name__ == "__main__":
    import sys
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--quick":
            print("⚡ 빠른 테스트 모드는 전체 모드를 사용하세요.")
            main_menu()
        else:
            main_menu()
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자가 중단했습니다.")
        import sys
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
