// login.js

const BACKEND_URL = '';

document.addEventListener('DOMContentLoaded', () => {
    // 탭 전환 로직 (기존 유지)
    window.switchTab = function(tab) {
        // ... (기존 탭 전환 로직)
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
            
            // 💡 수정 2: UI 필드(email)를 백엔드 DTO(loginId)에 맞게 매핑
            const loginPayload = {
                loginId: loginData.email,
                password: loginData.password,
            };

            try {
                // 💡 common.js의 apiFetch 대신 fetch를 사용하므로, BACKEND_URL을 명시합니다.
                const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(loginPayload)
                });

                if (response.ok) {
                    const data = await response.json();
                    
                    // 💡 수정 3: 백엔드의 LoginResponse는 'accessToken' 필드를 사용합니다.
                    if (data.accessToken) {
                        localStorage.setItem('accessToken', data.accessToken);
                        
                        // 💡 추가: common.js의 login 함수를 사용
                    } else {
                        throw new Error('토큰이 응답에 포함되지 않았습니다.');
                    }
                    
                    alert('로그인 성공!');
                    window.location.href = 'index.html';
                } else {
                    const errorText = await response.text();
                    alert(`로그인 실패: ${errorText || '아이디 또는 비밀번호를 확인해주세요.'}`);
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

            if (signupData.password !== signupData.passwordConfirm) {
                alert('비밀번호가 일치하지 않습니다.');
                return;
            }
            delete signupData.passwordConfirm;

            // 💡 추가/수정: 회원가입 시 필수 필드를 DTO에 맞게 매핑하고, 
            // 누락된 필드는 빈 문자열로 채워야 백엔드 에러를 방지할 수 있습니다.
            const signupPayload = {
                loginId: signupData.email, // UI email -> DTO loginId 매핑
                password: signupData.password,
                name: signupData.name,
                nickname: signupData.name, // 💡 임시: 닉네임 필드가 없으므로 name으로 대체
                email: signupData.email,
                phoneNumber: '', // 💡 누락 필드 (백엔드 JoinRequest 확인)
                address: '',     // 💡 누락 필드
                addressDetail: '', // 💡 누락 필드
                zipCode: '',     // 💡 누락 필드
            };

            try {
                const response = await fetch(`${BACKEND_URL}/api/auth/join`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(signupPayload) // 💡 signupPayload 사용
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
