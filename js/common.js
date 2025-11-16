// 공통 JavaScript 함수들

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 네비게이션 탭 활성화
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            navTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });
});

// 로그인/로그아웃 상태 확인
function checkAuth() {
    // 실제 구현 시 서버와 통신
    return localStorage.getItem('user') !== null;
}

// 사용자 정보 가져오기
function getUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// 로그인 처리
function login(userData) {
    localStorage.setItem('user', JSON.stringify(userData));
}

// 로그아웃 처리
function logout() {
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// 페이지 이동
function navigateTo(page) {
    window.location.href = page;
}

