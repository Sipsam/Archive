// 모집글 상세 페이지 JavaScript
let currentGroupBuy = null;
let currentUserId = null;
let isParticipant = false;

document.addEventListener('DOMContentLoaded', async function() {
    // 인증 확인
    if (!checkAuth()) {
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return;
    }

    // URL에서 모집글 ID 가져오기
    const urlParams = new URLSearchParams(window.location.search);
    const groupBuyId = urlParams.get('id');

    if (!groupBuyId) {
        alert('모집글 ID가 없습니다.');
        window.location.href = 'recruitment-list.html';
        return;
    }

    // 현재 사용자 정보 가져오기
    try {
        const myInfo = await apiFetch('/api/users/me');
        currentUserId = myInfo.id;
    } catch (error) {
        console.error('사용자 정보 로드 실패:', error);
    }

    // 모집글 상세 정보 로드
    await loadRecruitmentDetail(groupBuyId);
});

// recruitment-detail.js 수정본

async function loadRecruitmentDetail(groupBuyId) {
    try {
        // 1. 모집글 상세 정보 조회 (여기 안에 참여자 목록도 들어있음!)
        const groupBuy = await apiFetch(`/api/groupbuys/online/${groupBuyId}`);
        currentGroupBuy = groupBuy;

        // [삭제] 2. 참여 여부 확인을 위한 별도 요청 (이게 404 원인임)
        // const participations = await apiFetch(`/api/groupbuys/online/${groupBuyId}/participations`);
        
        // [수정] 2. 대신 상세정보 안에 있는 리스트를 사용
        const participations = groupBuy.participationList || []; // 데이터가 없으면 빈 배열

        isParticipant = participations.some(p => p.userId === currentUserId);

        // 3. 화면에 데이터 표시
        renderRecruitmentDetail(groupBuy, participations);

        // 4. 버튼 상태 설정
        setupJoinButton(groupBuy, participations);

    } catch (error) {
        console.error('모집글 상세 정보 로드 실패:', error);
        alert('모집글을 불러오지 못했습니다: ' + error.message);
        window.location.href = 'recruitment-list.html';
    }
}

// 모집글 상세 정보 렌더링
function renderRecruitmentDetail(groupBuy, participations) {
    // 모집자 정보
    const recruiterName = document.querySelector('.recruiter-name');
    const recruiterDate = document.querySelector('.recruiter-date');
    if (recruiterName) {
        recruiterName.textContent = groupBuy.hostUser?.nickname || groupBuy.hostUser?.name || '모집자';
    }
    if (recruiterDate) {
        const date = groupBuy.createdAt ? new Date(groupBuy.createdAt).toLocaleDateString('ko-KR') : '-';
        recruiterDate.textContent = date;
    }

    // 상품 정보
    const productName = document.querySelector('.product-info .info-value');
    if (productName && groupBuy.product) {
        const infoRows = document.querySelectorAll('.product-info .info-row');
        if (infoRows.length >= 1) {
            infoRows[0].querySelector('.info-value').textContent = groupBuy.product.name || '상품명 없음';
        }
        if (infoRows.length >= 2) {
            const totalPrice = groupBuy.product.price || 0;
            const perPersonPrice = Math.floor(totalPrice / (groupBuy.targetHeadcount || 1));
            infoRows[1].querySelector('.info-value').textContent = 
                `총 ${totalPrice.toLocaleString()}원 / 인당 ${perPersonPrice.toLocaleString()}원`;
        }
        if (infoRows.length >= 3) {
            infoRows[2].querySelector('.info-value').textContent = `${groupBuy.targetHeadcount || 0}명`;
        }
        if (infoRows.length >= 4) {
            infoRows[3].querySelector('.info-value').textContent = `${participations.length || 0}명`;
        }
    }

    // 상품 이미지
    if (groupBuy.product?.imageUrl) {
        const mainImage = document.querySelector('.main-image');
        if (mainImage) {
            mainImage.innerHTML = `<img src="${groupBuy.product.imageUrl}" style="width:100%; height:100%; object-fit:cover; border-radius:8px;" />`;
        }
    }
}

