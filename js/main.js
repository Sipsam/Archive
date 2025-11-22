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

// 검색 기능
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-input');
    const searchBtn = document.querySelector('.search-btn');
    
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

