# 패션 추천 시스템 - 실행 가이드

## 📋 목차
1. [사전 준비](#사전-준비)
2. [백엔드 수정사항](#백엔드-수정사항)
3. [프론트엔드 파일 구성](#프론트엔드-파일-구성)
4. [실행 방법](#실행-방법)
5. [테스트](#테스트)
6. [문제 해결](#문제-해결)

---

## 🔧 사전 준비

### 필수 패키지 설치
```bash
pip install fastapi uvicorn openai sentence-transformers faiss-cpu python-dotenv torch
```

### 환경 변수 설정
`.env` 파일에 OpenAI API 키 설정:
```
OPENAI_API_KEY=your_api_key_here
```

---

## ✏️ 백엔드 수정사항

### 1. main.py에 CORS 추가
`main.py` 파일 상단에 다음 코드를 추가하세요:

```python
from fastapi.middleware.cors import CORSMiddleware

# FastAPI 앱 생성 후 (app = FastAPI(...) 다음에)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**위치**: `app = FastAPI(...)` 바로 다음

### 2. utils.py에 refine_tpo_text 함수 추가
`utils.py` 파일 끝에 다음 함수를 추가하세요:

```python
def refine_tpo_text(tpo_raw: str) -> str:
    """
    TPO를 사용자 친화적인 텍스트로 정제
    """
    if not tpo_raw:
        return "일상 스타일"
    
    tpo_text = tpo_raw.strip()
    
    # 너무 길면 요약
    if len(tpo_text) > 50:
        tpo_text = tpo_text[:47] + "..."
    
    return tpo_text
```

### 3. demo_client.py 수정
`demo_client.py`의 `__init__` 메서드에 `self.user_tpo` 추가:

```python
def __init__(self):
    self.session_id = None
    self.base_url = BASE_URL
    self.user_tpo = None  # 추가
```

`test_3_tpo` 메서드에서 TPO 저장:

```python
def test_3_tpo(self, persona):
    # ... 기존 코드 ...
    tpo = input("\n💁‍♀️ 오늘의 TPO는 무엇인가요?: ").strip()
    
    while not tpo:
        print("⚠️ TPO는 필수 입력입니다.")
        tpo = input("💁‍♀️ 오늘의 TPO는 무엇인가요?: ").strip()
    
    self.user_tpo = tpo  # 추가: 원본 TPO 저장
    # ... 나머지 코드 ...
```

`test_7_show_all` 메서드에서 저장된 TPO 사용:

```python
def test_7_show_all(self):
    # ... 기존 코드 ...
    if response.status_code == 200:
        data = response.json()
        refined_tpo = refine_tpo_text(self.user_tpo)  # 수정
        print(f"✅ 최종 코디 완성!\n")
        print(f"📍 TPO: {refined_tpo}")  # 수정
        # ... 나머지 코드 ...
```

---

## 📁 프론트엔드 파일 구성

다음 파일들을 프로젝트 루트 디렉토리에 배치하세요:

```
project/
├── backend/
│   ├── main.py (수정됨)
│   ├── utils.py (수정됨)
│   ├── prompt.py
│   └── demo_client.py (수정됨)
├── frontend/
│   ├── home.html
│   ├── howitworks.html
│   ├── usage.html
│   ├── persona.html
│   ├── persona.css
│   ├── chat.html (수정됨)
│   ├── chat.css
│   ├── chat.js (새로 추가)
│   ├── result.html (새로 추가)
│   └── images/
│       ├── (모든 이미지 파일)
└── .env
```

---

## 🚀 실행 방법

### 1단계: 백엔드 서버 실행

터미널을 열고 백엔드 디렉토리로 이동한 후:

```bash
cd backend
python main.py
```

또는:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

서버가 정상적으로 시작되면 다음과 같은 메시지가 표시됩니다:
```
🚀 전역 리소스 로딩 중...
👉 DEVICE: cuda (또는 cpu)
👉 Embedding model is loading...
👉 DB cache is loading...
✅ 전역 리소스 로딩 완료!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2단계: 프론트엔드 실행

#### 방법 1: 로컬 서버 사용 (권장)
Python 내장 서버 사용:

```bash
cd frontend
python -m http.server 8080
```

브라우저에서 접속:
```
http://localhost:8080/home.html
```

#### 방법 2: VS Code Live Server 사용
1. VS Code에서 `home.html` 파일 열기
2. 우클릭 → "Open with Live Server"

#### 방법 3: 직접 파일 열기 (CORS 오류 가능)
`home.html` 파일을 더블클릭하여 브라우저에서 직접 열기
※ CORS 오류가 발생할 수 있으므로 권장하지 않음

---

## 🧪 테스트

### 전체 플로우 테스트

1. **홈페이지** (`home.html`)
   - "스타일 추천 시작하기" 버튼 클릭

2. **페르소나 선택** (`persona.html`)
   - 남자/여자 필터 선택 (선택사항)
   - 원하는 페르소나 카드 더블클릭

3. **채팅 시작** (`chat.html`)
   - 챗봇 인사 메시지 확인
   - 비선호 요소 입력:
     * 핏: "오버사이즈", "슬림", 또는 "없음"
     * 패턴: "로고", "스트라이프", "체크", 또는 "없음"
     * 가격: "10만원", "20만원", "30만원", 또는 "그 이상"
   
   - TPO 입력 예시:
     * "대학교 수업 듣고 친구랑 저녁 약속"
     * "친구 생일파티"
     * "회사 면접"
     * "주말 데이트"

4. **아이템 추천**
   - 각 카테고리별로 TOP-3 아이템 표시
   - 이미지 클릭하여 선택 또는
   - 피드백으로 재추천:
     * "세부 카테고리 변경"
     * "색상 변경"
     * "소재 변경"

5. **최종 결과** (`result.html`)
   - 선택된 모든 아이템 확인
   - 상품 페이지 링크 클릭
   - 결과 공유 또는 다시 추천받기

---

## 🔍 API 엔드포인트 확인

백엔드 서버가 실행 중일 때 브라우저에서 접속:

```
http://localhost:8000/docs
```

Swagger UI에서 모든 API 엔드포인트를 확인하고 테스트할 수 있습니다.

---

## 🐛 문제 해결

### 1. CORS 오류
**증상**: 브라우저 콘솔에 "CORS policy" 에러 표시

**해결**:
- `main.py`에 CORS 미들웨어가 제대로 추가되었는지 확인
- 백엔드 서버를 재시작

### 2. 세션 오류
**증상**: "Session not found" 오류

**해결**:
- 페이지를 새로고침하면 새 세션이 생성됨
- 브라우저 개발자 도구의 콘솔에서 세션 ID 확인

### 3. 추천이 느림
**증상**: 추천 시 30초 이상 소요

**원인**: 정상 동작 (임베딩 및 검색에 시간 소요)

**개선 방법**:
- GPU 사용 (`torch.cuda.is_available()` 확인)
- 더 작은 모델 사용
- DB 캐싱 최적화

### 4. 이미지가 표시되지 않음
**증상**: 아이템 카드에 이미지가 깨짐

**원인**: 
- 이미지 URL이 유효하지 않음
- CORS 정책으로 외부 이미지 차단

**해결**:
- 백엔드 DB의 `img_url` 확인
- 브라우저 콘솔에서 이미지 로딩 오류 확인

### 5. 로컬 서버 포트 충돌
**증상**: "Address already in use" 오류

**해결**:
```bash
# 포트 변경
python -m http.server 8081

# 또는 사용 중인 프로세스 종료
# Windows:
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:8080 | xargs kill -9
```

---

## 📊 백엔드 서버 상태 확인

### 활성 세션 조회
```bash
curl http://localhost:8000/admin/sessions
```

### 세션 정리
```bash
curl -X POST http://localhost:8000/admin/cleanup
```

### 서버 헬스 체크
```bash
curl http://localhost:8000/
```

---

## 💡 개발 팁

### 1. 디버깅
- 브라우저 개발자 도구 (F12) 콘솔 탭 확인
- 백엔드 터미널에서 로그 확인

### 2. 스트리밍 속도 조절
`chat.js`의 `typeText` 함수에서 `speed` 파라미터 조절:
```javascript
await typeText(bubbleText, text, 20);  // 더 빠르게
```

### 3. 개발 중 캐시 비활성화
브라우저 개발자 도구 → Network 탭 → "Disable cache" 체크

---

## 📝 주요 명령어 요약

```bash
# 백엔드 실행
cd backend
python main.py

# 프론트엔드 실행
cd frontend
python -m http.server 8080

# 패키지 설치
pip install -r requirements.txt

# API 문서 확인
# 브라우저에서: http://localhost:8000/docs

# 프론트엔드 접속
# 브라우저에서: http://localhost:8080/home.html
```

---

## ✨ 주요 기능

### 백엔드
- ✅ 멀티 세션 지원
- ✅ 페르소나 기반 추천
- ✅ TPO 파싱 및 충돌 감지
- ✅ 카테고리별 순차 추천
- ✅ 실시간 피드백 반영
- ✅ 이전 추천 캐싱

### 프론트엔드
- ✅ 반응형 UI
- ✅ 스트리밍 메시지 효과
- ✅ 아이템 카드 인터랙션
- ✅ 이미지 클릭 선택
- ✅ 실시간 피드백
- ✅ 최종 결과 페이지
- ✅ 결과 공유 기능

---

## 🎯 다음 단계

1. **성능 최적화**
   - 임베딩 모델 경량화
   - DB 쿼리 최적화
   - 캐싱 전략 개선

2. **UI/UX 개선**
   - 로딩 인디케이터 추가
   - 에러 처리 강화
   - 모바일 반응형 개선

3. **기능 확장**
   - 사용자 계정 시스템
   - 저장된 코디 관리
   - 소셜 공유 기능

---

## 📞 지원

문제가 발생하면:
1. 백엔드 로그 확인
2. 브라우저 콘솔 확인
3. API 문서 참조 (http://localhost:8000/docs)
4. GitHub Issues 등록

---

**즐거운 코딩 되세요! 🚀**
