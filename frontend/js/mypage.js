// frontend/js/mypage.js

let currentUserInfo = null;
let paymentWidgets = null; 
let selectedPointAmount = 0; 

document.addEventListener('DOMContentLoaded', async function() {
    // 1. 인증 확인
    if (!checkAuth()) { 
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return; 
    }
    
    // 2. 탭 및 초기 설정
    setupTabs();

    try {
        // 3. 내 정보 로드
        const myInfo = await apiFetch('/api/users/me'); 
        currentUserInfo = myInfo;
        
        // 프로필 바인딩
        const nameElement = document.getElementById('userName');
        if (nameElement) nameElement.textContent = myInfo.nickname || '사용자';
        
        const scoreElement = document.querySelector('.score');
        if (scoreElement) {
            const temp = myInfo.mannerTemp !== undefined ? myInfo.mannerTemp : 36.5;
            scoreElement.textContent = temp.toFixed(1);
        }
        
        updatePointUI(myInfo.points);
        populateSettingsForm(myInfo);
        
        // ⭐ [핵심] 참여 내역 로드 (비상 로직 포함)
        await loadMyParticipations();
        
        // 포인트 페이지 전용 로직
        if(document.getElementById('pointHistoryList')) await loadMyPointHistory();
        if (document.getElementById('payment-method')) await initPointPayment();

    } catch (error) {
        console.error('정보 로드 실패:', error);
    }

    setupSettingsForm();
});

