// js/main.js

// 1. UI 및 초기화 로직
document.addEventListener('DOMContentLoaded', function() {
    updateAuthButton(); // 로그인 버튼 상태 업데이트
    initChatSidebar();
    // 사이드바의 '모집글 신청' 버튼 이벤트 연결
    const modal = document.querySelector('.modal');
    const modalBtn = document.querySelector('.modal_btn'); 
    const closeBtn = document.querySelector('.close_btn');

    // 1-1. 모달 열기
    if (modalBtn && modal) {
        modalBtn.addEventListener('click', function() {
            if (!checkAuth()) {
                alert("로그인이 필요한 서비스입니다.");
                window.location.href = 'login.html';
                return;
            }
            modal.style.display = 'block';
        });
    }

    // 1-2. 모달 닫기
    if (closeBtn && modal) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
});

// UI 관련 함수들
function updateAuthButton() {
    const isAuthenticated = checkAuth();
    const authButton = document.getElementById('authButton');
    if (!authButton) return;

    if (isAuthenticated) {
        authButton.textContent = '로그아웃';
        authButton.href = '#';
        
        // main.js에서는 물어보지 않고 바로 logout() 함수를 부름 (수정했음)
        authButton.onclick = (e) => {
            e.preventDefault();
            logout(); 
        };
    } else {
        authButton.textContent = '로그인/회원가입';
        authButton.href = 'login.html';
        authButton.onclick = null;
    }
}


// 로딩 화면 표시/숨김 함수
function showLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
    }
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

// 2. 모집글 등록 로직
async function submitRecruitment() {
    if (!checkAuth()) {
        alert("로그인이 필요합니다.");
        window.location.href = 'login.html';
        return;
    }

    const productUrl = document.getElementById('productUrl').value;
    const targetHeadcount = document.getElementById('targetHeadcount').value;
    const title = document.getElementById('recruitTitle').value;
    const content = document.getElementById('recruitContent').value;
    const endDate = document.getElementById('recruitEndDate').value;
    
    if (!productUrl || !targetHeadcount || !title || !content || !endDate) {
        alert("모든 항목을 입력해주세요.");
        return;
    }

    const regex = /products\/(\d+)/; 
    const match = productUrl.match(regex);
    let productNumber;

    if (match && match[1]) {
        productNumber = parseInt(match[1], 10);
        console.log(`추출된 제품 ID (숫자): ${productNumber}`);
    } else {
        alert("상품 URL에서 유효한 제품 ID를 찾을 수 없습니다.");
        console.error(`URL에서 제품 ID를 찾을 수 없습니다: ${productUrl}`);
        return; 
    }

    // 로딩 화면 표시
    showLoading();
    
    try {
        await registerGroupBuy(productNumber, productUrl, targetHeadcount, title, content, endDate);
    } finally {
        // 성공/실패와 관계없이 로딩 화면 숨김
        hideLoading();
    }
}


// 3. API 호출 및 처리 함수
async function registerGroupBuy(productNumber, productUrl, targetHeadcount, title, content, endDate) { 

    const token = getToken(); 

    const headers = {
        'Content-Type': 'application/json', 
        'Authorization': `Bearer ${token}` 
    };
    
    try {
        let success = false;
        
        // 1. GET 요청 (URL 유효성 확인)
        const urlParams = new URLSearchParams({ url: productUrl });
        const responseGet = await fetch(`${API_BASE}/api/groupbuys/attempt?${urlParams}`, {
            method: 'GET',
            headers: headers
        });
        
        // 응답 처리 (JSON 또는 텍스트)
        let validationResult;
        const contentType = responseGet.headers.get('content-type') || '';
        
        try {
            if (contentType.includes('application/json')) {
                validationResult = await responseGet.json();
            } else {
                const textResult = await responseGet.text();
                // 텍스트가 JSON 형태인지 확인
                try {
                    validationResult = JSON.parse(textResult);
                } catch {
                    // 순수 텍스트인 경우
                    validationResult = textResult;
                }
            }
        } catch (e) {
            console.error('응답 파싱 오류:', e);
            validationResult = await responseGet.text();
        }
        
        // 검증 결과 확인
        const isValid = responseGet.ok && (
            validationResult === 'success' ||
            (typeof validationResult === 'object' && validationResult.success === true) ||
            (typeof validationResult === 'object' && validationResult.message === 'success')
        );
        if (!isValid) {
            // 검증 실패
            let errorMsg = '입력 정보를 확인해주세요.';
            if (typeof validationResult === 'object') {
                errorMsg = validationResult.message || validationResult.error || errorMsg;
            } else if (typeof validationResult === 'string') {
                errorMsg = validationResult;
            }
            alert(`등록 확인 실패: ${errorMsg}`);
            return;
        }
        
        // 2. POST 요청 (등록) - 검증 성공 시
        productNumber = validationResult.productNumber;
        const postData = {
            productId: productNumber,         
            targetHeadcount: parseInt(targetHeadcount, 10),
            title: title,                   
            content: content,               
            recruit_end_date: endDate         
        };

        const responsePost = await fetch(`${API_BASE}/api/groupbuys/online`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(postData) 
        });
        
        if (responsePost.ok) { 
            success = true;
        } else {
            let errorMessage = '서버 오류';
            try {
                const errorJson = await responsePost.json();
                errorMessage = errorJson.message || errorJson.error || errorMessage;
            } catch (e) {
                try {
                    const errorText = await responsePost.text();
                    errorMessage = errorText || errorMessage;
                } catch (e2) {
                    errorMessage = `HTTP ${responsePost.status}`;
                }
            }
            throw new Error(`모집글 등록 실패: ${errorMessage}`);
        }

        if (success) {
            alert("모집글이 성공적으로 등록되었습니다!");
            document.querySelector('.modal').style.display = 'none';
            window.location.reload(); 
        }
        
    } catch (error) {
        console.error("등록 처리 중 오류 발생:", error);
        alert("글 등록 처리 중 오류가 발생했습니다: " + error.message);
        // 에러 발생 시에도 로딩 화면은 hideLoading()에서 처리됨
    }
}
// ==========================================
// 2. 신규 기능: 실시간 채팅 사이드바 연동
// ==========================================

