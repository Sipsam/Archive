// frontend/js/board.js

document.addEventListener('DOMContentLoaded', function() {
    // 페이지 로드 시 목록 불러오기
    loadPosts();

    // 글쓰기 폼 이벤트 연결
    const writeForm = document.querySelector('.write-form');
    if (writeForm) {
        writeForm.addEventListener('submit', submitPost);
    }
});

// 1. 탭 전환 (목록 <-> 쓰기)
function switchBoardTab(tab) {
    const boardList = document.getElementById('boardList');
    const writeSection = document.getElementById('writeSection');
    const tabs = document.querySelectorAll('.board-tab');
    
    // 탭 스타일 초기화
    tabs.forEach(t => t.classList.remove('active'));

    if (tab === 'write') {
        // 로그인 체크 (글쓰기는 로그인 필수)
        if (!checkAuth()) {
            alert('로그인이 필요한 서비스입니다.');
            window.location.href = 'login.html';
            return;
        }
        // 화면 전환
        boardList.classList.add('hidden');
        writeSection.classList.remove('hidden');
        tabs[1].classList.add('active'); // '쓰기' 탭 활성화

    } else {
        // 화면 전환
        boardList.classList.remove('hidden');
        writeSection.classList.add('hidden');
        tabs[0].classList.add('active'); // '목록' 탭 활성화
        
        // 목록 최신화
        loadPosts();
    }
}

// 2. 게시글 목록 불러오기 (GET)
async function loadPosts() {
    const boardList = document.getElementById('boardList');
    if (!boardList) return;

    try {
        // 백엔드 API 호출: boardType이 'REVIEW'인 글만 조회
        // CommunityController의 getPost 메서드 호출
        const posts = await apiFetch('/api/posts?boardType=REVIEW');
        
        boardList.innerHTML = ''; // 기존 내용 초기화

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
            const dateStr = dateObj.toLocaleDateString(); // 날짜 포맷

            const itemDiv = document.createElement('div');
            itemDiv.className = 'board-item'; 
            itemDiv.innerHTML = `
                <span class="board-number" style="text-align:center;">${posts.length - index}</span>
                <span class="board-title" style="font-weight:bold; cursor:pointer;">${post.title}</span>
                <span class="board-author" style="text-align:center;">${post.authorName}</span>
                <span class="board-date" style="text-align:right; color:#888;">${dateStr}</span>
            `;

            // 제목 클릭 시 상세 내용 보기 (간단히 alert로 구현, 추후 모달/상세페이지로 확장 가능)
            itemDiv.querySelector('.board-title').addEventListener('click', () => {
                alert(`[${post.title}]\n\n${post.content}\n\n작성자: ${post.authorName}`);
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
    event.preventDefault(); // 폼 기본 제출 방지 (새로고침 막기)

    const titleInput = document.getElementById('title');
    const contentInput = document.getElementById('content');

    if (!titleInput.value.trim() || !contentInput.value.trim()) {
        alert("제목과 내용을 모두 입력해주세요.");
        return;
    }

    // 백엔드 PostDto.Request 구조에 맞춤
    const postData = {
        boardType: 'REVIEW', // 백엔드에서 이 값을 보고 포인트를 지급함
        title: titleInput.value,
        content: contentInput.value
    };

    try {
        console.log('Bearer '+localStorage.getItem('accessToken'));
        await apiFetch('/api/posts', {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer '+localStorage.getItem('accessToken'),
            },
            body: postData
        });

        alert('후기가 성공적으로 등록되었습니다!\n(100 포인트가 적립되었습니다)');
        
        // 입력창 비우기
        titleInput.value = '';
        contentInput.value = '';

        // 목록 화면으로 돌아가기
        switchBoardTab('list');

    } catch (error) {
        console.error('글 작성 실패:', error);
        alert('글 작성 중 오류가 발생했습니다: ' + error.message);
    }
}
