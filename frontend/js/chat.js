// frontend/js/chat.js

let currentRoomId = null;
let currentUser = null;
let socket = null;

// [설정] 웹소켓 주소
const WS_BASE_URL = 'ws://together1.kro.kr/ws/chat?token='+localStorage.getItem('accessToken'); 

document.addEventListener('DOMContentLoaded', async function() {
    // 1. 로그인 체크
    if (!checkAuth()) {
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return;
    }

    // 2. 내 정보 가져오기 (메시지 보낼 때 내 ID 확인용)
    try {
        currentUser = await apiFetch('/api/users/me');
    } catch (e) {
        console.error('유저 정보 로드 실패', e);
        return;
    }

    // 3. 채팅방 목록(내 참여 공구 목록) 로드
    await loadChatRoomList();
});

// --- 기능 1: 채팅방 목록 로드 (공구 제목 표시) ---
async function loadChatRoomList() {
    const listContainer = document.getElementById('chatRoomList');
    if (!listContainer) return;

    try {
        // 백엔드의 "내 참여 내역" API를 재활용하여 채팅방 목록을 구성합니다.
        const data = await apiFetch('/api/users/me/participations');
        
        // 온라인/오프라인 참여 내역 합치기 (필요시) - 지금은 온라인만 예시
        const onlineList = data.onlineParticipations || [];
        
        listContainer.innerHTML = ''; // 초기화

        // 채팅방이 있는 공구만 필터링
        const chatRooms = onlineList.filter(item => item.onlineGroupBuy && item.onlineGroupBuy.chatRoomId);

        if (chatRooms.length === 0) {
            listContainer.innerHTML = '<div style="padding:20px; text-align:center; color:#999;">참여 중인 채팅방이 없습니다.</div>';
            return;
        }

        // URL 파라미터에 roomId가 있다면 미리 선택
        const urlParams = new URLSearchParams(window.location.search);
        const urlRoomId = urlParams.get('roomId');

        chatRooms.forEach(item => {
            const groupBuy = item.onlineGroupBuy;
            const roomId = groupBuy.chatRoomId;
            const roomTitle = groupBuy.title || '제목 없는 공구방';

            // 목록 아이템 생성
            const div = document.createElement('div');
            div.className = 'chat-item';
            if (String(roomId) === String(urlRoomId)) {
                div.classList.add('active'); // 선택된 스타일
                selectRoom(roomId, roomTitle); // 바로 입장
            }
            
            div.innerHTML = `
                <div class="chat-avatar" style="font-size:16px;">💬</div>
                <div class="chat-info">
                    <div class="chat-name">${roomTitle}</div>
                    <div class="chat-preview" style="font-size:12px; color:#888;">참여 중인 공구 채팅방</div>
                </div>
            `;

            // 클릭 이벤트 연결
            div.addEventListener('click', () => {
                // 기존 active 제거 및 현재 클릭 활성화
                document.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
                div.classList.add('active');
                
                selectRoom(roomId, roomTitle);
            });

            listContainer.appendChild(div);
        });

    } catch (error) {
        console.error('채팅방 목록 로드 실패:', error);
        listContainer.innerHTML = '<div style="padding:20px; color:red;">목록을 불러오지 못했습니다.</div>';
    }
}

// --- 기능 2: 채팅방 선택 및 입장 ---
async function selectRoom(roomId, roomTitle) {
    if (currentRoomId === roomId) return; // 이미 들어와 있으면 무시
    
    currentRoomId = roomId;
    
    // UI 업데이트
    document.getElementById('chatRoomTitle').textContent = roomTitle;
    document.getElementById('chatInput').disabled = false;
    document.getElementById('sendBtn').disabled = false;

    // 기존 소켓 연결 끊기 (방 이동 시)
    if (socket) {
        socket.close();
    }

    // 메시지 내역 불러오기
    await loadChatHistory(roomId);

    // 새 소켓 연결
    connectWebSocket(roomId);
}

