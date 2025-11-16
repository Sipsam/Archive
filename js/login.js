// 로그인/회원가입 JavaScript
function switchTab(tab) {
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const tabs = document.querySelectorAll('.tab-btn');
    
    tabs.forEach(t => t.classList.remove('active'));
    
    if (tab === 'login') {
        loginForm.classList.add('active');
        signupForm.classList.remove('active');
        tabs[0].classList.add('active');
    } else {
        signupForm.classList.add('active');
        loginForm.classList.remove('active');
        tabs[1].classList.add('active');
    }
}

// 로그인 폼 제출
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const userData = {
        email: formData.get('email'),
        name: '사용자' // 실제로는 서버에서 가져옴
    };
    
    login(userData);
    alert('로그인 성공!');
    window.location.href = 'index.html';
});

// 회원가입 폼 제출
document.getElementById('signupForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    
    if (formData.get('password') !== formData.get('passwordConfirm')) {
        alert('비밀번호가 일치하지 않습니다.');
        return;
    }
    
    const userData = {
        name: formData.get('name'),
        email: formData.get('email')
    };
    
    login(userData);
    alert('회원가입 성공!');
    window.location.href = 'index.html';
});

