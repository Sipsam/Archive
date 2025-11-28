// js/mypage.js

let currentUserInfo = null;

document.addEventListener('DOMContentLoaded', async function() {
    // 1. 인증 확인
    if (!checkAuth()) { 
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return; 
    }
    
    // 2. 탭 기능 설정 (메뉴 클릭 시 화면 전환)
    setupTabs();

    // 3. 사용자 정보 로드
    try {
        const myInfo = await apiFetch('/api/users/me'); 
        currentUserInfo = myInfo;
        
        // 이름 바인딩
        const nameElement = document.getElementById('userName');
        if (nameElement) nameElement.textContent = myInfo.nickname || '사용자';
        
        // 매너온도 바인딩
        const scoreElement = document.querySelector('.score');
        if (scoreElement) {
            const temp = myInfo.mannerTemp !== undefined ? myInfo.mannerTemp : 36.5;
            scoreElement.textContent = temp.toFixed(1);
        }
        
        // 포인트 바인딩
        updatePointUI(myInfo.points);
        
        // 참여 중인 모집글 로드 (주문 내역)
        await loadMyParticipations();

        // 설정 폼 초기값 세팅
        populateSettingsForm(myInfo);

    } catch (error) {
        console.error('정보 로드 실패:', error);
    }

    setupSettingsForm();
});

// --- 탭(메뉴) 전환 기능 ---
function setupTabs() {
    const menuLinks = document.querySelectorAll('.menu-link');
    const tabContents = document.querySelectorAll('.tab-content');

    menuLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.dataset.tab;
            // 준비중인 메뉴(href="#")는 제외
            if (!targetId) return; 

            e.preventDefault();

            // 1. 모든 메뉴 활성화 해제 및 클릭한 메뉴 활성화
            menuLinks.forEach(item => item.classList.remove('active'));
            this.classList.add('active');

            // 2. 모든 컨텐츠 숨기기 및 타겟 컨텐츠 보여주기
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === targetId) {
                    content.classList.add('active');
                }
            });
        });
    });
}

// UI에 포인트 숫자를 업데이트하는 헬퍼 함수
function updatePointUI(points) {
    const safePoints = points || 0;
    const formatted = new Intl.NumberFormat().format(safePoints);
    
    const profilePoint = document.getElementById('userPoints');
    if(profilePoint) profilePoint.textContent = formatted;
}

// --- 참여 내역 로드 ---
async function loadMyParticipations() {
    const participationList = document.getElementById('participationList');
    if (!participationList) return;

    try {
        const participations = await apiFetch('/api/users/me/participations');
        
        participationList.innerHTML = ''; // 초기화

        if (!participations || participations.length === 0) {
            participationList.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #999; background: #f9f9f9; border-radius: 8px;">
                    참여 중인 모집글이 없습니다.
                </div>`;
            return;
        }

        // 참여 모집글 목록 표시
        participations.forEach(participation => {
            const groupBuy = participation.onlineGroupBuy || participation.groupBuy;
            if (!groupBuy) return;

            const itemDiv = document.createElement('div');
            itemDiv.className = 'activity-item';
            itemDiv.style.cursor = 'pointer';
            itemDiv.style.padding = '15px';
            itemDiv.style.marginBottom = '10px';
            itemDiv.style.border = '1px solid #eee';
            itemDiv.style.borderRadius = '8px';
            itemDiv.style.backgroundColor = '#fff';
            
            itemDiv.onclick = () => {
                if(groupBuy.id) window.location.href = `recruitment-detail.html?id=${groupBuy.id}`;
            };

            const endDateStr = groupBuy.recruitEndDate ? new Date(groupBuy.recruitEndDate).toLocaleDateString('ko-KR') : '-';
            const paymentStatus = participation.paymentStatus || 'PENDING';
            let statusColor = '#ffa500'; // 대기
            let statusText = '결제대기';

            if(paymentStatus === 'PAID') { statusColor = '#4a90e2'; statusText = '결제완료'; }
            else if(paymentStatus === 'CANCELLED') { statusColor = '#ff4444'; statusText = '취소됨'; }

            itemDiv.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: bold; font-size: 16px; color: #333;">${groupBuy.title || '제목 없음'}</div>
                        <div style="font-size: 14px; color: #666; margin-top: 4px;">상품: ${groupBuy.productName || groupBuy.product?.name || '-'}</div>
                        <div style="font-size: 12px; color: #999; margin-top: 4px;">마감일: ${endDateStr}</div>
                    </div>
                    <span style="padding: 5px 10px; background: ${statusColor}; color: white; border-radius: 5px; font-size: 12px;">
                        ${statusText}
                    </span>
                </div>
            `;
            participationList.appendChild(itemDiv);
        });

    } catch (error) {
        console.error('참여 모집글 로드 실패:', error);
    }
}

