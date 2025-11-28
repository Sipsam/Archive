// js/mypage.js

document.addEventListener('DOMContentLoaded', async function() {
    // 1. 인증 확인
    if (!checkAuth()) { 
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return; 
    }
    
    // 2. 사용자 정보 로드
    try {
        const myInfo = await apiFetch('/api/users/me'); 
        
        // 이름 바인딩
        const nameElement = document.getElementById('userName');
        if (nameElement) nameElement.textContent = myInfo.nickname || '사용자';
        
        // 매너온도 바인딩
        const scoreElement = document.querySelector('.score'); // 또는 id="manner_temp"
        if (scoreElement) {
            const temp = myInfo.mannerTemp !== undefined ? myInfo.mannerTemp : 36.5;
            scoreElement.textContent = temp.toFixed(1);
        }
        
        // 포인트 바인딩 (프로필 섹션 & 메인 타이틀 둘 다 갱신)
        updatePointUI(myInfo.points);
        
        // 3. 활동 내역 & 포인트 내역 로드
        // (activity-list가 있으면 활동 내역 로드, 없으면 패스)
        if(document.querySelector('.activity-list:not(#pointHistoryList)')) {
            await loadMyActivities();
        }
        
        // 포인트 페이지라면 포인트 내역 로드
        if(document.getElementById('pointHistoryList')) {
            await loadMyPointHistory();
        }

        // 4. 참여 중인 모집글 로드
        await loadMyParticipations();

    } catch (error) {
        console.error('정보 로드 실패:', error);
    }

    // 4. 포인트 구매 이벤트 연결
    setupPointPurchase();
});

// UI에 포인트 숫자를 업데이트하는 헬퍼 함수
function updatePointUI(points) {
    const safePoints = points || 0;
    const formatted = new Intl.NumberFormat().format(safePoints);
    
    // 프로필 쪽 포인트
    const profilePoint = document.getElementById('userPointsProfile');
    if(profilePoint) profilePoint.textContent = formatted;

    // 메인 타이틀 쪽 포인트
    const mainPoint = document.getElementById('userPoints');
    if(mainPoint) mainPoint.textContent = formatted + " P";
}


// --- API 호출 함수들 ---

// 1. 포인트 변동 내역 로드 (GET /api/points/history)
async function loadMyPointHistory() {
    const historyList = document.getElementById('pointHistoryList'); 
    if (!historyList) return; 

    try {
        const historyData = await apiFetch('/api/points/history');
        
        historyList.innerHTML = ''; // 초기화
        
        if (historyData && historyData.length > 0) {
            historyData.forEach(item => {
                const row = document.createElement('div');
                row.className = 'point-history-row';
                
                // 데이터 필드명 확인 필요 (createdAt, type, amount 가정)
                const dateStr = item.createdAt ? item.createdAt.substring(0, 10) : '-';
                const typeText = (item.type === 'PURCHASE' || item.type === 'CHARGE') ? '충전' : '사용';
                const isPositive = (item.type === 'PURCHASE' || item.type === 'CHARGE');
                const sign = isPositive ? '+' : '-';
                const amountClass = isPositive ? 'positive' : 'negative';

                row.innerHTML = `
                    <span class="history-date" style="color:#888;">${dateStr}</span>
                    <span class="history-type" style="font-weight:bold;">${typeText}</span>
                    <span class="history-amount ${amountClass}">
                        ${sign} ${new Intl.NumberFormat().format(item.amount)} P
                    </span>
                `;
                historyList.appendChild(row);
            });
        } else {
            historyList.innerHTML = '<div style="padding:20px; text-align:center; color:#999;">포인트 변동 내역이 없습니다.</div>';
        }

    } catch (error) {
        console.error('포인트 내역 로드 실패:', error);
        historyList.innerHTML = '<div style="padding:20px; text-align:center;">내역을 불러오지 못했습니다.</div>';
    }
}

// 2. 포인트 구매 요청 (POST /api/points/purchase)
async function purchasePoints(amount) {
    if (typeof amount !== 'number' || amount <= 0) return;
    
    if (!confirm(`${amount.toLocaleString()}원을 결제하고 포인트를 충전하시겠습니까?`)) {
        return;
    }

    try {
        const responseData = await apiFetch('/api/points/purchase', {
            method: 'POST',
            body: { amount: amount }
        });

        // 응답에 갱신된 userPoints가 있다고 가정
        if (responseData && responseData.userPoints !== undefined) {
            alert(`충전 완료! 현재 포인트: ${responseData.userPoints.toLocaleString()} P`);
            
            // UI 갱신
            updatePointUI(responseData.userPoints);
            
            // 내역 목록 새로고침
            await loadMyPointHistory(); 
            
        } else {
            // 포인트 값이 안 넘어오면 다시 내 정보 조회해서 갱신
            alert("충전되었습니다.");
            window.location.reload();
        }

    } catch (error) {
        console.error("포인트 구매 오류:", error);
        alert("충전 중 오류 발생: " + error.message);
    }
}

