// js/common.js

// 1. ⚙️ 환경 설정 (Nginx 프록시 사용 전제)
const API_BASE = ''; 

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 네비게이션 탭 활성화
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            navTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });
});

// 2. 🔑 인증 및 토큰 관리 유틸리티

function getToken() {
    return localStorage.getItem('accessToken');
}

function checkAuth() {
    return !!getToken();
}

function login(userData) {
    if (userData && userData.accessToken) {
        console.log("token stored");
        localStorage.setItem('accessToken', userData.accessToken);
    }
}

/**
 * 로그아웃 처리 (수정했음)
 * 함수 실행 시 확인 창을 띄우고, 확인을 눌러야만 로그아웃이 진행됨
 */
function logout() {
    // 1. 확인 창 띄우기
    if (!confirm("정말 로그아웃 하시겠습니까?")) {
        return; // 취소 버튼을 누르면 함수 종료 (로그아웃 안 함)
    }

    // 2. 확인 버튼을 눌렀을 때만 실행
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user'); 
    
    alert("로그아웃 되었습니다."); // 선택 사항
    window.location.href = 'index.html';
}


// 3. 🌐 공통 API 호출 래퍼 (apiFetch)

async function apiFetch(path, { method = 'GET', headers = {}, body } = {}) {
    const token = getToken();

    const response = await fetch(`${API_BASE}${path}`, {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
    });

    if (response.status === 401) {
        // 여기서 logout()을 호출하면 401 에러 시에도 "로그아웃 하시겠습니까?"가 뜰 수 있기 때문에
        // 강제 로그아웃이 필요할 때는 confirm 없이 처리하는 것이 좋으므로,
        // 여기서는 수동으로 삭제하거나 별도 함수를 쓰는 것이 좋지만,
        // 일단 기존 흐름 유지를 위해 logout() 대신 로컬스토리지 삭제만 수행
        localStorage.removeItem('accessToken');
        localStorage.removeItem('user');
        alert('로그인이 만료되었거나 권한이 없습니다. 다시 로그인해주세요.');
        window.location.href = 'login.html';
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
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


function navigateTo(page) {
    window.location.href = page;
}

// 전역 함수로 노출
window.getToken = getToken;
window.checkAuth = checkAuth;
window.login = login;
window.logout = logout;
window.apiFetch = apiFetch;
window.navigateTo = navigateTo;
