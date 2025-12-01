// frontend/js/main.js

document.addEventListener('DOMContentLoaded', async function() {
    // 기존 초기화 로직
    updateAuthButton(); 
    initChatSidebar();
    setupModalEvents(); // 모달 이벤트 연결 함수 호출

    // 검색 버튼 및 엔터키 이벤트 연결
    const searchBtn = document.getElementById('searchButton');
    const searchInput = document.getElementById('searchInput');

    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', () => searchGroupBuys(searchInput.value));
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchGroupBuys(searchInput.value);
        });
    }

    // 초기 화면: 인기 모집글 3개 로드
    await loadPopularGroupBuys();
});

// ==========================================
// 수정 : 인기 모집글 및 검색 기능
// ==========================================

// 인기 모집글 로드 함수
async function loadPopularGroupBuys() {
    const contentGrid = document.getElementById('contentGrid');
    if (!contentGrid) return;

    try {
        const groupBuys = await apiFetch('/api/groupbuys/online');
        
        // 참여자 수(participationList 크기) 기준으로 내림차순 정렬 후 상위 3개 자르기
        const popularList = groupBuys
            .sort((a, b) => (b.participationList?.length || 0) - (a.participationList?.length || 0))
            .slice(0, 3);

        if (popularList.length === 0) {
            contentGrid.innerHTML = '<p style="text-align:center; color:#888; grid-column:1/-1; padding: 40px;">등록된 모집글이 없습니다.</p>';
            return;
        }

        // 화면 그리기
        contentGrid.innerHTML = '<h3 style="grid-column:1/-1; margin-bottom:10px; color:#4a90e2;">🔥 지금 핫한 모집글</h3>';
        popularList.forEach(gb => renderCard(gb, contentGrid));

    } catch (error) {
        console.error('인기글 로드 실패:', error);
    }
}

