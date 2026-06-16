// ====================================
// 전역 변수
// ====================================
const API_BASE_URL = 'http://127.0.0.1:8000';
let sessionId = null;
let currentPersona = null;
let conversationState = 'GREETING'; // GREETING -> NEGATIVE -> TPO -> RECOMMENDATION -> COMPLETE
let currentCategory = null;
let categoryIndex = 0;
let previousCandidates = null; // 이전 추천 캐싱
let currentCandidates = []; // 현재 표시 중인 후보들

// 카테고리 세부 옵션 맵
const DETAIL_MAP = {
    "sub_cat_name": {
        "상의": ['긴소매 티셔츠', '니트/스웨터', '후드 티셔츠', '피케/카라 티셔츠', '맨투맨/스웨트', '셔츠/블라우스'],
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
    "texture": {
        "상의": ['면', '니트', '폴리에스테르'],
        "바지": ['폴리에스테르', '면', '나일론'],
        "아우터": ['나일론', '울', '니트', '면', '폴리에스테르'],
        "신발": ['천연가죽', '스웨이드', '폴리에스테르', '인조가죽'],
        "가방": ['나일론', '면', '폴리에스테르']
    }
};

// ====================================
// DOM 요소
// ====================================
const chatFlow = document.getElementById("chatMessages");
const userInput = document.getElementById("userInput");

// ====================================
// 초기화
// ====================================
async function initialize() {
    // URL에서 persona 가져오기
    const params = new URLSearchParams(window.location.search);
    currentPersona = params.get('persona');
    
    if (!currentPersona) {
        alert('페르소나를 선택해주세요!');
        window.location.href = 'persona.html';
        return;
    }
    
    // 페르소나에 따른 스타일 적용
    document.body.classList.add(`persona-${currentPersona}`);
    
    // 세션 생성
    await createSession();
    
    // 페르소나 설정
    await setPersona();
    
    // 인사 메시지
    await showGreeting();
}

// ====================================
// API 호출 함수
// ====================================
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (sessionId) {
        headers['X-Session-ID'] = sessionId;
    }
    
    const options = {
        method,
        headers
    };
    
    if (body && method !== 'GET') {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'API 호출 실패');
    }
    
    return await response.json();
}

// ====================================
// 세션 관리
// ====================================
async function createSession() {
    try {
        const data = await apiCall('/session/create', 'POST');
        sessionId = data.session_id;
        console.log('세션 생성 완료:', sessionId);
    } catch (error) {
        console.error('세션 생성 실패:', error);
        alert('서버 연결에 실패했습니다. 서버가 실행 중인지 확인해주세요.');
    }
}

async function setPersona() {
    try {
        await apiCall('/session/persona', 'POST', { persona: currentPersona });
        console.log('페르소나 설정 완료:', currentPersona);
    } catch (error) {
        console.error('페르소나 설정 실패:', error);
    }
}

// ====================================
// 세션 종료 및 나가기
// ====================================
async function exitSession() {
    if (confirm('정말 나가시겠어요? 현재 진행 상황이 저장되지 않습니다.')) {
        try {
            if (sessionId) {
                await apiCall('/session/delete', 'DELETE');
            }
        } catch (error) {
            console.error('세션 삭제 실패:', error);
        }
        window.location.href = 'home.html';
    }
}

// 나가기 버튼 추가
function addExitButton() {
    const exitBtn = document.createElement('button');
    exitBtn.id = 'exitBtn';
    exitBtn.innerHTML = '← 나가기';
    exitBtn.style.cssText = `
        position: fixed;
        top: 180px;
        left: 60px;
        z-index: 100;
        padding: 12px 24px;
        background: rgba(255, 255, 255, 0.9);
        border: 2px solid var(--bot-bubble-bg);
        border-radius: 999px;
        color: var(--bot-bubble-bg);
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    `;
    
    exitBtn.onmouseenter = () => {
        exitBtn.style.background = 'var(--bot-bubble-bg)';
        exitBtn.style.color = 'white';
        exitBtn.style.transform = 'translateX(-4px)';
    };
    
    exitBtn.onmouseleave = () => {
        exitBtn.style.background = 'rgba(255, 255, 255, 0.9)';
        exitBtn.style.color = 'var(--bot-bubble-bg)';
        exitBtn.style.transform = 'translateX(0)';
    };
    
    exitBtn.onclick = exitSession;
    
    document.body.appendChild(exitBtn);
}

// ====================================
// 메시지 표시 함수
// ====================================
function addUserMessage(text) {
    const message = document.createElement("div");
    message.className = "message user";
    
    message.innerHTML = `
        <div class="bubble-box user">
            <div class="bubble-text">${escapeHtml(text)}</div>
        </div>
        <img src="images/user_black.svg" class="profile" alt="User" />
    `;
    
    chatFlow.appendChild(message);
    scrollToBottom();
}

