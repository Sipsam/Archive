// js/mypage.js

document.addEventListener('DOMContentLoaded', async function() {
    // 1. **인증 상태 확인 및 강제 리다이렉션**

    if (!checkAuth()) { // common.js의 checkAuth() 사용
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return; // 로그인 상태가 아니면 함수 종료
    }
    
    // 2. **마이페이지 데이터 로드**
    try {
        // GET /api/users/me 호출. apiFetch가 자동으로 토큰을 헤더에 포함합니다.
        const myInfo = await apiFetch('/api/users/me'); 
        
        // myInfo는 UserResponse DTO 구조를 가집니다. (nickname, points, manner_temp 등)
        
        // 3. **DOM에 데이터 바인딩**
        
        // 닉네임 (HTML id="userName")
        const nameElement = document.getElementById('userName');
        if (nameElement) {
            nameElement.textContent = myInfo.nickname || '사용자';
        }        
        // 매너 온도 (UI: score 클래스)
        const scoreElement = document.querySelector('.score');
        if (scoreElement) {
            scoreElement.textContent = myInfo.manner_temp.toFixed(1); // 소수점 첫째 자리까지 표시
        }
        
        // 포인트
        document.getElementById('userPoints').textContent = new Intl.NumberFormat().format(myInfo.points);
        
        // 4. **내 활동 내역 (주문 내역, 후기 등)**을 로드하는 함수 호출
        loadMyActivities();

    } catch (error) {
        // apiFetch에서 401 에러는 이미 common.js에서 처리되므로,
        // 여기서는 데이터 로드 실패나 다른 오류를 처리합니다.
        console.error('마이페이지 정보 로드 실패:', error);
        if(document.getElementById('userName')) {
            document.getElementById('userName').textContent = '-';
        }
        window.location.href = 'index.html'; // 예외 처리 후 메인으로 보냄
    }
});

// 5.내 활동 내역을 로드하는 함수
async function loadMyActivities() {
    try {
        // 백엔드: GET /api/users/me/participations 호출 (주문 내역)
        const participations = await apiFetch('/api/users/me/participations');
        const activityList = document.querySelector('.activity-list');
        
        // (주문 내역을 activityList에 동적으로 삽입하는 로직 구현)
        if (activityList && participations) {
             // 기존 목록 초기화 (중복 방지)
             activityList.innerHTML = '';

             // 예시: 데이터 구조에 따라 수정 필요 (onlineParticipations가 배열이라고 가정)
             const list = participations.onlineParticipations || []; 
             
             /* 추가 수정 필요
             list.forEach(p => {
                 const item = document.createElement('div');
                 item.className = 'activity-item';
                 // 백엔드 데이터 필드명 확인 필요 (p.title, p.status 등)
                 item.textContent = `주문: ${product_id || p.id} / 상태: ${p.paymentStatus}`;
                 activityList.appendChild(item);
             });
             */
        }
        
    } catch (error) {
        console.error('활동 내역 로드 실패:', error);
    }
}
