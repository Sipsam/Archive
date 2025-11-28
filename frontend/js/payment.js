// 결제 페이지 JavaScript
let currentGroupBuy = null;
let paymentStatus = 'PENDING'; // PENDING, READY, PAID
let widgets = null; // 토스페이먼츠 위젯 객체 저장용
let currentAmount = 0; // 총 결제 금액 저장용

document.addEventListener('DOMContentLoaded', async function() {
    // 1. 인증 확인
    if (!checkAuth()) {
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return;
    }

    // 2. URL에서 모집글 ID 가져오기
    const urlParams = new URLSearchParams(window.location.search);
    const groupBuyId = urlParams.get('groupBuyId');

    if (!groupBuyId) {
        alert('모집글 ID가 없습니다.');
        window.location.href = 'recruitment-list.html';
        return;
    }

    // 3. 사용자 정보 및 모집글 정보 로드
    // (순서 중요: 사용자 정보를 먼저 가져와야 customerKey 등으로 활용 가능)
    await loadUserInfo();
    await loadPaymentInfo(groupBuyId);
});

// 사용자 정보 로드 및 자동 입력
async function loadUserInfo() {
    try {
        const user = await apiFetch('/api/users/me');
        
        // 폼에 사용자 정보 자동 입력
        const nameInput = document.getElementById('username'); // HTML ID와 일치시킴
        const emailInput = document.getElementById('email');
        const phoneInput = document.getElementById('mobile');
        const addressInput = document.querySelector('input[name="address"]');
        
        if (nameInput && user.name) nameInput.value = user.name;
        if (emailInput && user.email) emailInput.value = user.email;
        if (phoneInput && user.phoneNumber) phoneInput.value = user.phoneNumber;
        if (addressInput && user.address) {
            addressInput.value = user.address + (user.addressDetail ? ' ' + user.addressDetail : '');
        }
    } catch (error) {
        console.error('사용자 정보 로드 실패:', error);
    }
}

// 결제 정보 및 모집글 로드
async function loadPaymentInfo(groupBuyId) {
    try {
        // 모집글 상세 정보 조회
        currentGroupBuy = await apiFetch(`/api/groupbuys/online/${groupBuyId}`);
        
        // 참여 정보 조회 (결제 상태 확인)
        const participations = await apiFetch(`/api/groupbuys/online/${groupBuyId}/participations`);
        const myInfo = await apiFetch('/api/users/me');
        const myParticipation = participations.find(p => p.user?.id === myInfo.id);
        
        if (myParticipation) {
            paymentStatus = myParticipation.paymentStatus || 'PENDING';
        }

        // 1. 상품 정보 표시하고 결제 금액 계산해오기
        currentAmount = renderProductInfo(currentGroupBuy);
        
        // 2. 토스페이먼츠 위젯 초기화 (금액이 확정된 후 실행)
        await initTossPayments(currentAmount);

        // 3. 결제 버튼 상태 설정
        setupPaymentButton();

    } catch (error) {
        console.error('결제 정보 로드 실패:', error);
        alert('결제 정보를 불러오지 못했습니다: ' + error.message);
        // window.location.href = 'recruitment-list.html'; // 디버깅을 위해 주석 처리 가능
    }
}

// ⭐ [추가] 토스페이먼츠 위젯 초기화 함수
async function initTossPayments(amount) {
    const clientKey = "test_ck_LlDJaYngroyZROYGmRlx3ezGdRpX"; // 테스트용 클라이언트 키
    const tossPayments = TossPayments(clientKey);
    
    // 회원 고유 키 (로그인된 사용자 ID 등을 사용하면 좋으나, 여기선 랜덤 생성)
    const customerKey = "customer_" + new Date().getTime(); 
    
    widgets = tossPayments.widgets({ customerKey });

    // 결제 금액 설정
    await widgets.setAmount({
        currency: "KRW",
        value: amount,
    });

    await Promise.all([
        // 결제 UI 렌더링
        widgets.renderPaymentMethods({
            selector: "#payment-method",
            variantKey: "DEFAULT",
        }),
        // 이용약관 UI 렌더링
        widgets.renderAgreement({ selector: "#agreement", variantKey: "AGREEMENT" }),
    ]);
}

