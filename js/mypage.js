// 마이페이지 JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const user = getUser();
    
    if (user) {
        document.getElementById('userName').textContent = user.name || '사용자';
        // 포인트는 실제로는 서버에서 가져옴
        document.getElementById('userPoints').textContent = '1,000';
    } else {
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
    }
});

