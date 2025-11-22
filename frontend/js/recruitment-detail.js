// 모집글 상세 페이지 JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const joinBtn = document.querySelector('.btn-join');
    const commentForm = document.querySelector('.comment-form');
    
    if (joinBtn) {
        joinBtn.addEventListener('click', function() {
            if (confirm('이 공동구매에 참여하시겠습니까?')) {
                alert('참여 신청이 완료되었습니다!');
                // 실제 참여 로직 구현
            }
        });
    }
    
    if (commentForm) {
        const submitBtn = commentForm.querySelector('.btn');
        submitBtn.addEventListener('click', function() {
            const textarea = commentForm.querySelector('textarea');
            if (textarea.value.trim()) {
                alert('댓글이 작성되었습니다!');
                textarea.value = '';
                // 실제 댓글 작성 로직 구현
            } else {
                alert('댓글을 입력해주세요.');
            }
        });
    }
});