// 상품 정보 렌더링 (수정: 총 금액 반환하도록 변경)
function renderProductInfo(groupBuy) {
    const productName = document.querySelector('.product-name');
    if (productName && groupBuy.product) {
        productName.textContent = groupBuy.product.name || '상품명 없음';
    }

    // 가격 정보 계산
    const totalPrice = groupBuy.product?.price || 0;
    const perPersonPrice = Math.floor(totalPrice / (groupBuy.targetHeadcount || 1));
    
    const productDetails = document.querySelector('.product-details');
    if (productDetails) {
        productDetails.innerHTML = `
            <span>수량: 1개</span>
            <span>가격: ${perPersonPrice.toLocaleString()}원</span>
        `;
    }

    // 요약 정보 업데이트
    const summaryRows = document.querySelectorAll('.summary-row');
    if (summaryRows.length >= 1) {
        summaryRows[0].querySelector('span:last-child').textContent = `${perPersonPrice.toLocaleString()}원`;
    }
    
    const deliveryFee = 3000; // 배송비
    if (summaryRows.length >= 2) {
        summaryRows[1].querySelector('span:last-child').textContent = `${deliveryFee.toLocaleString()}원`;
    }
    
    const totalAmount = perPersonPrice + deliveryFee;
    if (summaryRows.length >= 3) {
        summaryRows[2].querySelector('span:last-child').textContent = `${totalAmount.toLocaleString()}원`;
    }

    // 원형 금액 표시
    const amountCircle = document.querySelector('.amount');
    if (amountCircle) {
        amountCircle.textContent = `${totalAmount.toLocaleString()}원`;
    }

    return totalAmount; // ⭐ 계산된 총 금액 반환
}

// 결제 버튼 상태 설정
function setupPaymentButton() {
    const paymentBtn = document.getElementById('payment-button'); // ID로 선택 권장
    if (!paymentBtn) return;

    // 결제 가능 조건: 모집글 상태가 진행중이거나, 결제 준비가 되었거나, 내 상태가 READY 일 때
    const isPaymentReady = currentGroupBuy?.status === 'IN_PROGRESS' || 
                           currentGroupBuy?.paymentReady === true ||
                           paymentStatus === 'READY';
    
    if (!isPaymentReady) {
        paymentBtn.disabled = true;
        paymentBtn.style.backgroundColor = '#ccc';
        paymentBtn.style.cursor = 'not-allowed';
        paymentBtn.textContent = '결제 대기중';
    } else {
        paymentBtn.disabled = false;
        paymentBtn.style.backgroundColor = '#4a90e2';
        paymentBtn.style.cursor = 'pointer';
        paymentBtn.textContent = '결제하기';
        
        // ⭐ 버튼 클릭 이벤트 연결 (기존 onclick 속성 대신 addEventListener 사용 권장)
        // HTML에 onclick="processPayment()"가 있다면 제거하거나 그대로 둬도 덮어씌워질 수 있습니다.
        paymentBtn.onclick = processPayment; 
    }
}

// ⭐ [수정] 결제 처리 함수 (토스페이먼츠 요청)
async function processPayment() {
    const paymentBtn = document.getElementById('payment-button');
    if (paymentBtn && paymentBtn.disabled) {
        alert('아직 결제를 진행할 수 없습니다.');
        return;
    }

    // 1. 입력 폼 유효성 검사
    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const phone = document.getElementById("mobile").value;
    const address = document.querySelector('input[name="address"]').value;

    if (!username || !email || !phone || !address) {
        alert("주문자 정보를 모두 입력해주세요.");
        return;
    }

    // 2. 토스페이먼츠 결제창 호출
    try {
        const orderId = "ORDER_" + new Date().getTime(); // 고유 주문번호 생성

        await widgets.requestPayment({
            orderId: orderId,
            orderName: currentGroupBuy?.title || "공동구매 상품", // 주문명
            successUrl: window.location.origin + "/success.html", // 성공 리다이렉트
            failUrl: window.location.origin + "/fail.html",       // 실패 리다이렉트
            customerEmail: email,
            customerName: username,
            customerMobilePhone: phone,
        });
        
    } catch (error) {
        console.error("결제 요청 실패:", error);
        alert("결제 요청 중 오류가 발생했습니다.");
    }
}