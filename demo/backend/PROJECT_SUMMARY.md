# Fashion Recommendation API - 완성된 FastAPI 백엔드

## 📦 제공된 파일 목록

```
project/
├── backend.py              # FastAPI 서버
├── utils.py                # 기존 유틸리티 함수
├── prompt.py               # 기존 프롬프트
├── main.py                 # (참고용, 기존 데모 코드)
├── requirements.txt        # 필요한 패키지
├── .env                    # 환경 변수 (생성 필요)
├── run_server.sh           # 서버 실행 스크립트
├── test_client.py          # 테스트 클라이언트
└── faiss/                  # FAISS 벡터 DB
    ├── style/
    │   ├── 상의/
    │   ├── 아우터/
    │   ├── 바지/
    │   ├── 신발/
    │   └── 가방/
    └── tpo/
        ├── 상의/
        ├── 아우터/
        ├── 바지/
        ├── 신발/
        └── 가방/
```

## 🎯 주요 기능

### 1. 세션 관리
- 모델 및 DB 초기화
- 페르소나 설정
- TPO 파싱 및 충돌 감지

### 2. 추천 시스템
- FAISS 벡터 검색
- Style/TPO 스코어 퓨전
- LLM 기반 조화도 리랭킹
- 추천 이유 자동 생성

### 3. 피드백 루프
- 실시간 제약 조건 업데이트
- 색상 유사 확장
- 재추천 지원

### 4. 아이템 선택
- 추천 결과 캐싱
- 선택 히스토리 관리
- 컨텍스트 자동 업데이트


## 📋 API 엔드포인트 요약

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/session/init` | 세션 초기화 (모델/DB 로드) |
| POST | `/session/persona` | 페르소나 선택 |
| POST | `/session/tpo` | TPO 입력 및 파싱 |
| POST | `/recommend/{category}` | 카테고리별 추천 (TOP-3) |
| POST | `/feedback/{category}` | 피드백 반영 |
| POST | `/select/{category}` | 아이템 선택 확정 |
| GET | `/session/result` | 최종 코디 결과 조회 |
| GET | `/` | 헬스 체크 |


## ⚙️ 기술 스택

- **FastAPI**: 웹 프레임워크
- **Pydantic**: 데이터 검증
- **Uvicorn**: ASGI 서버
- **OpenAI API**: LLM 추론
- **FAISS**: 벡터 검색
- **SentenceTransformers**: 임베딩

## 📊 아키텍처

```
Client (Web/Mobile/CLI)
    ↓
FastAPI Backend (backend.py)
    ↓
┌─────────────────────────────────┐
│ Session State                   │
│ - Model                         │
│ - DB Cache                      │
│ - User Context                  │
│ - Recommendations Cache         │
└─────────────────────────────────┘
    ↓
┌─────────────┬──────────────┬─────────────┐
│ FAISS DB    │ OpenAI API   │ Utils       │
│ (Style/TPO) │ (LLM)        │ (Filters)   │
└─────────────┴──────────────┴─────────────┘
```

## 📞 지원

문제가 발생하면:
1. 로그 확인 (콘솔 출력)
2. API 문서 재확인 (/docs)
3. 테스트 클라이언트 실행
4. 환경 설정 점검

---

✨ **준비 완료!** 이제 `/docs`에서 API를 직접 테스트해보세요!
