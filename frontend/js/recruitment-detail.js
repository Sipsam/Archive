// frontend/js/recruitment-detail.js

let currentGroupBuy = null;
let currentUserId = null;
let isParticipant = false;

document.addEventListener('DOMContentLoaded', async function() {
    // 1. 로그인 인증 확인
    if (!checkAuth()) {
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return;
    }

    // 2. URL에서 ID 파싱
    const urlParams = new URLSearchParams(window.location.search);
    const groupBuyId = urlParams.get('id');

    if (!groupBuyId) {
        alert('잘못된 접근입니다 (ID 없음).');
        window.location.href = 'recruitment-list.html';
        return;
    }

    // 3. 내 정보 가져오기 (ID 비교용)
    try {
        const myInfo = await apiFetch('/api/users/me');
        currentUserId = myInfo.id;
    } catch (error) {
        console.error('사용자 정보 로드 실패:', error);
    }

    // 4. 상세 정보 로드
    await loadRecruitmentDetail(groupBuyId);

    // 5. 댓글 작성 이벤트
    setupCommentEvent();
});

// 상세 정보 로드
async function loadRecruitmentDetail(groupBuyId) {
    try {
        const groupBuy = await apiFetch(`/api/groupbuys/online/${groupBuyId}`);
        currentGroupBuy = groupBuy;

        const participations = groupBuy.participationList || [];
        
        // 내 아이디가 참여자 목록에 있는지 확인
        isParticipant = participations.some(p => String(p.userId) === String(currentUserId));

        // 화면 렌더링
        renderRecruitmentDetail(groupBuy, participations);
        
        // 버튼 설정
        setupJoinButton(groupBuy, participations);

    } catch (error) {
        console.error('상세 정보 로드 실패:', error);
        alert('모집글 정보를 불러오지 못했습니다.');
        window.location.href = 'recruitment-list.html';
    }
}

// 화면 렌더링 함수
function renderRecruitmentDetail(groupBuy, participations) {
    const hostNameEl = document.getElementById('hostName');
    const recruitDateEl = document.getElementById('recruitDate');

    if (hostNameEl) {
        hostNameEl.textContent = groupBuy.hostName || '알 수 없음';
    }
    if (recruitDateEl) {
        const date = groupBuy.createdAt ? new Date(groupBuy.createdAt).toLocaleDateString() : '-';
        recruitDateEl.textContent = date;
    }

    const imageEl = document.getElementById('productImage');
    if (imageEl && groupBuy.productImageUrl) { 
        imageEl.innerHTML = `<img src="${groupBuy.productImageUrl}" alt="${groupBuy.productName}" style="width: 100%; height: 100%; object-fit: contain; border-radius: 8px;">`;
    }
    
    const productNameEl = document.getElementById('productName');
    if (productNameEl) productNameEl.textContent = groupBuy.productName || '상품명 없음';

    const priceInfoEl = document.getElementById('priceInfo');
    if (priceInfoEl) {
        const totalPrice = groupBuy.productPrice || 0;
        const targetHeadcount = groupBuy.targetHeadcount || 1; 
        const perPersonPrice = Math.floor(totalPrice / targetHeadcount); 

        priceInfoEl.innerHTML = `
            <span style="font-weight:bold; color:#333;">총 ${totalPrice.toLocaleString()}원</span>
            <span style="color:#666; font-size:0.9em;"> (1인당 약 ${perPersonPrice.toLocaleString()}원)</span>
        `;
    }

    if (groupBuy.productLink) {
        const linkRow = document.getElementById('sourceLinkRow');
        const linkTag = document.getElementById('sourceLink');
        if(linkRow && linkTag) {
            linkRow.style.display = 'block'; 
            linkTag.href = groupBuy.productLink;
        }
    }

    const targetCountEl = document.getElementById('targetCount');
    const currentCountEl = document.getElementById('currentCount');

    if (targetCountEl) targetCountEl.textContent = `${groupBuy.targetHeadcount || 0}명`;
    if (currentCountEl) currentCountEl.textContent = `${participations.length}명`;
}

