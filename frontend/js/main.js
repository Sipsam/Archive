// 메인페이지 JavaScript
function filterContent(type) {
    const cards = document.querySelectorAll('.content-card');
    const tabs = document.querySelectorAll('.nav-tab');
    
    // 탭 활성화
    tabs.forEach(tab => {
        if (tab.textContent.includes(type === 'online' ? '온라인' : '오프라인')) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
    
    // 카드 필터링
    cards.forEach(card => {
        if (card.dataset.type === type) {
            card.classList.remove('hidden');
        } else {
            card.classList.add('hidden');
        }
    });
}

// 인증 상태에 따라 헤더의 버튼을 '로그인/가입' 또는 '로그아웃'으로 변경합니다.

function updateAuthButton() {
    // common.js의 checkAuth() 함수 사용
    const isAuthenticated = checkAuth(); 
    const authButton = document.getElementById('authButton'); // index.html에 ID를 추가해야 함

    if (!authButton) return;

    if (isAuthenticated) {
        // ✅ 로그인 상태: 로그아웃 버튼으로 변경
        authButton.textContent = '로그아웃';
        authButton.href = '#'; 
        authButton.classList.remove('btn-secondary');
        authButton.classList.add('btn-primary'); // 스타일 변경 (선택 사항)

        authButton.onclick = function(e) {
            e.preventDefault();
            if (confirm('로그아웃 하시겠습니까?')) {
                logout(); // common.js의 logout() 호출
            }
        };

    } else {
        // ❌ 비로그인 상태: 로그인/회원가입 버튼 유지
        authButton.textContent = '로그인/회원가입';
        authButton.href = 'login.html';
        authButton.classList.remove('btn-primary');
        authButton.classList.add('btn-secondary');
        authButton.onclick = null; // 기본 링크 동작
    }
}

// 검색 기능
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-input');
    const searchBtn = document.querySelector('.search-btn');
    
    updateAuthButton(); 

    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            const query = searchInput.value;
            if (query.trim()) {
                alert('검색 기능: ' + query);
                // 실제 검색 로직 구현
            }
        });
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchBtn.click();
            }
        });
    }
});

