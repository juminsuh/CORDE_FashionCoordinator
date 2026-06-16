from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from urllib.parse import unquote
from typing import List, Dict, Optional, Any
import uvicorn
from contextlib import asynccontextmanager
import uuid
from datetime import datetime, timedelta
import gc
import torch
from fastapi.middleware.cors import CORSMiddleware

# 기존 utils, prompt 임포트
from utils import *
from prompt import *

# ===============================
# Session State (멀티 세션 지원)
# ===============================
class SessionState:
    def __init__(self):
        self.model = None
        self.db_cache = None
        self.persona = None
        self.user_gender = None
        self.tpo_raw = None
        self.refined_tpo = None
        self.parsed_tpo = []
        self.conflict = False
        self.selected_items = {}
        self.selected_context_text = ""
        self.hard_constraints_by_category = {}
        self.negatives = {"fit": [], "pattern": [], "price_raw": 500000}
        self.base_style_query = ""
        self.base_tpo_query = ""
        # 최근 추천 결과 캐시 (카테고리별)
        self.recent_recommendations = {}
        # 이전 추천 백업 (피드백으로 인해 빈 결과가 나올 때 사용)
        self.previous_recommendations = {}
        # 현재 진행 중인 카테고리
        self.current_category_index = 0
        self.categories = ["상의", "아우터", "바지", "신발", "가방"]
        # 세션 메타 정보
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        
    def reset_state_only(self):
        """상태만 초기화 (모델/DB는 유지)"""
        self.persona = None
        self.user_gender = None
        self.tpo_raw = None
        self.refined_tpo = None
        self.parsed_tpo = []
        self.conflict = False
        self.selected_items = {}
        self.selected_context_text = ""
        self.hard_constraints_by_category = {}
        self.negatives = {"fit": [], "pattern": [], "price_raw": 500000}
        self.base_style_query = ""
        self.base_tpo_query = ""
        self.recent_recommendations = {}
        self.previous_recommendations = {}
        self.current_category_index = 0
        self.last_accessed = datetime.now()
    
    def get_current_category(self):
        """현재 진행 중인 카테고리 반환"""
        if self.current_category_index < len(self.categories):
            return self.categories[self.current_category_index]
        return None
    
    def move_to_next_category(self):
        """다음 카테고리로 이동"""
        self.current_category_index += 1
    
    def is_complete(self):
        """모든 카테고리 완료 여부"""
        return self.current_category_index >= len(self.categories)
    
    def touch(self):
        """세션 접근 시간 갱신"""
        self.last_accessed = datetime.now()

