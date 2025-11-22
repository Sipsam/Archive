// Q/A 페이지 JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const qaForm = document.querySelector('.qa-form');
    
    if (qaForm) {
        qaForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            alert('질문이 등록되었습니다!');
            this.reset();
        });
    }
    
    // Q/A 항목 클릭 시 상세 보기
    const qaItems = document.querySelectorAll('.qa-item');
    qaItems.forEach(item => {
        item.addEventListener('click', function() {
            const content = this.querySelector('.qa-content');
            if (content.style.display === 'none') {
                content.style.display = 'block';
            } else {
                content.style.display = 'none';
            }
        });
    });
});

