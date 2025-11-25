// js/login.js
const BACKEND_URL = '';

document.addEventListener('DOMContentLoaded', () => {
    // 탭 전환 로직 (기존 유지)
    window.switchTab = function(tab) {
        const loginForm = document.getElementById('loginForm');
        const signupForm = document.getElementById('signupForm');
        const tabs = document.querySelectorAll('.tab-btn');
        
        tabs.forEach(t => t.classList.remove('active'));
        
        if (tab === 'login') {
            loginForm.classList.add('active');
            signupForm.classList.remove('active');
            tabs[0].classList.add('active');
        } else {
            signupForm.classList.add('active');
            loginForm.classList.remove('active');
            tabs[1].classList.add('active');
        }
    };

    // 1. 로그인 폼 제출 처리
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault(); // 기본 제출 동작 막기

            // 폼 데이터 가져오기
            const formData = new FormData(loginForm);
            const loginData = Object.fromEntries(formData.entries());

            try {
                // 백엔드 API로 요청 (POST)
                const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(loginData)
                });

                if (response.ok) {
                    const data = await response.json();
                    
                    // 중요: 받은 토큰(JWT)을 로컬 스토리지에 저장
                    // (백엔드가 { "token": "..." } 형태로 준다고 가정)
                    localStorage.setItem('accessToken', data.accessToken); 
                    
                    alert('로그인 성공!');
                    window.location.href = 'index.html'; // 메인으로 이동
                } else {
                    alert('로그인 실패: 아이디 또는 비밀번호를 확인해주세요.');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('서버 통신 중 오류가 발생했습니다.');
            }
        });
    }

    // 2. 회원가입 폼 제출 처리
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(signupForm);
            const signupData = Object.fromEntries(formData.entries());

            // 비밀번호 확인 검증
            if (signupData.password !== signupData.passwordConfirm) {
                alert('비밀번호가 일치하지 않습니다.');
                return;
            }
            // 전송 시 passwordConfirm은 제외 (선택사항)
            delete signupData.passwordConfirm;

            try {
                const response = await fetch(`${BACKEND_URL}/api/auth/join`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(signupData)
                });

                if (response.ok) {
                    alert('회원가입 성공! 로그인해주세요.');
                    window.switchTab('login'); // 로그인 탭으로 자동 전환
                } else {
                    const errorData = await response.json();
                    alert(`회원가입 실패: ${errorData.message || '입력 정보를 확인해주세요.'}`);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('서버 통신 중 오류가 발생했습니다.');
            }
        });
    }
});
