// frontend/js/main.js

let allGroupBuys = []; // 전체 공구 리스트 저장
let currentPage = 1;   // 현재 페이지
const itemsPerPage = 4; // 페이지당 4개씩 표시 (1~4위: 1페이지, 5~8위: 2페이지)

document.addEventListener('DOMContentLoaded', async function() {
    updateAuthButton(); 
    initChatSidebar();
    setupModalEvents();

    const searchBtn = document.getElementById('searchButton');
    const searchInput = document.getElementById('searchInput');

    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', () => searchGroupBuys(searchInput.value));
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchGroupBuys(searchInput.value);
        });
    }

    await loadPopularGroupBuys();
});

// [핵심 수정] 핫한 모집글 로드 (꽉 찬 공구 제외)
async function loadPopularGroupBuys() {
    const contentGrid = document.getElementById('contentGrid');
    if (!contentGrid) return;

    try {
        const groupBuys = await apiFetch('/api/groupbuys/online');
        
        // 1. 필터링: 
        //    - 상태가 'COMPLETED'(종료)가 아닐 것
        //    - AND 현재인원 < 목표인원 (꽉 차지 않은 것만 표시)
        // 2. 정렬: 참여자 수 많은 순서 (내림차순)
        allGroupBuys = groupBuys
            .filter(gb => {
                const current = gb.participationList?.length || 0;
                const target = gb.targetHeadcount || 0;
                // [수정 포인트] 종료되지 않았고, 아직 자리가 남은 공구만 통과
                return gb.status !== 'COMPLETED' && current < target;
            })
            .sort((a, b) => (b.participationList?.length || 0) - (a.participationList?.length || 0));

        if (allGroupBuys.length === 0) {
            contentGrid.innerHTML = '<p style="text-align:center; color:#888; grid-column:1/-1; padding: 40px;">참여 가능한 모집글이 없습니다.</p>';
            return;
        }

        // 1페이지 렌더링 시작
        renderPage(1);

    } catch (error) {
        console.error('글 로드 실패:', error);
    }
}

// 페이지 렌더링 함수
function renderPage(page) {
    currentPage = page;
    const contentGrid = document.getElementById('contentGrid');
    
    contentGrid.innerHTML = ''; // 초기화
    
    // 데이터 슬라이싱 (4개씩)
    // page 1: 0~4 (4개)
    // page 2: 4~8 (4개)
    const start = (page - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const itemsToShow = allGroupBuys.slice(start, end);

    contentGrid.innerHTML = '<h3 style="grid-column:1/-1; margin-bottom:10px; color:#4a90e2;">🔥 핫한 모집글 (참여 가능)</h3>';
    
    if(itemsToShow.length === 0) {
        contentGrid.innerHTML += '<p style="text-align:center; padding:20px;">이 페이지에 표시할 모집글이 없습니다.</p>';
    } else {
        itemsToShow.forEach(gb => renderCard(gb, contentGrid));
    }

    // 페이지네이션 버튼 업데이트
    renderPaginationControls();
}

// 페이지네이션 버튼 생성
function renderPaginationControls() {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;
    
    pagination.innerHTML = '';
    const totalPages = Math.ceil(allGroupBuys.length / itemsPerPage);

    // 버튼 생성 (1, 2, 3 ...)
    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = 'page-btn';
        
        btn.style.padding = '8px 12px';
        btn.style.margin = '0 3px';
        btn.style.border = '1px solid #ddd';
        btn.style.borderRadius = '4px';
        btn.style.backgroundColor = '#fff';
        btn.style.cursor = 'pointer';

        // 현재 페이지 강조
        if (i === currentPage) {
            btn.style.backgroundColor = '#4a90e2';
            btn.style.color = 'white';
            btn.style.fontWeight = 'bold';
            btn.style.borderColor = '#4a90e2';
        }
        
        btn.onclick = () => renderPage(i);
        pagination.appendChild(btn);
    }
}

async function searchGroupBuys(keyword) {
    const contentGrid = document.getElementById('contentGrid');
    const pagination = document.getElementById('pagination');
    if (!contentGrid) return;

    if (!keyword.trim()) {
        alert('검색어를 입력해주세요.');
        return;
    }

    try {
        const groupBuys = await apiFetch('/api/groupbuys/online');
        // 검색 결과에서도 종료되거나 꽉 찬 공구는 제외하고 싶은 경우 필터 추가 가능
        // 여기서는 검색어 일치 여부만 확인
        const results = groupBuys.filter(gb => 
            gb.title.includes(keyword) || (gb.product && gb.product.name.includes(keyword))
        );

        contentGrid.innerHTML = ''; 
        if (pagination) pagination.innerHTML = ''; // 검색 시에는 페이지네이션 숨김

        if (results.length === 0) {
            contentGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 50px;">'${keyword}' 검색 결과가 없습니다.</div>`;
            return;
        }

        contentGrid.innerHTML = `<h3 style="grid-column:1/-1;">'${keyword}' 검색 결과</h3>`;
        results.forEach(gb => renderCard(gb, contentGrid));

    } catch (error) {
        console.error('검색 실패:', error);
    }
}

