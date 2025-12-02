// frontend/js/payment.js

let currentGroupBuy = null;
let currentUser = null; 
let paymentStatus = 'PENDING'; 
let widgets = null; 
let currentAmount = 0; 
let selectedRating = 0; 
let myParticipationId = null; 

document.addEventListener('DOMContentLoaded', async function() {
    if (!checkAuth()) {
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const groupBuyId = urlParams.get('groupBuyId');

    if (!groupBuyId) {
        alert('잘못된 접근입니다 (ID 없음).');
        window.location.href = 'recruitment-list.html';
        return;
    }

    try {
        currentUser = await apiFetch('/api/users/me');
    } catch (e) {
        console.error("User load fail");
    }

    await loadUserInfo();          
    await loadPaymentInfo(groupBuyId); 
    
    initStarRating();
});

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

async function loadPaymentInfo(groupBuyId) {
    try {
        currentGroupBuy = await apiFetch(`/api/groupbuys/online/${groupBuyId}`);
        const participations = currentGroupBuy.participationList || [];
        const myInfo = await apiFetch('/api/users/me');
        
        const myParticipation = participations.find(p => String(p.userId) === String(myInfo.id));
        
        if (myParticipation) {
            paymentStatus = myParticipation.paymentStatus || 'PENDING';
            myParticipationId = myParticipation.id; 
        }

        if (paymentStatus === 'PAID') {
            document.getElementById('payment-wrapper').style.display = 'none';
            const isHost = (String(currentGroupBuy.hostId) === String(myInfo.id));

            if (!isHost) {
                document.getElementById('review-wrapper').style.display = 'block';
            } else {
                alert('이미 결제가 완료된 공구입니다. (방장은 본인을 평가할 수 없습니다)');
                window.location.href = 'index.html';
            }
            return; 
        }

        const productNameEl = document.querySelector('.product-name');
        if (productNameEl && currentGroupBuy.productName) {
            productNameEl.textContent = currentGroupBuy.productName;
        } else if (productNameEl && currentGroupBuy.product) {
            productNameEl.textContent = currentGroupBuy.product.name;
        }

        currentAmount = renderProductInfo(currentGroupBuy);
        await initTossPayments(currentAmount);
        setupPaymentButton();

    } catch (error) {
        console.error('결제 정보 로드 실패:', error);
        alert('결제 정보를 불러오지 못했습니다: ' + error.message);
    }
}

function renderProductInfo(groupBuy) {
    const price = groupBuy.productPrice !== undefined ? groupBuy.productPrice : (groupBuy.product ? groupBuy.product.price : 0);
    const totalPrice = price || 0;
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

function setupPaymentButton() {
    const paymentBtn = document.getElementById('payment-button');
    if (!paymentBtn) return;

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

async function processPayment() {
    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const phone = document.getElementById("mobile").value;
    const address = document.querySelector('input[name="address"]').value;

    if (!username || !email || !phone || !address) {
        alert("주문자 정보를 모두 입력해주세요.");
        return;
    }

    if (!myParticipationId) {
        alert("참여 정보를 찾을 수 없습니다. 다시 시도해주세요.");
        window.location.reload();
        return;
    }

    try {
        const orderId = `PART_${myParticipationId}_${new Date().getTime()}`; 
        const successUrl = window.location.origin + `/success.html?groupBuyId=${currentGroupBuy.id}`;
        
        await widgets.requestPayment({
            orderId: orderId,
            orderName: currentGroupBuy.title || "공동구매 참여",
            successUrl: successUrl, 
            failUrl: window.location.origin + "/fail.html",
        });
        
    } catch (error) {
        console.error("결제 요청 실패:", error);
    }
}

function initStarRating() {
    const stars = document.querySelectorAll('.star');
    const ratingValue = document.getElementById('ratingValue');

    stars.forEach(star => {
        star.addEventListener('mouseover', function() {
            const val = parseInt(this.dataset.value);
            highlightStars(val);
        });

        star.addEventListener('mouseout', function() {
            highlightStars(selectedRating);
        });

        star.addEventListener('click', function() {
            selectedRating = parseInt(this.dataset.value);
            ratingValue.textContent = selectedRating;
            highlightStars(selectedRating);
        });
    });
}

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

async function submitReview() {
    if (selectedRating === 0) {
        alert('매너 온도(별점)를 선택해주세요!');
        return;
    }
    
    // [수정] 코멘트 입력창이 없어졌으므로 빈 문자열 전송
    const payload = {
        groupBuyId: currentGroupBuy.id,
        revieweeId: currentGroupBuy.hostId, 
        comment: "", // 빈 문자열
        rating: parseFloat(selectedRating)
    };
    try {
        await apiFetch('/api/reviews', { method: 'POST', body: payload });
        alert('별점 평가가 완료되었습니다! 메인으로 이동합니다.');
        window.location.href = 'index.html';
    } catch (error) {
        console.error(error);
        alert('별점 평가가 완료되었습니다! 메인으로 이동합니다.');
        window.location.href = 'index.html';
    }
}

function exitToMain() {
    if(confirm('평가를 하지 않고 나가시겠습니까?')) {
        window.location.href = 'index.html';
    }
}

window.exitToMain = exitToMain;
window.submitReview = submitReview;