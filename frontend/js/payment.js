// 결제 페이지 JavaScript
let currentGroupBuy = null;
let paymentStatus = 'PENDING'; // PENDING, READY, PAID

document.addEventListener('DOMContentLoaded', async function() {
    // 인증 확인
    if (!checkAuth()) {
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return;
    }

    // URL에서 모집글 ID 가져오기
    const urlParams = new URLSearchParams(window.location.search);
    const groupBuyId = urlParams.get('groupBuyId');

    if (!groupBuyId) {
        alert('모집글 ID가 없습니다.');
        window.location.href = 'recruitment-list.html';
        return;
    }

    // 모집글 정보 및 결제 상태 로드
    await loadPaymentInfo(groupBuyId);
    
    // 사용자 정보 자동 입력
    await loadUserInfo();
});

// 결제 정보 로드
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

        // 상품 정보 표시
        renderProductInfo(currentGroupBuy);
        
        // 결제 버튼 상태 설정 (정보 로드 후)
        setupPaymentButton();

    } catch (error) {
        console.error('결제 정보 로드 실패:', error);
        alert('결제 정보를 불러오지 못했습니다: ' + error.message);
        window.location.href = 'recruitment-list.html';
    }
}

// 상품 정보 렌더링
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

    // 총 결제 금액 업데이트
    const summaryRows = document.querySelectorAll('.summary-row');
    if (summaryRows.length >= 1) {
        summaryRows[0].querySelector('span:last-child').textContent = `${perPersonPrice.toLocaleString()}원`;
    }
    
    const deliveryFee = 3000; // 배송비 고정
    if (summaryRows.length >= 2) {
        summaryRows[1].querySelector('span:last-child').textContent = `${deliveryFee.toLocaleString()}원`;
    }
    
    const totalAmount = perPersonPrice + deliveryFee;
    if (summaryRows.length >= 3) {
        summaryRows[2].querySelector('span:last-child').textContent = `${totalAmount.toLocaleString()}원`;
    }

    // 원형 결제 금액 표시
    const amountCircle = document.querySelector('.amount');
    if (amountCircle) {
        amountCircle.textContent = `${totalAmount.toLocaleString()}원`;
    }
}

// 사용자 정보 로드 및 자동 입력
async function loadUserInfo() {
    try {
        const user = await apiFetch('/api/users/me');
        
        const nameInput = document.querySelector('input[name="name"]');
        const emailInput = document.querySelector('input[name="email"]');
        const phoneInput = document.querySelector('input[name="phone"]');
        const addressInput = document.querySelector('input[name="address"]');
        
        if (nameInput && user.name) {
            nameInput.value = user.name;
        }
        if (emailInput && user.email) {
            emailInput.value = user.email;
        }
        if (phoneInput && user.phoneNumber) {
            phoneInput.value = user.phoneNumber;
        }
        if (addressInput && user.address) {
            addressInput.value = user.address + (user.addressDetail ? ' ' + user.addressDetail : '');
        }
    } catch (error) {
        console.error('사용자 정보 로드 실패:', error);
    }
}

// 결제 버튼 상태 설정
function setupPaymentButton() {
    const paymentBtn = document.querySelector('.btn-payment');
    if (!paymentBtn) return;

    // 결제 상태 확인
    // 방장이 결제 상태로 변경했는지 확인 (모집글 상태가 IN_PROGRESS이거나 결제 준비 상태인지)
    // 또는 참여 정보의 paymentStatus가 READY인지 확인
    const isPaymentReady = currentGroupBuy?.status === 'IN_PROGRESS' || 
                           currentGroupBuy?.paymentReady === true ||
                           paymentStatus === 'READY';
    
    if (!isPaymentReady) {
        // 결제 준비가 안 된 경우: 회색 버튼 (비활성화)
        paymentBtn.disabled = true;
        paymentBtn.style.backgroundColor = '#ccc';
        paymentBtn.style.cursor = 'not-allowed';
        paymentBtn.style.opacity = '0.6';
        paymentBtn.textContent = '결제하기';
    } else {
        // 결제 준비가 된 경우: 파란색 버튼 (활성화)
        paymentBtn.disabled = false;
        paymentBtn.style.backgroundColor = '#4a90e2';
        paymentBtn.style.cursor = 'pointer';
        paymentBtn.style.opacity = '1';
        paymentBtn.textContent = '결제하기';
    }
}

// 결제 처리
function processPayment() {
    const paymentBtn = document.querySelector('.btn-payment');
    
    // 결제 버튼이 비활성화된 경우
    if (paymentBtn && paymentBtn.disabled) {
        alert('host가 결제 상태로 변경 후 결제가 가능합니다!');
        return;
    }

    const form = document.querySelector('.orderer-form');
    const formData = new FormData(form);
    
    // 필수 필드 확인
    let isValid = true;
    form.querySelectorAll('input[required]').forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.style.borderColor = '#ff4444';
        } else {
            input.style.borderColor = '#ddd';
        }
    });
    
    if (!isValid) {
        alert('모든 필수 정보를 입력해주세요.');
        return;
    }
    
    if (confirm('결제를 진행하시겠습니까?')) {
        // TODO: 실제 결제 처리 API 호출
        alert('결제가 완료되었습니다!');
        window.location.href = 'mypage.html';
    }
}
