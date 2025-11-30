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

    // 3. 현재 로그인한 내 정보 가져오기
    try {
        const myInfo = await apiFetch('/api/users/me');
        currentUserId = myInfo.id;
        console.log("내 ID:", currentUserId); // 디버깅용 로그
    } catch (error) {
        console.error('사용자 정보 로드 실패:', error);
    }

    // 4. 상세 정보 로드
    await loadRecruitmentDetail(groupBuyId);

    // 5. 댓글 이벤트 연결
    setupCommentEvent();
});

async function loadRecruitmentDetail(groupBuyId) {
    try {
        const groupBuy = await apiFetch(`/api/groupbuys/online/${groupBuyId}`);
        currentGroupBuy = groupBuy;
        console.log("모집글 정보:", groupBuy); // 디버깅용 로그

        // 참여자 리스트 확인
        const participations = groupBuy.participationList || [];
        
        // ⭐ [수정] 참여 여부 확인 시 ID 형변환 안전하게 처리
        isParticipant = participations.some(p => p.user && String(p.user.id) === String(currentUserId));

        renderRecruitmentDetail(groupBuy, participations);
        setupJoinButton(groupBuy, participations);

    } catch (error) {
        console.error('상세 정보 로드 실패:', error);
        alert('모집글 정보를 불러오지 못했습니다.');
        window.location.href = 'recruitment-list.html';
    }
}

function renderRecruitmentDetail(groupBuy, participations) {
    // 1. 모집자 정보
    const hostNameEl = document.getElementById('hostName');
    const recruitDateEl = document.getElementById('recruitDate');

    if (hostNameEl) {
        hostNameEl.textContent = groupBuy.hostUser?.nickname || groupBuy.hostUser?.name || '알 수 없음';
    }
    if (recruitDateEl) {
        const date = groupBuy.createdAt ? new Date(groupBuy.createdAt).toLocaleDateString() : '-';
        recruitDateEl.textContent = date;
    }

    // 2. 상품 정보
    const product = groupBuy.product;
    if (product) {
        const imageEl = document.getElementById('productImage');
        if (imageEl && product.imageUrl) {
            imageEl.innerHTML = `<img src="${product.imageUrl}" alt="${product.name}" style="width: 100%; height: 100%; object-fit: contain; border-radius: 8px;">`;
        }

        const productNameEl = document.getElementById('productName');
        if (productNameEl) productNameEl.textContent = product.name;

        const priceInfoEl = document.getElementById('priceInfo');
        if (priceInfoEl) {
            const totalPrice = product.price || 0;
            const targetHeadcount = groupBuy.targetHeadcount || 1; 
            const perPersonPrice = Math.floor(totalPrice / targetHeadcount);

            priceInfoEl.innerHTML = `
                <span style="font-weight:bold; color:#333;">총 ${totalPrice.toLocaleString()}원</span>
                <span style="color:#666; font-size:0.9em;"> (1인당 약 ${perPersonPrice.toLocaleString()}원)</span>
            `;
        }

        if (product.sourceUrl) {
            const linkRow = document.getElementById('sourceLinkRow');
            const linkTag = document.getElementById('sourceLink');
            if(linkRow && linkTag) {
                linkRow.style.display = 'block'; 
                linkTag.href = product.sourceUrl;
            }
        }
    }

    // 3. 인원 정보
    const targetCountEl = document.getElementById('targetCount');
    const currentCountEl = document.getElementById('currentCount');
    if (targetCountEl) targetCountEl.textContent = `${groupBuy.targetHeadcount || 0}명`;
    if (currentCountEl) currentCountEl.textContent = `${participations.length}명`;
}

// ⭐ [핵심 수정] 방장 여부(isHost) 판단 로직 강화
function setupJoinButton(groupBuy, participations) {
    const joinBtn = document.querySelector('.btn-join');
    if (!joinBtn) return;

    const currentCount = participations.length;
    const targetCount = groupBuy.targetHeadcount || 0;
    const isFull = currentCount >= targetCount;

    // ⭐ ID 비교 시 String으로 변환하여 비교 (타입 불일치 방지)
    // groupBuy.hostUser가 null일 경우를 대비해 옵셔널 체이닝(?.) 사용
    const hostId = groupBuy.hostUser?.id;
    const isHost = (String(hostId) === String(currentUserId));

    console.log(`방장ID: ${hostId}, 내ID: ${currentUserId}, 방장인가요?: ${isHost}`);

    // 버튼 초기화
    joinBtn.disabled = false;
    joinBtn.style.backgroundColor = '#4a90e2';
    joinBtn.style.cursor = 'pointer';
    joinBtn.onclick = null;

    if (isHost) {
        // [케이스 1] 방장일 때 -> 결제 상태 변경
        joinBtn.textContent = '결제 상태로 변경하기 (방장 전용)';
        joinBtn.onclick = changePaymentStatus;
        
    } else if (isParticipant) {
        // [케이스 2] 이미 참여자일 때 -> 채팅방 이동
        joinBtn.textContent = '채팅방으로 이동';
        joinBtn.onclick = () => {
            if (groupBuy.chatRoomId) {
                window.location.href = `chat.html?roomId=${groupBuy.chatRoomId}`;
            } else {
                alert('아직 채팅방이 생성되지 않았습니다.');
            }
        };

    } else if (isFull) {
        // [케이스 3] 만석일 때
        joinBtn.textContent = '모집인원이 다 찼습니다.';
        joinBtn.disabled = true;
        joinBtn.style.backgroundColor = '#ccc';
        joinBtn.style.cursor = 'not-allowed';

    } else {
        // [케이스 4] 참여 가능할 때
        joinBtn.textContent = '참여하기';
        joinBtn.onclick = () => joinGroupBuy(groupBuy.id);
    }
}

async function joinGroupBuy(groupBuyId) {
    if (!confirm('이 공동구매에 참여하시겠습니까?')) return;
    try {
        await apiFetch(`/api/groupbuys/online/${groupBuyId}/participate`, { method: 'POST' });
        alert('참여가 완료되었습니다! 채팅방으로 이동할 수 있습니다.');
        window.location.reload();
    } catch (error) {
        console.error(error);
        alert('참여 실패: ' + error.message);
    }
}

async function changePaymentStatus() {
    if (!confirm('결제 상태로 변경하시겠습니까?\n변경 후에는 참여자들이 결제를 진행할 수 있게 됩니다.')) return;
    try {
        await apiFetch(`/api/groupbuys/online/${currentGroupBuy.id}/change-payment-status`, { method: 'POST' });
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
            if (!content) { alert('댓글 내용을 입력해주세요.'); return; }
            alert('댓글 기능은 준비 중입니다.\n(작성 내용: ' + content + ')');
            inputComment.value = '';
        });
    }
}