# ===============================
# Global Session Manager
# ===============================
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
        self.global_model = None
        self.global_db_cache = None
        self.max_sessions = 20  # 최대 동시 세션 수
        
    def create_session(self) -> str:
        """새로운 세션 생성"""
        # 세션 수 제한 체크
        if len(self.sessions) >= self.max_sessions:
            # 오래된 세션 먼저 정리 시도
            self.cleanup_old_sessions(max_age_minutes=30)
            
            # 그래도 많으면 에러
            if len(self.sessions) >= self.max_sessions:
                raise HTTPException(
                    status_code=503, 
                    detail=f"Too many active sessions ({len(self.sessions)}). Please try again later."
                )
        
        session_id = str(uuid.uuid4())
        session = SessionState()
        
        # 전역 모델과 DB 공유 (메모리 절약)
        session.model = self.global_model
        session.db_cache = self.global_db_cache
        
        self.sessions[session_id] = session
        print(f"✅ 세션 생성: {session_id[:8]}... (총 세션 수: {len(self.sessions)})")
        return session_id
    
    def get_session(self, session_id: str) -> SessionState:
        """세션 조회"""
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="Session not found. Please create a new session.")
        session = self.sessions[session_id]
        session.touch()
        return session
    
    def delete_session(self, session_id: str):
        """세션 삭제 + 메모리 정리"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # 세션 내부 큰 객체들 정리
            session.recent_recommendations.clear()
            session.previous_recommendations.clear()
            session.selected_items.clear()
            
            del self.sessions[session_id]
            
            # 메모리 정리
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            print(f"🗑️ 세션 삭제: {session_id[:8]}... (총 세션 수: {len(self.sessions)})")
    
    def cleanup_old_sessions(self, max_age_minutes: int = 60):
        """오래된 세션 정리"""
        now = datetime.now()
        to_delete = []
        
        for session_id, session in self.sessions.items():
            age = now - session.last_accessed
            if age > timedelta(minutes=max_age_minutes):
                to_delete.append(session_id)
        
        for session_id in to_delete:
            self.delete_session(session_id)
        
        if to_delete:
            print(f"🧹 오래된 세션 {len(to_delete)}개 정리 완료")
        
        return len(to_delete)
    
    def load_global_resources(self):
        """전역 모델과 DB 로드 (서버 시작 시 1회)"""
        print("🚀 전역 리소스 로딩 중...")
        
        # 임베딩 모델 로드
        self.global_model = load_embedding_model()
        
        # DB 캐시 로드
        self.global_db_cache = load_all_dbs(STYLE_DB_ROOT, TPO_DB_ROOT, CATEGORY_ORDER)
        
        print("✅ 전역 리소스 로딩 완료!")
        print(f"   - 모델 디바이스: {'cuda' if torch.cuda.is_available() else 'cpu'}")
        print(f"   - 최대 세션 수: {self.max_sessions}")

# 전역 세션 매니저
session_manager = SessionManager()

# ===============================
# Pydantic Models
# ===============================
class SessionCreateResponse(BaseModel):
    session_id: str
    message: str

class PersonaRequest(BaseModel):
    persona: str

class PersonaResponse(BaseModel):
    persona: str
    user_gender: str

class TPORequest(BaseModel):
    tpo: str
    persona: str

class TPOResponse(BaseModel):
    parsed_tpo: List[str]
    conflict: bool
    refined_tpo: str

class NegativeRequest(BaseModel):
    fit: Optional[List[str]] = None
    pattern: Optional[List[str]] = None
    price_threshold: Optional[int] = None

class NegativeResponse(BaseModel):
    status: str
    negatives: Dict[str, Any]

class CandidateItem(BaseModel):
    product_id: str
    product_name: str
    brand: str
    price: str
    item_url: str
    img_url: str
    score: float
    reason: str
    sub_cat_name: Optional[str] = None
    color: Optional[str] = None
    fit: Optional[str] = None
    pattern: Optional[str] = None
    texture: Optional[str] = None
    description: Optional[str] = None

class CurrentRecommendResponse(BaseModel):
    category: str
    category_index: int
    total_categories: int
    candidates: List[CandidateItem]
    is_last_category: bool
    is_restored_from_previous: bool = False  

class FeedbackRequest(BaseModel):
    type: str
    value: List[str]

class FeedbackResponse(BaseModel):
    status: str
    category: str
    message: str

class SelectRequest(BaseModel):
    product_id: str

class SelectResponse(BaseModel):
    status: str
    category: str
    next_category: Optional[str]
    is_complete: bool

class ShowAllResponse(BaseModel):
    tpo: str
    selected_items: Dict[str, Any]
    total_count: int
    
# ===============================
# Lifespan (startup/shutdown)
# ===============================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 서버 시작 중...")
    session_manager.load_global_resources()
    yield
    # Shutdown
    print("🛑 서버 종료 중...")
    # 모든 세션 정리
    for session_id in list(session_manager.sessions.keys()):
        session_manager.delete_session(session_id)

# ===============================
# FastAPI App
# ===============================
app = FastAPI(
    title="Fashion Recommendation API (Multi-Session + Memory Optimized)",
    description="데모데이용 멀티 세션 + 메모리 최적화 패션 코디 추천 시스템",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CATEGORY_ORDER = ["상의", "아우터", "바지", "신발", "가방"]
STYLE_DB_ROOT = "./faiss/style"
TPO_DB_ROOT = "./faiss/tpo"

# ===============================
# Endpoints
# ===============================

@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "message": "Fashion Recommendation API v3.0 (Multi-Session + Memory Optimized)",
        "status": "running",
        "active_sessions": len(session_manager.sessions),
        "max_sessions": session_manager.max_sessions,
        "docs": "/docs"
    }

@app.post("/session/create", response_model=SessionCreateResponse)
async def create_session():
    """새 세션 생성"""
    try:
        # 오래된 세션 자동 정리 (30분 이상 미사용)
        session_manager.cleanup_old_sessions(max_age_minutes=30)
        
        # 새 세션 생성
        session_id = session_manager.create_session()
        
        # hard_constraints 초기화
        session = session_manager.get_session(session_id)
        for cat in CATEGORY_ORDER:
            session.hard_constraints_by_category[cat] = init_hard_constraints()
        
        return SessionCreateResponse(
            session_id=session_id,
            message="Session created successfully. Use this session_id in X-Session-ID header for all requests."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session creation failed: {str(e)}")

@app.delete("/session/delete")
async def delete_session(session_id: str = Header(..., alias="X-Session-ID")):
    """세션 삭제"""
    try:
        session_manager.delete_session(session_id)
        return {
            "status": "deleted", 
            "message": "Session deleted successfully",
            "active_sessions": len(session_manager.sessions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/reset")
async def reset_session(session_id: str = Header(..., alias="X-Session-ID")):
    """세션 리셋 (상태만 초기화, 모델/DB는 유지)"""
    try:
        session = session_manager.get_session(session_id)
        session.reset_state_only()
        
        # hard_constraints 재초기화
        for cat in CATEGORY_ORDER:
            session.hard_constraints_by_category[cat] = init_hard_constraints()
        
        # 메모리 정리
        gc.collect()
        
        return {
            "status": "reset",
            "message": "Session state reset successfully. Model and DB are still loaded."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/persona", response_model=PersonaResponse)
async def set_persona(request: PersonaRequest, session_id: str = Header(..., alias="X-Session-ID")):
    """페르소나 선택"""
    try:
        session = session_manager.get_session(session_id)
        persona = request.persona.lower()
        
        if persona not in GENDER_MAP:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid persona. Choose from: {list(GENDER_MAP.keys())}"
            )
        
        session.persona = persona
        session.user_gender = GENDER_MAP[persona]
        session.base_style_query = safe_join(PERSONA_MOOD[persona])
        
        return PersonaResponse(
            persona=session.persona,
            user_gender=session.user_gender
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/tpo", response_model=TPOResponse)
async def set_tpo(request: TPORequest, session_id: str = Header(..., alias="X-Session-ID")):
    """TPO 입력 및 파싱"""
    try:
        session = session_manager.get_session(session_id)
        
        if not session.persona:
            raise HTTPException(status_code=400, detail="Persona not set. Call /session/persona first.")
        
        session.tpo_raw = request.tpo
        session.refined_tpo = refine_tpo_text(session.tpo_raw) 
        session.parsed_tpo = parse_tpo(session.tpo_raw)
        session.base_tpo_query = safe_join(session.parsed_tpo)
        session.conflict = judge_conflict(session.persona, session.parsed_tpo)
        
        return TPOResponse(
            parsed_tpo=session.parsed_tpo,
            conflict=session.conflict,
            refined_tpo=session.refined_tpo
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/negatives", response_model=NegativeResponse)
async def set_negatives(request: NegativeRequest, session_id: str = Header(..., alias="X-Session-ID")):
    """비선호 요소 조사 및 설정"""
    try:
        session = session_manager.get_session(session_id)
        
        if not session.persona:
            raise HTTPException(status_code=400, detail="Persona not set. Call /session/persona first.")
        
        session.negatives = {
            "fit": request.fit or [],
            "pattern": request.pattern or [],
            "price_threshold": request.price_threshold if request.price_threshold else 500000
        }

        print(f"🚫 [NEGATIVES SET] fit={session.negatives['fit']}, pattern={session.negatives['pattern']}, price_threshold={session.negatives['price_threshold']}")

        return NegativeResponse(
            status="negatives_set",
            negatives=session.negatives
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend/next", response_model=CurrentRecommendResponse)
async def recommend_next_category(session_id: str = Header(..., alias="X-Session-ID")):
    """
    현재 진행 중인 카테고리에 대한 추천
    순차적 워크플로우: 상의 -> 아우터 -> 바지 -> 신발 -> 가방
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session.persona:
            raise HTTPException(status_code=400, detail="Persona not set. Call /session/persona first.")
        
        if not session.parsed_tpo:
            raise HTTPException(status_code=400, detail="TPO not set. Call /session/tpo first.")
        
        # 현재 카테고리 가져오기
        category = session.get_current_category()
        
        if category is None:
            raise HTTPException(
                status_code=400, 
                detail="All categories completed. Call /show_all to see final results."
            )
        
        # 현재 카테고리의 hard_constraints 가져오기
        hard_constraints = session.hard_constraints_by_category[category]
        
        # 쿼리 준비
        style_query = session.base_style_query
        tpo_query = session.base_tpo_query
        
        # FAISS 검색
        style_items, tpo_items = retrieve_candidates_by_category(
            persona=session.persona,
            category=category,
            style_query=style_query,
            tpo_query=tpo_query,
            db_cache=session.db_cache,
            model=session.model,
            negatives=session.negatives,
            user_gender=session.user_gender,
            hard_constraints=hard_constraints,
            topk=5
        )
        
        # 검색 결과가 없을 경우: 이전 추천 결과 복구
        if not style_items and not tpo_items:
            # 이전 추천이 있는지 확인
            if category in session.previous_recommendations:
                print(f"⚠️ [{category}] 조건을 만족하는 아이템이 없습니다. 이전 추천 결과를 복구합니다.")
                
                # 이전 추천 결과를 현재 추천으로 복원
                session.recent_recommendations[category] = session.previous_recommendations[category].copy()
                
                # 이전 candidates 복구
                previous_candidates = list(session.previous_recommendations[category].values())
                
                return CurrentRecommendResponse(
                    category=category,
                    category_index=session.current_category_index,
                    total_categories=len(session.categories),
                    candidates=previous_candidates,
                    is_last_category=session.current_category_index == len(session.categories) - 1,
                    is_restored_from_previous=True
                )
            else:
                # 이전 추천도 없는 경우
                return CurrentRecommendResponse(
                    category=category,
                    category_index=session.current_category_index,
                    total_categories=len(session.categories),
                    candidates=[],
                    is_last_category=session.current_category_index == len(session.categories) - 1,
                    is_restored_from_previous=False
                )
        
        # 스코어 퓨전
        fused_candidates = fuse_candidates(style_items, tpo_items, session.conflict, topk=5)
        
        # LLM 리랭킹 (TOP-3)
        top_item_ids = rerank_with_llm(
            persona=session.persona,
            parsed_tpo=session.parsed_tpo,
            conflict=session.conflict,
            fused_candidates=fused_candidates,
            selected_items=session.selected_items,
            topk=3
        )
        
        # 추천 이유 생성
        reason_query = build_reason_query(session.persona, session.parsed_tpo)
        
        candidates = []
        for pid in top_item_ids:
            item = lookup_item_by_id(pid, fused_candidates)
            if item is None:
                continue
            
            reason = generate_reason(
                reason_query=reason_query,
                selected_context_text=session.selected_context_text,
                item_desc=f"{item.get('main_cat_name')}({item.get('sub_cat_name')}): {item.get('description')}"
            )
            
            candidates.append(CandidateItem(
                product_id=str(item.get('product_id')),
                product_name=item.get('product_name', ''),
                brand=item.get('brand', ''),
                price=item.get('price', ''),
                item_url=item.get('item_url', ''),
                img_url=item.get('img_url', ''),
                score=item.get('score', 0.0),
                reason=reason,
                sub_cat_name=item.get('sub_cat_name'),
                color=item.get('color'),
                fit=item.get('fit'),
                pattern=item.get('pattern'),
                texture=item.get('texture'),
                description=item.get('description')
            ))
        
        # fuse/rerank 후 빈 결과: LLM이 모든 후보를 부적합 판단한 경우
        if not candidates:
            print(f"⚠️ [{category}] LLM 리랭킹 후 적합한 아이템이 없습니다.")
            if category in session.previous_recommendations and session.previous_recommendations[category]:
                print(f"⚠️ [{category}] 이전 추천 결과를 복구합니다.")
                session.recent_recommendations[category] = session.previous_recommendations[category].copy()
                previous_candidates = list(session.previous_recommendations[category].values())
                return CurrentRecommendResponse(
                    category=category,
                    category_index=session.current_category_index,
                    total_categories=len(session.categories),
                    candidates=previous_candidates,
                    is_last_category=session.current_category_index == len(session.categories) - 1,
                    is_restored_from_previous=True
                )
            else:
                return CurrentRecommendResponse(
                    category=category,
                    category_index=session.current_category_index,
                    total_categories=len(session.categories),
                    candidates=[],
                    is_last_category=session.current_category_index == len(session.categories) - 1,
                    is_restored_from_previous=False
                )

        # 현재 추천을 이전 추천에 누적 (기존 아이템 보존)
        if category not in session.previous_recommendations:
            session.previous_recommendations[category] = {}
        
        # 현재 recent_recommendations의 아이템들을 previous로 이동 (중복 없이)
        if category in session.recent_recommendations:
            for pid, item in session.recent_recommendations[category].items():
                if pid not in session.previous_recommendations[category]:
                    session.previous_recommendations[category][pid] = item
        
        # 새 추천을 previous에도 추가 (중복 없이)
        for item in candidates:
            if item.product_id not in session.previous_recommendations[category]:
                session.previous_recommendations[category][item.product_id] = item
        
        # 추천 결과를 세션에 캐시
        session.recent_recommendations[category] = {
            item.product_id: item for item in candidates
        }
        
        # 메모리 정리 (임베딩 후)
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return CurrentRecommendResponse(
            category=category,
            category_index=session.current_category_index,
            total_categories=len(session.categories),
            candidates=candidates,
            is_last_category=session.current_category_index == len(session.categories) - 1,
            is_restored_from_previous=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback", response_model=FeedbackResponse)
async def apply_feedback(request: FeedbackRequest, session_id: str = Header(..., alias="X-Session-ID")):
    """현재 카테고리에 대한 피드백 반영"""
    try:
        session = session_manager.get_session(session_id)
        category = session.get_current_category()
        
        if category is None:
            raise HTTPException(
                status_code=400,
                detail="No active category. All recommendations completed."
            )
        
        hard_constraints = session.hard_constraints_by_category[category]
        
        feedback_obj = {
            "intent": request.type,
            "include": request.value
        }
        
        # color의 경우 유사 색상 확장
        if request.type == "color":
            for color in request.value:
                alter = []
                if color == "화이트":
                    alter = ["크림", "아이보리"]
                elif color == "그린":
                    alter = ["카키"]
                elif color == "버건디":
                    alter = ["와인", "레드"]
                elif color == "그레이":
                    alter = ["실버", "회색"]
                
                if alter:
                    feedback_obj["include"].extend(alter)
        
        apply_feedback_to_constraints(feedback_obj, hard_constraints)
        
        return FeedbackResponse(
            status="feedback_applied",
            category=category,
            message=f"{category} 카테고리에 피드백이 반영되었습니다. /recommend/next를 다시 호출하여 재추천을 받으세요."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/select", response_model=SelectResponse)
async def select_item(request: SelectRequest, session_id: str = Header(..., alias="X-Session-ID")):
    """현재 카테고리의 아이템 선택 및 다음 카테고리로 이동"""
    try:
        session = session_manager.get_session(session_id)
        category = session.get_current_category()
        
        if category is None:
            raise HTTPException(
                status_code=400,
                detail="No active category. All recommendations completed."
            )
        
        # 🔥 recent_recommendations와 previous_recommendations 모두에서 찾기
        candidate = None
        
        # 1. 최근 추천에서 찾기
        if category in session.recent_recommendations:
            cached_items = session.recent_recommendations[category]
            if request.product_id in cached_items:
                candidate = cached_items[request.product_id]
                print(f"✅ 최근 추천에서 아이템 찾음: {request.product_id}")
        
        # 2. 이전 추천에서 찾기
        if candidate is None and category in session.previous_recommendations:
            previous_items = session.previous_recommendations[category]
            if request.product_id in previous_items:
                candidate = previous_items[request.product_id]
                print(f"✅ 이전 추천에서 아이템 찾음: {request.product_id}")
        
        # 3. 둘 다 없으면 에러
        if candidate is None:
            raise HTTPException(
                status_code=404,
                detail=f"Product ID {request.product_id} not found in recent or previous recommendations."
            )
        
        # 🔥 CandidateItem 객체를 딕셔너리로 변환
        chosen_item = {
            "product_id": candidate.product_id,
            "product_name": candidate.product_name,
            "main_cat_name": category,
            "sub_cat_name": candidate.sub_cat_name or "",
            "brand": candidate.brand,
            "price": candidate.price,
            "item_url": candidate.item_url,
            "img_url": candidate.img_url,
            "description": candidate.description or "",
            "color": candidate.color,
            "fit": candidate.fit,
            "pattern": candidate.pattern,
            "texture": candidate.texture
        }
        
        add_selected_item(category, session.selected_items, chosen_item)
        
        session.selected_context_text = append_selected_context(
            session.selected_context_text, 
            chosen_item
        )
        
        session.move_to_next_category()
        
        next_category = session.get_current_category()
        is_complete = session.is_complete()
        
        return SelectResponse(
            status="selected",
            category=category,
            next_category=next_category,
            is_complete=is_complete
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 선택 처리 실패: {str(e)}")  # 🔥 디버깅용 로그 추가
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/show_all", response_model=ShowAllResponse)
async def show_all(session_id: str = Header(..., alias="X-Session-ID")):
    """최종 선택된 모든 아이템 조회"""
    try:
        session = session_manager.get_session(session_id)
        
        if not session.refined_tpo:
            raise HTTPException(status_code=400, detail="TPO not set.")
        
        if not session.is_complete():
            current = session.get_current_category()
            raise HTTPException(
                status_code=400,
                detail=f"Recommendation not complete. Current category: {current}. Continue with /recommend/next."
            )
        
        return ShowAllResponse(
            tpo=session.refined_tpo,
            selected_items=session.selected_items,
            total_count=len(session.selected_items)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/status")
async def get_session_status(session_id: str = Header(..., alias="X-Session-ID")):
    """현재 세션 상태 확인"""
    session = session_manager.get_session(session_id)
    return {
        "session_id": session_id[:8] + "...",
        "initialized": session.model is not None and session.db_cache is not None,
        "model_loaded": session.model is not None,
        "db_loaded": session.db_cache is not None,
        "persona": session.persona,
        "user_gender": session.user_gender,
        "tpo_set": bool(session.parsed_tpo),
        "parsed_tpo": session.parsed_tpo,
        "conflict": session.conflict,
        "current_category": session.get_current_category(),
        "category_index": session.current_category_index,
        "total_categories": len(session.categories),
        "is_complete": session.is_complete(),
        "selected_items_count": len(session.selected_items),
        "selected_categories": list(session.selected_items.keys()),
        "created_at": session.created_at.isoformat(),
        "last_accessed": session.last_accessed.isoformat()
    }

@app.get("/admin/sessions")
async def get_all_sessions():
    """관리자: 모든 활성 세션 조회"""
    sessions_info = []
    for sid, session in session_manager.sessions.items():
        age = datetime.now() - session.last_accessed
        sessions_info.append({
            "session_id": sid[:8] + "...",
            "persona": session.persona,
            "current_category": session.get_current_category(),
            "is_complete": session.is_complete(),
            "age_minutes": int(age.total_seconds() / 60),
            "last_accessed": session.last_accessed.isoformat()
        })
    
    return {
        "total_sessions": len(session_manager.sessions),
        "max_sessions": session_manager.max_sessions,
        "sessions": sessions_info
    }

@app.post("/admin/cleanup")
async def manual_cleanup(max_age_minutes: int = 30):
    """관리자: 수동 세션 정리"""
    cleaned = session_manager.cleanup_old_sessions(max_age_minutes)
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    return {
        "status": "cleanup_complete",
        "cleaned_sessions": cleaned,
        "active_sessions": len(session_manager.sessions)
    }


    
# ===============================
# Run Server
# ===============================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False  # 멀티 세션에서는 reload 비활성화 권장
    )