// --- 기능 3: 지난 대화 내용 불러오기 ---
async function loadChatHistory(roomId) {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = ''; // 초기화
    
    try {
        const messages = await apiFetch(`/api/chat/rooms/${roomId}/messages`);
        
        if (!messages || messages.length === 0) {
            messagesContainer.innerHTML = '<div style="text-align:center; color:#999; padding:20px;">대화 내용이 없습니다. 첫 메시지를 남겨보세요!</div>';
            return;
        }

        messages.forEach(msg => appendMessageToUI(msg));
        scrollToBottom();

    } catch (error) {
        console.error('채팅 내역 로드 실패:', error);
    }
}

// --- 기능 4: 화면에 메시지 그리기 ---
function appendMessageToUI(msg) {
    const messagesContainer = document.getElementById('chatMessages');
    
    // "대화 내용 없음" 안내 문구 제거
    if (messagesContainer.innerText.includes('대화 내용이 없습니다')) {
        messagesContainer.innerHTML = '';
    }

    const isMyMessage = (msg.senderId === currentUser.id);
    const date = new Date(msg.sentAt);
    const timeStr = String(date.getHours()).padStart(2, '0') + ':' + String(date.getMinutes()).padStart(2, '0');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isMyMessage ? 'sent' : 'received'}`;
    
    // 상대방 메시지일 때만 닉네임 표시
    const nameHtml = !isMyMessage ? `<div style="font-size:12px; color:#666; margin-bottom:4px;">${msg.senderNickname || '알 수 없음'}</div>` : '';

    messageDiv.innerHTML = `
        ${nameHtml}
        <div class="message-content">${msg.message}</div>
        <div class="message-time">${timeStr}</div>
    `;

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// --- 기능 5: 웹소켓 연결 ---
function connectWebSocket(roomId) {
    const token = getToken();
    if (!token) return;

    // 쿼리 파라미터로 토큰과 방 번호 전달
    socket = new WebSocket(WS_BASE_URL);

    socket.onopen = function() {
        console.log(`채팅방 ${roomId} 연결 성공`);
        // 입장 메시지 혹은 인증 메시지가 필요하다면 여기서 send
        // 예: socket.send(JSON.stringify({ type: 'ENTER', roomId: roomId, token: token }));
    };

    socket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            
            // 현재 보고 있는 방의 메시지만 표시
            if (String(data.roomId) === String(currentRoomId) && data.type === 'CHAT') {
                // 메시지 형식이 단순 텍스트가 아니라 객체라고 가정
                appendMessageToUI({
                    senderId: data.senderId,
                    senderNickname: data.senderNickname,
                    message: data.message,
                    sentAt: data.sentAt || new Date()
                });
            }
        } catch (e) {
            console.error('소켓 메시지 파싱 에러:', e);
        }
    };

    socket.onclose = function() {
        console.log('소켓 연결 종료');
    };
}

// --- 기능 6: 메시지 전송 ---
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        alert('채팅 서버와 연결되지 않았습니다.');
        return;
    }

    const payload = {
        type: "CHAT", // 백엔드 Enum 타입과 일치해야 함
        roomId: parseInt(currentRoomId),
        message: message
    };

    socket.send(JSON.stringify(payload));
    input.value = ''; // 입력창 비우기
    
    // 이 부분은 논의 필요함. 오프라인 회의 때 결정
    // (선택 사항) 내가 보낸 메시지를 즉시 화면에 띄우고 싶다면:
    // appendMessageToUI({ ...payload, senderNickname: currentUser.nickname, sentAt: new Date() });
    // 하지만 보통 소켓 onmessage로 다시 받는 것을 권장합니다.
}

// UI 헬퍼
function scrollToBottom() {
    const container = document.getElementById('chatMessages');
    container.scrollTop = container.scrollHeight;
}

// 이벤트 리스너 연결
const sendBtn = document.getElementById('sendBtn');
const chatInput = document.getElementById('chatInput');

if (sendBtn) sendBtn.addEventListener('click', sendMessage);
if (chatInput) {
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
}

    });
}