async function addBotMessage(text, isStreaming = true) {
    const message = document.createElement("div");
    message.className = "message bot";
    
    message.innerHTML = `
        <img src="images/lookie_black.svg" class="profile" alt="Lookie" />
        <div class="bubble-box bot">
            <div class="bubble-text"></div>
        </div>
    `;
    
    chatFlow.appendChild(message);
    const bubbleText = message.querySelector('.bubble-text');
    
    if (isStreaming) {
        // 스트리밍 효과
        await typeText(bubbleText, text);
    } else {
        // \n을 <br>로 변환하여 innerHTML에 할당
        bubbleText.innerHTML = escapeHtml(text).replace(/\n/g, '<br>');
    }
    
    scrollToBottom();
}

async function typeText(element, text, speed = 30) {
    element.innerHTML = ''; // textContent → innerHTML로 변경
    
    for (let i = 0; i < text.length; i++) {
        if (text[i] === '\n') {
            element.innerHTML += '<br>'; // \n을 <br>로 변환
        } else {
            element.innerHTML += escapeHtml(text[i]); // 개별 문자 이스케이프
        }
        scrollToBottom();
        await sleep(speed);
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function scrollToBottom() {
    chatFlow.scrollTop = chatFlow.scrollHeight;
}

// ====================================
// 인사 & 대화 흐름
// ====================================
async function showGreeting() {
    await addBotMessage(
        "안녕하세요! 저는 오늘 스타일링을 도와드릴 'Lookie'입니다. 👀\n\n" +
        "저는 여러분의 페르소나와 TPO를 기반으로 상의, 아우터, 바지, 신발, 가방까지 완벽한 코디를 추천해드려요!\n\n" +
        "먼저, 더 나은 추천을 위해 몇 가지 질문을 드릴게요!"
    );
    
    
    await sleep(1000);
    conversationState = 'NEGATIVE';
    await askNegativeFit();
}

// ====================================
// Negative 조사
// ====================================
async function askNegativeFit() {
    await addBotMessage(
        "비선호하는 핏이 있나요? \n\n" +
        "• 오버사이즈\n" +
        "• 슬림\n" +
        "• 없음\n"
    );
}

let negativeData = {
    fit: null,
    pattern: null,
    price_threshold: null
};

async function handleNegativeFit(userInput) {
    const FIT_KEYWORDS = ['오버사이즈', '슬림'];
    const fitMatches = FIT_KEYWORDS.filter(kw => userInput.includes(kw));

    if (fitMatches.length > 1) {
        negativeData.fit = fitMatches;
        await addBotMessage(`네, ${fitMatches.join(', ')} 핏을 모두 제외하고 추천드릴게요! ✅`);
    } else if (fitMatches.length === 1) {
        negativeData.fit = fitMatches;
        await addBotMessage(`네, ${fitMatches[0]} 핏을 제외하고 추천드릴게요! ✅`);
    } else {
        negativeData.fit = [];
        await addBotMessage(`네, 모든 핏을 포함해서 추천드릴게요! ✅`);
    }

    await askNegativePattern();
}

async function askNegativePattern() {
    await addBotMessage(
        "비선호하는 패턴이 있나요?\n\n" +
        "• 로고\n" +
        "• 스트라이프\n" +
        "• 체크\n" +
        "• 없음\n"
    );
    conversationState = 'NEGATIVE_PATTERN';
}

async function handleNegativePattern(userInput) {
    const PATTERN_KEYWORDS = ['로고', '스트라이프', '체크'];
    const patternMatches = PATTERN_KEYWORDS.filter(kw => userInput.includes(kw));

    if (patternMatches.length > 1) {
        negativeData.pattern = patternMatches;
        await addBotMessage(`네, ${patternMatches.join(', ')} 패턴을 모두 제외하고 추천드릴게요! ✅`);
    } else if (patternMatches.length === 1) {
        negativeData.pattern = patternMatches;
        await addBotMessage(`네, ${patternMatches[0]} 패턴을 제외하고 추천드릴게요! ✅`);
    } else {
        negativeData.pattern = [];
        await addBotMessage(`네, 모든 패턴을 포함해서 추천드릴게요! ✅`);
    }
    
    await askNegativePrice();
}

async function askNegativePrice() {
    await addBotMessage(
        "옷 한 벌에 최대 얼마까지 사용하시나요?\n\n" +
        "• 10만원\n" +
        "• 20만원\n" +
        "• 30만원\n" +
        "• 50만원"
    );
    conversationState = 'NEGATIVE_PRICE';
}

async function handleNegativePrice(userInput) {
    // 1. 입력값에서 숫자만 추출 (예: "40만원" -> 40, "약 15만" -> 15)
    const numberMatch = userInput.match(/\d+/);
    
    if (!numberMatch) {
        await addBotMessage("정확한 가격(숫자)을 말씀해 주시면 기준을 맞춰드릴 수 있어요! 🧐");
        return;
    }

    const inputNum = parseInt(numberMatch[0]);
    let threshold = 500000; // 기본값
    let label = '50만원';

    // 2. Ceiling(올림) 로직 적용
    if (inputNum <= 10) {
        threshold = 100000;
        label = '10만원';
    } else if (inputNum <= 20) {
        threshold = 200000;
        label = '20만원';
    } else if (inputNum <= 30) {
        threshold = 300000;
        label = '30만원';
    } else {
        // 30 초과 50 이하, 혹은 그 이상인 경우 모두 50으로 처리
        threshold = 500000;
        label = '50만원';
    }

    // 데이터 업데이트
    negativeData.price_threshold = threshold;

    // 3. 동적인 응답 메시지
    // 사용자가 입력한 숫자와 우리가 설정한 기준이 다를 때 "상위 기준으로 제안"하는 멘트 추가
    if (inputNum !== (threshold / 10000)) {
        await addBotMessage(`네, 말씀하신 금액을 고려해서, ${label} 이하의 상품들 위주로 넉넉하게 찾아볼게요! ✅`);
    } else {
        await addBotMessage(`네, ${label} 이하의 상품들로 필터링해서 추천해 드릴게요! ✅`);
    }

    // 백엔드로 전송
    try {
        await apiCall('/session/negatives', 'POST', negativeData);
        console.log('Negative 설정 완료:', negativeData);
    } catch (error) {
        console.error('Negative 설정 실패:', error);
    }
    
    await addBotMessage("좋아요! 선호도가 반영되었습니다. ✨");
    await sleep(1000);
    
    conversationState = 'TPO';
    await askTPO();
}

// ====================================
// TPO 조사
// ====================================
async function askTPO() {
    await addBotMessage(
        "이제 TPO를 알려주세요!\n\n" +
        "📌 TPO는 Time(시간), Place(장소), Occasion(상황)을 의미해요.\n\n" +
        "예시:\n" +
        "• 대학교 수업 듣고 친구랑 저녁 약속\n" +
        "• 친구 생일파티\n" +
        "• 회사 면접\n" +
        "• 애인과 데이트\n\n" +
        "어떤 하루를 보내실 건가요?"
    );
}

async function handleTPO(userInput) {
    try {
        // 로딩 메시지 추가
        const loadingMessage = document.createElement("div");
        loadingMessage.className = "message bot";
        
        loadingMessage.innerHTML = `
            <img src="images/lookie_black.svg" class="profile" alt="Lookie" />
            <div class="bubble-box bot">
                <div class="bubble-text" style="display: flex; align-items: center; gap: 8px;">
                    TPO를 분석하고 있어요
                    <div class="loading-dots-container" style="display: flex; gap: 6px; align-items: center;">
                        <div class="loading-dot" style="width: 10px; height: 10px; background: white; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.32s;"></div>
                        <div class="loading-dot" style="width: 10px; height: 10px; background: white; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.16s;"></div>
                        <div class="loading-dot" style="width: 10px; height: 10px; background: white; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both;"></div>
                    </div>
                </div>
            </div>
        `;
        
        chatFlow.appendChild(loadingMessage);
        scrollToBottom();
        
        // CSS 애니메이션 추가 (없을 경우)
        if (!document.getElementById('loading-animation-style')) {
            const style = document.createElement('style');
            style.id = 'loading-animation-style';
            style.textContent = `
                @keyframes bounce {
                    0%, 80%, 100% { 
                        transform: scale(0);
                        opacity: 0.5;
                    }
                    40% { 
                        transform: scale(1);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        const data = await apiCall('/session/tpo', 'POST', {
            tpo: userInput,
            persona: currentPersona
        });
        
        console.log('TPO 설정 완료:', data);
        
        // 로딩 메시지 제거
        loadingMessage.remove();
        
        // conflict 여부에 따른 메세지 내용 추가
        let conflictMessage = "";
        if (data.conflict) {
            conflictMessage = "오늘은 평소와 다른 스타일링이 필요하겠군요! 🎨\n새로운 시도를 위한 특별한 추천을 준비할게요.";
        } else {
            conflictMessage = "평소 스타일과 잘 어울리는 TPO네요! 👍\n당신의 페르소나에 딱 맞는 코디를 찾아드릴게요.";
        }
        await addBotMessage(conflictMessage);
        
        await sleep(800); // 약간의 딜레이
        
        await addBotMessage(
            `좋아요! "${data.refined_tpo}"에 맞는 스타일을 찾아드릴게요! 🎯\n\n` +
            "이제 상의부터 아이템별로 추천을 시작합니다!"
        );
        await sleep(1500);
        conversationState = 'RECOMMENDATION';
        await startRecommendation();
        
    } catch (error) {
        console.error('TPO 설정 실패:', error);
        await addBotMessage("TPO 분석 중 오류가 발생했어요. 다시 입력해주시겠어요?");
    }
}

// ====================================
// 추천 시작
// ====================================
async function startRecommendation() {
    await getNextRecommendation();
}

async function getNextRecommendation() {
    try {
        // 로딩 메시지 추가
        const loadingMessage = document.createElement("div");
        loadingMessage.className = "message bot";
        
        loadingMessage.innerHTML = `
            <img src="images/lookie_black.svg" class="profile" alt="Lookie" />
            <div class="bubble-box bot">
                <div class="bubble-text" style="display: flex; align-items: center; gap: 8px;">
                    추천 아이템을 찾고 있어요
                    <div class="loading-dots-container" style="display: flex; gap: 6px; align-items: center;">
                        <div class="loading-dot" style="width: 10px; height: 10px; background: white; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.32s;"></div>
                        <div class="loading-dot" style="width: 10px; height: 10px; background: white; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.16s;"></div>
                        <div class="loading-dot" style="width: 10px; height: 10px; background: white; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both;"></div>
                    </div>
                </div>
            </div>
        `;
        
        chatFlow.appendChild(loadingMessage);
        scrollToBottom();
        
        // CSS 애니메이션 추가 (없을 경우)
        if (!document.getElementById('loading-animation-style')) {
            const style = document.createElement('style');
            style.id = 'loading-animation-style';
            style.textContent = `
                @keyframes bounce {
                    0%, 80%, 100% { 
                        transform: scale(0);
                        opacity: 0.5;
                    }
                    40% { 
                        transform: scale(1);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        const data = await apiCall('/recommend/next', 'POST');
        
        // 로딩 메시지 제거
        await sleep(500);
        loadingMessage.remove();
        
        currentCategory = data.category;
        categoryIndex = data.category_index;
        
        console.log('받은 추천 데이터:', data.candidates); // 디버깅용
        
    if (data.candidates && data.candidates.length > 0) {
        // 🔥 백엔드 플래그로 체크 (기존 코드 삭제하고 이것만 추가)
        if (data.is_restored_from_previous) {
            await addBotMessage(
                "⚠️ 현재 조건에 맞는 새로운 아이템이 없어서 이전 추천 목록을 다시 보여드릴게요!\n\n" +
                "다른 조건으로 변경하거나, 마음에 드는 아이템을 선택해주세요. 😊"
            );
        }
        
        previousCandidates = data.candidates;
        await displayRecommendations(data.candidates, data.category, false);

        } else {
            await handleEmptyRecommendation();
        }
        
    } catch (error) {
        console.error('추천 실패:', error);
        await addBotMessage("추천 중 오류가 발생했어요. 다시 시도해주시겠어요?");
    }
}
// ====================================
// 추천 결과 표시 (수정됨)
// ====================================
async function displayRecommendations(candidates, category, showPreviousLabel = false) {
    currentCandidates = candidates;
    
    let message = `${category} 추천 결과예요! 😊\n\n` +
                  `마음에 드는 아이템을 클릭해서 선택하거나, 다른 옵션을 원하시면 피드백을 주세요!\n\n` +
                  `👉 세부 카테고리, 색상, 소재를 변경할 수 있어요.`;
    
    await addBotMessage(message);
    
    // 아이템 카드 표시
    await displayItemCards(candidates, showPreviousLabel);
}


async function displayItemCards(candidates, showPreviousLabel = false) {
    // 봇 메시지 형태로 카드 컨테이너를 추가
    const messageWrapper = document.createElement("div");
    messageWrapper.className = "message bot";
    messageWrapper.style.width = "100%";
    
    const cardsContainer = document.createElement("div");
    cardsContainer.className = "item-cards-wrapper";
    cardsContainer.style.cssText = `
        display: flex;
        gap: 20px;
        padding: 20px;
        overflow-x: auto;
        max-width: 100%;
        background: transparent;
    `;
    
    for (let i = 0; i < candidates.length; i++) {
        const item = candidates[i];
        console.log(`카드 ${i + 1} 데이터:`, item);
        
        // 🔥 핵심: _source 태그로 이전 추천 여부 판단
        const isPrevious = showPreviousLabel && item._source === 'previous';
        
        const card = createItemCard(item, i, isPrevious);
        cardsContainer.appendChild(card);
        
        // 카드 추가 애니메이션
        await sleep(150);
    }
    
    messageWrapper.appendChild(cardsContainer);
    chatFlow.appendChild(messageWrapper);
    scrollToBottom();
}

function createItemCard(item, index, isPrevious = false) {
    const card = document.createElement("div");
    card.className = "item-card";
    card.style.cssText = `
        min-width: 300px;
        max-width: 300px;
        border-radius: 16px;
        overflow: hidden;
        background: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        cursor: pointer;
        transition: transform 0.3s, box-shadow 0.3s;
        position: relative;
        flex-shrink: 0;
    `;
    
    const labelColor = isPrevious ? '#888' : '#4CAF50';
    const labelText = isPrevious ? '📌 이전 추천' : '🆕 새 추천';
    
    // 데이터 안전성 체크
    const imgUrl = item.img_url || 'https://via.placeholder.com/300x300?text=No+Image';
    const productName = item.product_name || '상품명 없음';
    const brand = item.brand || '브랜드 정보 없음';
    const price = item.price || '가격 정보 없음';
    const reason = item.reason || '추천 이유가 없습니다.';
    const itemUrl = item.item_url || '#';
    const color = item.color || 'N/A';
    const fit = item.fit || 'N/A';
    
    card.innerHTML = `
        ${isPrevious ? `
            <div style="
                position: absolute; 
                top: 10px; 
                left: 10px; 
                background: ${labelColor}; 
                color: white; 
                padding: 6px 12px; 
                border-radius: 20px; 
                font-size: 12px; 
                font-weight: 600;
                z-index: 10;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            ">${labelText}</div>
        ` : ''}
        <div style="position: relative; width: 100%; height: 300px; overflow: hidden; background: #f5f5f5;">
            <img src="${imgUrl}" alt="${productName}" 
                 style="width: 100%; height: 100%; object-fit: cover;" 
                 onerror="this.src='https://via.placeholder.com/300x300?text=No+Image'" />
        </div>
        <div style="padding: 16px;">
            <h3 style="margin: 0 0 8px 0; font-size: 15px; font-weight: 600; color: #333; line-height: 1.4; min-height: 42px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                ${productName}
            </h3>
            <p style="margin: 4px 0; font-size: 13px; color: #666; font-weight: 500;">
                ${brand}
            </p>
            <p style="margin: 12px 0; font-size: 20px; font-weight: 700; color: var(--bot-bubble-bg);">
                ${price}
            </p>
            <div style="margin: 12px 0; padding: 12px; background: #f8f9fa; border-radius: 8px; position: relative;">
                <div class="reason-container" style="max-height: 60px; overflow: hidden; transition: max-height 0.3s;">
                    <p style="margin: 0; font-size: 12px; color: #555; line-height: 1.6;">
                        💬 ${reason}
                    </p>
                </div>
                <button class="toggle-reason-btn" style="
                    margin-top: 8px;
                    padding: 4px 12px;
                    font-size: 11px;
                    color: #666;
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    cursor: pointer;
                    display: block;
                    width: 100%;
                " onclick="
                    event.stopPropagation();
                    const container = this.previousElementSibling;
                    if (container.style.maxHeight === '60px' || container.style.maxHeight === '') {
                        container.style.maxHeight = '1000px';
                        this.textContent = '접기 ▲';
                    } else {
                        container.style.maxHeight = '60px';
                        this.textContent = '더보기 ▼';
                    }
                ">더보기 ▼</button>
            </div>
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;">
                <p style="margin: 0 0 8px 0; font-size: 11px; color: #999;">
                    색상: ${color} | 핏: ${fit}
                </p>
                <a href="${itemUrl}" target="_blank" 
                   class="item-link"
                   style="
                       display: inline-block;
                       width: 100%;
                       padding: 10px 0;
                       text-align: center;
                       background: var(--bot-bubble-bg);
                       color: white;
                       text-decoration: none;
                       border-radius: 8px;
                       font-size: 13px;
                       font-weight: 600;
                       transition: opacity 0.3s;
                   "
                   onclick="event.stopPropagation();">
                    🔗 상품 페이지 보기
                </a>
            </div>
        </div>
    `;
    
    // 호버 효과
    card.onmouseenter = () => {
        card.style.transform = 'translateY(-8px) scale(1.02)';
        card.style.boxShadow = '0 12px 28px rgba(0,0,0,0.25)';
        
        const link = card.querySelector('.item-link');
        if (link) link.style.opacity = '0.9';
    };
    card.onmouseleave = () => {
        card.style.transform = 'translateY(0) scale(1)';
        card.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        
        const link = card.querySelector('.item-link');
        if (link) link.style.opacity = '1';
    };
    
    // 클릭 시 선택
    card.onclick = async (e) => {
        // 링크 클릭은 무시
        if (e.target.classList.contains('item-link') || e.target.closest('.item-link')) {
            return;
        }
        await selectItem(item);
    };
    
    return card;
}

// ====================================
// 아이템 선택
// ====================================
async function selectItem(item) {
    try {
        // 선택된 아이템을 user 메시지 형태로 표시
        const message = document.createElement("div");
        message.className = "message user";
        message.style.width = "100%";
        
        message.innerHTML = `
            <div style="display: flex; justify-content: flex-end; width: 100%;">
                <div style="
                    min-width: 300px;
                    max-width: 300px;
                    border-radius: 16px;
                    overflow: hidden;
                    background: white;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                ">
                    <div style="position: relative; width: 100%; height: 300px; overflow: hidden; background: #f5f5f5;">
                        <img src="${item.img_url}" alt="${item.product_name}" 
                             style="width: 100%; height: 100%; object-fit: cover;" 
                             onerror="this.src='https://via.placeholder.com/300x300?text=No+Image'" />
                    </div>
                    <div style="padding: 16px;">
                        <h3 style="margin: 0 0 8px 0; font-size: 15px; font-weight: 600; color: #333; line-height: 1.4;">
                            ${item.product_name}
                        </h3>
                        <p style="margin: 4px 0; font-size: 13px; color: #666; font-weight: 500;">
                            ${item.brand}
                        </p>
                        <p style="margin: 12px 0; font-size: 20px; font-weight: 700; color: var(--bot-bubble-bg);">
                            ${item.price}
                        </p>
                        <div style="margin: 12px 0; padding: 12px; background: #f8f9fa; border-radius: 8px; position: relative;">
                            <div class="reason-container" style="max-height: 60px; overflow: hidden; transition: max-height 0.3s;">
                                <p style="margin: 0; font-size: 12px; color: #555; line-height: 1.6;">
                                    💬 ${item.reason}
                                </p>
                            </div>
                            <button class="toggle-reason-btn" style="
                                margin-top: 8px;
                                padding: 4px 12px;
                                font-size: 11px;
                                color: #666;
                                background: white;
                                border: 1px solid #ddd;
                                border-radius: 4px;
                                cursor: pointer;
                            " onclick="
                                const container = this.previousElementSibling;
                                if (container.style.maxHeight === '60px' || container.style.maxHeight === '') {
                                    container.style.maxHeight = 'none';
                                    this.textContent = '접기 ▲';
                                } else {
                                    container.style.maxHeight = '60px';
                                    this.textContent = '더보기 ▼';
                                }
                            ">더보기 ▼</button>
                        </div>
                        <a href="${item.item_url}" target="_blank" 
                           style="
                               display: inline-block;
                               width: 100%;
                               padding: 10px 0;
                               text-align: center;
                               background: var(--bot-bubble-bg);
                               color: white;
                               text-decoration: none;
                               border-radius: 8px;
                               font-size: 13px;
                               font-weight: 600;
                               margin-top: 12px;
                           ">
                            🔗 상품 페이지 보기
                        </a>
                    </div>
                </div>
            </div>
        `;
        
        chatFlow.appendChild(message);
        scrollToBottom();
        
        const data = await apiCall('/select', 'POST', {
            product_id: item.product_id
        });
        
        const postL = ["상의", "바지", "아우터"];
        const postU = ["신발", "가방"];
        let postposition = "";
        if (postL.some(keyword => currentCategory.includes(keyword))){
            postposition = "를";
        }
        else if (postU.some(keyword => currentCategory.includes(keyword))){
            postposition = "을";
        }
        await addBotMessage(`좋아요! ${currentCategory}${postposition} 선택했습니다! ✨`);
        
        if (data.is_complete) {
            // 모든 추천 완료
            conversationState = 'COMPLETE';
            await showFinalResults();
        } else {
            // 다음 카테고리
            await sleep(1000);
            await addBotMessage(`다음은 ${data.next_category} 추천이에요!`);
            await sleep(1000);
            previousCandidates = null; // 다음 카테고리로 넘어가면 캐시 초기화
            await getNextRecommendation();
        }
        
    } catch (error) {
        console.error('선택 실패:', error);
        await addBotMessage("선택 처리 중 오류가 발생했어요. 다시 시도해주세요.");
    }
}

// ====================================
// 피드백 처리
// ====================================
async function handleFeedback(userInput) {
    const input = userInput.toLowerCase().replace(/\s/g, '');
    
    let feedbackType = null;
    
    if (input.includes('세부') || input.includes('카테고리')) {
        feedbackType = 'sub_cat_name';
    } else if (input.includes('색상') || input.includes('색')) {
        feedbackType = 'color';
    } else if (input.includes('소재')) {
        feedbackType = 'texture';
    }
    
    if (feedbackType) {
        await showFeedbackOptions(feedbackType);
        conversationState = `FEEDBACK_${feedbackType.toUpperCase()}`;
    } else {
        await addBotMessage(
            "조금 더 취향에 맞게 추천해드릴게요!\n\n" +
            "더 구체적인 추천을 위해 어떤 부분을 바꿔보면 좋을지 골라주세요!\n" +
            "• 세부 카테고리 변경\n" +
            "• 색상 변경\n" +
            "• 소재 변경"
        );
    }
}

async function showFeedbackOptions(feedbackType) {
    const options = DETAIL_MAP[feedbackType][currentCategory];
    
    const typeNameMap = {
        'sub_cat_name': '세부 카테고리',
        'color': '색상',
        'texture': '소재'
    };
    
    const typeName = typeNameMap[feedbackType];
    const optionsText = options.map(item => `• ${item}`).join('\n');

    const postLs = ["세부 카테고리", "소재"];
    const postUs = ["색상"];
    let postposition = "";
    if (postLs.some(keyword => typeName.includes(keyword))){
        postposition = "를";
    }
    else if (postUs.some(keyword => typeName.includes(keyword))){
        postposition = "을";
    }
    await addBotMessage(
        `${currentCategory}의 ${typeName}${postposition} 변경하시는군요!\n\n` +
        `다음 중 원하시는 것을 선택해주세요:\n\n` +
        `${optionsText}`
    );
}

async function applyFeedback(feedbackType, userInput) {

    const options = (DETAIL_MAP[feedbackType] || {})[currentCategory] || [];
    let selectedOptions = [];

    const SUB_CAT_ALIASES = {
        '긴소매 티셔츠':      ['긴팔'],
        '니트/스웨터':        ['니트', '스웨터'],
        '후드 티셔츠':        ['후드티', '후드'],
        '피케/카라 티셔츠':   ['피케', '카라'],
        '맨투맨/스웨트':      ['맨투맨', '스웨트'],
        '셔츠/블라우스':      ['셔츠', '블라우스'],
        '데님 팬츠':          ['데님', '청바지'],
        '코튼 팬츠':          ['코튼'],
        '슈트 팬츠/슬랙스':   ['슬랙스'],
        '트레이닝/조거 팬츠': ['트레이닝', '조거', '고무줄'],
        '롱패딩/헤비 아우터': ['롱패딩'],
        '무스탕/퍼':          ['무스탕', '퍼'],
        '플리스/뽀글이':      ['플리스', '뽀글이'],
        '겨울 싱글 코트':     ['코트'],
        '숏패딩/헤비 아우터': ['숏패딩'],
        '슈트/블레이저 재킷': ['블레이저', '재킷', '자켓', '수트'],
        '카디건':             ['가디건'],
        '후드 집업':          ['집업'],
        '스니커즈':           ['운동화'],
        '부츠/워커':          ['부츠', '워커'],
        '패딩/퍼 신발':       ['퍼신발', '털신발'],
        '백팩':               ['책가방'],
        '메신저/크로스 백':   ['메신저', '크로스'],
        '숄더백':             ['숄더'],
    };

    const COLOR_ALIASES = {
        '화이트': ['하얀', '흰색', '하얀색'],
        '블랙':   ['검정'],
        '그레이': ['회색'],
        '네이비': ['남색'],
        '브라운': ['갈색'],
        '핑크':   ['분홍'],
        '블루':   ['파란', '하늘'],
        '버건디': ['빨간', '빨강'],
    };

    if (feedbackType === 'sub_cat_name') {
        selectedOptions = options.filter(opt =>
            userInput.includes(opt) ||
            (SUB_CAT_ALIASES[opt] || []).some(alias => userInput.includes(alias))
        );
    } else if (feedbackType === 'color') {
        selectedOptions = options.filter(opt =>
            userInput.includes(opt) ||
            (COLOR_ALIASES[opt] || []).some(alias => userInput.includes(alias))
        );
    } else if (feedbackType === 'texture') {
        selectedOptions = options.filter(opt => userInput.includes(opt));
    }
    if (selectedOptions.length === 0) {
        await addBotMessage("일치하는 옵션을 찾지 못했어요. 다시 선택해주세요!");
        return;
    }
    
    try {
        // 로딩 메시지 추가
        const loadingMessage = document.createElement("div");
        loadingMessage.className = "message bot";
        
        loadingMessage.innerHTML = `
            <img src="images/lookie_black.svg" class="profile" alt="Lookie" />
            <div class="bubble-box bot">
                <div class="bubble-text" style="display: flex; align-items: center; gap: 8px;">
                    피드백을 반영해서 다시 추천드릴게요
                    <div class="loading-dots-container" style="display: flex; gap: 6px; align-items: center;">
                        <div class="loading-dot" style="width: 10px; height: 10px; background: white; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.32s;"></div>
                        <div class="loading-dot" style="width: 10px; height: 10px; background: white; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.16s;"></div>
                        <div class="loading-dot" style="width: 10px; height: 10px; background: white; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both;"></div>
                    </div>
                </div>
            </div>
        `;
    
        chatFlow.appendChild(loadingMessage);
        scrollToBottom();
        
        await apiCall('/feedback', 'POST', {
            type: feedbackType,
            value: selectedOptions
        });
        
        // 재추천
        const data = await apiCall('/recommend/next', 'POST');
        
        // 로딩 메시지 제거
        loadingMessage.remove();
        
        // 🔥 핵심 수정: 백엔드 플래그 체크 추가
        if (data.candidates && data.candidates.length > 0) {
            // ✅ 이전 추천 복구 여부 확인
            if (data.is_restored_from_previous) {
                await addBotMessage(
                    "⚠️ 현재 조건에 맞는 새로운 아이템이 없어서 이전 추천 목록을 다시 보여드릴게요!\n\n" +
                    "다른 조건으로 변경하거나, 마음에 드는 아이템을 선택해주세요. 😊"
                );
                
                // 이전 추천만 표시 (새 추천 없음)
                previousCandidates = data.candidates;
                await displayRecommendations(data.candidates, currentCategory, false);
            } else {
                // ✅ 새 추천이 있는 경우: 기존 로직대로 새 추천 + 이전 추천 합치기
                const allCandidates = [];
                
                // 새 추천의 product_id 수집 (중복 체크용)
                const newProductIds = new Set();
                data.candidates.forEach(item => {
                    item._source = 'new';  // ✅ 새 추천 표시
                    allCandidates.push(item);
                    newProductIds.add(item.product_id);
                });
                
                // 이전 추천 추가 (중복 제거: 새 추천에 없는 것만)
                if (previousCandidates && previousCandidates.length > 0) {
                    previousCandidates.forEach(item => {
                        if (!newProductIds.has(item.product_id)) {
                            item._source = 'previous';  // ✅ 이전 추천 표시
                            allCandidates.push(item);
                        }
                    });
                }
                
                // 🔥 핵심: 현재 추천을 이전 추천으로 백업 (다음 피드백을 위해)
                previousCandidates = allCandidates.slice();  // 전체 복사
                
                await displayRecommendations(allCandidates, currentCategory, true);  // ✅ showPreviousLabel=true
            }
        } else {
            await handleEmptyRecommendation();
        }
        
        conversationState = 'RECOMMENDATION';
        
    } catch (error) {
        console.error('피드백 적용 실패:', error);
        await addBotMessage("피드백 적용 중 오류가 발생했어요. 다시 시도해주세요.");
    }
}

// ====================================
// 빈 추천 처리 (문제 2 해결)
// ====================================
async function handleEmptyRecommendation() {
    await addBotMessage(
        "아쉽게도 현재 조건에 맞는 아이템이 없어요. 😢\n\n" +
        "다음 옵션을 선택해주세요:\n\n" +
        "1️⃣ 이전 추천 목록 보기\n" +
        "2️⃣ 조건 완화하기"
    );
    
    conversationState = 'EMPTY_CHOICE';
}

async function handleEmptyChoice(userInput) {
    const input = userInput.replace(/\s/g, '').toLowerCase();
    
    if (input.includes('1') || input.includes('이전')) {
        // 이전 추천 복구
        if (previousCandidates && previousCandidates.length > 0) {
            await addBotMessage("이전 추천 목록을 다시 보여드릴게요!");
            await displayRecommendations(previousCandidates, currentCategory, false);
            conversationState = 'RECOMMENDATION';  // ✅ 정상 추천 상태로 복귀
        } else {
            await addBotMessage(
                "이전 추천 목록이 없어요. 😢\n\n" +
                "조건을 완화해볼까요? (2번 입력)"
            );
            // conversationState는 'EMPTY_CHOICE' 유지 (재입력 대기)
        }
    } else if (input.includes('2') || input.includes('완화')) {
        await addBotMessage(
            "조건을 완화하기 위해 비선호 요소를 다시 설정할게요!\n\n" +
            "먼저, 비선호하는 핏이 있나요?\n\n" +
            "• 오버사이즈\n" +
            "• 슬림\n" +
            "• 없음"
        );
        conversationState = 'NEGATIVE';  // ✅ 비선호 조사부터 다시 시작
    } else {
        // 🔥 추가: 잘못된 입력 처리
        await addBotMessage(
            "죄송해요, 이해하지 못했어요. 😅\n\n" +
            "1️⃣ 이전 추천 목록 보기\n" +
            "2️⃣ 조건 완화하기\n\n" +
            "중 하나를 선택해주세요!"
        );
        // conversationState는 'EMPTY_CHOICE' 유지 (재입력 대기)
    }
}
// ====================================
// 최종 결과
// ====================================
async function showFinalResults() {
    await addBotMessage("코디 추천이 완료되었어요! 🎉\n\n최종 코디를 확인하고 있어요...");
    
    try {
        const data = await apiCall('/show_all', 'GET');
        
        // 결과를 로컬 스토리지에 저장
        localStorage.setItem('finalOutfit', JSON.stringify(data));
        
        await addBotMessage(
            `완벽한 코디가 완성되었어요! ✨\n\n` +
            `TPO: ${data.tpo}\n` +
            `총 ${data.total_count}개의 아이템이 선택되었습니다!\n\n` +
            `결과 페이지로 이동할게요!`
        );
        
        await sleep(2000);
        
        // 결과 페이지로 이동 (persona 파라미터 포함)
        window.location.href = `result.html?persona=${currentPersona}`;
        
    } catch (error) {
        console.error('최종 결과 조회 실패:', error);
        await addBotMessage("결과를 불러오는 중 오류가 발생했어요. 😢");
    }
}

// ====================================
// 사용자 입력 처리
// ====================================
function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;
    
    addUserMessage(text);
    userInput.value = "";
    
    // 상태에 따라 처리
    handleUserInput(text);
}

async function handleUserInput(text) {
    switch (conversationState) {
        case 'NEGATIVE':
            await handleNegativeFit(text);
            break;
            
        case 'NEGATIVE_PATTERN':
            await handleNegativePattern(text);
            break;
            
        case 'NEGATIVE_PRICE':
            await handleNegativePrice(text);
            break;
            
        case 'TPO':
            await handleTPO(text);
            break;
            
        case 'RECOMMENDATION':
            await handleFeedback(text);
            break;
            
        case 'FEEDBACK_SUB_CAT_NAME':
            await applyFeedback('sub_cat_name', text);
            break;
            
        case 'FEEDBACK_COLOR':
            await applyFeedback('color', text);
            break;
            
        case 'FEEDBACK_TEXTURE':
            await applyFeedback('texture', text);
            break;
            
        case 'EMPTY_CHOICE':
            await handleEmptyChoice(text);
            break;
            
        default:
            await addBotMessage("죄송해요, 이해하지 못했어요. 😅");
    }
}

// ====================================
// 이벤트 리스너
// ====================================
userInput.addEventListener("keydown", (e) => {
    if (e.isComposing || e.keyCode === 229) return;
    if (e.key === "Enter") {
        e.preventDefault();
        sendMessage();
    }
});

// 페이지 이탈 시 확인
window.addEventListener('beforeunload', (e) => {
    if (conversationState !== 'COMPLETE' && sessionId) {
        e.preventDefault();
        e.returnValue = '';
    }
});

// ====================================
// 페이지 로드 시 초기화
// ====================================
window.addEventListener('DOMContentLoaded', () => {
    initialize();
    addExitButton(); // 나가기 버튼 추가
});

const logoLink = document.querySelector('.logo-link');
if (logoLink) {
    logoLink.addEventListener('click', async (e) => {
        e.preventDefault();
        
        // 세션 삭제 (확인창 없이 바로 삭제)
        try {
            if (sessionId) {
                await apiCall('/session/delete', 'DELETE');
                console.log('CORDE 로고 클릭 - 세션 삭제 완료');
            }
        } catch (error) {
            console.error('세션 삭제 실패:', error);
        }
        
        // home.html로 이동
        window.location.href = 'home.html';
    });
}