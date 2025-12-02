// frontend/js/mypage.js

let currentUserInfo = null;
let paymentWidgets = null; 
let selectedPointAmount = 0; 

document.addEventListener('DOMContentLoaded', async function() {
    if (!checkAuth()) { 
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return; 
    }
    
    setupTabs();

    try {
        const myInfo = await apiFetch('/api/users/me'); 
        currentUserInfo = myInfo;
        
        const nameElement = document.getElementById('userName');
        if (nameElement) nameElement.textContent = myInfo.nickname || '사용자';
        
        const scoreElement = document.querySelector('.score');
        if (scoreElement) {
            const temp = myInfo.mannerTemp !== undefined ? myInfo.mannerTemp : 36.5;
            scoreElement.textContent = temp.toFixed(1);
        }
        
        updatePointUI(myInfo.points);
        populateSettingsForm(myInfo);
        
        // 참여 내역 로드
        await loadMyParticipations();
        
        if(document.getElementById('pointHistoryList')) await loadMyPointHistory();
        if (document.getElementById('payment-method')) await initPointPayment();

    } catch (error) {
        console.error('정보 로드 실패:', error);
    }

    setupSettingsForm();
});

// [수정됨] 참여 내역 로드 및 분류
async function loadMyParticipations() {
    const activeListContainer = document.getElementById('participationList');
    const completedListContainer = document.getElementById('completedList'); 

    if (!activeListContainer) return;

    try {
        const data = await apiFetch('/api/users/me/participations');
        const onlineList = data.onlineParticipations || [];
        
        if (onlineList.length === 0) {
            activeListContainer.innerHTML = '<div style="padding:20px; text-align:center; color:#999;">참여한 내역이 없습니다.</div>';
            return;
        }

        // 상세 정보 보정 (Lazy Loading 대응)
        const enrichedList = await Promise.all(onlineList.map(async (item) => {
            let groupBuy = item.onlineGroupBuy;
            if (groupBuy && groupBuy.id && !groupBuy.title) {
                try {
                    const fullInfo = await apiFetch(`/api/groupbuys/online/${groupBuy.id}`);
                    const pId = fullInfo.product?.id || fullInfo.productId;
                    if (pId && (!fullInfo.product || !fullInfo.product.name)) {
                         try {
                             const productInfo = await apiFetch(`/api/products/${pId}`);
                             fullInfo.product = productInfo;
                         } catch(e) {}
                    }
                    item.onlineGroupBuy = fullInfo;
                } catch (e) {}
            }
            return item;
        }));

        // 리스트 초기화
        activeListContainer.innerHTML = '';
        if (completedListContainer) completedListContainer.innerHTML = '';

        // 분류 및 렌더링
        enrichedList.forEach(item => {
            const groupBuy = item.onlineGroupBuy;
            if (!groupBuy) return;

            const gbStatus = groupBuy.status;
            const myPayStatus = item.paymentStatus;

            // [핵심 수정] 완료된 목록으로 보내는 기준 변경
            // 1. 공구 자체가 종료됨 (COMPLETED)
            // 2. OR 내 결제가 완료됨 (PAID) -> 내 할일은 끝났으므로 완료 탭으로 이동
            const isFinished = (gbStatus === 'COMPLETED' || myPayStatus === 'PAID');
            
            const targetContainer = isFinished ? completedListContainer : activeListContainer;

            if (targetContainer) {
                renderParticipationItem(item, targetContainer);
            }
        });

        // 빈 상태 처리
        if (activeListContainer.children.length === 0) {
            activeListContainer.innerHTML = '<div style="padding:20px; text-align:center; color:#999;">진행 중인 공구가 없습니다.</div>';
        }
        if (completedListContainer && completedListContainer.children.length === 0) {
            completedListContainer.innerHTML = '<div style="padding:20px; text-align:center; color:#999;">완료된 공구가 없습니다.</div>';
        }

    } catch (error) {
        console.error('참여 내역 로드 실패:', error);
    }
}

function renderParticipationItem(item, container) {
    const groupBuy = item.onlineGroupBuy;
    const product = groupBuy.product;
    const dateStr = item.createdAt ? new Date(item.createdAt).toLocaleDateString() : '-';
    
    // 상태 텍스트 변환
    const statusText = getStatusText(item);

    const card = document.createElement('div');
    card.className = 'activity-item'; 
    card.style.borderLeft = '4px solid #4a90e2';
    card.style.marginBottom = '15px';
    card.style.padding = '15px';
    card.style.backgroundColor = '#fff';
    card.style.boxShadow = '0 2px 4px rgba(0,0,0,0.05)';
    card.style.borderRadius = '8px';
    
    // 채팅방 버튼
    let chatButtonHtml = '';
    if (groupBuy.chatRoomId) {
        chatButtonHtml = `
            <button onclick="location.href='chat.html?roomId=${groupBuy.chatRoomId}'" 
                    style="margin-top:10px; padding:8px 12px; background:#4a90e2; color:white; border:none; border-radius:4px; cursor:pointer; font-weight:bold; font-size:13px;">
                💬 채팅방
            </button>
        `;
    }

    card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:start;">
            <div style="flex: 1;">
                <h3 style="margin-bottom:8px; font-size:16px; color:#333; font-weight:bold;">
                    <a href="recruitment-detail.html?id=${groupBuy.id}" style="text-decoration:none; color:#333;">
                        ${groupBuy.title || '제목 로딩 실패'}
                    </a>
                </h3>
                <p style="margin-bottom:5px; color:#666; font-size:14px;">상품: ${product ? product.name : '정보 없음'}</p>
                <p style="font-size:13px; color:#888;">참여일: ${dateStr}</p>
                <span style="display:inline-block; margin-top:8px; font-size:13px; font-weight:bold; color:#4a90e2; background-color:#eef6ff; padding:3px 8px; border-radius:4px;">
                    상태: ${statusText}
                </span>
            </div>
            <div style="text-align:right; min-width: 80px;">
                 ${chatButtonHtml}
            </div>
        </div>
    `;
    container.appendChild(card);
}

function getStatusText(item) {
    const gbStatus = item.onlineGroupBuy.status; 
    const myPayStatus = item.paymentStatus;      

    if (gbStatus === 'COMPLETED') return '종료됨 (배송 준비)';
    if (myPayStatus === 'PAID') return '결제 완료';
    if (gbStatus === 'IN_PROGRESS') return '결제 진행 중';
    
    return '모집 중 (참여 완료)';
}

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