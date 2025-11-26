// js/common.js

// 1. ⚙️ 환경 설정 (Nginx 프록시 사용 전제)
// Nginx 프록시를 통해 요청이 백엔드 서버로 전달되므로, BASE URL을 비워둡니다.
const API_BASE = ''; 
// 백엔드 서버의 주소(http://localhost:8080)는 Nginx/Docker 환경에서 처리합니다.

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 네비게이션 탭 활성화 (기존 유지)
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            navTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });
});

// 2. 🔑 인증 및 토큰 관리 유틸리티

/**
 * JWT 토큰을 로컬 스토리지에서 가져옵니다.
 * @returns {string | null}
 */
function getToken() {
    return localStorage.getItem('accessToken');
}

/**
 * 로그인 상태인지 확인합니다. (토큰 존재 여부로 판단)
 * @returns {boolean}
 */
function checkAuth() {
    return !!getToken();
}

/**
 * 로그인 처리: 토큰을 저장하고, 필요하다면 사용자 정보도 저장합니다.
 * @param {object} userData - 백엔드에서 받은 응답 데이터 (최소 { accessToken: '...' } 포함)
 */
function login(userData) {
    // 백엔드 LoginResponse DTO는 accessToken 필드를 사용합니다.
    if (userData && userData.accessToken) {
        console.log("token stored");
        localStorage.setItem('accessToken', userData.accessToken);
    }
    // 선택 사항: 마이페이지에 바로 사용할 사용자 정보를 추가로 저장할 수 있습니다.
    // (현재 백엔드는 로그인 시 토큰만 반환하므로, 필요시 mypage.js에서 /me API를 통해 가져와야 함)
}

/**
 * 로그아웃 처리: 토큰을 삭제하고, 페이지를 메인으로 이동시킵니다.
 */
function logout() {
    localStorage.removeItem('accessToken');
    // 사용자 정보를 저장했다면 함께 삭제합니다.
    localStorage.removeItem('user'); 
    window.location.href = 'index.html';
}


// 3. 🌐 공통 API 호출 래퍼 (apiFetch)

/**
 * 백엔드 API를 호출하는 공통 함수. JWT 토큰을 자동으로 헤더에 추가합니다.
 * @param {string} path - API 경로 (예: '/api/auth/login')
 * @param {object} options - fetch 옵션 (method, headers, body 등)
 * @returns {Promise<object | null>} - JSON 응답 데이터 또는 204 No Content 시 null
 */
async function apiFetch(path, { method = 'GET', headers = {}, body } = {}) {
    const token = getToken();

    const response = await fetch(`${API_BASE}${path}`, {
        method,
        headers: {
            'Content-Type': 'application/json',
            // 인증 토큰이 있으면 Authorization 헤더를 추가
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
    });

    // 401 Unauthorized 에러 처리 (토큰 만료, 미인증 접근)
    if (response.status === 401) {
        logout(); // 토큰 삭제 및 메인 페이지 리다이렉트
        alert('로그인이 만료되었거나 권한이 없습니다. 다시 로그인해주세요.');
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
        // 서버에서 보낸 에러 메시지를 추출하여 반환
        let errorMessage = `API Error: ${response.status}`;
        try {
            const errorJson = await response.json();
            errorMessage = errorJson.message || errorMessage;
        } catch (e) {
            errorMessage = await response.text();
        }
        throw new Error(errorMessage);
    }

    return response.status === 204 ? null : response.json();
}


// 페이지 이동 (기존 유지)
function navigateTo(page) {
    window.location.href = page;
}

// 💡 전역 함수로 노출
// 다른 JS 파일에서 이 함수들을 사용할 수 있도록 window 객체에 추가하거나,
// HTML에서 <script> 태그를 사용하여 순서대로 로드해야 합니다.
window.getToken = getToken;
window.checkAuth = checkAuth;
window.login = login;
window.logout = logout;
window.apiFetch = apiFetch;
window.navigateTo = navigateTo;


// 모집글 신청 (모달 팝업)
const modal = document.querySelector('.modal');
const modalOpen = document.querySelector('.modal_btn');
const modalClose = document.querySelector('.close_btn');

// 열기 버튼을 눌렀을 때 모달팝업이 열림
modalOpen.addEventListener('click',function(){
    modal.style.display = 'block';
});
// 닫기 버튼을 눌렀을 때 모달팝업이 닫힘
modalClose.addEventListener('click',function(){
    modal.style.display = 'none';
});

async function submitRecruitment() {
    // 1. 로그인 체크 (common.js의 함수 활용)
    if (!checkAuth()) {
        alert("로그인이 필요한 서비스입니다.");
        window.location.href = 'login.html';
        return;
    }

    // 2. 입력값 가져오기
    const title = document.getElementById('recruitTitle').value;
    const content = document.getElementById('recruitContent').value;
    const endDate = document.getElementById('recruitEndDate').value;

    // 3. 유효성 검사 (빈 값 체크)
    if (!title || !content || !endDate) {
        alert("제목, 내용, 마감 시간을 모두 입력해주세요.");
        return;
    }

    try {
        // 4. API 호출 (POST 요청)
        const response = await apiFetch('/api/groupbuys/online', {
            method: 'POST',
            body: {
                title: title,
                content: content,
                recruitEndDate: endDate
            }
        });

        // 5. 성공 처리
        alert("모집글이 성공적으로 등록되었습니다!");
        
        // 모달 닫기 (common.js의 로직이 단순 display none이므로 여기서도 수동으로 닫거나 새로고침)
        document.querySelector('.modal').style.display = 'none';
        
        // 페이지 새로고침하여 목록 갱신
        window.location.reload();

    } catch (error) {
        console.error("등록 실패:", error);
        alert("글 등록 중 오류가 발생했습니다.");
    }
}