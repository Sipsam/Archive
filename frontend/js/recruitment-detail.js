// frontend/js/recruitment-detail.js

let currentGroupBuy = null;
let currentUserId = null;
let isParticipant = false;

document.addEventListener('DOMContentLoaded', async function() {
    if (!checkAuth()) {
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const groupBuyId = urlParams.get('id');

    if (!groupBuyId) {
        alert('잘못된 접근입니다 (ID 없음).');
        window.location.href = 'recruitment-list.html';
        return;
    }

    try {
        const myInfo = await apiFetch('/api/users/me');
        currentUserId = myInfo.id;
    } catch (error) {
        console.error('사용자 정보 로드 실패:', error);
    }

    await loadRecruitmentDetail(groupBuyId);
    setupCommentEvent();
});

async function loadRecruitmentDetail(groupBuyId) {
    try {
        const groupBuy = await apiFetch(`/api/groupbuys/online/${groupBuyId}`);
        currentGroupBuy = groupBuy;

        const participations = groupBuy.participationList || [];
        isParticipant = participations.some(p => String(p.userId) === String(currentUserId));

        renderRecruitmentDetail(groupBuy, participations);
        setupJoinButton(groupBuy, participations);
        setupHeaderChatButton(groupBuy);

        // [추가 API 호출] 방장 상세 정보(닉네임, 매너온도) 로드
        loadHostDetailInfo(groupBuy.hostId, groupBuy.hostName);

    } catch (error) {
        console.error('상세 정보 로드 실패:', error);
        alert('모집글 정보를 불러오지 못했습니다.');
        window.location.href = 'recruitment-list.html';
    }
}

// 방장 정보 추가 로드 함수
async function loadHostDetailInfo(hostId, defaultName) {
    const hostNameEl = document.getElementById('hostName');
    if (!hostNameEl) return;

    try {
        const reviews = await apiFetch(`/api/users/${hostId}/reviews`);
        let nickname = defaultName || '알 수 없음';
        let mannerTemp = 36.5;

        if (reviews && reviews.length > 0) {
            const info = reviews[0].reviewee;
            if (info) {
                nickname = info.nickname || info.name || nickname;
                mannerTemp = info.mannerTemp !== undefined ? info.mannerTemp : 36.5;
            }
        }
        
        // HTML 업데이트
        hostNameEl.innerHTML = `${nickname} <span style="font-size:0.8em; color:#4a90e2;">(${mannerTemp.toFixed(1)}℃)</span>`;

    } catch (e) {
        // 실패 시 기본값 표시
        hostNameEl.innerHTML = `${defaultName || '알 수 없음'} <span style="font-size:0.8em; color:#4a90e2;">(36.5℃)</span>`;
    }
}

function setupHeaderChatButton(groupBuy) {
    const btnHeaderChat = document.getElementById('btnHeaderChat');
    if (!btnHeaderChat) return;

    const isHost = (String(groupBuy.hostId) === String(currentUserId));
    
    if (isParticipant || isHost) {
        btnHeaderChat.style.display = 'block'; 
        btnHeaderChat.onclick = () => {
            if (groupBuy.chatRoomId) {
                window.location.href = `chat.html?roomId=${groupBuy.chatRoomId}`;
            } else {
                alert('아직 채팅방이 생성되지 않았습니다.');
            }
        };
    } else {
        btnHeaderChat.style.display = 'none';
    }
}

function renderRecruitmentDetail(groupBuy, participations) {
    const hostNameEl = document.getElementById('hostName');
    const recruitDateEl = document.getElementById('recruitDate');

    if (hostNameEl) hostNameEl.textContent = (groupBuy.hostName || '알 수 없음') + ' (로딩중...)';
    
    if (recruitDateEl) {
        const date = groupBuy.createdAt ? new Date(groupBuy.createdAt).toLocaleDateString() : '-';
        recruitDateEl.textContent = date;
    }

    const imageEl = document.getElementById('productImage');
    if (imageEl) {
        if (groupBuy.productImageUrl) { 
            imageEl.innerHTML = `<img src="${groupBuy.productImageUrl}" alt="${groupBuy.productName}" style="width: 100%; height: 100%; object-fit: contain; border-radius: 8px;">`;
        } else {
            imageEl.innerHTML = `<div style="display:flex; align-items:center; justify-content:center; height:100%; color:#999;">이미지 없음</div>`;
        }
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

function setupJoinButton(groupBuy, participations) {
    const joinBtn = document.querySelector('.btn-join');
    if (!joinBtn) return;

    const currentCount = participations.length;
    const targetCount = groupBuy.targetHeadcount || 0;
    const isFull = currentCount >= targetCount;
    const isHost = (String(groupBuy.hostId) === String(currentUserId));
    
    const isRecruiting = (groupBuy.status === 'RECRUITING');
    const isPaying = (groupBuy.status === 'IN_PROGRESS'); 

    joinBtn.disabled = false;
    joinBtn.style.backgroundColor = '#4a90e2'; 
    joinBtn.style.cursor = 'pointer';
    joinBtn.onclick = null; 

    const goToPayment = () => {
        window.location.href = `payment.html?groupBuyId=${groupBuy.id}`;
    };

    if (isHost) {
        if (isRecruiting) {
            joinBtn.textContent = '결제 상태로 변경하기 (방장 전용)';
            joinBtn.onclick = changePaymentStatus;
        } else if (isPaying) {
            joinBtn.textContent = '결제하기 (방장)';
            joinBtn.style.backgroundColor = '#ff4444'; 
            joinBtn.onclick = goToPayment;
        } else {
            joinBtn.textContent = '종료된 공구';
            joinBtn.disabled = true;
            joinBtn.style.backgroundColor = '#ccc';
        }
        
    } else if (isParticipant) {
        if (isPaying) {
            joinBtn.textContent = '결제하기';
            joinBtn.style.backgroundColor = '#ff4444'; 
            joinBtn.onclick = goToPayment;
        } else if (isRecruiting) {
            joinBtn.textContent = '채팅방 입장 (상단 버튼)';
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
        joinBtn.textContent = '모집인원이 다 찼습니다.';
        joinBtn.disabled = true;
        joinBtn.style.backgroundColor = '#ccc';
        joinBtn.style.cursor = 'not-allowed';

    } else {
        joinBtn.textContent = '참여하기';
        joinBtn.onclick = () => joinGroupBuy(groupBuy.id);
    }
}

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

async function changePaymentStatus() {
    if (!confirm('결제 상태로 변경하시겠습니까?\n변경 후에는 본인을 포함한 모든 참여자가 결제를 진행해야 합니다.')) return;

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