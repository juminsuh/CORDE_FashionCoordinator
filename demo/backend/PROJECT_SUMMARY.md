# Fashion Recommendation API - 완성된 FastAPI 백엔드

## 📦 제공된 파일 목록

```
outputs/
├── backend.py           # FastAPI 메인 서버 코드
├── requirements.txt     # 필요한 Python 패키지
├── README.md           # 상세 API 문서
├── QUICKSTART.md       # 빠른 시작 가이드
├── test_client.py      # API 테스트 클라이언트
├── run_server.sh       # 서버 실행 스크립트 (Linux/Mac)
└── .env       # 환경 변수 템플릿
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

## 🚀 실행 방법

### 1단계: 환경 준비

```bash
# 1. 필요한 파일 복사
# - backend.py
# - utils.py (기존 파일)
# - prompt.py (기존 파일)
# - requirements.txt

# 2. .env 파일 생성
cp .env.example .env
# 그 다음 .env 파일을 열어서 실제 OpenAI API 키 입력

# 3. FAISS DB 디렉토리 확인
# ./faiss/style/ 및 ./faiss/tpo/ 디렉토리가 존재해야 함
```

### 2단계: 패키지 설치

```bash
pip install -r requirements.txt
```

### 3단계: 서버 실행

```bash
# 방법 1: 스크립트 사용
./run_server.sh

# 방법 2: Python 직접 실행
python backend.py

# 방법 3: uvicorn 사용
uvicorn backend:app --reload --port 8000
```

### 4단계: API 테스트

브라우저에서 http://localhost:8000/docs 접속하여 Swagger UI에서 직접 테스트하거나:

```bash
python test_client.py
```

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

## 💡 사용 예시 (Python)

```python
import requests

BASE = "http://localhost:8000"

# 1. 초기화
requests.post(f"{BASE}/session/init")

# 2. 페르소나 설정
requests.post(f"{BASE}/session/persona", json={"persona": "pme"})

# 3. TPO 설정
requests.post(f"{BASE}/session/tpo", 
    json={"tpo": "대학교 수업 후 저녁 약속", "persona": "pme"})

# 4. 상의 추천
resp = requests.post(f"{BASE}/recommend/상의")
items = resp.json()["candidates"]

# 5. 아이템 선택
requests.post(f"{BASE}/select/상의", 
    json={"product_id": items[0]["product_id"]})

# 6. 결과 확인
result = requests.get(f"{BASE}/session/result")
print(result.json())
```

## 🔧 주요 개선사항

### 기존 CLI 코드 대비:

1. **RESTful API 제공**
   - 웹/모바일 앱과 통합 가능
   - Swagger UI 자동 문서화

2. **세션 캐싱**
   - 추천 결과를 세션에 저장
   - 선택 시 DB 재조회 불필요

3. **타입 안전성**
   - Pydantic 모델로 입출력 검증
   - 자동 JSON 직렬화/역직렬화

4. **에러 핸들링**
   - HTTP 상태 코드 기반
   - 명확한 에러 메시지

5. **확장성**
   - 비동기 지원 (async/await)
   - 미들웨어 추가 가능
   - 다중 세션 지원 가능

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

## 🔒 보안 고려사항

1. **API 키 보호**: `.env` 파일 사용 (Git에 커밋 X)
2. **입력 검증**: Pydantic 모델로 자동 검증
3. **에러 메시지**: 민감 정보 노출 방지
4. **CORS**: 필요시 미들웨어 추가

## 🚀 프로덕션 배포 체크리스트

- [ ] 환경 변수 설정 (.env)
- [ ] FAISS DB 파일 준비
- [ ] 패키지 설치 (requirements.txt)
- [ ] 포트 설정 확인 (기본: 8000)
- [ ] CORS 설정 (필요시)
- [ ] 로깅 설정
- [ ] Redis 세션 저장소 (다중 사용자)
- [ ] Docker 컨테이너화
- [ ] 모니터링 설정
- [ ] 백업 전략

## 🐛 문제 해결

### "Module not found"
```bash
pip install -r requirements.txt
```

### "FAISS DB not found"
- `./faiss/style/` 및 `./faiss/tpo/` 확인
- 각 카테고리별 하위 디렉토리 확인

### "OpenAI API key not found"
- `.env` 파일에 유효한 키 설정
- 파일 위치가 올바른지 확인

### "Session not initialized"
- `/session/init` 먼저 호출
- 엔드포인트 순서 준수

## 📈 향후 개선 방향

1. **다중 세션 지원**
   - 세션 ID 기반 관리
   - Redis 백엔드 사용

2. **인증/인가**
   - JWT 토큰 기반 인증
   - 사용자별 권한 관리

3. **비동기 최적화**
   - DB 쿼리 비동기화
   - 병렬 추천 처리

4. **캐싱 전략**
   - 임베딩 결과 캐싱
   - LLM 응답 캐싱

5. **모니터링**
   - 로깅 시스템
   - 메트릭 수집
   - 성능 추적

## 📞 지원

문제가 발생하면:
1. 로그 확인 (콘솔 출력)
2. API 문서 재확인 (/docs)
3. 테스트 클라이언트 실행
4. 환경 설정 점검

---

✨ **준비 완료!** 이제 `/docs`에서 API를 직접 테스트해보세요!
