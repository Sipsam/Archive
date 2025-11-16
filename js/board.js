// 게시판 JavaScript
function switchBoardTab(tab) {
    const boardList = document.getElementById('boardList');
    const writeSection = document.getElementById('writeSection');
    const tabs = document.querySelectorAll('.board-tab');
    
    tabs.forEach(t => t.classList.remove('active'));
    
    if (tab === 'write') {
        boardList.classList.add('hidden');
        writeSection.classList.remove('hidden');
        tabs[0].classList.add('active');
    } else if (tab === 'qa') {
        window.location.href = 'qa.html';
    } else {
        boardList.classList.remove('hidden');
        writeSection.classList.add('hidden');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const writeForm = document.querySelector('.write-form');
    
    if (writeForm) {
        writeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            alert('후기가 작성되었습니다!');
            this.reset();
            switchBoardTab('list');
        });
    }
    
    // 게시글 클릭 이벤트
    const boardItems = document.querySelectorAll('.board-item');
    boardItems.forEach(item => {
        item.addEventListener('click', function() {
            const title = this.querySelector('.board-title').textContent;
            alert('게시글 상세: ' + title);
            // 실제로는 상세 페이지로 이동
        });
    });
});