// 채팅 기능 초기화 함수
function initChatSidebar() {
    const chatListContainer = document.getElementById('chatListContainer');
    
    // 1. 로그인 여부 확인 (토큰 존재 여부)
    const token = localStorage.getItem('accessToken'); 

    if (!token) {
        // 비로그인 상태면 안내 문구 표시
        if(chatListContainer) {
            chatListContainer.innerHTML = '<li style="padding:8px; text-align:center; color:#888;">로그인이 필요합니다.</li>';
        }
        return; 
    }

    // 2. 로그인 상태라면: 초기 데이터 로드 + 소켓 연결
    loadChatRooms(token); 
    connectWebSocket(token);
}

// [API] 채팅방 목록 불러오기 (REST API)
async function loadChatRooms(token) {
    try {
        // FIXME: 백엔드 API 주소 확인 필요 (예: /api/chat/rooms)
        const response = await fetch('/api/chat/rooms', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const rooms = await response.json();
            renderChatList(rooms); // 화면 그리기
        } else {
            console.error('채팅 목록 로드 실패:', response.status);
        }
    } catch (error) {
        console.error('채팅 목록 에러:', error);
    }
}

// [UI] 채팅방 목록 화면에 그리기
function renderChatList(rooms) {
    const chatListContainer = document.getElementById('chatListContainer');
    if (!chatListContainer) return;

    chatListContainer.innerHTML = ''; // 기존 목록 초기화

    if (rooms.length === 0) {
        chatListContainer.innerHTML = '<li style="padding:10px; color:#888;">참여 중인 채팅방이 없습니다.</li>';
        return;
    }

    rooms.forEach(room => {
        // li 요소 생성
        const li = document.createElement('li');
        li.className = 'chat-item'; // CSS 스타일링용 클래스
        
        // 안 읽은 메시지 배지 처리
        const badgeHtml = room.unreadCount > 0 
            ? `<span class="badge">${room.unreadCount}</span>` 
            : '';

        // 클릭 시 해당 채팅방으로 이동 (chat.html)
        li.innerHTML = `
            <a href="chat.html?roomId=${room.roomId}" style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                <span class="room-name">${room.roomName}</span>
                ${badgeHtml}
            </a> 
        `;
        chatListContainer.appendChild(li);
    });
}

// [Socket] 실시간 소켓 연결 (WebSocket)
function connectWebSocket(token) {
    // FIXME: 백엔드 소켓 주소 확인 필요 (ws:// 또는 wss://)
    const socketUrl = 'ws://together1.kro.kr:8080/ws/chat'; 
    let socket;

    try {
        socket = new WebSocket(socketUrl);
    } catch (e) {
        console.error('소켓 생성 실패:', e);
        return;
    }

    socket.onopen = function() {
        console.log('실시간 채팅 서버 연결됨');
        // 필요하다면 연결 후 인증 토큰을 전송하는 로직 추가
        // socket.send(JSON.stringify({ type: 'AUTH', token: token }));
    };

    socket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);

            // FIXME: 백엔드에서 정한 이벤트 타입 확인 필요 (예: 'NEW_MESSAGE', 'ROOM_UPDATE')
            if (data.type === 'NEW_MESSAGE' || data.type === 'ROOM_UPDATE') {
                console.log('새 메시지 감지! 목록을 갱신합니다.');
                
                // 화면을 새로고침하지 않고 목록만 다시 불러옴
                loadChatRooms(token);
            }
        } catch (e) {
            console.error('소켓 데이터 파싱 에러:', e);
        }
    };

    socket.onclose = function() {
        console.log('채팅 서버 연결 끊김. 5초 후 재연결 시도...');
        setTimeout(() => connectWebSocket(token), 5000);
    };
}