// 버튼 상태 관리 (수정사항!!!)
function setupJoinButton(groupBuy, participations) {
    const joinBtn = document.querySelector('.btn-join');
    if (!joinBtn) return;

    const currentCount = participations.length;
    const targetCount = groupBuy.targetHeadcount || 0;
    const isFull = currentCount >= targetCount;
    
    // 방장 여부 확인
    const isHost = (String(groupBuy.hostId) === String(currentUserId));
    
    // 상태 확인
    const isRecruiting = (groupBuy.status === 'RECRUITING');
    const isPaying = (groupBuy.status === 'IN_PROGRESS'); // 결제 진행 중 상태

    joinBtn.disabled = false;
    joinBtn.style.backgroundColor = '#4a90e2';
    joinBtn.style.cursor = 'pointer';
    joinBtn.onclick = null; 

    if (isHost) {
        // [케이스 1] 방장
        if (isRecruiting) {
            joinBtn.textContent = '결제 상태로 변경하기 (방장 전용)';
            joinBtn.onclick = changePaymentStatus;
        } else if (isPaying) {
            joinBtn.textContent = '결제 진행 중 (참여자 대기)';
            joinBtn.disabled = true;
            joinBtn.style.backgroundColor = '#888';
        } else {
            joinBtn.textContent = '모집 완료됨';
            joinBtn.disabled = true;
            joinBtn.style.backgroundColor = '#888';
        }
        
    } else if (isParticipant) {
        // [케이스 2] 참여자
        
        if (isPaying) {
            // [결제 버튼 노출] 결제 진행 중 상태라면 -> 결제 페이지로 이동
            joinBtn.textContent = '결제하기';
            joinBtn.style.backgroundColor = '#ff4444'; // 강조색 (빨강)
            joinBtn.onclick = () => {
                window.location.href = `payment.html?groupBuyId=${groupBuy.id}`;
            };
        } else if (isRecruiting) {
            // 아직 모집 중이면 채팅방 이동
            joinBtn.textContent = '채팅방으로 이동';
            joinBtn.onclick = () => {
                if (groupBuy.chatRoomId) {
                    window.location.href = `chat.html?roomId=${groupBuy.chatRoomId}`;
                } else {
                    alert('아직 채팅방이 생성되지 않았습니다.');
                }
            };
        } else {
            joinBtn.textContent = '종료된 공구';
            joinBtn.disabled = true;
            joinBtn.style.backgroundColor = '#ccc';
        }

    } else if (isFull) {
        // [케이스 3] 만석
        joinBtn.textContent = '모집인원이 다 찼습니다.';
        joinBtn.disabled = true;
        joinBtn.style.backgroundColor = '#ccc';
        joinBtn.style.cursor = 'not-allowed';

    } else {
        // [케이스 4] 일반 참여 (아직 미참여)
        joinBtn.textContent = '참여하기';
        joinBtn.onclick = () => joinGroupBuy(groupBuy.id);
    }
}

// 참여하기 요청
async function joinGroupBuy(groupBuyId) {
    if (!confirm('이 공동구매에 참여하시겠습니까?')) return;

    try {
        await apiFetch(`/api/groupbuys/online/${groupBuyId}/participate`, { method: 'POST' });
        
        alert('참여가 완료되었습니다! 채팅방으로 이동할 수 있습니다.');
        
        const token = getToken();
        if (token && currentGroupBuy?.chatRoomId) {
            localStorage.setItem(`chatRoom_${currentGroupBuy.chatRoomId}`, JSON.stringify({
                roomId: currentGroupBuy.chatRoomId,
                groupBuyId: groupBuyId
            }));
        }

        window.location.reload(); 

    } catch (error) {
        console.error(error);
        alert('참여 실패: ' + error.message);
    }
}

// 결제 상태 변경 요청
async function changePaymentStatus() {
    if (!confirm('결제 상태로 변경하시겠습니까?\n변경 후에는 참여자들이 결제를 진행할 수 있게 됩니다.')) return;

    try {
        await apiFetch(`/api/payment/start/${currentGroupBuy.id}`, { method: 'POST' });
        alert('상태가 변경되었습니다. 참여자들이 이제 결제할 수 있습니다.');
        window.location.reload();
    } catch (error) {
        alert('상태 변경 실패: ' + error.message);
    }
}

// 댓글 작성 이벤트
function setupCommentEvent() {
    const btnWrite = document.getElementById('btnWriteComment');
    const inputComment = document.getElementById('commentInput');

    if (btnWrite && inputComment) {
        btnWrite.addEventListener('click', async function() {
            const content = inputComment.value.trim();
            if (!content) {
                alert('댓글 내용을 입력해주세요.');
                return;
            }
            alert('댓글 기능은 준비 중입니다.\n(작성 내용: ' + content + ')');
            inputComment.value = '';
        });
    }
}