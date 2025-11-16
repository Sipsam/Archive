// 채팅 페이지 JavaScript
function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) {
        return;
    }
    
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message sent';
    
    const now = new Date();
    const time = now.getHours() + ':' + String(now.getMinutes()).padStart(2, '0');
    
    messageDiv.innerHTML = `
        <div class="message-content">${message}</div>
        <div class="message-time">${time}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    input.value = '';
    
    // 스크롤을 맨 아래로
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // 자동 응답 (시뮬레이션)
    setTimeout(() => {
        const responseDiv = document.createElement('div');
        responseDiv.className = 'message received';
        const responseTime = new Date();
        const responseTimeStr = responseTime.getHours() + ':' + String(responseTime.getMinutes()).padStart(2, '0');
        
        responseDiv.innerHTML = `
            <div class="message-content">네, 알겠습니다!</div>
            <div class="message-time">${responseTimeStr}</div>
        `;
        
        messagesContainer.appendChild(responseDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 1000);
}

document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatInput');
    
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // 채팅 목록 클릭 이벤트
    const chatItems = document.querySelectorAll('.chat-item');
    chatItems.forEach(item => {
        item.addEventListener('click', function() {
            chatItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            const chatName = this.querySelector('.chat-name').textContent;
            const chatHeader = document.querySelector('.chat-partner span');
            if (chatHeader) {
                chatHeader.textContent = chatName;
            }
        });
    });
});