// 내 참여 내역 로드 (데이터 누락 시 재요청 로직 추가)
async function loadMyParticipations() {
    const listContainer = document.getElementById('participationList');
    if (!listContainer) return;

    try {
        // 1. 목록 조회 (백엔드 Lazy Loading으로 인해 껍데기만 올 가능성 있음)
        const data = await apiFetch('/api/users/me/participations');
        const onlineList = data.onlineParticipations || [];
        
        listContainer.innerHTML = '<div style="padding:20px; text-align:center; color:#666;">데이터를 불러오는 중...</div>';

        if (onlineList.length === 0) {
            listContainer.innerHTML = '<div style="padding:20px; text-align:center; color:#999;">참여한 내역이 없습니다.</div>';
            return;
        }

        // 2. 제목이 없는 항목들은 ID로 상세 정보를 다시 긁어옵니다. (수정 api 2번 호출)
        const enrichedList = await Promise.all(onlineList.map(async (item) => {
            let groupBuy = item.onlineGroupBuy;
            
            // "ID는 있는데 제목이 없다?" -> 백엔드가 내용을 안 보내준 상황
            if (groupBuy && groupBuy.id && !groupBuy.title) {
                try {
                    // 상세 API를 호출해서 꽉 찬 정보를 받아옴. (상세 조회 API에서도 product가 Lazy면 상품명은 여전히 없을 수 있음)
                    const fullInfo = await apiFetch(`/api/groupbuys/online/${groupBuy.id}`);
                    
                    // 만약 상세 조회한 정보에 상품 정보가 또 없다면? (3차 비상 - 상품 ID로 조회)
                    if (fullInfo.product && !fullInfo.product.name && fullInfo.product.id) {
                         try {
                             const productInfo = await apiFetch(`/api/products/${fullInfo.product.id}`);
                             fullInfo.product = productInfo;
                         } catch(e) {}
                    }

                    // 정보를 교체
                    item.onlineGroupBuy = fullInfo;
                } catch (e) {
                    console.warn(`공구 ID ${groupBuy.id} 상세 정보 복구 실패`, e);
                }
            }
            return item;
        }));

        listContainer.innerHTML = ''; // 로딩 문구 제거

        // 3. 화면 그리기
        enrichedList.forEach(item => {
            const groupBuy = item.onlineGroupBuy; 
            if (!groupBuy) return;

            const product = groupBuy.product;
            const dateStr = item.createdAt ? new Date(item.createdAt).toLocaleDateString() : '-';

            const card = document.createElement('div');
            card.className = 'activity-item'; 
            card.style.borderLeft = '4px solid #4a90e2';
            card.style.marginBottom = '15px';
            
            // 채팅방 버튼
            let chatButtonHtml = '';
            if (groupBuy.chatRoomId) {
                chatButtonHtml = `
                    <button onclick="location.href='chat.html?roomId=${groupBuy.chatRoomId}'" 
                            style="margin-top:10px; padding:8px 12px; background:#4a90e2; color:white; border:none; border-radius:4px; cursor:pointer; font-weight:bold;">
                        💬 채팅방 입장
                    </button>
                `;
            } else {
                chatButtonHtml = `<span style="font-size:12px; color:#999; display:inline-block; margin-top:10px;">(채팅방 준비중)</span>`;
            }

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <h3 style="margin-bottom:5px; font-size:16px; color:#333;">
                            <a href="recruitment-detail.html?id=${groupBuy.id}" style="text-decoration:none; color:#333;">
                                ${groupBuy.title || '제목 로딩 실패'}
                            </a>
                        </h3>
                        <p style="margin-bottom:5px; color:#666; font-size:14px;">상품: ${product ? product.name : '정보 없음'}</p>
                        <p style="font-size:13px; color:#888;">참여일: ${dateStr}</p>
                        <span style="display:inline-block; margin-top:5px; font-size:13px; font-weight:bold; color:#4a90e2;">
                            상태: ${item.paymentStatus || '결제 대기'}
                        </span>
                    </div>
                    <div style="text-align:right;">
                         ${chatButtonHtml}
                    </div>
                </div>
            `;
            listContainer.appendChild(card);
        });

    } catch (error) {
        console.error('참여 내역 로드 실패:', error);
        listContainer.innerHTML = '<div style="padding:20px; text-align:center; color:red;">목록을 불러오지 못했습니다.</div>';
    }
}

// --- [기존 기능 유지] 포인트 결제, 탭, 설정 등 ---

async function initPointPayment() {
    const clientKey = "test_gck_docs_Ovk5rk1EwkEbP0W43n07xlzm"; 
    const tossPayments = TossPayments(clientKey);
    const customerKey = "user_" + (currentUserInfo?.id || new Date().getTime());
    
    paymentWidgets = tossPayments.widgets({ customerKey });

    await paymentWidgets.setAmount({ currency: "KRW", value: 1000 });

    await Promise.all([
        paymentWidgets.renderPaymentMethods({ selector: "#payment-method", variantKey: "DEFAULT" }),
        paymentWidgets.renderAgreement({ selector: "#agreement", variantKey: "AGREEMENT" }),
    ]);
    
    document.getElementById('payment-widget-area').style.display = 'block';
    setupPointPurchaseEvents();
}

function setupPointPurchaseEvents() {
    const purchaseItems = document.querySelectorAll('.point-purchase-list .purchase-item');
    const purchaseBtn = document.getElementById('point-payment-btn');
    
    purchaseItems.forEach(item => {
        item.addEventListener('click', async function() {
            purchaseItems.forEach(i => i.classList.remove('selected'));
            this.classList.add('selected');
            const price = parseInt(this.dataset.price, 10);
            selectedPointAmount = price;
            await paymentWidgets.setAmount({ currency: "KRW", value: price });
            if (purchaseBtn) {
                purchaseBtn.textContent = `${price.toLocaleString()}원 결제하기`;
                purchaseBtn.disabled = false;
            }
        });
    });

    if (purchaseBtn) {
        purchaseBtn.textContent = "충전할 금액을 선택해주세요";
        purchaseBtn.disabled = true;
        purchaseBtn.addEventListener('click', async function() {
            if (selectedPointAmount <= 0) { alert('충전할 포인트를 선택해주세요.'); return; }
            try {
                const orderId = "POINT_" + new Date().getTime();
                await paymentWidgets.requestPayment({
                    orderId: orderId,
                    orderName: `포인트 ${selectedPointAmount.toLocaleString()}P 충전`,
                    successUrl: window.location.origin + "/success.html",
                    failUrl: window.location.origin + "/fail.html",
                    customerEmail: currentUserInfo?.email || "unknown@example.com",
                    customerName: currentUserInfo?.name || "사용자",
                });
            } catch (error) { console.error("결제 요청 실패:", error); }
        });
    }
}

function setupTabs() {
    const menuLinks = document.querySelectorAll('.menu-link');
    const tabContents = document.querySelectorAll('.tab-content');
    if (!menuLinks.length) return;
    menuLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.dataset.tab;
            if (!targetId) return; 
            e.preventDefault();
            menuLinks.forEach(item => item.classList.remove('active'));
            this.classList.add('active');
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === targetId) content.classList.add('active');
            });
        });
    });
}

function updatePointUI(points) {
    const safePoints = points || 0;
    const formatted = new Intl.NumberFormat().format(safePoints);
    const profilePoint = document.getElementById('userPointsProfile');
    const mainPoint = document.getElementById('userPoints');
    if(profilePoint) profilePoint.textContent = formatted;
    if(mainPoint) mainPoint.textContent = formatted + " P";
}

async function loadMyPointHistory() {
    const historyList = document.getElementById('pointHistoryList'); 
    if (!historyList) return; 
    try {
        const historyData = await apiFetch('/api/points/history');
        historyList.innerHTML = ''; 
        if (historyData && historyData.length > 0) {
            historyData.forEach(item => {
                const row = document.createElement('div');
                row.className = 'activity-item'; 
                row.style.display = 'flex';
                row.style.justifyContent = 'space-between';
                const dateStr = item.createdAt ? new Date(item.createdAt).toLocaleDateString() : '-';
                const isPositive = (item.amount > 0);
                const sign = isPositive ? '+' : '';
                const color = isPositive ? '#4a90e2' : '#ff4444';
                row.innerHTML = `<div><span style="font-weight:bold; color:#555;">[포인트]</span> <span style="color:#888; font-size:14px; margin-left:5px;">${dateStr}</span></div><span style="font-weight:bold; color:${color};">${sign}${new Intl.NumberFormat().format(item.amount)} P</span>`;
                historyList.appendChild(row);
            });
        } else {
            historyList.innerHTML = '<div style="padding:20px; text-align:center; color:#999;">포인트 변동 내역이 없습니다.</div>';
        }
    } catch (error) { console.error('포인트 내역 로드 실패:', error); }
}

function populateSettingsForm(user) {
    if (!document.getElementById('settingsForm')) return;
    setVal('settingName', user.name);
    setVal('settingNickname', user.nickname);
    setVal('settingEmail', user.email);
    setVal('settingPhone', user.phoneNumber);
    setVal('settingAddress', user.address);
    setVal('settingAddressDetail', user.addressDetail);
    setVal('settingZip', user.zipCode);
}

function setVal(id, val) { const el = document.getElementById(id); if (el) el.value = val || ''; }

function setupSettingsForm() {
    const form = document.getElementById('settingsForm');
    if (!form) return;
    form.addEventListener('submit', async function(e) { e.preventDefault(); await saveSettings(); });
}

async function saveSettings() {
    const password = document.getElementById('settingPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmNewPassword = document.getElementById('confirmNewPassword').value;

    if (!password) { alert('정보를 수정하려면 현재 비밀번호를 입력해야 합니다.'); return; }
    if (newPassword || confirmNewPassword) {
        if (newPassword !== confirmNewPassword) { alert('새 비밀번호가 일치하지 않습니다.'); return; }
    }

    const updateData = {
        nickname: getInputValue('settingNickname'),
        address: getInputValue('settingAddress'),
        addressDetail: getInputValue('settingAddressDetail'),
        zipCode: getInputValue('settingZip')
    };

    try {
        await apiFetch('/api/users/me', { method: 'PUT', body: updateData });
        alert('회원 정보가 수정되었습니다.');
        window.location.reload();
    } catch (error) { console.error(error); alert('정보 수정 실패: ' + error.message); }
}

function getInputValue(inputId) { const el = document.getElementById(inputId); return el ? el.value : null; }