function renderCard(groupBuy, container) {
    const product = groupBuy.product;
    const currentCount = groupBuy.participationList?.length || 0;
    
    const card = document.createElement('div');
    card.className = 'content-card';
    card.onclick = () => window.location.href = `recruitment-detail.html?id=${groupBuy.id}`;

    let imgHtml = `<div class="card-image">이미지 없음</div>`;
    if (groupBuy.productImageUrl) {
        imgHtml = `<div class="card-image" style="padding:0;"><img src="${groupBuy.productImageUrl}" alt="${groupBuy.productName}" style="width: 100%; height: 100%; object-fit: cover;"></div>`;
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

// UI 및 모달 관련
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
        authButton.onclick = (e) => { e.preventDefault(); logout(); };
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
    if (!checkAuth()) { alert("로그인이 필요합니다."); window.location.href = 'login.html'; return; }

    const productUrl = document.getElementById('productUrl').value;
    const targetHeadcount = document.getElementById('targetHeadcount').value;
    const title = document.getElementById('recruitTitle').value;
    const content = document.getElementById('recruitContent').value;
    const endDate = document.getElementById('recruitEndDate').value;
    
    if (!productUrl || !targetHeadcount || !title || !content || !endDate) {
        alert("모든 항목을 입력해주세요."); return;
    }

    const regex = /products\/(\d+)/; 
    const match = productUrl.match(regex);
    let productNumber;
    if (match && match[1]) productNumber = parseInt(match[1], 10);
    else { alert("상품 URL에서 ID를 찾을 수 없습니다."); return; }

    showLoading();
    try { await registerGroupBuy(productNumber, productUrl, targetHeadcount, title, content, endDate); }
    finally { hideLoading(); }
}

async function registerGroupBuy(productNumber, productUrl, targetHeadcount, title, content, endDate) { 
    const token = getToken(); 
    const headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` };
    
    try {
        const urlParams = new URLSearchParams({ url: productUrl });
        const responseGet = await fetch(`${API_BASE}/api/groupbuys/attempt?${urlParams}`, { method: 'GET', headers: headers });
        let validationResult = await responseGet.text();
        try { validationResult = JSON.parse(validationResult); } catch {}
        
        if (!responseGet.ok) { alert('등록 확인 실패'); return; }
        
        productNumber = validationResult.productNumber || productNumber;
        const postData = { productId: productNumber, targetHeadcount: parseInt(targetHeadcount, 10), title: title, content: content, recruitEndDate: endDate };

        const responsePost = await fetch(`${API_BASE}/api/groupbuys/online`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(postData) 
        });
        
        if (responsePost.ok) {
            alert("모집글이 성공적으로 등록되었습니다!");
            document.querySelector('.modal').style.display = 'none';
            window.location.reload(); 
        } else { throw new Error('등록 실패'); }
        
    } catch (error) { console.error(error); alert("오류 발생: " + error.message); }
}

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
    } catch (error) { console.error(error); }
}

function renderChatList(rooms) {
    const chatListContainer = document.getElementById('chatListContainer');
    if (!chatListContainer) return;
    chatListContainer.innerHTML = ''; 
    if (rooms.length === 0) { chatListContainer.innerHTML = '<li style="padding:10px; color:#888;">채팅방이 없습니다.</li>'; return; }
    rooms.forEach(room => {
        const li = document.createElement('li');
        li.className = 'chat-item';
        const badgeHtml = room.unreadCount > 0 ? `<span class="badge">${room.unreadCount}</span>` : '';
        li.innerHTML = `<a href="chat.html?roomId=${room.roomId}" style="display:flex; justify-content:space-between; align-items:center; width:100%;"><span class="room-name">${room.roomName}</span>${badgeHtml}</a>`;
        chatListContainer.appendChild(li);
    });
}

function connectWebSocket(token) {
    let socket;
    try { socket = new WebSocket(`ws://together1.kro.kr/ws/chat?token=${token}`); } catch (e) { return; }
    socket.onmessage = function(event) {
        try { const data = JSON.parse(event.data); if (data.type === 'NEW_MESSAGE') loadChatRooms(token); } catch (e) {}
    };
    socket.onclose = function() { setTimeout(() => connectWebSocket(token), 5000); };
}