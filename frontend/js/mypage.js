// frontend/js/mypage.js

let currentUserInfo = null;
let paymentWidgets = null; 
let selectedPointAmount = 0; 

document.addEventListener('DOMContentLoaded', async function() {
    // 1. 인증 확인
    if (!checkAuth()) { 
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return; 
    }
    
    // 2. 탭 기능 설정
    setupTabs();

    // 3. 사용자 정보 및 내역 로드
    try {
        const myInfo = await apiFetch('/api/users/me'); 
        currentUserInfo = myInfo;
        
        // UI 바인딩
        const nameElement = document.getElementById('userName');
        if (nameElement) nameElement.textContent = myInfo.nickname || '사용자';
        
        const scoreElement = document.querySelector('.score');
        if (scoreElement) {
            const temp = myInfo.mannerTemp !== undefined ? myInfo.mannerTemp : 36.5;
            scoreElement.textContent = temp.toFixed(1);
        }
        
        updatePointUI(myInfo.points);
        populateSettingsForm(myInfo);
        
        // ⭐ 참여 내역 로드 함수 호출
        await loadMyParticipations();
        
        if(document.getElementById('pointHistoryList')) await loadMyPointHistory();
        if (document.getElementById('payment-method')) await initPointPayment();

    } catch (error) {
        console.error('정보 로드 실패:', error);
    }

    setupSettingsForm();
});

