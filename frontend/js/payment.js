// frontend/js/payment.js

let currentGroupBuy = null;
let currentUser = null; // 내 정보 저장용
let paymentStatus = 'PENDING'; 
let widgets = null; 
let currentAmount = 0; 
let selectedRating = 0; // 선택된 별점

document.addEventListener('DOMContentLoaded', async function() {
    // 1. 로그인 인증 확인
    if (!checkAuth()) {
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return;
    }

    // 2. URL 파라미터 확인
    const urlParams = new URLSearchParams(window.location.search);
    const groupBuyId = urlParams.get('groupBuyId');

    if (!groupBuyId) {
        alert('잘못된 접근입니다 (ID 없음).');
        window.location.href = 'recruitment-list.html';
        return;
    }

    // 3. 내 정보 로드 (방장 여부 체크 등을 위해)
    try {
        currentUser = await apiFetch('/api/users/me');
    } catch (e) {
        console.error("User load fail");
    }

    // 4. 데이터 로드 및 초기화
    await loadUserInfo();          
    await loadPaymentInfo(groupBuyId); 
    
    // 별점 이벤트 초기화
    initStarRating();
});

// 사용자 정보 로드 및 폼 채우기
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

// 결제 정보 로드 (상태 체크 포함)
async function loadPaymentInfo(groupBuyId) {
    try {
        currentGroupBuy = await apiFetch(`/api/groupbuys/online/${groupBuyId}`);
        const participations = await apiFetch(`/api/groupbuys/online/${groupBuyId}/participations`);
        const myInfo = await apiFetch('/api/users/me');
        const myParticipation = participations.find(p => p.user?.id === myInfo.id);
        
        if (myParticipation) {
            paymentStatus = myParticipation.paymentStatus || 'PENDING';
        }

        // 이미 결제된 상태(PAID)라면 결제창 숨기고 리뷰창 표시
        if (paymentStatus === 'PAID') {
            document.getElementById('payment-wrapper').style.display = 'none';
            
            // 내가 방장이 아니라면 리뷰창 표시 (참여자만 후기 작성)
            if (String(currentGroupBuy.hostId) !== String(myInfo.id)) {
                document.getElementById('review-wrapper').style.display = 'block';
            } else {
                // 방장이면 리뷰창 없이 알림 후 메인 이동
                alert('이미 결제가 완료된 공구입니다. (방장)');
                window.location.href = 'recruitment-detail.html?id=' + groupBuyId;
            }
            return; // 이후 결제 로직 실행 안 함
        }

        // 결제 전이라면 상품 정보 표시
        const productNameEl = document.querySelector('.product-name');
        if (productNameEl && currentGroupBuy.product) {
            productNameEl.textContent = currentGroupBuy.product.name;
        }

        currentAmount = renderProductInfo(currentGroupBuy);
        await initTossPayments(currentAmount);
        setupPaymentButton();

    } catch (error) {
        console.error('결제 정보 로드 실패:', error);
        alert('결제 정보를 불러오지 못했습니다.');
    }
}

// 상품 정보 및 가격 렌더링
function renderProductInfo(groupBuy) {
    const totalPrice = groupBuy.product?.price || 0;
    const perPersonPrice = Math.floor(totalPrice / (groupBuy.targetHeadcount || 1));
    const deliveryFee = 1000; 
    const totalAmount = perPersonPrice + deliveryFee;

    const detailsDiv = document.querySelector('.product-details');
    if(detailsDiv) {
        detailsDiv.innerHTML = `
            <span>수량: 1개 (1/N 분담)</span>
            <span>상품가격: ${perPersonPrice.toLocaleString()}원</span>
        `;
    }

    const summaryRows = document.querySelectorAll('.summary-row');
    if (summaryRows.length >= 3) {
        summaryRows[0].querySelector('span:last-child').textContent = `${perPersonPrice.toLocaleString()}원`;
        summaryRows[1].querySelector('span:last-child').textContent = `${deliveryFee.toLocaleString()}원`;
        summaryRows[2].querySelector('span:last-child').textContent = `${totalAmount.toLocaleString()}원`;
    }

    const amountCircle = document.querySelector('.amount');
    if (amountCircle) amountCircle.textContent = `${totalAmount.toLocaleString()}원`;

    return totalAmount;
}

