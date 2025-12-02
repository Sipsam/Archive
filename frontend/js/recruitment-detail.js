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

        // 참여자 리스트 확인
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

// 화면 렌더링 (이미지, 가격, 링크 등 포함)
function renderRecruitmentDetail(groupBuy, participations) {
    // 1. 방장 정보
    const hostNameEl = document.getElementById('hostName');
    const recruitDateEl = document.getElementById('recruitDate');

    if (hostNameEl) hostNameEl.textContent = groupBuy.hostName || '알 수 없음';
    if (recruitDateEl) {
        const date = groupBuy.createdAt ? new Date(groupBuy.createdAt).toLocaleDateString() : '-';
        recruitDateEl.textContent = date;
    }

    // 2. 상품 이미지
    const imageEl = document.getElementById('productImage');
    if (imageEl) {
        if (groupBuy.productImageUrl) { 
            imageEl.innerHTML = `<img src="${groupBuy.productImageUrl}" alt="${groupBuy.productName}" style="width: 100%; height: 100%; object-fit: contain; border-radius: 8px;">`;
        } else {
            imageEl.innerHTML = `<div style="display:flex; align-items:center; justify-content:center; height:100%; color:#999;">이미지 없음</div>`;
        }
    }
    
    // 3. 상품명
    const productNameEl = document.getElementById('productName');
    if (productNameEl) productNameEl.textContent = groupBuy.productName || '상품명 없음';

    // 4. 가격 정보 (1/N 계산)
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

    // 5. 구매 링크 (있을 경우에만 표시)
    if (groupBuy.productLink) {
        const linkRow = document.getElementById('sourceLinkRow');
        const linkTag = document.getElementById('sourceLink');
        if(linkRow && linkTag) {
            linkRow.style.display = 'block'; 
            linkTag.href = groupBuy.productLink;
        }
    }

    // 6. 인원 정보
    const targetCountEl = document.getElementById('targetCount');
    const currentCountEl = document.getElementById('currentCount');

    if (targetCountEl) targetCountEl.textContent = `${groupBuy.targetHeadcount || 0}명`;
    if (currentCountEl) currentCountEl.textContent = `${participations.length}명`;
}

// 하단 버튼 상태 관리 로직
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
    const isPaying = (groupBuy.status === 'IN_PROGRESS'); // 결제 진행 중

    // 버튼 초기화
    joinBtn.disabled = false;
    joinBtn.style.backgroundColor = '#4a90e2'; // 기본 파란색
    joinBtn.style.cursor = 'pointer';
    joinBtn.onclick = null; 

    if (isHost) {
        // [케이스 1] 방장
        if (isRecruiting) {
            joinBtn.textContent = '결제 상태로 변경하기 (방장 전용)';
            joinBtn.onclick = changePaymentStatus;
        } else if (isPaying) {
            joinBtn.textContent = '결제 진행 중 (참여자 결제 대기)';
            joinBtn.disabled = true;
            joinBtn.style.backgroundColor = '#888';
        } else {
            joinBtn.textContent = '종료된 공구';
            joinBtn.disabled = true;
            joinBtn.style.backgroundColor = '#ccc';
        }
        
    } else if (isParticipant) {
        // [케이스 2] 참여자
        if (isPaying) {
            // [결제 버튼 노출] 결제 진행 중 상태라면 -> 결제 페이지로 이동
            joinBtn.textContent = '결제하기';
            joinBtn.style.backgroundColor = '#ff4444'; // 빨간색 강조
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
            // 그 외 상태 (완료 등)
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
        // [케이스 4] 일반 유저 (아직 참여 안 함)
        joinBtn.textContent = '참여하기';
        joinBtn.onclick = () => joinGroupBuy(groupBuy.id);
    }
}

// [API] 참여하기 요청
async function joinGroupBuy(groupBuyId) {
    if (!confirm('이 공동구매에 참여하시겠습니까?')) return;

    try {
        await apiFetch(`/api/groupbuys/online/${groupBuyId}/participate`, { method: 'POST' });
        
        alert('참여가 완료되었습니다! 채팅방으로 이동할 수 있습니다.');
        
        // 채팅방 토큰 저장 (선택 사항)
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

// [API] 결제 상태 변경 요청 (방장 전용)
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