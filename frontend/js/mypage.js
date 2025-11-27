// js/mypage.js

document.addEventListener('DOMContentLoaded', async function() {
    // 1. **인증 상태 확인 및 강제 리다이렉션** (common.js에서 처리)
    if (!checkAuth()) { 
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return; 
    }
    
    // 2. **마이페이지 데이터 로드**
    try {
        const myInfo = await apiFetch('/api/users/me'); 
        
        // 3. **DOM에 데이터 바인딩**
        
        // 닉네임
        const nameElement = document.getElementById('userName');
        if (nameElement) {
            nameElement.textContent = myInfo.nickname || '사용자';
        }
        
        // 매너 온도 (🚨 필드명 수정: manner_temp -> mannerTemp)
        const scoreElement = document.querySelector('.score');
        if (scoreElement && myInfo.mannerTemp !== undefined) {
            scoreElement.textContent = myInfo.mannerTemp.toFixed(1);
        } else if (scoreElement) {
            scoreElement.textContent = '36.5'; // 기본값
        }
        
        // 포인트 (숫자 포맷팅 적용)
        const userPoints = myInfo.points || 0;
        const pointElements = document.querySelectorAll('#userPoints');
        pointElements.forEach(el => {
             el.textContent = new Intl.NumberFormat().format(userPoints);
        });
        
        // 4. **활동/포인트 내역 로드 함수 호출**
        await loadMyActivities();
        await loadMyPointHistory(); // ⭐ 추가: 포인트 내역 로드 함수 호출
        
    } catch (error) {
        console.error('마이페이지 정보 로드 실패:', error);
        
        if(document.getElementById('userName')) {
            document.getElementById('userName').textContent = '정보 로드 실패';
        }
    }

    // 5. **포인트 구매 UI 이벤트 연결**
    setupPointPurchase(); 
});


// 5-1. 내 활동 내역을 로드하는 함수 (기존 로직 유지)
async function loadMyActivities() {
    const activityList = document.querySelector('.activity-list'); // HTML에서 이 클래스 이름이 '활동 내역'에 사용되어야 합니다.
    if (!activityList) return;
    
    try {
        // 백엔드: GET /api/users/me/participations 호출
        const participations = await apiFetch('/api/users/me/participations');
        
        activityList.innerHTML = ''; // 기존 항목 초기화
        let hasActivities = false;

        // 온라인 참여 내역 처리 
        if (participations.onlineParticipations?.length > 0) {
             participations.onlineParticipations.forEach(p => {
                 const item = document.createElement('div');
                 item.className = 'activity-item';
                 item.textContent = `[온라인 참여] 주문 ID: ${p.id} / 상태: ${p.paymentStatus || '미결제'}`;
                 activityList.appendChild(item);
                 hasActivities = true;
             });
        }

        // 오프라인 참여 내역 처리
        if (participations.offlineParticipations?.length > 0) {
             participations.offlineParticipations.forEach(p => {
                 const item = document.createElement('div');
                 item.className = 'activity-item';
                 item.textContent = `[오프라인 참여] 모임 ID: ${p.id} / 등록일: ${p.createdAt.substring(0, 10)}`;
                 activityList.appendChild(item);
                 hasActivities = true;
             });
        }
        
        if (!hasActivities) {
             activityList.innerHTML = '<div class="activity-item">최근 활동 내역이 없습니다.</div>';
        }
        
    } catch (error) {
        console.error('활동 내역 로드 실패:', error);
        activityList.innerHTML = '<div class="activity-item">활동 내역을 불러오는 데 실패했습니다.</div>';
    }
}