// --- 설정 폼 관련 ---

function populateSettingsForm(user) {
    if (!user) return;
    document.getElementById('settingName').value = user.name || '';
    document.getElementById('settingNickname').value = user.nickname || '';
    document.getElementById('settingEmail').value = user.email || '';
    document.getElementById('settingPhone').value = user.phoneNumber || '';
    document.getElementById('settingAddress').value = user.address || '';
    document.getElementById('settingAddressDetail').value = user.addressDetail || '';
    document.getElementById('settingZip').value = user.zipCode || '';
}

function setupSettingsForm() {
    const form = document.getElementById('settingsForm');
    if (!form) return;

    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        await saveSettings();
    });
}

// 정보 저장 및 비밀번호 변경 로직
async function saveSettings() {
    const saveBtn = document.getElementById('settingsSaveBtn');
    
    // 1. 값 가져오기
    const currentPassword = getInputValue('settingPassword');
    const newPassword = getInputValue('newPassword');
    const confirmNewPassword = getInputValue('confirmNewPassword');

    // 2. 현재 비밀번호 확인 (필수)
    if (!currentPassword) {
        alert('정보를 변경하려면 본인 확인을 위해 [현재 비밀번호]를 입력해주세요.');
        document.getElementById('settingPassword').focus();
        return;
    }

    // 3. 새 비밀번호 유효성 검사 (입력했을 경우만)
    if (newPassword || confirmNewPassword) {
        if (newPassword !== confirmNewPassword) {
            alert('새 비밀번호가 일치하지 않습니다. 다시 확인해주세요.');
            return;
        }
        if (newPassword.length < 4) { 
            alert('비밀번호는 4자 이상이어야 합니다.');
            return;
        }
    }

    // 4. 전송할 데이터 구성
    const payload = {
        name: getInputValue('settingName'),
        nickname: getInputValue('settingNickname'),
        email: getInputValue('settingEmail'),
        phoneNumber: getInputValue('settingPhone'),
        address: getInputValue('settingAddress'),
        addressDetail: getInputValue('settingAddressDetail'),
        zipCode: getInputValue('settingZip')
    };

    // 새 비밀번호가 있다면 추가 (백엔드 변수명: password)
    if (newPassword) {
        payload.password = newPassword; 
    }

    Object.keys(payload).forEach(key => {
        if (payload[key] === '') payload[key] = null;
    });

    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.textContent = '저장 중...';
    }

    try {
        // 5. 현재 비밀번호 검증 (로그인 API 활용)
        await verifyCurrentPassword(currentPassword);

        // 6. 정보 수정 요청 (PUT)
        const updatedUser = await apiFetch('/api/users/me', {
            method: 'PUT',
            body: payload
        });

        // 7. 성공 처리
        currentUserInfo = updatedUser;
        populateSettingsForm(updatedUser);
        
        // 닉네임 변경 반영
        const nameElement = document.getElementById('userName');
        if (nameElement) nameElement.textContent = updatedUser.nickname || '사용자';

        // 비밀번호 입력창 초기화
        document.getElementById('settingPassword').value = '';
        document.getElementById('newPassword').value = '';
        document.getElementById('confirmNewPassword').value = '';

        alert('회원 정보가 성공적으로 수정되었습니다.');

    } catch (error) {
        console.error('정보 저장 실패:', error);
        alert(error.message ? error.message : '정보 저장 중 오류가 발생했습니다. (현재 비밀번호를 확인해주세요)');
    } finally {
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.textContent = '저장하기';
        }
    }
}

function getInputValue(inputId) {
    const input = document.getElementById(inputId);
    return input ? input.value.trim() : '';
}

// 현재 비밀번호 검증용 (로그인 API 호출)
async function verifyCurrentPassword(password) {
    const loginId = currentUserInfo ? currentUserInfo.loginId : null;
    
    // loginId가 없으면 검증 불가 (백엔드 스펙에 따라 다름)
    if(!loginId) return; 

    const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            loginId: loginId,
            password: password
        })
    });

    if (!response.ok) {
        throw new Error('현재 비밀번호가 일치하지 않습니다.');
    }
}