// 참여하기 버튼 설정
function setupJoinButton(groupBuy, participations) {
    const joinBtn = document.querySelector('.btn-join');
    if (!joinBtn) return;

    const currentParticipantCount = participations.length || 0;
    const targetHeadcount = groupBuy.targetHeadcount || 0;
    const isFull = currentParticipantCount >= targetHeadcount;
    const isHost = groupBuy.hostUser?.id === currentUserId;

    // 버튼 초기화
    joinBtn.className = 'btn btn-primary btn-join';
    joinBtn.disabled = false;
    joinBtn.onclick = null;

    if (isHost) {
        // 방장인 경우: 결제상태로 변경하기 버튼
        joinBtn.textContent = '결제상태로 변경하기';
        joinBtn.onclick = async () => {
            await changePaymentStatus();
        };
    } else if (isParticipant) {
        // 이미 참여한 경우: 결제하기 버튼
        joinBtn.textContent = '결제하기';
        joinBtn.onclick = () => {
            window.location.href = `payment.html?groupBuyId=${groupBuy.id}`;
        };
    } else if (isFull) {
        // 모집 인원이 다 찬 경우
        joinBtn.textContent = '모집인원이 다 찼습니다.';
        joinBtn.className = 'btn btn-secondary btn-join';
        joinBtn.disabled = true;
        joinBtn.style.backgroundColor = '#ccc';
        joinBtn.style.cursor = 'not-allowed';
    } else {
        // 참여 가능한 경우: 참여하기 버튼
        joinBtn.textContent = '참여하기';
        joinBtn.onclick = async () => {
            await joinGroupBuy(groupBuy.id);
        };
    }
}

// 모집글 참여하기
async function joinGroupBuy(groupBuyId) {
    if (!confirm('이 공동구매에 참여하시겠습니까?')) {
        return;
    }

    try {
        // 참여 API 호출
        await apiFetch(`/api/groupbuys/online/${groupBuyId}/participate`, {
            method: 'POST'
        });

        alert('참여 신청이 완료되었습니다!');
        
        // 채팅방 참여 (토큰 사용)
        const token = getToken();
        if (token && currentGroupBuy?.chatRoomId) {
            // 채팅방 참여 정보를 로컬스토리지에 저장
            localStorage.setItem(`chatRoom_${currentGroupBuy.chatRoomId}`, JSON.stringify({
                roomId: currentGroupBuy.chatRoomId,
                groupBuyId: groupBuyId,
                token: token
            }));
        }

        // 페이지 새로고침하여 버튼 상태 업데이트
        window.location.reload();

    } catch (error) {
        console.error('참여 실패:', error);
        alert('참여 신청 중 오류가 발생했습니다: ' + error.message);
    }
}

// 결제 상태 변경하기 (방장 전용)
async function changePaymentStatus() {
    if (!confirm('결제 상태로 변경하시겠습니까? 변경 후 참여자들이 결제할 수 있습니다.')) {
        return;
    }

    try {
        await apiFetch(`/api/groupbuys/online/${currentGroupBuy.id}/change-payment-status`, {
            method: 'POST'
        });

        alert('결제 상태로 변경되었습니다!');
        window.location.reload();

    } catch (error) {
        console.error('결제 상태 변경 실패:', error);
        alert('결제 상태 변경 중 오류가 발생했습니다: ' + error.message);
    }
}

// 댓글 작성
document.addEventListener('DOMContentLoaded', function() {
    const commentForm = document.querySelector('.comment-form');
    if (commentForm) {
        const submitBtn = commentForm.querySelector('.btn');
        submitBtn.addEventListener('click', async function() {
            const textarea = commentForm.querySelector('textarea');
            if (!textarea.value.trim()) {
                alert('댓글을 입력해주세요.');
                return;
            }

            // TODO: 댓글 작성 API 호출
            alert('댓글이 작성되었습니다!');
            textarea.value = '';
        });
    }
});
