// 결제 페이지 JavaScript
function processPayment() {
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
        alert('결제가 완료되었습니다!');
        // 실제 결제 처리 로직
        window.location.href = 'mypage.html';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // 사용자 정보 자동 입력
    const user = getUser();
    if (user) {
        const nameInput = document.querySelector('input[name="name"]');
        const emailInput = document.querySelector('input[name="email"]');
        
        if (nameInput && user.name) {
            nameInput.value = user.name;
        }
        if (emailInput && user.email) {
            emailInput.value = user.email;
        }
    }
});