// 검색 함수
async function searchGroupBuys(keyword) {
    const contentGrid = document.getElementById('contentGrid');
    if (!contentGrid) return;

    if (!keyword.trim()) {
        alert('검색어를 입력해주세요.');
        return;
    }

    try {
        // 전체 목록 가져와서 필터링
        const groupBuys = await apiFetch('/api/groupbuys/online');
        const results = groupBuys.filter(gb => 
            gb.title.includes(keyword) || (gb.product && gb.product.name.includes(keyword))
        );

        contentGrid.innerHTML = ''; // 초기화

        if (results.length === 0) {
            // 결과 없음 문구 표시
            contentGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 50px; color: #666;">
                    <p style="font-size: 18px; font-weight: bold;">'${keyword}'에 대한 검색 결과가 없습니다.</p>
                    <p style="font-size: 14px; margin-top: 10px;">아직 모집글이 등록되지 않았습니다!</p>
                </div>`;
            return;
        }

        contentGrid.innerHTML = `<h3 style="grid-column:1/-1; margin-bottom:10px;">'${keyword}' 검색 결과</h3>`;
        results.forEach(gb => renderCard(gb, contentGrid));

    } catch (error) {
        console.error('검색 실패:', error);
    }
}

// 카드 그리기 헬퍼 함수
function renderCard(groupBuy, container) {
    const product = groupBuy.product;
    const currentCount = groupBuy.participationList?.length || 0;
    
    const card = document.createElement('div');
    card.className = 'content-card';
    card.onclick = () => window.location.href = `recruitment-detail.html?id=${groupBuy.id}`;

    // HTML에서 이미지가 들어갈 요소를 선택
    const imageEl = document.getElementById('productImage');

    // 요소가 실제로 존재하는지 확인 (에러 방지)
    if (imageEl) {
        // groupBuy 객체에 이미지 URL이 있는지 확인
        if (groupBuy && groupBuy.productImageUrl) {
            // 이미지가 있다면: img 태그를 생성해서 넣음
            imageEl.innerHTML = `<img src="${groupBuy.productImageUrl}" alt="${groupBuy.productName}" style="width: 100%; height: 100%; object-fit: contain; border-radius: 8px;">`;
        } else {
            // 이미지가 없다면: '이미지 없음' 박스로 유지
            imageEl.innerHTML = `<div class="card-image">이미지 없음</div>`;
        }
    }

    card.innerHTML = `
        ${imgHtml}
        <div class="card-info">
            <h3>${groupBuy.title}</h3>
            <p style="color:#666; font-size:14px; margin-bottom:5px;">${product ? product.name : '상품정보 없음'}</p>
            <div style="margin-top:10px; display:flex; justify-content:space-between; color:#4a90e2; font-weight:bold;">
                <span>👤 ${currentCount}명 참여</span>
                <span>목표 ${groupBuy.targetHeadcount}명</span>
            </div>
        </div>
    `;
    container.appendChild(card);
}

// ==========================================
// 2. 기존 기능: UI 및 모집글 등록
// ==========================================

function setupModalEvents() {
    const modal = document.querySelector('.modal');
    const modalBtn = document.querySelector('.modal_btn'); 
    const closeBtn = document.querySelector('.close_btn');

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

    if (closeBtn && modal) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
}

function updateAuthButton() {
    const isAuthenticated = checkAuth();
    const authButton = document.getElementById('authButton');
    if (!authButton) return;

    if (isAuthenticated) {
        authButton.textContent = '로그아웃';
        authButton.href = '#';
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

function showLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) loadingOverlay.style.display = 'none';
}

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
    } else {
        alert("상품 URL에서 유효한 제품 ID를 찾을 수 없습니다.");
        return; 
    }

    showLoading();
    try {
        await registerGroupBuy(productNumber, productUrl, targetHeadcount, title, content, endDate);
    } finally {
        hideLoading();
    }
}

async function registerGroupBuy(productNumber, productUrl, targetHeadcount, title, content, endDate) { 
    const token = getToken(); 
    const headers = {
        'Content-Type': 'application/json', 
        'Authorization': `Bearer ${token}` 
    };
    
    try {
        const urlParams = new URLSearchParams({ url: productUrl });
        const responseGet = await fetch(`${API_BASE}/api/groupbuys/attempt?${urlParams}`, {
            method: 'GET',
            headers: headers
        });
        
        let validationResult;
        const contentType = responseGet.headers.get('content-type') || '';
        try {
            if (contentType.includes('application/json')) validationResult = await responseGet.json();
            else validationResult = await responseGet.text();
            
            if (typeof validationResult === 'string') {
                try { validationResult = JSON.parse(validationResult); } catch {}
            }
        } catch (e) {
            validationResult = await responseGet.text();
        }
        
        const isValid = responseGet.ok && (
            validationResult === 'success' ||
            (typeof validationResult === 'object' && validationResult.success === true) ||
            (typeof validationResult === 'object' && validationResult.message === 'success')
        );

        if (!isValid) {
            let errorMsg = '입력 정보를 확인해주세요.';
            if (typeof validationResult === 'object') errorMsg = validationResult.message || validationResult.error || errorMsg;
            else if (typeof validationResult === 'string') errorMsg = validationResult;
            alert(`등록 확인 실패: ${errorMsg}`);
            return;
        }
        
        // 검증 성공 시 등록
        productNumber = validationResult.productNumber || productNumber;
        const postData = {
            productId: productNumber,         
            targetHeadcount: parseInt(targetHeadcount, 10),
            title: title,                   
            content: content,               
            recruitEndDate: endDate         
        };

        const responsePost = await fetch(`${API_BASE}/api/groupbuys/online`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify(postData) 
        });
        
        if (responsePost.ok) {
            alert("모집글이 성공적으로 등록되었습니다!");
            document.querySelector('.modal').style.display = 'none';
            window.location.reload(); 
        } else {
            throw new Error(`등록 실패 (HTTP ${responsePost.status})`);
        }
        
    } catch (error) {
        console.error("등록 처리 중 오류 발생:", error);
        alert("글 등록 처리 중 오류가 발생했습니다: " + error.message);
    }
}

// ==========================================
// 3. 기존 기능: 실시간 채팅 사이드바
// ==========================================

function initChatSidebar() {
    const chatListContainer = document.getElementById('chatListContainer');
    const token = localStorage.getItem('accessToken'); 
    if (!token) {
        if(chatListContainer) chatListContainer.innerHTML = '<li style="padding:8px; text-align:center; color:#888;">로그인이 필요합니다.</li>';
        return; 
    }
    loadChatRooms(token); 
    connectWebSocket(token);
}

async function loadChatRooms(token) {
    try {
        const response = await fetch('/api/chat/rooms', {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            const rooms = await response.json();
            renderChatList(rooms);
        }
    } catch (error) {
        console.error('채팅 목록 에러:', error);
    }
}

function renderChatList(rooms) {
    const chatListContainer = document.getElementById('chatListContainer');
    if (!chatListContainer) return;
    chatListContainer.innerHTML = ''; 

    if (rooms.length === 0) {
        chatListContainer.innerHTML = '<li style="padding:10px; color:#888;">참여 중인 채팅방이 없습니다.</li>';
        return;
    }

    rooms.forEach(room => {
        const li = document.createElement('li');
        li.className = 'chat-item';
        const badgeHtml = room.unreadCount > 0 ? `<span class="badge">${room.unreadCount}</span>` : '';
        li.innerHTML = `
            <a href="chat.html?roomId=${room.roomId}" style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                <span class="room-name">${room.roomName}</span>
                ${badgeHtml}
            </a> 
        `;
        chatListContainer.appendChild(li);
    });
}

function connectWebSocket(token) {
    let socket;
    try { socket = new WebSocket(`ws://together1.kro.kr/ws/chat?token=${token}`); } catch (e) { return; }

    socket.onopen = function() { console.log('실시간 채팅 서버 연결됨'); };
    socket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'NEW_MESSAGE' || data.type === 'ROOM_UPDATE') {
                loadChatRooms(token);
            }
        } catch (e) {}
    };
    socket.onclose = function() { setTimeout(() => connectWebSocket(token), 5000); };
}
