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

// 상세 정보 로드 함수 (데이터 누락 시 2번 호출)
async function loadRecruitmentDetail(groupBuyId) {
    try {
        // 1차 호출: 모집글 정보 가져오기
        const groupBuy = await apiFetch(`/api/groupbuys/online/${groupBuyId}`);
        
        // -----------------------------------------------------------
        // 상품 정보가 비어있다면 ID로 다시 긁어오기
        // -----------------------------------------------------------
        
        // 백엔드 구조에 따라 product.id 혹은 productId 필드에 ID가 있을 수 있음
        const productId = groupBuy.product?.id || groupBuy.productId;

        // "ID는 있는데 상품명(name)이 없다?" -> 백엔드가 Lazy Loading으로 껍데기만 보낸 상황
        if (productId && (!groupBuy.product || !groupBuy.product.name)) {
            console.log(`[Frontend Workaround] 상품 정보 누락. ID(${productId})로 2차 조회 시도...`);
            
            try {
                // 2차 호출: 상품 상세 API
                const productDetail = await apiFetch(`/api/products/${productId}`);
                
                // 받아온 상세 정보를 원래 객체에 덮어씌우기 (합체!)
                if (productDetail) {
                    groupBuy.product = productDetail;
                }
            } catch (err) {
                console.warn("2차 상품 조회 실패 (상품 API가 없거나 오류):", err);
                // 실패하면 어쩔 수 없이 화면에 '상품명 없음'으로 뜸
            }
        }

        // 데이터 합체 완료 후 전역 변수에 저장
        currentGroupBuy = groupBuy;

        // 참여자 리스트 확인 및 내 참여 여부 체크
        const participations = groupBuy.participationList || [];
        isParticipant = participations.some(p => p.user && String(p.user.id) === String(currentUserId));

        // 화면 렌더링
        renderRecruitmentDetail(groupBuy, participations);
        
        // 하단 버튼 설정
        setupJoinButton(groupBuy, participations);

    } catch (error) {
        console.error('상세 정보 로드 실패:', error);
        alert('모집글 정보를 불러오지 못했습니다.');
        window.location.href = 'recruitment-list.html';
    }
}

// 화면 렌더링 함수
function renderRecruitmentDetail(groupBuy, participations) {
    // 1. 모집자(방장) 정보 표시
    const hostNameEl = document.getElementById('hostName');
    const recruitDateEl = document.getElementById('recruitDate');

    if (hostNameEl) {
        hostNameEl.textContent = groupBuy.hostUser?.nickname || groupBuy.hostUser?.name || '알 수 없음';
    }
    if (recruitDateEl) {
        const date = groupBuy.createdAt ? new Date(groupBuy.createdAt).toLocaleDateString() : '-';
        recruitDateEl.textContent = date;
    }

    // 2. 상품(Product) 정보 표시
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
            const perPersonPrice = Math.floor(totalPrice / targetHeadcount); // 1/N 가격

            priceInfoEl.innerHTML = `
                <span style="font-weight:bold; color:#333;">총 ${totalPrice.toLocaleString()}원</span>
                <span style="color:#666; font-size:0.9em;"> (1인당 약 ${perPersonPrice.toLocaleString()}원)</span>
            `;
        }

        // (4) 구매 링크
        if (product.sourceUrl) {
            const linkRow = document.getElementById('sourceLinkRow');
            const linkTag = document.getElementById('sourceLink');
            if(linkRow && linkTag) {
                linkRow.style.display = 'block'; 
                linkTag.href = product.sourceUrl;
            }
        }
    }

    // 3. 인원 정보 표시
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
    
    // 방장 여부 확인 (문자열 변환 비교)
    const hostId = groupBuy.hostUser?.id;
    const isHost = (String(hostId) === String(currentUserId));

    // 버튼 초기화
    joinBtn.disabled = false;
    joinBtn.style.backgroundColor = '#4a90e2';
    joinBtn.style.cursor = 'pointer';
    joinBtn.onclick = null; 

    if (isHost) {
        // [케이스 1] 방장 -> 결제 상태 변경
        joinBtn.textContent = '결제 상태로 변경하기 (방장 전용)';
        joinBtn.onclick = changePaymentStatus;
        
    } else if (isParticipant) {
        // [케이스 2] 참여자 -> 채팅방 이동
        joinBtn.textContent = '채팅방으로 이동';
        joinBtn.onclick = () => {
            if (groupBuy.chatRoomId) {
                window.location.href = `chat.html?roomId=${groupBuy.chatRoomId}`;
            } else {
                alert('아직 채팅방이 생성되지 않았습니다.');
            }
        };

    } else if (isFull) {
        // [케이스 3] 만석 -> 비활성화
        joinBtn.textContent = '모집인원이 다 찼습니다.';
        joinBtn.disabled = true;
        joinBtn.style.backgroundColor = '#ccc';
        joinBtn.style.cursor = 'not-allowed';

    } else {
        // [케이스 4] 일반 -> 참여하기
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
        
        // 채팅방 토큰 저장
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

// [API] 결제 상태 변경 요청
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