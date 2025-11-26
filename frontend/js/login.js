// login.js

const BACKEND_URL = ''; 

document.addEventListener('DOMContentLoaded', () => {
    // 탭 전환 로직 (유지)
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
            e.preventDefault(); 
            const formData = new FormData(loginForm);
            const loginData = Object.fromEntries(formData.entries());
            
            // DTO 매핑: UI email -> DTO loginId
            const loginPayload = {
                loginId: loginData.loginId,
                password: loginData.password,
            };

            try {
                const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(loginData),
                });

                if (response.ok) {
                    const data = await response.json();
                    // 🚨 핵심 수정: 백엔드 응답 키 'accessToken' 사용
                    if (data.accessToken) { 
                        // 토큰 저장 성공!
                        localStorage.setItem('accessToken', data.accessToken);
                        // login(data); 
                    } else {
                        throw new Error('서버 응답에 인증 토큰이 포함되어 있지 않습니다.');
                    }
                    
                    alert('로그인 성공!');
                    window.location.href = 'index.html';
                } else {
                    const errorText = await response.text();
                    alert(`로그인 실패: ${errorText || '아이디 또는 비밀번호를 확인해주세요.'}`);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('서버 통신 중 오류가 발생했습니다. (Nginx 설정 확인 필요)');
            }
        });
    }

    // 2. 회원가입 폼 제출 처리 (Nginx 환경에 맞게 fetch 사용 및 DTO 필드 매핑만 유지)
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(signupForm);
            const signupData = Object.fromEntries(formData.entries());

            if (signupData.password !== signupData.passwordConfirm) {
                alert('비밀번호가 일치하지 않습니다.');
                return;
            }
            delete signupData.passwordConfirm;

            // DTO 필수 필드 매핑 및 누락 필드 빈 문자열 처리
            const signupPayload = {
                loginId: signupData.loginId, 
                password: signupData.password,
                name: signupData.name,
                nickname: signupData.nickname, 
                email: signupData.email,
                phoneNumber: signupData.phoneNumber, 
                address: signupData.address,     
                addressDetail: signupData.addressDetail, 
                zipCode: signupData.zipCode,     
            };

            try {
                const response = await fetch(`${BACKEND_URL}/api/auth/join`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(signupPayload)
                });

                if (response.ok) {
                    alert('회원가입 성공! 로그인해주세요.');
                    window.switchTab('login');
                } else {
                    const errorText = await response.text();
                    alert(`회원가입 실패: ${errorText || '입력 정보를 확인해주세요.'}`);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('서버 통신 중 오류가 발생했습니다.');
            }
        });
    }
});
