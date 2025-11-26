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

    try {
        // 4. API 호출 (백엔드로 데이터 전송)
        // 백엔드 개발자에게 body의 변수명(key)이 맞는지 꼭 확인하세요!
        /*const response = await apiFetch('https://openapi.naver.com/v1/search/shop.json', {
            method: 'GET',

            body: {
                productName: productName,       // 상품명
                productUrl: productUrl,         // 구매 링크
                targetHeadcount: parseInt(targetHeadcount), // 모집 인원 (숫자로 변환)
                
                title: title,                   // 게시글 제목
                content: content,               // 내용
                recruitEndDate: endDate         // 마감 시간
            }
        });*/

        const clientId = 'AN9TaXRlbzATdnmERqWg';
        const clientSecret = 'WgV1Isj_ne';
        const query = encodeURIComponent(productName);

        fetch(`https://openapi.naver.com/v1/search/shop.json?query=${query}`, {
        method: 'GET',
        headers: {
            'X-Naver-Client-Id': clientId,
            'X-Naver-Client-Secret': clientSecret
        }
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            // 5. 성공 처리
            alert("모집글이 성공적으로 등록되었습니다!");
            document.querySelector('.modal').style.display = 'none';
            window.location.reload(); // 목록 새로고침
        })
        .catch(error => console.error(error));

    } catch (error) {
        console.error("등록 실패:", error);
        alert("글 등록 중 오류가 발생했습니다: " + error.message);
    }
}