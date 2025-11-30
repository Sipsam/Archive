// frontend/js/mypage.js

let currentUserInfo = null;
let paymentWidgets = null; // 토스페이먼츠 위젯 객체
let selectedPointAmount = 0; // 선택된 포인트 금액

document.addEventListener('DOMContentLoaded', async function() {
    // 1. 인증 확인
    if (!checkAuth()) { 
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return; 
    }
    
    // 2. 탭 기능 설정
    setupTabs();

    // 3. 사용자 정보 및 내역 로드
    try {
        const myInfo = await apiFetch('/api/users/me'); 
        currentUserInfo = myInfo;
        
        // UI 바인딩 (이름, 매너온도, 포인트)
        const nameElement = document.getElementById('userName');
        if (nameElement) nameElement.textContent = myInfo.nickname || '사용자';
        
        const scoreElement = document.querySelector('.score');
        if (scoreElement) {
            const temp = myInfo.mannerTemp !== undefined ? myInfo.mannerTemp : 36.5;
            scoreElement.textContent = temp.toFixed(1);
        }
        
        updatePointUI(myInfo.points);
        
        // ⭐ [핵심] 내 참여 내역(주문 내역) 로드 (+채팅방 버튼)
        await loadMyParticipations();
        
        // 설정 폼 초기화
        populateSettingsForm(myInfo);
        
        // 포인트 페이지일 경우 포인트 내역 로드
        if(document.getElementById('pointHistoryList')) {
            await loadMyPointHistory();
        }

        // 포인트 결제 초기화 (point.html용)
        if (document.getElementById('payment-method')) {
            await initPointPayment();
        }

    } catch (error) {
        console.error('정보 로드 실패:', error);
    }

    setupSettingsForm();
});

// --- 1. 내 참여 내역 로드 & 채팅방 입장 버튼 ---
async function loadMyParticipations() {
    const listContainer = document.getElementById('participationList');
    if (!listContainer) return;

    try {
        // API 호출: 내가 참여한 공구 목록
        // (UserService.java의 getMyParticipations 반환값 구조에 맞춤)
        const data = await apiFetch('/api/users/me/participations');
        
        // data.onlineParticipations 배열을 가져옴
        const onlineList = data.onlineParticipations || [];
        
        listContainer.innerHTML = ''; // 초기화

        if (onlineList.length === 0) {
            listContainer.innerHTML = '<div style="padding:20px; text-align:center; color:#999;">참여한 내역이 없습니다.</div>';
            return;
        }

        onlineList.forEach(item => {
            // item 구조: { id, onlineGroupBuy: { ... }, paymentStatus, ... }
            const groupBuy = item.onlineGroupBuy; 
            const product = groupBuy.product;
            
            const card = document.createElement('div');
            card.className = 'activity-item'; 
            card.style.borderLeft = '4px solid #4a90e2';
            card.style.marginBottom = '15px';
            
            // 채팅방 버튼 HTML 생성 (chatRoomId가 있을 경우에만 표시)
            let chatButtonHtml = '';
            if (groupBuy.chatRoomId) {
                // 버튼 클릭 시 chat.html로 이동하며 roomId 전달
                chatButtonHtml = `
                    <button onclick="location.href='chat.html?roomId=${groupBuy.chatRoomId}'" 
                            style="margin-top:10px; padding:8px 12px; background:#4a90e2; color:white; border:none; border-radius:4px; cursor:pointer; font-weight:bold;">
                        💬 채팅방 입장
                    </button>
                `;
            } else {
                chatButtonHtml = `<span style="font-size:12px; color:#999;">(채팅방 준비중)</span>`;
            }

            // 날짜 포맷팅
            const dateStr = item.createdAt ? new Date(item.createdAt).toLocaleDateString() : '-';

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <h3 style="margin-bottom:5px; font-size:16px; color:#333;">${groupBuy.title || '제목 없음'}</h3>
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


// --- 2. 토스페이먼츠 포인트 결제 로직 ---
async function initPointPayment() {
    const clientKey = "test_gck_docs_Ovk5rk1EwkEbP0W43n07xlzm"; 
    const tossPayments = TossPayments(clientKey);
    const customerKey = "user_" + (currentUserInfo?.id || new Date().getTime());
    
    paymentWidgets = tossPayments.widgets({ customerKey });

    await paymentWidgets.setAmount({
        currency: "KRW",
        value: 1000, 
    });

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
            if (selectedPointAmount <= 0) {
                alert('충전할 포인트를 선택해주세요.');
                return;
            }
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
            } catch (error) {
                console.error("결제 요청 실패:", error);
            }
        });
    }
}


// --- ⭐ 3. 공통 UI 및 헬퍼 함수들 (탭, 포인트표시, 설정폼) ---

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
                if (content.id === targetId) {
                    content.classList.add('active');
                }
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
                const isPositive = (item.amount > 0); // 양수면 획득, 음수면 사용
                const sign = isPositive ? '+' : ''; // 음수는 숫자에 -가 포함됨
                const color = isPositive ? '#4a90e2' : '#ff4444';

                row.innerHTML = `
                    <div>
                        <span style="font-weight:bold; color:#555;">[포인트]</span> 
                        <span style="color:#888; font-size:14px; margin-left:5px;">${dateStr}</span>
                    </div>
                    <span style="font-weight:bold; color:${color};">
                        ${sign}${new Intl.NumberFormat().format(item.amount)} P
                    </span>
                `;
                historyList.appendChild(row);
            });
        } else {
            historyList.innerHTML = '<div style="padding:20px; text-align:center; color:#999;">포인트 변동 내역이 없습니다.</div>';
        }

    } catch (error) {
        console.error('포인트 내역 로드 실패:', error);
    }
}

// --- 설정 폼 관련 ---
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

function setVal(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val || '';
}

function setupSettingsForm() {
    const form = document.getElementById('settingsForm');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        await saveSettings();
    });
}

async function saveSettings() {
    const password = document.getElementById('settingPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmNewPassword = document.getElementById('confirmNewPassword').value;

    if (!password) {
        alert('정보를 수정하려면 현재 비밀번호를 입력해야 합니다.');
        return;
    }

    // 비밀번호 변경 시도 시 확인
    if (newPassword || confirmNewPassword) {
        if (newPassword !== confirmNewPassword) {
            alert('새 비밀번호가 일치하지 않습니다.');
            return;
        }
    }

    // TODO: 비밀번호 검증 로직이 필요하다면 백엔드 API 추가 필요
    // 현재는 정보 수정 요청만 보냄

    const updateData = {
        nickname: getInputValue('settingNickname'),
        address: getInputValue('settingAddress'),
        addressDetail: getInputValue('settingAddressDetail'),
        zipCode: getInputValue('settingZip')
        // 비밀번호 변경은 별도 API가 필요할 수 있음
    };

    try {
        await apiFetch('/api/users/me', {
            method: 'PUT',
            body: updateData
        });
        alert('회원 정보가 수정되었습니다.');
        window.location.reload();
    } catch (error) {
        console.error(error);
        alert('정보 수정 실패: ' + error.message);
    }
}

function getInputValue(inputId) {
    const el = document.getElementById(inputId);
    return el ? el.value : null;
}