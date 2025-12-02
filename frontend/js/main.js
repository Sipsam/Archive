// frontend/js/main.js

let allGroupBuys = []; 
let currentPage = 1;   
const itemsPerPage = 4; 

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

// [수정] 핫한 모집글 로드 (필터링 강화)
async function loadPopularGroupBuys() {
    const contentGrid = document.getElementById('contentGrid');
    if (!contentGrid) return;

    try {
        const groupBuys = await apiFetch('/api/groupbuys/online');
        
        // 필터링 조건:
        // 1. 상태가 COMPLETED(종료)가 아닐 것
        // 2. 현재 참여 인원이 목표 인원보다 작을 것 (꽉 차면 안 보임)
        allGroupBuys = groupBuys
            .filter(gb => {
                const current = gb.participationList ? gb.participationList.length : 0;
                const target = gb.targetHeadcount || 0;
                // [핵심] 종료 안 됨 AND 자리 남음
                return gb.status !== 'COMPLETED' && current < target;
            })
            .sort((a, b) => (b.participationList?.length || 0) - (a.participationList?.length || 0));

        if (allGroupBuys.length === 0) {
            contentGrid.innerHTML = '<p style="text-align:center; color:#888; grid-column:1/-1; padding: 40px;">참여 가능한 모집글이 없습니다.</p>';
            return;
        }

        renderPage(1);

    } catch (error) {
        console.error('글 로드 실패:', error);
    }
}

function renderPage(page) {
    currentPage = page;
    const contentGrid = document.getElementById('contentGrid');
    contentGrid.innerHTML = ''; 
    
    const start = (page - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const itemsToShow = allGroupBuys.slice(start, end);

    contentGrid.innerHTML = '<h3 style="grid-column:1/-1; margin-bottom:10px; color:#4a90e2;">🔥 핫한 모집글 (참여 가능)</h3>';
    
    if(itemsToShow.length === 0) {
        contentGrid.innerHTML += '<p style="text-align:center; padding:20px;">이 페이지에 표시할 모집글이 없습니다.</p>';
    } else {
        itemsToShow.forEach(gb => renderCard(gb, contentGrid));
    }

    renderPaginationControls();
}

function renderPaginationControls() {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;
    
    pagination.innerHTML = '';
    const totalPages = Math.ceil(allGroupBuys.length / itemsPerPage);

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
        // 검색 결과는 꽉 찼더라도 보여주는 것이 일반적이지만, 
        // 핫한 모집글과 동일하게 숨기려면 아래 조건을 추가하면 됩니다.
        const results = groupBuys.filter(gb => 
            gb.title.includes(keyword) || (gb.product && gb.product.name.includes(keyword))
        );

        contentGrid.innerHTML = ''; 
        if (pagination) pagination.innerHTML = ''; 

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
            <p style="color:#666; font-size:14px; margin-bottom:5px;">${groupBuy.productName ? groupBuy.productName : '상품정보 없음'}</p>
            <div style="margin-top:10px; display:flex; justify-content:space-between; color:#4a90e2; font-weight:bold;">
                <span>👤 ${currentCount}명 참여</span>
                <span>목표 ${groupBuy.targetHeadcount}명</span>
            </div>
        </div>
    `;
    container.appendChild(card);
}

// ==========================================
// UI 및 기타 로직
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

// [수정] 메인페이지 채팅 사이드바 (종료된 채팅방 숨김)
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
        // 1. 채팅방 목록
        const response = await fetch('/api/chat/rooms', {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            const rooms = await response.json();

            // 2. 내 참여 목록 (Status 확인용)
            const participationsResponse = await fetch('/api/users/me/participations', {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
            });

            let validRoomIds = new Set();
            if (participationsResponse.ok) {
                const data = await participationsResponse.json();
                const onlineList = data.onlineParticipations || [];
                
                // [핵심] 상태가 COMPLETED이면 제외
                onlineList.forEach(p => {
                    // DTO Lazy Loading 이슈 대비
                    const gb = p.onlineGroupBuy;
                    // 상세 정보가 없을 수 있으므로 일단 추가하거나, 상세 조회를 할 수 있음
                    // 여기서는 간단히 있는 정보로 체크
                    if (gb && gb.chatRoomId) {
                        // 만약 gb.status가 없으면(SimpleDto) 통과시키거나, 별도 조회 필요
                        // 보통 상세 리스트에는 status가 없으므로 일단 추가하고 chat.html에서 거르는게 일반적이나
                        // "메인페이지에서 안 뜨게" 하려면 여기서 걸러야 함.
                        
                        // 안전장치: Status가 명시적으로 'COMPLETED'인 것만 뺌
                        // (Status 필드가 없으면 일단 보여줌)
                        if (gb.status !== 'COMPLETED') {
                            validRoomIds.add(gb.chatRoomId);
                        }
                    }
                });
            }

            // 필터링 적용 (내가 참여 중이고, 완료되지 않은 방만)
            const activeRooms = rooms.filter(room => validRoomIds.has(room.roomId));

            renderChatList(activeRooms);
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
    try { socket = new WebSocket(`wss://together1.kro.kr/ws/chat?token=${token}`); } catch (e) { return; }

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
