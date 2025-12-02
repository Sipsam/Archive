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

function logout() {
    if (!confirm("정말 로그아웃 하시겠습니까?")) {
        return; 
    }
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user'); 
    alert("로그아웃 되었습니다.");
    window.location.href = 'index.html';
}


// 3. 🌐 공통 API 호출 래퍼 (apiFetch) - [핵심 수정됨]

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
        localStorage.removeItem('accessToken');
        localStorage.removeItem('user');
        alert('로그인이 만료되었거나 권한이 없습니다. 다시 로그인해주세요.');
        window.location.href = 'login.html';
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
        let errorMessage = `API Error: ${response.status}`;
        try {
            // 에러 메시지도 JSON인지 텍스트인지 확인
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const errorJson = await response.json();
                errorMessage = errorJson.message || errorMessage;
            } else {
                errorMessage = await response.text();
            }
        } catch (e) {
            // 무시
        }
        throw new Error(errorMessage);
    }

    if (response.status === 204) return null;

    // [핵심 수정] 응답 타입에 따라 JSON 또는 텍스트로 자동 변환
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
        return response.json();
    } else {
        return response.text(); // 텍스트만 반환하는 경우 대응 (SyntaxError 방지)
    }
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