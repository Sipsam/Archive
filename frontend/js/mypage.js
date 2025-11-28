// js/mypage.js

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
    
    // 2. 탭 기능 설정 (mypage.html용)
    setupTabs();

    // 3. 사용자 정보 로드
    try {
        const myInfo = await apiFetch('/api/users/me'); 
        currentUserInfo = myInfo;
        
        // UI 바인딩
        const nameElement = document.getElementById('userName');
        if (nameElement) nameElement.textContent = myInfo.nickname || '사용자';
        
        const scoreElement = document.querySelector('.score');
        if (scoreElement) {
            const temp = myInfo.mannerTemp !== undefined ? myInfo.mannerTemp : 36.5;
            scoreElement.textContent = temp.toFixed(1);
        }
        
        updatePointUI(myInfo.points);
        
        // 내역 로드
        await loadMyParticipations();
        
        // 설정 폼 초기화
        populateSettingsForm(myInfo);
        
        // 포인트 페이지일 경우 포인트 내역 로드
        if(document.getElementById('pointHistoryList')) {
            await loadMyPointHistory();
        }

        // ⭐ 포인트 결제 초기화 (point.html용)
        if (document.getElementById('payment-method')) {
            await initPointPayment();
        }

    } catch (error) {
        console.error('정보 로드 실패:', error);
    }

    setupSettingsForm();
});

// --- ⭐ 토스페이먼츠 포인트 결제 로직 ---

async function initPointPayment() {
    const clientKey = "test_gck_docs_Ovk5rk1EwkEbP0W43n07xlzm"; // 테스트용 클라이언트 키
    const tossPayments = TossPayments(clientKey);
    
    // 회원 고유 키 생성 (로그인 ID 활용 권장)
    const customerKey = "user_" + (currentUserInfo?.id || new Date().getTime());
    
    paymentWidgets = tossPayments.widgets({ customerKey });

    // 초기 금액 설정 (0원 혹은 기본값)
    await paymentWidgets.setAmount({
        currency: "KRW",
        value: 1000, // 위젯 렌더링을 위해 임시 값 설정 (실제 결제 시 변경됨)
    });

    // 위젯 렌더링
    await Promise.all([
        paymentWidgets.renderPaymentMethods({
            selector: "#payment-method",
            variantKey: "DEFAULT",
        }),
        paymentWidgets.renderAgreement({ selector: "#agreement", variantKey: "AGREEMENT" }),
    ]);
    
    // 위젯 영역 표시 및 이벤트 연결
    document.getElementById('payment-widget-area').style.display = 'block';
    setupPointPurchaseEvents();
}

function setupPointPurchaseEvents() {
    const purchaseItems = document.querySelectorAll('.point-purchase-list .purchase-item');
    const purchaseBtn = document.getElementById('point-payment-btn');
    
    // 1. 포인트 선택 이벤트
    purchaseItems.forEach(item => {
        item.addEventListener('click', async function() {
            // 스타일 업데이트
            purchaseItems.forEach(i => i.classList.remove('selected'));
            this.classList.add('selected');

            // 금액 가져오기
            const price = parseInt(this.dataset.price, 10);
            selectedPointAmount = price;

            // ⭐ 위젯 금액 업데이트
            await paymentWidgets.setAmount({
                currency: "KRW",
                value: price,
            });

            // 버튼 텍스트 업데이트
            if (purchaseBtn) {
                purchaseBtn.textContent = `${price.toLocaleString()}원 결제하기`;
                purchaseBtn.disabled = false;
            }
        });
    });

    // 2. 결제하기 버튼 클릭 이벤트
    if (purchaseBtn) {
        // 초기에는 비활성화 (선택 전)
        purchaseBtn.textContent = "충전할 금액을 선택해주세요";
        purchaseBtn.disabled = true;

        purchaseBtn.addEventListener('click', async function() {
            if (selectedPointAmount <= 0) {
                alert('충전할 포인트를 선택해주세요.');
                return;
            }

            try {
                // 포인트 충전용 고유 주문번호 생성 (POINT_ 접두어 사용)
                const orderId = "POINT_" + new Date().getTime();

                // ⭐ 결제 요청
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
                alert("결제 요청 중 오류가 발생했습니다.");
            }
        });
    }
}


// --- 탭(메뉴) 전환 기능 (기존 유지) ---
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

// UI 포인트 업데이트 헬퍼
function updatePointUI(points) {
    const safePoints = points || 0;
    const formatted = new Intl.NumberFormat().format(safePoints);
    
    // 프로필 및 메인 타이틀 포인트 업데이트
    const profilePoint = document.getElementById('userPointsProfile');
    const mainPoint = document.getElementById('userPoints');
    
    if(profilePoint) profilePoint.textContent = formatted;
    if(mainPoint) mainPoint.textContent = formatted + " P";
}

// --- 참여 내역 로드 ---
async function loadMyParticipations() {
    const participationList = document.getElementById('participationList');
    if (!participationList) return;

    // ... (기존 로직 유지) ...
}

// --- 포인트 변동 내역 로드 (point.html용) ---
async function loadMyPointHistory() {
    const historyList = document.getElementById('pointHistoryList'); 
    if (!historyList) return; 

    try {
        const historyData = await apiFetch('/api/points/history');
        
        historyList.innerHTML = ''; 
        
        if (historyData && historyData.length > 0) {
            historyData.forEach(item => {
                const row = document.createElement('div');
                row.className = 'activity-item'; // 스타일 재사용
                row.style.display = 'flex';
                row.style.justifyContent = 'space-between';
                
                const dateStr = item.createdAt ? new Date(item.createdAt).toLocaleDateString() : '-';
                const typeText = (item.type === 'PURCHASE' || item.type === 'CHARGE') ? '충전' : '사용';
                const isPositive = (item.type === 'PURCHASE' || item.type === 'CHARGE');
                const sign = isPositive ? '+' : '-';
                const color = isPositive ? '#4a90e2' : '#ff4444';

                row.innerHTML = `
                    <div>
                        <span style="font-weight:bold; color:#555;">[${typeText}]</span> 
                        <span style="color:#888; font-size:14px; margin-left:5px;">${dateStr}</span>
                    </div>
                    <span style="font-weight:bold; color:${color};">
                        ${sign} ${new Intl.NumberFormat().format(item.amount)} P
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

// --- 설정 폼 관련 (기존 유지) ---
function populateSettingsForm(user) { /* ... 기존 코드 ... */ }
function setupSettingsForm() { /* ... 기존 코드 ... */ }
async function saveSettings() { /* ... 기존 코드 ... */ }
function getInputValue(inputId) { /* ... 기존 코드 ... */ }
async function verifyCurrentPassword(password) { /* ... 기존 코드 ... */ }