// 토스 페이먼츠 초기화
async function initTossPayments(amount) {
    const clientKey = "test_gck_docs_Ovk5rk1EwkEbP0W43n07xlzm"; 
    const tossPayments = TossPayments(clientKey);
    const customerKey = "customer_" + new Date().getTime(); 
    widgets = tossPayments.widgets({ customerKey });

    await widgets.setAmount({ currency: "KRW", value: amount });
    await Promise.all([
        widgets.renderPaymentMethods({ selector: "#payment-method", variantKey: "DEFAULT" }),
        widgets.renderAgreement({ selector: "#agreement", variantKey: "AGREEMENT" }),
    ]);
}

// 결제 버튼 상태 관리
function setupPaymentButton() {
    const paymentBtn = document.getElementById('payment-button');
    if (!paymentBtn) return;

    // 공구 상태가 'IN_PROGRESS'(진행중=결제중) 일 때만 결제 가능
    const isPaymentOpen = (currentGroupBuy.status === 'IN_PROGRESS'); 

    if (!isPaymentOpen) {
        paymentBtn.style.backgroundColor = '#ccc';
        paymentBtn.style.cursor = 'not-allowed';
        paymentBtn.textContent = '아직 결제 단계가 아닙니다';
        paymentBtn.onclick = function() { alert('방장이 결제를 시작해야 합니다.'); };
    } else {
        paymentBtn.style.backgroundColor = '#4a90e2';
        paymentBtn.style.cursor = 'pointer';
        paymentBtn.textContent = '결제하기';
        paymentBtn.onclick = processPayment;
    }
}

// 결제 요청 프로세스
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
        const orderId = "ORDER_" + new Date().getTime(); 
        // 결제 성공 시 다시 이 페이지(payment.html)로 돌아오게 함 -> 그러면 위 로직(paymentStatus === 'PAID')에 의해 리뷰창이 뜸
        const successUrl = window.location.origin + `/success.html?groupBuyId=${currentGroupBuy.id}`;
        
        await widgets.requestPayment({
            orderId: orderId,
            orderName: currentGroupBuy?.title || "공동구매 참여",
            successUrl: successUrl, 
            failUrl: window.location.origin + "/fail.html",
            customerEmail: email,
            customerName: username,
            customerMobilePhone: phone,
        });
        
    } catch (error) {
        console.error("결제 요청 실패:", error);
    }
}

// 별점 및 리뷰 관련 함수들 (순수 프론트엔드 처리)

// 별점 기능 초기화
function initStarRating() {
    const stars = document.querySelectorAll('.star');
    const ratingValue = document.getElementById('ratingValue');

    stars.forEach(star => {
        // 1. 마우스 오버: 해당 별과 그 이전 별들을 채움 (CSS class 추가)
        star.addEventListener('mouseover', function() {
            const val = parseInt(this.dataset.value);
            highlightStars(val);
        });

        // 2. 마우스 아웃: 선택된 점수가 없으면 초기화, 있으면 선택된 점수만큼 표시
        star.addEventListener('mouseout', function() {
            highlightStars(selectedRating);
        });

        // 3. 클릭: 점수 확정
        star.addEventListener('click', function() {
            selectedRating = parseInt(this.dataset.value);
            ratingValue.textContent = selectedRating;
            highlightStars(selectedRating);
        });
    });
}

// 별 색상 변경 처리 (CSS filled 클래스 제어)
function highlightStars(count) {
    const stars = document.querySelectorAll('.star');
    stars.forEach(s => {
        const sVal = parseInt(s.dataset.value);
        if (sVal <= count) {
            s.classList.add('filled');
        } else {
            s.classList.remove('filled');
        }
    });
}

// 리뷰 제출 (평가 완료)
async function submitReview() {
    if (selectedRating === 0) {
        alert('매너 온도(별점)를 선택해주세요!');
        return;
    }

    const comment = document.getElementById('reviewComment').value;
    
    // 백엔드 API 규격에 맞는 데이터 생성
    const payload = {
        groupBuyId: currentGroupBuy.id,
        revieweeId: currentGroupBuy.hostId, // 방장 ID
        comment: comment,
        rating: parseFloat(selectedRating)  // 별점
    };

    try {
        // 백엔드로 리뷰 전송
        await apiFetch('/api/reviews', {
            method: 'POST',
            body: payload
        });
        
        alert('소중한 후기가 등록되었습니다! 메인으로 이동합니다.');
        window.location.href = 'index.html';
        
    } catch (error) {
        console.error(error);
        alert('리뷰 등록 중 문제가 발생했습니다.');
        window.location.href = 'index.html';
    }
}

// 평가 건너뛰기
function exitToMain() {
    if(confirm('평가를 하지 않고 나가시겠습니까?')) {
        window.location.href = 'index.html';
    }
}

// 전역 함수 노출
window.exitToMain = exitToMain;
window.submitReview = submitReview;