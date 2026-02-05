# 🚀 Quick Start Guide

## 1️⃣ 필수 준비사항

### 파일 구조
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

### 환경 변수 설정
`.env` 파일을 생성하고 OpenAI API 키를 입력하세요:

```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

## 2️⃣ 설치

```bash
# 패키지 설치
pip install -r requirements.txt
```

## 3️⃣ 서버 실행

### 방법 1: 스크립트 사용 (권장)
```bash
./run_server.sh
```

### 방법 2: 직접 실행
```bash
python main.py
```

### 방법 3: uvicorn 사용
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 4️⃣ API 문서 확인

서버가 실행되면 브라우저에서 다음 URL을 열어보세요:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 5️⃣ 테스트 실행

```bash
python test_client.py
```

## 6️⃣ API 사용 예시

### Python으로 전체 플로우 실행

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 세션 초기화
requests.post(f"{BASE_URL}/session/init")

# 2. 페르소나 선택
requests.post(f"{BASE_URL}/session/persona", json={"persona": "pme"})

# 3. TPO 설정
requests.post(
    f"{BASE_URL}/session/tpo",
    json={"tpo": "대학교 수업 듣고 친구랑 저녁 약속", "persona": "pme"}
)

# 4. 상의 추천
response = requests.post(f"{BASE_URL}/recommend/상의")
candidates = response.json()["candidates"]

# 5. 아이템 선택
if candidates:
    requests.post(
        f"{BASE_URL}/select/상의",
        json={"product_id": candidates[0]["product_id"]}
    )

# 6. 최종 결과 확인
result = requests.get(f"{BASE_URL}/session/result")
print(result.json())
```

### cURL로 테스트

```bash
# 1. 세션 초기화
curl -X POST http://localhost:8000/session/init

# 2. 페르소나 선택
curl -X POST http://localhost:8000/session/persona \
  -H "Content-Type: application/json" \
  -d '{"persona":"pme"}'

# 3. TPO 설정
curl -X POST http://localhost:8000/session/tpo \
  -H "Content-Type: application/json" \
  -d '{"tpo":"대학교 수업 듣고 친구랑 저녁 약속","persona":"pme"}'

# 4. 상의 추천
curl -X POST http://localhost:8000/recommend/상의
```

## 7️⃣ 페르소나 목록

- `pme` - 김프메 (남, 24) - 프레피/단정
- `nowon` - 정노원 (남, 27) - 캐주얼
- `ob` - 최오비 (남, 26) - 스트릿
- `moyeon` - 이모연 (여, 24) - 힙한/보이시
- `seoksa` - 주석사 (여, 25) - 캐주얼
- `promie` - 정프로미 (여, 23) - 페미닌

## 8️⃣ 카테고리 순서

1. 상의
2. 아우터
3. 바지
4. 신발
5. 가방

## ⚠️ 문제 해결

### 1. "Module not found" 에러
```bash
pip install -r requirements.txt
```

### 2. "FAISS DB not found" 에러
- `./faiss/style/` 및 `./faiss/tpo/` 디렉토리가 존재하는지 확인
- 각 카테고리별 하위 디렉토리가 있는지 확인

### 3. "OpenAI API key not found" 에러
- `.env` 파일에 유효한 API 키가 설정되어 있는지 확인
- 환경 변수가 올바르게 로드되는지 확인

### 4. "Session not initialized" 에러
- 반드시 `/session/init` 엔드포인트를 먼저 호출해야 함

### 5. Port 8000이 이미 사용 중일 때
```bash
# 다른 포트로 실행
uvicorn backend:app --reload --port 8001
```

## 📝 주요 특징

✅ **RESTful API**: 표준 HTTP 메서드 사용
✅ **자동 문서화**: Swagger UI 제공
✅ **타입 검증**: Pydantic 모델 사용
✅ **에러 핸들링**: 명확한 에러 메시지
✅ **세션 관리**: 상태 유지 가능
✅ **피드백 반영**: 실시간 추천 개선

## 🎯 다음 단계

1. 프로덕션 환경에서는 Redis를 사용한 세션 관리 권장
2. 다중 사용자 지원을 위한 세션 ID 기반 시스템 구현
3. 로깅 및 모니터링 시스템 추가
4. 인증/인가 시스템 구현 (JWT 등)
5. Docker 컨테이너화
6. CI/CD 파이프라인 구성

## 📚 추가 자료

- FastAPI 공식 문서: https://fastapi.tiangolo.com/
- Pydantic 문서: https://docs.pydantic.dev/
- FAISS 문서: https://github.com/facebookresearch/faiss