// 5-2. 추가: 포인트 변동 내역을 로드하는 함수 (GET /api/points/history)
async function loadMyPointHistory() {
    // HTML에서 포인트 변동 내역을 표시할 적절한 영역을 찾아야 합니다.
    // 예: <div id="pointHistoryList"></div> 에 표시한다고 가정합니다.
    const historyList = document.getElementById('pointHistoryList'); 
    if (!historyList) return; 

    try {
        const historyData = await apiFetch('/api/points/history');
        
        historyList.innerHTML = ''; // 기존 항목 초기화
        
        if (historyData && historyData.length > 0) {
            historyData.forEach(item => {
                const row = document.createElement('div');
                row.className = 'point-history-row';
                // amount: 변동 금액, type: 변동 유형 (구매/사용), createdAt: 날짜 필드가 있다고 가정
                const typeText = item.type === 'PURCHASE' ? '구매' : '사용';
                const amountSign = item.type === 'PURCHASE' ? '+' : '-';

                row.innerHTML = `
                    <span class="history-date">${item.createdAt?.substring(0, 10) || ''}</span>
                    <span class="history-type">${typeText}</span>
                    <span class="history-amount ${item.type === 'PURCHASE' ? 'positive' : 'negative'}">
                        ${amountSign} ${new Intl.NumberFormat().format(item.amount)} P
                    </span>
                `;
                historyList.appendChild(row);
            });
        } else {
            historyList.innerHTML = '<div class="point-history-row">포인트 변동 내역이 없습니다.</div>';
        }

    } catch (error) {
        console.error('포인트 내역 로드 실패:', error);
        historyList.innerHTML = '<div class="point-history-row">포인트 내역을 불러오는 데 실패했습니다.</div>';
    }
}


// 6. 포인트 구매 함수 (purchasePoints) (기존 로직 유지)
async function purchasePoints(amount) {
    if (typeof amount !== 'number' || amount <= 0) {
        alert("유효하지 않은 금액입니다.");
        return;
    }
    
    if (!confirm(`${amount.toLocaleString()}원을 결제하고 포인트를 구매하시겠습니까?`)) {
        return;
    }

    try {
        const responseData = await apiFetch('/api/points/purchase', {
            method: 'POST',
            body: { amount: amount }
        });

        if (responseData && responseData.userPoints !== undefined) {
            const updatedPoints = responseData.userPoints;
            
            alert(`포인트 구매 성공! 현재 보유 포인트는 ${updatedPoints.toLocaleString()}입니다.`);
            
            // 모든 포인트 표시 요소를 갱신
            document.querySelectorAll('#userPoints').forEach(el => {
                el.textContent = new Intl.NumberFormat().format(updatedPoints);
            });
            
            // 포인트 구매 후 내역을 다시 로드하여 최신화
            await loadMyPointHistory(); 
            
        } else {
            alert("포인트 구매에 성공했으나, 갱신된 포인트를 확인할 수 없습니다.");
        }

    } catch (error) {
        console.error("포인트 구매 오류:", error);
        alert("포인트 구매 중 오류가 발생했습니다: " + error.message);
    }
}

// 7. ⭐ 이벤트 연결 함수 (setupPointPurchase) (중복 제거 및 로직 복구)
function setupPointPurchase() {
    const purchaseItems = document.querySelectorAll('.point-purchase-list .purchase-item');
    
    // 항목 선택 로직
    purchaseItems.forEach(item => {
        item.addEventListener('click', function() {
            purchaseItems.forEach(i => i.classList.remove('selected'));
            this.classList.add('selected');
            // 콘솔 로그 로직은 유지하거나 제거할 수 있습니다.
        });
    });

    // 구매 버튼 클릭 이벤트
    const purchaseBtn = document.querySelector('.purchase-btn');
    // ⭐ 여기에 async를 추가하고 purchasePoints를 호출하는 로직으로 변경합니다.
    purchaseBtn.addEventListener('click', async function() { 
        const selectedItem = document.querySelector('.purchase-item.selected');
        if (!selectedItem) {
            alert('구매할 포인트를 선택해주세요.');
            return;
        }
        
        // data-price에서 가격을 가져와 숫자로 변환합니다.
        const price = parseInt(selectedItem.dataset.price, 10);
        
        // ⭐ 핵심: 실제 구매 함수 호출 ⭐
        await purchasePoints(price); 
    });
}