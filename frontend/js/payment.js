// frontend/js/payment.js

let currentGroupBuy = null;
let paymentStatus = 'PENDING'; 
let widgets = null; // 토스페이먼츠 위젯
let currentAmount = 0; // 총 결제 금액

document.addEventListener('DOMContentLoaded', async function() {
    // 1. 로그인 인증 확인
    if (!checkAuth()) {
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return;
    }

    // 2. URL 파라미터 확인 (모집글 ID)
    const urlParams = new URLSearchParams(window.location.search);
    const groupBuyId = urlParams.get('groupBuyId');

    if (!groupBuyId) {
        alert('잘못된 접근입니다 (ID 없음).');
        window.location.href = 'recruitment-list.html';
        return;
    }

    // 3. 데이터 로드 시작
    await loadUserInfo();          // 주문자 정보(내 정보) 채우기
    await loadPaymentInfo(groupBuyId); // 상품 정보 및 결제 금액 계산
});

// [API] 사용자 정보 로드 및 폼 자동 입력
async function loadUserInfo() {
    try {
        const user = await apiFetch('/api/users/me');
        
        const nameInput = document.getElementById('username'); 
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

// [API] 결제 정보(모집글+참여상태) 로드
async function loadPaymentInfo(groupBuyId) {
    try {
        // 모집글 상세 조회
        currentGroupBuy = await apiFetch(`/api/groupbuys/online/${groupBuyId}`);
        
        // 내 결제 상태 확인
        const participations = await apiFetch(`/api/groupbuys/online/${groupBuyId}/participations`);
        const myInfo = await apiFetch('/api/users/me');
        const myParticipation = participations.find(p => p.user?.id === myInfo.id);
        
        if (myParticipation) {
            paymentStatus = myParticipation.paymentStatus || 'PENDING';
        }

        // 1. 상품명 표시 (productName)
        const productNameEl = document.querySelector('.product-name');
        if (productNameEl && currentGroupBuy.product) {
            productNameEl.textContent = currentGroupBuy.product.name;
        }

        // 2. 금액 계산 및 화면 표시
        currentAmount = renderProductInfo(currentGroupBuy);
        
        // 3. 토스페이먼츠 위젯 초기화
        await initTossPayments(currentAmount);

        // 4. 결제하기 버튼 상태 설정 (회색/파란색 처리)
        setupPaymentButton();

    } catch (error) {
        console.error('결제 정보 로드 실패:', error);
        alert('결제 정보를 불러오지 못했습니다.');
    }
}

// [UI] 상품 정보 및 금액 렌더링
function renderProductInfo(groupBuy) {
    const totalPrice = groupBuy.product?.price || 0;
    // 인당 가격 계산 (총 가격 / 목표 인원)
    const perPersonPrice = Math.floor(totalPrice / (groupBuy.targetHeadcount || 1));
    
    // 배송비 (고정 1,000원 가정)
    const deliveryFee = 1000; 
    const totalAmount = perPersonPrice + deliveryFee;

    // 왼쪽 '상품정보' 디테일 업데이트
    const detailsDiv = document.querySelector('.product-details');
    if(detailsDiv) {
        detailsDiv.innerHTML = `
            <span>수량: 1개 (1/N 분담)</span>
            <span>상품가격: ${perPersonPrice.toLocaleString()}원</span>
        `;
    }

    // 오른쪽 '총결제 내용' 업데이트
    const summaryRows = document.querySelectorAll('.summary-row');
    if (summaryRows.length >= 3) {
        // 상품 금액
        summaryRows[0].querySelector('span:last-child').textContent = `${perPersonPrice.toLocaleString()}원`;
        // 배송비
        summaryRows[1].querySelector('span:last-child').textContent = `${deliveryFee.toLocaleString()}원`;
        // 총 결제금액
        summaryRows[2].querySelector('span:last-child').textContent = `${totalAmount.toLocaleString()}원`;
    }

    // 원형 금액 표시
    const amountCircle = document.querySelector('.amount');
    if (amountCircle) amountCircle.textContent = `${totalAmount.toLocaleString()}원`;

    return totalAmount; // 최종 결제 금액 반환
}

// [Toss] 결제 위젯 초기화
async function initTossPayments(amount) {
    const clientKey = "test_gck_docs_Ovk5rk1EwkEbP0W43n07xlzm"; // 테스트 키
    const tossPayments = TossPayments(clientKey);
    
    // 유저 고유 키 생성
    const customerKey = "customer_" + new Date().getTime(); 
    widgets = tossPayments.widgets({ customerKey });

    // 금액 설정
    await widgets.setAmount({
        currency: "KRW",
        value: amount,
    });

    // 위젯 렌더링
    await Promise.all([
        widgets.renderPaymentMethods({ selector: "#payment-method", variantKey: "DEFAULT" }),
        widgets.renderAgreement({ selector: "#agreement", variantKey: "AGREEMENT" }),
    ]);
}

// ⭐ [핵심] 결제 버튼 상태 관리 (회색 vs 파란색)
function setupPaymentButton() {
    const paymentBtn = document.getElementById('payment-button');
    if (!paymentBtn) return;

    // 결제 가능 조건: 
    // 백엔드 GroupBuyStatus가 PAYING 또는 IN_PROGRESS 등 결제 허용 상태여야 함.
    // "방장이 상태를 변경했는지"를 status로 판단함.
    // (기본 RECRUITING 상태면 결제 불가)
    
    const isPaymentOpen = (currentGroupBuy.status !== 'RECRUITING'); 

    if (!isPaymentOpen) {
        // [상태 1] 아직 결제 불가능 (회색 버튼)
        paymentBtn.style.backgroundColor = '#ccc'; // 회색
        paymentBtn.style.cursor = 'pointer'; 
        paymentBtn.textContent = '결제 대기중';
        
        // 클릭 시 Alert 띄우기
        paymentBtn.onclick = function() {
            alert('Host가 결제 상태로 변경 후 결제가 가능합니다!');
        };
    } else {
        // [상태 2] 결제 가능 (파란색 버튼)
        paymentBtn.style.backgroundColor = '#4a90e2'; // 파란색
        paymentBtn.style.cursor = 'pointer';
        paymentBtn.textContent = '결제하기';
        
        // 클릭 시 진짜 결제 함수 실행
        paymentBtn.onclick = processPayment;
    }
}

// [Toss] 실제 결제 요청 함수
async function processPayment() {
    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const phone = document.getElementById("mobile").value;
    const address = document.querySelector('input[name="address"]').value;

    if (!username || !email || !phone || !address) {
        alert("주문자 정보를 모두 입력해주세요.");
        return;
    }

    try {
        const orderId = "ORDER_" + new Date().getTime(); // 주문번호 생성

        await widgets.requestPayment({
            orderId: orderId,
            orderName: currentGroupBuy?.title || "공동구매 참여",
            successUrl: window.location.origin + "/success.html",
            failUrl: window.location.origin + "/fail.html",
            customerEmail: email,
            customerName: username,
            customerMobilePhone: phone,
        });
        
    } catch (error) {
        console.error("결제 요청 실패:", error);
        // 에러 처리는 필요 시 추가
    }
}