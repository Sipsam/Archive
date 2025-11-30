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

    // 3. 현재 로그인한 내 정보 가져오기 (ID 비교용)
    try {
        const myInfo = await apiFetch('/api/users/me');
        currentUserId = myInfo.id;
    } catch (error) {
        console.error('사용자 정보 로드 실패:', error);
    }

    // 4. 모집글 상세 정보 로드 시작
    await loadRecruitmentDetail(groupBuyId);

    // 5. 댓글 작성 버튼 이벤트 연결
    setupCommentEvent();
});

// 상세 정보 로드 함수
async function loadRecruitmentDetail(groupBuyId) {
    try {
        // API 호출: 상세 정보 + Product 정보 포함
        const groupBuy = await apiFetch(`/api/groupbuys/online/${groupBuyId}`);
        currentGroupBuy = groupBuy;

        // 참여자 리스트에서 내가 있는지 확인
        const participations = groupBuy.participationList || [];
        isParticipant = participations.some(p => p.user && p.user.id === currentUserId);

        // 화면에 정보 뿌리기 (렌더링)
        renderRecruitmentDetail(groupBuy, participations);

        // 하단 버튼(참여하기/결제하기) 상태 설정
        setupJoinButton(groupBuy, participations);

    } catch (error) {
        console.error('상세 정보 로드 실패:', error);
        alert('모집글 정보를 불러오지 못했습니다.');
        window.location.href = 'recruitment-list.html';
    }
}

// 화면 렌더링 함수
function renderRecruitmentDetail(groupBuy, participations) {
    // --- 1. 모집자(방장) 정보 표시 ---
    const hostNameEl = document.getElementById('hostName');
    const recruitDateEl = document.getElementById('recruitDate');

    if (hostNameEl) {
        // 닉네임 > 이름 > '알 수 없음'
        hostNameEl.textContent = groupBuy.hostUser?.nickname || groupBuy.hostUser?.name || '알 수 없음';
    }
    if (recruitDateEl) {
        const date = groupBuy.createdAt ? new Date(groupBuy.createdAt).toLocaleDateString() : '-';
        recruitDateEl.textContent = date;
    }

    // --- 2. 상품(Product) 정보 표시 ---
    const product = groupBuy.product;
    if (product) {
        // (1) 이미지
        const imageEl = document.getElementById('productImage');
        if (imageEl && product.imageUrl) {
            imageEl.innerHTML = `<img src="${product.imageUrl}" alt="${product.name}" style="width: 100%; height: 100%; object-fit: contain; border-radius: 8px;">`;
        }

        // (2) 상품명
        const productNameEl = document.getElementById('productName');
        if (productNameEl) productNameEl.textContent = product.name;

        // (3) 가격 계산 (총 가격 & 인당 예상 가격)
        const priceInfoEl = document.getElementById('priceInfo');
        if (priceInfoEl) {
            const totalPrice = product.price || 0;
            const targetHeadcount = groupBuy.targetHeadcount || 1; 
            const perPersonPrice = Math.ceil(totalPrice / targetHeadcount); // 1/N 가격 (소수점 올림)

            priceInfoEl.innerHTML = `
                <span style="font-weight:bold; color:#333;">총 ${totalPrice.toLocaleString()}원</span>
                <span style="color:#666; font-size:0.9em;"> (1인당 약 ${perPersonPrice.toLocaleString()}원)</span>
            `;
        }

        // (4) 구매 링크 (크롤링된 원본 URL이 있다면)
        if (product.sourceUrl) {
            const linkRow = document.getElementById('sourceLinkRow');
            const linkTag = document.getElementById('sourceLink');
            // HTML에 해당 ID가 존재할 때만 처리
            if(linkRow && linkTag) {
                linkRow.style.display = 'block'; // 숨겨둔 링크 표시
                linkTag.href = product.sourceUrl;
            }
        }
    }

    // --- 3. 인원 정보 표시 ---
    const targetCountEl = document.getElementById('targetCount');
    const currentCountEl = document.getElementById('currentCount');

    if (targetCountEl) targetCountEl.textContent = `${groupBuy.targetHeadcount || 0}명`;
    if (currentCountEl) currentCountEl.textContent = `${participations.length}명`;
}

// 하단 버튼 상태 관리 함수
function setupJoinButton(groupBuy, participations) {
    const joinBtn = document.querySelector('.btn-join');
    if (!joinBtn) return;

    const currentCount = participations.length;
    const targetCount = groupBuy.targetHeadcount || 0;
    const isFull = currentCount >= targetCount;
    const isHost = (groupBuy.hostUser?.id === currentUserId); // 방장인지 확인

    // 버튼 기본 초기화
    joinBtn.disabled = false;
    joinBtn.style.backgroundColor = '#4a90e2';
    joinBtn.style.cursor = 'pointer';
    joinBtn.onclick = null; // 기존 이벤트 제거

    // 조건별 버튼 설정
    if (isHost) {
        // 케이스 1: 내가 방장일 때
        joinBtn.textContent = '결제 상태로 변경 (방장 전용)';
        joinBtn.onclick = changePaymentStatus;
        
    } else if (isParticipant) {
        // 케이스 2: 이미 참여했을 때 -> 결제 페이지로 이동
        joinBtn.textContent = '결제 하러가기';
        joinBtn.onclick = () => {
            window.location.href = `payment.html?groupBuyId=${groupBuy.id}`;
        };

    } else if (isFull) {
        // 케이스 3: 인원이 꽉 찼을 때
        joinBtn.textContent = '모집 마감 (인원 초과)';
        joinBtn.disabled = true;
        joinBtn.style.backgroundColor = '#ccc';
        joinBtn.style.cursor = 'not-allowed';

    } else {
        // 케이스 4: 참여 가능할 때
        joinBtn.textContent = '참여하기';
        joinBtn.onclick = () => joinGroupBuy(groupBuy.id);
    }
}

// [API] 참여하기 요청
async function joinGroupBuy(groupBuyId) {
    if (!confirm('이 공동구매에 참여하시겠습니까?')) return;

    try {
        await apiFetch(`/api/groupbuys/online/${groupBuyId}/participate`, { method: 'POST' });
        
        alert('참여 신청이 완료되었습니다!');
        
        // 채팅방 토큰 저장 로직 (필요 시)
        const token = getToken();
        if (token && currentGroupBuy?.chatRoomId) {
            localStorage.setItem(`chatRoom_${currentGroupBuy.chatRoomId}`, JSON.stringify({
                roomId: currentGroupBuy.chatRoomId,
                groupBuyId: groupBuyId
            }));
        }

        window.location.reload(); // 새로고침해서 상태 업데이트

    } catch (error) {
        console.error(error);
        alert('참여 실패: ' + error.message);
    }
}

// [API] 결제 상태 변경 요청 (방장)
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

// 댓글 작성 이벤트 설정 (기존 코드 유지)
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

            // TODO: 실제 백엔드 댓글 API가 있다면 여기에 fetch 호출 추가
            // 현재는 UI 동작만 확인
            alert('댓글 기능은 준비 중입니다.\n(작성 내용: ' + content + ')');
            inputComment.value = '';
        });
    }
}