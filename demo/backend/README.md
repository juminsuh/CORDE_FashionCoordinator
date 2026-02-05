# Fashion Recommendation API

Persona & TPO 기반 패션 코디 추천 시스템 FastAPI 백엔드

## 설치

```bash
pip install -r requirements.txt
```

## 환경 변수 설정

`.env` 파일을 생성하고 OpenAI API 키를 설정하세요:

```
OPENAI_API_KEY=your_api_key_here
```

## 실행

```bash
python backend.py
```

또는

```bash
uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

## API 문서

서버 실행 후 다음 URL에서 Swagger UI를 확인할 수 있습니다:

- http://localhost:8000/docs
- http://localhost:8000/redoc

## API 엔드포인트

### 1. POST /session/init
세션 초기화, 모델 및 DB 로드

**Response:**
```json
{
  "status": "ok",
  "categories": ["상의", "아우터", "바지", "신발", "가방"]
}
```

### 2. POST /session/persona
페르소나 선택

**Request:**
```json
{
  "persona": "pme"
}
```

**Response:**
```json
{
  "persona": "pme",
  "user_gender": "남자"
}
```

**Available Personas:**
- `pme` (김프메, 남, 24) - 프레피/단정
- `nowon` (정노원, 남, 27) - 캐주얼
- `ob` (최오비, 남, 26) - 스트릿
- `moyeon` (이모연, 여, 24) - 힙한/보이시
- `seoksa` (주석사, 여, 25) - 캐주얼
- `promie` (정프로미, 여, 23) - 페미닌

### 3. POST /session/tpo
TPO 입력 및 파싱

**Request:**
```json
{
  "tpo": "대학교 수업 듣고 친구랑 저녁 약속",
  "persona": "pme"
}
```

**Response:**
```json
{
  "parsed_tpo": ["대학교 수업", "캐주얼", "저녁 약속"],
  "conflict": false
}
```

### 4. POST /recommend/{category}
카테고리별 아이템 추천

**Categories:** `상의`, `아우터`, `바지`, `신발`, `가방`

**Response:**
```json
{
  "category": "상의",
  "candidates": [
    {
      "product_id": "123",
      "product_name": "옥스포드 셔츠",
      "brand": "무신사스탠다드",
      "price": "59,000원",
      "item_url": "https://...",
      "img_url": "https://...",
      "score": 0.87,
      "reason": "대학교 수업과 저녁 약속 모두에 어울리는 캐주얼한 무드입니다.",
      "sub_cat_name": "셔츠/블라우스",
      "color": "화이트",
      "fit": "레귤러",
      "pattern": "단색",
      "texture": "면"
    }
  ]
}
```

### 5. POST /feedback/{category}
피드백 반영 (재추천용)

**Request:**
```json
{
  "type": "fit",
  "value": ["슬림"]
}
```

**Feedback Types:**
- `sub_cat_name`: 서브 카테고리
- `color`: 색상
- `fit`: 핏
- `pattern`: 패턴
- `texture`: 소재

**Response:**
```json
{
  "status": "constraints_updated",
  "category": "상의"
}
```

### 6. POST /select/{category}
아이템 선택 및 확정

**Request:**
```json
{
  "product_id": "123"
}
```

**Response:**
```json
{
  "status": "selected",
  "category": "상의"
}
```

### 7. GET /session/result
최종 코디 결과 조회

**Response:**
```json
{
  "tpo": "대학교 수업 후 친구와 저녁 약속",
  "outfit": {
    "상의": {
      "product_id": "123",
      "product_name": "옥스포드 셔츠",
      "brand": "무신사스탠다드",
      "price": "59,000원",
      "item_url": "https://...",
      "img_url": "https://..."
    },
    "바지": {...}
  }
}
```

## 사용 흐름 예시

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 세션 초기화
response = requests.post(f"{BASE_URL}/session/init")
print(response.json())

# 2. 페르소나 선택
response = requests.post(
    f"{BASE_URL}/session/persona",
    json={"persona": "pme"}
)
print(response.json())

# 3. TPO 설정
response = requests.post(
    f"{BASE_URL}/session/tpo",
    json={
        "tpo": "대학교 수업 듣고 친구랑 저녁 약속",
        "persona": "pme"
    }
)
print(response.json())

# 4. 상의 추천
response = requests.post(f"{BASE_URL}/recommend/상의")
candidates = response.json()["candidates"]
print(candidates)

# 5. (선택적) 피드백 반영
response = requests.post(
    f"{BASE_URL}/feedback/상의",
    json={"type": "color", "value": ["화이트"]}
)
print(response.json())

# 6. 아이템 선택
response = requests.post(
    f"{BASE_URL}/select/상의",
    json={"product_id": candidates[0]["product_id"]}
)
print(response.json())

# 7. 다른 카테고리도 반복...

# 8. 최종 결과 확인
response = requests.get(f"{BASE_URL}/session/result")
print(response.json())
```

## 주의사항

1. **FAISS DB 경로**: `./faiss/style` 및 `./faiss/tpo` 디렉토리가 존재해야 합니다.
2. **OpenAI API 키**: `.env` 파일에 유효한 API 키가 설정되어 있어야 합니다.
3. **순차 호출**: 엔드포인트는 순서대로 호출해야 합니다 (init → persona → tpo → recommend).
4. **세션 관리**: 현재는 단일 세션만 지원합니다. 다중 사용자 지원을 위해서는 세션 ID 기반 관리가 필요합니다.

## 개발 노트

- `/select/{category}` 엔드포인트는 현재 간단한 구현으로, 실제로는 최근 추천 결과를 세션에 캐시하여 사용해야 합니다.
- 프로덕션 환경에서는 Redis 등을 사용한 세션 관리를 권장합니다.
- 에러 핸들링 및 로깅을 추가하면 더 견고한 시스템이 됩니다.