// ⭐ [참여 내역 로드] 이 부분이 화면에 목록을 그려줍니다.
async function loadMyParticipations() {
    const listContainer = document.getElementById('participationList');
    if (!listContainer) return;

    try {
        const data = await apiFetch('/api/users/me/participations');
        // 데이터 구조: { onlineParticipations: [...], offlineParticipations: [...] }
        const onlineList = data.onlineParticipations || [];
        
        listContainer.innerHTML = ''; // 초기화

        if (onlineList.length === 0) {
            listContainer.innerHTML = `
                <div style="padding: 40px; text-align: center; color: #999; background-color: #f9f9f9; border-radius: 8px;">
                    <p>아직 참여한 모집글이 없습니다.</p>
                    <a href="index.html" style="color: #4a90e2; text-decoration: none; font-weight: bold; margin-top: 10px; display: inline-block;">
                        모집글 보러 가기 &rarr;
                    </a>
                </div>`;
            return;
        }

        onlineList.forEach(item => {
            const groupBuy = item.onlineGroupBuy; 
            
            // 만약 백엔드에서 groupBuy 정보가 안 왔다면 건너뜀 (에러 방지)
            if (!groupBuy) return;

            const product = groupBuy.product;
            const dateStr = item.createdAt ? new Date(item.createdAt).toLocaleDateString() : '-';

            const card = document.createElement('div');
            card.className = 'activity-item'; 
            card.style.borderLeft = '4px solid #4a90e2';
            card.style.marginBottom = '15px';
            
            // 채팅방 버튼
            let chatButtonHtml = '';
            if (groupBuy.chatRoomId) {
                chatButtonHtml = `
                    <button onclick="location.href='chat.html?roomId=${groupBuy.chatRoomId}'" 
                            style="margin-top:10px; padding:8px 12px; background:#4a90e2; color:white; border:none; border-radius:4px; cursor:pointer; font-weight:bold;">
                        💬 채팅방 입장
                    </button>
                `;
            } else {
                chatButtonHtml = `<span style="font-size:12px; color:#999; margin-top:10px; display:inline-block;">(채팅방 준비중)</span>`;
            }

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <h3 style="margin-bottom:5px; font-size:16px; color:#333;">
                            <a href="recruitment-detail.html?id=${groupBuy.id}" style="text-decoration:none; color:#333;">
                                ${groupBuy.title || '제목 없음'}
                            </a>
                        </h3>
                        <p style="margin-bottom:5px; color:#666; font-size:14px;">상품: ${product ? product.name : '정보 없음'}</p>
                        <p style="font-size:13px; color:#888;">참여일: ${dateStr}</p>
                        <span style="display:inline-block; margin-top:5px; font-size:13px; font-weight:bold; color:#4a90e2;">
                            상태: ${item.paymentStatus || '결제 대기'}
                        </span>
                    </div>
                    <div style="text-align:right;">
                         ${chatButtonHtml}
                    </div>
                </div>
            `;
            listContainer.appendChild(card);
        });

    } catch (error) {
        console.error('참여 내역 로드 실패:', error);
        listContainer.innerHTML = '<div style="padding:20px; text-align:center; color:red;">목록을 불러오지 못했습니다.</div>';
    }
}


// --- ⭐ 3. 공통 UI 및 헬퍼 함수들 (탭, 포인트표시, 설정폼) ---

function setupTabs() {
    const menuLinks = document.querySelectorAll('.menu-link');
    const tabContents = document.querySelectorAll('.tab-content');

    if (!menuLinks.length) return;

    menuLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.dataset.tab;
            if (!targetId) return; 

            e.preventDefault();
            menuLinks.forEach(item => item.classList.remove('active'));
            this.classList.add('active');

            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === targetId) {
                    content.classList.add('active');
                }
            });
        });
    });
}

function updatePointUI(points) {
    const safePoints = points || 0;
    const formatted = new Intl.NumberFormat().format(safePoints);
    
    const profilePoint = document.getElementById('userPointsProfile');
    const mainPoint = document.getElementById('userPoints');
    
    if(profilePoint) profilePoint.textContent = formatted;
    if(mainPoint) mainPoint.textContent = formatted + " P";
}

async function loadMyPointHistory() {
    const historyList = document.getElementById('pointHistoryList'); 
    if (!historyList) return; 

    try {
        const historyData = await apiFetch('/api/points/history');
        historyList.innerHTML = ''; 
        
        if (historyData && historyData.length > 0) {
            historyData.forEach(item => {
                const row = document.createElement('div');
                row.className = 'activity-item'; 
                row.style.display = 'flex';
                row.style.justifyContent = 'space-between';
                
                const dateStr = item.createdAt ? new Date(item.createdAt).toLocaleDateString() : '-';
                const isPositive = (item.amount > 0); // 양수면 획득, 음수면 사용
                const sign = isPositive ? '+' : ''; // 음수는 숫자에 -가 포함됨
                const color = isPositive ? '#4a90e2' : '#ff4444';

                row.innerHTML = `
                    <div>
                        <span style="font-weight:bold; color:#555;">[포인트]</span> 
                        <span style="color:#888; font-size:14px; margin-left:5px;">${dateStr}</span>
                    </div>
                    <span style="font-weight:bold; color:${color};">
                        ${sign}${new Intl.NumberFormat().format(item.amount)} P
                    </span>
                `;
                historyList.appendChild(row);
            });
        } else {
            historyList.innerHTML = '<div style="padding:20px; text-align:center; color:#999;">포인트 변동 내역이 없습니다.</div>';
        }

    } catch (error) {
        console.error('포인트 내역 로드 실패:', error);
    }
}

// --- 설정 폼 관련 ---
function populateSettingsForm(user) {
    if (!document.getElementById('settingsForm')) return;
    
    setVal('settingName', user.name);
    setVal('settingNickname', user.nickname);
    setVal('settingEmail', user.email);
    setVal('settingPhone', user.phoneNumber);
    setVal('settingAddress', user.address);
    setVal('settingAddressDetail', user.addressDetail);
    setVal('settingZip', user.zipCode);
}

function setVal(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val || '';
}

function setupSettingsForm() {
    const form = document.getElementById('settingsForm');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        await saveSettings();
    });
}

async function saveSettings() {
    const password = document.getElementById('settingPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmNewPassword = document.getElementById('confirmNewPassword').value;

    if (!password) {
        alert('정보를 수정하려면 현재 비밀번호를 입력해야 합니다.');
        return;
    }

    // 비밀번호 변경 시도 시 확인
    if (newPassword || confirmNewPassword) {
        if (newPassword !== confirmNewPassword) {
            alert('새 비밀번호가 일치하지 않습니다.');
            return;
        }
    }

    // TODO: 비밀번호 검증 로직이 필요하다면 백엔드 API 추가 필요
    // 현재는 정보 수정 요청만 보냄

    const updateData = {
        nickname: getInputValue('settingNickname'),
        address: getInputValue('settingAddress'),
        addressDetail: getInputValue('settingAddressDetail'),
        zipCode: getInputValue('settingZip')
        // 비밀번호 변경은 별도 API가 필요할 수 있음
    };

    try {
        await apiFetch('/api/users/me', {
            method: 'PUT',
            body: updateData
        });
        alert('회원 정보가 수정되었습니다.');
        window.location.reload();
    } catch (error) {
        console.error(error);
        alert('정보 수정 실패: ' + error.message);
    }
}

function getInputValue(inputId) {
    const el = document.getElementById(inputId);
    return el ? el.value : null;
}