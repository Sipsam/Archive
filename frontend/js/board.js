// frontend/js/board.js

// 1. 화면 전환 함수 (목록 <-> 글쓰기)
function switchBoardTab(tab) {
    const boardList = document.getElementById('boardList');
    const writeSection = document.getElementById('writeSection');
    const tabs = document.querySelectorAll('.board-tab');
    
    // 탭 활성화 스타일 초기화
    tabs.forEach(t => t.classList.remove('active'));

    if (tab === 'write') {
        // 로그인 체크
        if (!checkAuth()) {
            alert('로그인이 필요한 서비스입니다.');
            window.location.href = 'login.html';
            return;
        }
        // 글쓰기 화면 표시
        if(boardList) boardList.classList.add('hidden');
        if(writeSection) writeSection.classList.remove('hidden');
        
        // '쓰기' 탭 활성화 (인덱스 1번)
        if(tabs[1]) tabs[1].classList.add('active');

    } else {
        // 목록 화면 표시
        if(boardList) boardList.classList.remove('hidden');
        if(writeSection) writeSection.classList.add('hidden');
        
        // '목록' 탭 활성화 (인덱스 0번)
        if(tabs[0]) tabs[0].classList.add('active');
        
        // 목록 데이터 갱신
        loadPosts();
    }
}

// 2. 게시글 목록 불러오기 (GET)
async function loadPosts() {
    const boardList = document.getElementById('boardList');
    if (!boardList) return;

    try {
        // 백엔드 API 호출: boardType이 'REVIEW'인 글만 가져옴
        const posts = await apiFetch('/api/posts?boardType=REVIEW');
        
        boardList.innerHTML = ''; // 초기화

        if (!posts || posts.length === 0) {
            boardList.innerHTML = `
                <div style="text-align: center; padding: 50px; color: #666; background: #f9f9f9; border-radius: 8px;">
                    <p>아직 등록된 후기가 없습니다.</p>
                    <p style="font-size: 0.9em; margin-top: 10px;">첫 번째 후기를 남겨보세요!</p>
                </div>`;
            return;
        }

        // 받아온 데이터로 HTML 생성
        posts.forEach((post, index) => {
            const dateObj = new Date(post.createdAt);
            const dateStr = dateObj.toLocaleDateString();

            const itemDiv = document.createElement('div');
            itemDiv.className = 'board-item'; // CSS 스타일 적용 클래스
            itemDiv.innerHTML = `
                <span class="board-number" style="width: 50px; text-align: center;">${posts.length - index}</span>
                <span class="board-title" style="flex: 1; font-weight: bold;">${post.title}</span>
                <span class="board-author" style="width: 100px; text-align: center;">${post.authorName}</span>
                <span class="board-date" style="width: 100px; text-align: right; color: #888;">${dateStr}</span>
            `;

            // 클릭 시 내용 보기 (알림창)
            itemDiv.addEventListener('click', () => {
                alert(`[${post.title}]\n\n${post.content}`);
            });

            boardList.appendChild(itemDiv);
        });

    } catch (error) {
        console.error('게시글 로드 실패:', error);
        boardList.innerHTML = '<div style="text-align: center; padding: 20px; color: red;">데이터를 불러오지 못했습니다.</div>';
    }
}

// 3. 게시글 작성하기 (POST)
async function submitPost(event) {
    event.preventDefault(); // 새로고침 방지

    const titleInput = document.getElementById('title');
    const contentInput = document.getElementById('content');

    if (!titleInput.value.trim() || !contentInput.value.trim()) {
        alert("제목과 내용을 모두 입력해주세요.");
        return;
    }

    const postData = {
        boardType: 'REVIEW', // 백엔드 식별용
        title: titleInput.value,
        content: contentInput.value
    };

    try {
        await apiFetch('/api/posts', {
            method: 'POST',
            body: postData
        });

        alert('후기가 등록되었습니다! (100 포인트 적립)');
        
        // 입력창 비우고 목록으로 돌아가기
        titleInput.value = '';
        contentInput.value = '';
        switchBoardTab('list');

    } catch (error) {
        console.error('글 작성 실패:', error);
        alert('글 작성 중 오류가 발생했습니다.\n' + error.message);
    }
}

// 4. 초기화 이벤트
document.addEventListener('DOMContentLoaded', function() {
    loadPosts(); // 페이지 열리면 목록 불러오기

    // 글쓰기 폼 전송 이벤트 연결
    const writeForm = document.querySelector('.write-form');
    if (writeForm) {
        writeForm.addEventListener('submit', submitPost);
    }
});