// --- 이벤트 설정 함수 ---

function setupPointPurchase() {
    const purchaseItems = document.querySelectorAll('.point-purchase-list .purchase-item');
    const purchaseBtn = document.querySelector('.purchase-btn');
    
    if(!purchaseItems.length || !purchaseBtn) return;

    // 1. 항목 클릭 시 선택 스타일 적용
    purchaseItems.forEach(item => {
        item.addEventListener('click', function() {
            // 기존 선택 제거
            purchaseItems.forEach(i => i.classList.remove('selected'));
            // 현재 선택 추가
            this.classList.add('selected');
        });
    });

    // 2. 구매 버튼 클릭
    purchaseBtn.addEventListener('click', async function() {
        const selectedItem = document.querySelector('.purchase-item.selected');
        if (!selectedItem) {
            alert('구매할 금액을 선택해주세요.');
            return;
        }
        
        const price = parseInt(selectedItem.dataset.price, 10);
        await purchasePoints(price);
    });
}

// 참여 중인 모집글 로드
async function loadMyParticipations() {
    const participationList = document.getElementById('participationList');
    if (!participationList) return;

    try {
        const participations = await apiFetch('/api/users/me/participations');
        
        participationList.innerHTML = ''; // 초기화

        if (!participations || participations.length === 0) {
            participationList.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #999; background: #f9f9f9; border-radius: 8px;">
                    참여 중인 모집글이 없습니다.
                </div>`;
            return;
        }

        // 참여 모집글 목록 표시
        participations.forEach(participation => {
            const groupBuy = participation.onlineGroupBuy || participation.groupBuy;
            if (!groupBuy) return;

            const itemDiv = document.createElement('div');
            itemDiv.className = 'activity-item';
            itemDiv.style.cursor = 'pointer';
            itemDiv.style.padding = '15px';
            itemDiv.style.marginBottom = '10px';
            itemDiv.style.border = '1px solid #eee';
            itemDiv.style.borderRadius = '8px';
            itemDiv.style.transition = 'all 0.3s';
            
            itemDiv.onmouseenter = () => {
                itemDiv.style.backgroundColor = '#f5f5f5';
                itemDiv.style.borderColor = '#4a90e2';
            };
            itemDiv.onmouseleave = () => {
                itemDiv.style.backgroundColor = '#fff';
                itemDiv.style.borderColor = '#eee';
            };
            
            itemDiv.onclick = () => {
                window.location.href = `recruitment-detail.html?id=${groupBuy.id}`;
            };

            const dateStr = groupBuy.createdAt ? new Date(groupBuy.createdAt).toLocaleDateString('ko-KR') : '-';
            const endDateStr = groupBuy.recruitEndDate ? new Date(groupBuy.recruitEndDate).toLocaleDateString('ko-KR') : '-';
            const paymentStatus = participation.paymentStatus || 'PENDING';
            const paymentStatusText = paymentStatus === 'PAID' ? '결제완료' : paymentStatus === 'CANCELLED' ? '결제취소' : '결제대기';

            itemDiv.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-weight: bold; font-size: 16px; margin-bottom: 5px; color: #333;">
                            ${groupBuy.title || '제목 없음'}
                        </div>
                        <div style="font-size: 14px; color: #666; margin-bottom: 5px;">
                            상품명: ${groupBuy.product?.name || '상품명 없음'}
                        </div>
                        <div style="font-size: 12px; color: #999;">
                            모집 마감일: ${endDateStr} | 참여일: ${dateStr}
                        </div>
                    </div>
                    <div style="margin-left: 20px;">
                        <span style="padding: 5px 10px; background: ${paymentStatus === 'PAID' ? '#4a90e2' : paymentStatus === 'CANCELLED' ? '#ff4444' : '#ffa500'}; color: white; border-radius: 5px; font-size: 12px;">
                            ${paymentStatusText}
                        </span>
                    </div>
                </div>
            `;

            participationList.appendChild(itemDiv);
        });

    } catch (error) {
        console.error('참여 모집글 로드 실패:', error);
        participationList.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #ff4444; background: #fff3cd; border-radius: 8px;">
                참여 모집글을 불러오지 못했습니다.
            </div>`;
    }
}

// 활동 내역 로드 (기존 함수가 없으면 추가)
async function loadMyActivities() {
    const activityList = document.getElementById('activityList');
    if (!activityList) return;

    try {
        // 활동 내역 API 호출 넣어야 함
        // const activities = await apiFetch('/api/users/me/activities');
        
        // 임시로 빈 상태 표시
        activityList.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #999;">
                활동 내역이 없습니다.
            </div>`;
    } catch (error) {
        console.error('활동 내역 로드 실패:', error);
    }
}