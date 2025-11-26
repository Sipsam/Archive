// js/main.js

// 1. UI 및 초기화 로직
document.addEventListener('DOMContentLoaded', function() {
    updateAuthButton(); // 로그인 버튼 상태 업데이트

    // 사이드바의 '모집글 신청' 버튼 이벤트 연결
    const modal = document.querySelector('.modal');
    const modalBtn = document.querySelector('.modal_btn'); // 사이드바 버튼
    const closeBtn = document.querySelector('.close_btn');

    // 1-1. 모달 열기 (사이드바 버튼 클릭 시)
    if (modalBtn && modal) {
        modalBtn.addEventListener('click', function() {
            // 로그인 체크
            if (!checkAuth()) {
                alert("로그인이 필요한 서비스입니다.");
                window.location.href = 'login.html';
                return;
            }
            // 모달 열기
            modal.style.display = 'block';
        });
    }

    // 1-2. 모달 닫기
    if (closeBtn && modal) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
});

// UI 관련 함수들 (필터, 버튼 등) - 기존 유지
function updateAuthButton() {
    const isAuthenticated = checkAuth();
    const authButton = document.getElementById('authButton');
    if (!authButton) return;

    if (isAuthenticated) {
        authButton.textContent = '로그아웃';
        authButton.href = '#';
        authButton.onclick = (e) => {
            e.preventDefault();
            if (confirm('로그아웃 하시겠습니까?')) logout();
        };
    } else {
        authButton.textContent = '로그인/회원가입';
        authButton.href = 'login.html';
        authButton.onclick = null;
    }
}


// 2. ⭐ 핵심: 모집글 등록 로직 (입력값 6개 전송) ⭐
async function submitRecruitment() {
    // 1. 로그인 재확인
    if (!checkAuth()) {
        alert("로그인이 필요합니다.");
        window.location.href = 'login.html';
        return;
    }

    // 2. 입력값 가져오기 (6개)
    const productName = document.getElementById('productName').value;
    const productUrl = document.getElementById('productUrl').value;
    const targetHeadcount = document.getElementById('targetHeadcount').value;
    
    const title = document.getElementById('recruitTitle').value;
    const content = document.getElementById('recruitContent').value;
    const endDate = document.getElementById('recruitEndDate').value;

    // 3. 유효성 검사 (빈 값 체크)
    if (!productName || !productUrl || !targetHeadcount || !title || !content || !endDate) {
        alert("모든 항목을 입력해주세요.");
        return;
    }

    // 상품 고유 ID 추출
    // 1. 정규 표현식 정의
    // /products\/(\d+)\??/
    // - products\/: 'products/' 문자열에 정확히 일치 (슬래시 /는 이스케이프 \/ 처리)
    // - (\d+): 하나 이상의 숫자(\d+)를 캡처 그룹으로 묶어 추출
    // - \??: 캡처 그룹 뒤에 물음표 ?가 있을 수도 있고 없을 수도 있음을 의미
    const regex = /products\/(\d+)/; 

    // 2. 문자열에서 패턴 검색
    const match = productUrl.match(regex);

    let productNumber;

    if (match && match[1]) {
        // 3. 캡처된 문자열(match[1])을 10진수(10) 정수로 변환하여 productID에 할당
        // productNumber = parseInt(match[1], 10);
        
        console.log(`추출된 제품 ID (문자열): ${match[1]}`);
        console.log(`숫자로 변환된 제품 ID: ${productNumber}`);
        console.log(`데이터 타입 확인: ${typeof productNumber}`);
        
    } else {
        console.log(`URL에서 제품 ID를 찾을 수 없습니다.`);
    }
}

    async function registerGroupBuy() { // 함수로 묶어 비동기 처리를 명확히 합니다.

    try {
        // 두 번째 API 호출: 등록 시도 확인 또는 다른 작업 (GET)
        // 2. GET 요청이므로, 데이터를 URL 쿼리 파라미터로 전달
        const urlParams = new URLSearchParams({ url: productUrl });
        const responseGet = await fetch(`${BACKEND_URL}/api/groupbuys/attempt?${urlParams}`, {
            method: 'GET'
        });
        
        // GET 요청의 성공/실패 확인
        if (responseData.text() === 'success') {
            // 3. 성공 처리
            // 첫 번째 API 호출: 모집글 등록 (POST)
            // 1. JS 객체를 JSON 문자열로 변환 (JSON.stringify)
            const postData = {
                productId: productNumber,         // 상품 고유 ID
                targetHeadcount: parseInt(targetHeadcount), // 모집 인원 (숫자로 변환)
                title: title,                   // 게시글 제목
                content: content,               // 내용
                recruit_end_date: endDate         // 마감 시간
            };

            const responsePost = await fetch(`${BACKEND_URL}/api/groupbuys/online`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json' // JSON 형식임을 명시
                },
                body: JSON.stringify(postData) 
            });
            
            // POST 요청의 성공/실패 확인
            if (!responsePost.ok) { // response.ok는 200-299 상태 코드를 체크합니다.
                const errorText = await responsePost.text();
                throw new Error(`모집글 등록 실패: ${errorText || '서버 오류'}`);
            }
            alert("모집글이 성공적으로 등록되었습니다!");
        } else {
            const errorText = await responseGet.text();
            alert(`등록 확인 실패: ${errorText || '입력 정보를 확인해주세요.'}`);
        }
        document.querySelector('.modal').style.display = 'none';
        window.location.reload(); // 목록 새로고침
        
    } catch (error) {
        // 모든 종류의 오류 (네트워크 오류, fetch 실패, 응답 실패 등) 처리
        console.error("등록 처리 중 오류 발생:", error);
        alert("글 등록 처리 중 오류가 발생했습니다: " + error.message);
    }
}