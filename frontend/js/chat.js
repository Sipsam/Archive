// chat.js - 실시간 채팅 로직 (백엔드 연동)

let currentRoomId = null;
let currentUser = null;
let socket = null;

// [설정] 웹소켓 주소
const WS_BASE_URL = '';

document.addEventListener('DOMContentLoaded', async function() {
    // 1. 로그인 체크
    if (!checkAuth()) {
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return;
    }

    // 2. URL에서 방 번호(roomId) 가져오기
    const urlParams = new URLSearchParams(window.location.search);
    currentRoomId = urlParams.get('roomId');

    if (!currentRoomId) {
        alert('잘못된 접근입니다. (채팅방 정보 없음)');
        window.location.href = 'index.html';
        return;
    }

    // 3. 내 정보 가져오기 (내가 쓴 글 구분용)
    try {
        currentUser = await apiFetch('/api/users/me');
    } catch (e) {
        console.error('유저 정보 로드 실패', e);
    }

    // 4. 초기화 실행
    await loadChatHistory(); // 기존 대화 불러오기
    connectWebSocket();      // 소켓 연결하기
    setupEventListeners();   // 버튼 이벤트 연결
    
    // UI 타이틀 설정
    document.querySelector('.page-title').textContent = `채팅방`;
});

// --- 기능 함수들 ---

// 1. 지난 대화 내용 불러오기 (API 호출)
async function loadChatHistory() {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    try {
        // 백엔드에서 메시지 목록 가져오기
        const messages = await apiFetch(`/api/chat/rooms/${currentRoomId}/messages`);
        
        messagesContainer.innerHTML = ''; // 기존 내용 초기화

        if (!messages || messages.length === 0) {
            messagesContainer.innerHTML = '<div style="text-align:center; color:#999; padding:20px;">대화 내용이 없습니다.</div>';
            return;
        }

        messages.forEach(msg => {
            appendMessageToUI(msg);
        });

        scrollToBottom();

    } catch (error) {
        console.error('채팅 내역 로드 실패:', error);
    }
}

// 2. 화면에 메시지 그리기
function appendMessageToUI(msg) {
    const messagesContainer = document.getElementById('chatMessages');
    
    // 내가 보낸 메시지인지 확인
    const isMyMessage = (msg.senderId === currentUser.id);
    
    // 시간 포맷 (예: 14:30)
    const date = new Date(msg.sentAt);
    const timeStr = String(date.getHours()).padStart(2, '0') + ':' + String(date.getMinutes()).padStart(2, '0');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isMyMessage ? 'sent' : 'received'}`;
    
    // 상대방 메시지면 닉네임 표시
    const nameHtml = !isMyMessage ? `<div style="font-size:12px; color:#666; margin-bottom:4px;">${msg.senderNickname}</div>` : '';

    messageDiv.innerHTML = `
        ${nameHtml}
        <div class="message-content">${msg.message}</div>
        <div class="message-time">${timeStr}</div>
    `;
    
    // "대화 내용 없음" 안내 문구가 있다면 제거
    if (messagesContainer.firstChild && messagesContainer.firstChild.innerText === '대화 내용이 없습니다.') {
        messagesContainer.innerHTML = '';
    }

    messagesContainer.appendChild(messageDiv);
}

// 3. 웹소켓 연결 (실시간 통신)
function connectWebSocket() {
    const token = getToken();
    if (!token) return;

    // 토큰을 쿼리 파라미터로 전달
    const socketUrl = `${WS_BASE_URL}?token=${token}`;

    socket = new WebSocket(socketUrl);

    socket.onopen = function() {
        console.log('채팅 서버에 연결되었습니다.');
    };

    socket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            
            // 백엔드에서 '새 메시지 왔다'는 신호(NEW_MESSAGE)를 받으면
            if (data.type === 'NEW_MESSAGE') {
                // 현재 방에 온 메시지라면 목록 새로고침
                if (String(data.roomId) === String(currentRoomId)) {
                    loadChatHistory(); 
                }
            }
        } catch (e) {
            console.error('메시지 파싱 에러:', e);
        }
    };

    socket.onclose = function() {
        console.log('연결 종료. 3초 후 재연결...');
        setTimeout(connectWebSocket, 3000);
    };
}

// 4. 메시지 전송
function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        alert('서버와 연결되지 않았습니다. 잠시만 기다려주세요.');
        return;
    }

    // 백엔드 DTO 양식에 맞춰 전송
    const payload = {
        type: "CHAT",
        roomId: parseInt(currentRoomId),
        message: message
    };

    socket.send(JSON.stringify(payload));
    input.value = ''; // 입력창 비우기
}

// 이벤트 리스너 설정
function setupEventListeners() {
    // 전송 버튼
    const sendBtn = document.querySelector('.send-btn');
    if (sendBtn) {
        // 기존 onclick 제거하고 새로 연결
        sendBtn.onclick = null;
        sendBtn.addEventListener('click', sendMessage);
    }

    // 엔터키 입력
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
