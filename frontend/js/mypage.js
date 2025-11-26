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
        
        // 포인트
        document.getElementById('userPoints').textContent = new Intl.NumberFormat().format(myInfo.points);
        
        // 4. **내 활동 내역 로드 함수 호출**
        await loadMyActivities(); // await를 사용하여 완료 후 다음 로직이 실행되도록 합니다.

    } catch (error) {
        console.error('마이페이지 정보 로드 실패:', error);
        
        // 🚨 과도한 강제 리다이렉션 로직 제거 (페이지에 남도록 함)
        // alert(`정보 로드 중 오류 발생: ${error.message}`); 
        
        if(document.getElementById('userName')) {
            document.getElementById('userName').textContent = '정보 로드 실패';
        }
        // window.location.href = 'index.html'; // 🚨 이 라인을 주석 처리하거나 제거해야 합니다.
    }
});


// 5. 내 활동 내역을 로드하는 함수
async function loadMyActivities() {
    const activityList = document.querySelector('.activity-list');
    if (!activityList) return;
    
    try {
        // 백엔드: GET /api/users/me/participations 호출
        const participations = await apiFetch('/api/users/me/participations');
        
        activityList.innerHTML = ''; // 기존 항목 초기화
        let hasActivities = false;

        // 온라인 참여 내역 처리 (onlineParticipations가 배열이라고 가정)
        if (participations.onlineParticipations && participations.onlineParticipations.length > 0) {
             participations.onlineParticipations.forEach(p => {
                 const item = document.createElement('div');
                 item.className = 'activity-item';
                 // p.onlineGroupBuy.title 필드 등이 백엔드에 있다고 가정해야 구체화 가능
                 item.textContent = `[온라인 참여] 주문 ID: ${p.id} / 상태: ${p.paymentStatus || '미결제'}`;
                 activityList.appendChild(item);
                 hasActivities = true;
             });
        }

        // 오프라인 참여 내역 처리
        if (participations.offlineParticipations && participations.offlineParticipations.length > 0) {
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
        // 401 에러는 common.js에서 처리되므로, 다른 오류 (API 미구현 등) 처리
        console.error('활동 내역 로드 실패:', error);
        activityList.innerHTML = '<div class="activity-item">활동 내역을 불러오는 데 실패했습니다.</div>';
    }
}