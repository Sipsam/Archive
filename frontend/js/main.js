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
    const productUrl = document.getElementById('productUrl').value;
    const targetHeadcount = document.getElementById('targetHeadcount').value;
    const title = document.getElementById('recruitTitle').value;
    const content = document.getElementById('recruitContent').value;
    const endDate = document.getElementById('recruitEndDate').value;
    
    // (productName은 유효성 검사에 사용되었으나, 백엔드 전송 데이터에는 포함되지 않은 것으로 가정하고 삭제)

    // 3. 유효성 검사 (빈 값 체크)
    if (!productUrl || !targetHeadcount || !title || !content || !endDate) {
        alert("모든 항목을 입력해주세요.");
        return;
    }

    // 상품 고유 ID 추출 로직 (이전에 논의된 내용)
    const regex = /products\/(\d+)/; 
    const match = productUrl.match(regex);
    let productNumber;

    if (match && match[1]) {
        // ⭐ 문제 해결: 주석을 풀고, 10진수 정수로 변환하여 할당합니다.
        productNumber = parseInt(match[1], 10);
        
        console.log(`추출된 제품 ID (숫자): ${productNumber}`);
    } else {
        alert("상품 URL에서 유효한 제품 ID를 찾을 수 없습니다.");
        console.error(`URL에서 제품 ID를 찾을 수 없습니다: ${productUrl}`);
        return; // ID 추출 실패 시 등록 중단
    }

    // ⭐ 문제 해결: 모든 데이터 준비가 끝난 후, 핵심 함수를 호출합니다.
    await registerGroupBuy(productNumber, productUrl, targetHeadcount, title, content, endDate);
}


// 3. API 호출 및 처리 함수
// ⭐ 문제 해결: submitRecruitment에서 추출된 모든 데이터를 인수로 받습니다.
async function registerGroupBuy(productNumber, productUrl, targetHeadcount, title, content, endDate) { 

    const token = getToken(); // 토큰을 가져옵니다.

    const headers = {
        'Content-Type': 'application/json', // 데이터 형식 지정 (기존 POST 요청에 필요)
        // 토큰 추가: Authorization 헤더에 'Bearer 토큰값' 형식으로 추가
        'Authorization': `Bearer ${token}` 
    };
    
    try {
        let success = false;
        
        // 1. 첫 번째 API 호출: URL 유효성/등록 가능 여부 확인 (GET)
        // GET 요청이므로, 데이터를 URL 쿼리 파라미터로 전달
        const urlParams = new URLSearchParams({ url: productUrl });
        const responseGet = await fetch(`${API_BASE}/api/groupbuys/attempt?${urlParams}`, {
            method: 'GET',
            headers: headers
        });
        
        // GET 요청의 성공/실패 확인 (HTTP 상태 코드가 200-299인지 확인)
        if (responseGet.ok) {
            // ⭐ 문제 해결: 응답 본문을 텍스트로 읽고(await response.text()) 'success'와 비교합니다.
            const validationResult = await responseGet.text(); 
            
            if (validationResult.trim() === 'success') {
                // 2. URL 검증 성공 시: 모집글 등록 (POST) 실행
                const postData = {
                    productId: productNumber,         
                    targetHeadcount: parseInt(targetHeadcount, 10), // 숫자로 확실히 변환
                    title: title,                   
                    content: content,               
                    recruit_end_date: endDate         
                };

                const responsePost = await fetch(`${API_BASE}/api/groupbuys/online`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json' 
                    },
                    body: JSON.stringify(postData) // JSON 문자열로 변환하여 전송
                });
                
                // POST 요청의 성공/실패 확인
                if (responsePost.ok) { 
                    success = true;
                } else {
                    const errorText = await responsePost.text();
                    throw new Error(`모집글 등록 실패: ${errorText || '서버 오류'}`);
                }
                
            } else {
                 // GET 요청의 응답 텍스트가 'success'가 아닐 때 (예: 'fail', 'already registered')
                alert(`등록 확인 실패: ${validationResult || '입력 정보를 확인해주세요.'}`);
            }

        } else {
            // GET 요청 자체가 HTTP 오류 상태일 때 (4xx, 5xx 등)
            const errorText = await responseGet.text();
            alert(`URL 검증 중 서버 오류: ${errorText || '서버 응답 확인 필요'}`);
        }

        // 성공 여부에 따른 최종 처리
        if (success) {
            alert("모집글이 성공적으로 등록되었습니다!");
        }

        document.querySelector('.modal').style.display = 'none';
        window.location.reload(); 
        
    } catch (error) {
        // 모든 종류의 오류 처리 (네트워크 오류, throw new Error 등)
        console.error("등록 처리 중 오류 발생:", error);
        alert("글 등록 처리 중 오류가 발생했습니다: " + error.message);
    }
}