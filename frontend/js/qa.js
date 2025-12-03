// frontend/js/qa.js

document.addEventListener('DOMContentLoaded', function() {
    const qaForm = document.querySelector('.qa-form');
    
    // 1. 질문 등록 폼 제출 이벤트
    if (qaForm) {
        qaForm.addEventListener('submit', async function(e) {
            e.preventDefault(); // 기본 제출 방지

            // 폼 데이터 가져오기
            const title = this.querySelector('input[name="title"]').value;
            const message = this.querySelector('textarea[name="message"]').value;

            // API 호출 함수 실행
            await sendQuestion(title, message);
        });
    }
    
    // 2. Q/A 항목 클릭 시 상세 보기
    const qaItems = document.querySelectorAll('.qa-item');
    qaItems.forEach(item => {
        item.addEventListener('click', function() {
            const content = this.querySelector('.qa-content');
            if (content.style.display === 'none' || content.style.display === '') {
                content.style.display = 'block';
            } else {
                content.style.display = 'none';
            }
        });
    });
});

// 질문 전송 함수 (사용자가 질문을 등록하면 관리자의 이메일로 발송되도록 설정)
async function sendQuestion(title, content) {
    // 로컬 스토리지에서 토큰 가져오기
    const token = localStorage.getItem('accessToken');

    // 로그인 확인
    if (!token) {
        alert("로그인이 필요합니다.");
        window.location.href = 'login.html';
        return;
    }

    try {
        // 백엔드로 POST 요청 보내기
        const res = await fetch("/api/email", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token // 헤더에 토큰 추가
            },
            body: JSON.stringify({
                title: title,
                message: content
            })
        });

        // 응답 처리
        if (res.ok) {
            alert("Q/A 전송 성공! 관리자의 이메일로 전송됩니다.");
            // 성공 시 폼 초기화
            const form = document.querySelector('.qa-form');
            if (form) form.reset();
            // 필요 시 페이지 새로고침: window.location.reload();
        } else {
            // 에러 메시지가 있다면 표시, 없으면 기본 메시지
            try {
                const errorData = await res.text(); 
                alert("Q/A 전송 실패: " + errorData);
            } catch (e) {
                alert("Q/A 전송 실패");
            }
        }
    } catch (error) {
        console.error("API Error:", error);
        alert("전송 중 오류가 발생했습니다.");
    }
}
