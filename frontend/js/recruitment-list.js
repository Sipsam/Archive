// frontend/js/recruitment-list.js

document.addEventListener('DOMContentLoaded', async function() {
    await loadRecruitmentList();
});

// 모집글 목록 불러오기
async function loadRecruitmentList() {
    const recruitmentList = document.querySelector('.recruitment-list');
    if (!recruitmentList) return;

    try {
        // 1. 전체 모집글 조회 (백엔드 API 호출)
        const groupBuys = await apiFetch('/api/groupbuys/online');
        
        // 2. 내 참여 내역 조회 (로그인 상태인 경우에만)
        let myParticipations = [];
        if (checkAuth()) {
            try {
                // 사용자가 참여한 내역을 가져옴
                const myData = await apiFetch('/api/users/me/participations');
                myParticipations = myData.onlineParticipations || [];
            } catch (e) {
                console.log('비로그인 상태 또는 내역 로드 실패 (무시 가능)');
            }
        }

        // 내가 참여한 글의 ID 목록 추출
        const myJoinedIds = myParticipations.map(p => p.onlineGroupBuy.id);

        recruitmentList.innerHTML = ''; // 기존 내용 초기화

        if (!groupBuys || groupBuys.length === 0) {
            recruitmentList.innerHTML = `
                <div style="text-align: center; padding: 50px; color: #666; background: #f9f9f9; border-radius: 8px;">
                    <p>등록된 모집글이 없습니다.</p>
                </div>`;
            return;
        }

        // 정렬: 내가 참여한 글을 맨 위로 올림
        // (true인 것이 앞으로 오도록 정렬)
        groupBuys.sort((a, b) => {
            const aJoined = myJoinedIds.includes(a.id);
            const bJoined = myJoinedIds.includes(b.id);
            // 둘 다 참여했거나 둘 다 안 했으면 순서 유지(0), a만 참여했으면 앞으로(-1), b만 참여했으면 뒤로(1)
            return (aJoined === bJoined) ? 0 : aJoined ? -1 : 1; 
        });

        // 리스트 렌더링
        groupBuys.forEach(groupBuy => {
            const isJoined = myJoinedIds.includes(groupBuy.id);
            const dateObj = new Date(groupBuy.recruitEndDate);
            const dateStr = dateObj.toLocaleDateString('ko-KR');
            const createdDate = groupBuy.createdAt ? new Date(groupBuy.createdAt).toLocaleDateString('ko-KR') : '-';
            
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recruitment-item';
            
            // 파란 테두리 + 뱃지를 이용하여 참여 중인 글 디자인 강조함
            let badgeHtml = '';
            if (isJoined) {
                // 스타일에 직접 접근하여 테두리 추가
                itemDiv.style.border = '3px solid #4a90e2'; 
                itemDiv.style.position = 'relative';
                // 오른쪽 상단에 '참여중' 뱃지 추가
                badgeHtml = `
                    <div style="position:absolute; top:15px; right:15px; background:#4a90e2; color:white; padding:5px 12px; border-radius:20px; font-size:12px; font-weight:bold; box-shadow:0 2px 4px rgba(0,0,0,0.2); z-index: 10;">
                        참여중
                    </div>
                `;
            }

            // 클릭 시 상세 페이지로 이동
            itemDiv.onclick = () => navigateTo(`recruitment-detail.html?id=${groupBuy.id}`);
            
            itemDiv.innerHTML = `
                ${badgeHtml}
                <div class="recruitment-header">
                    <div class="recruiter-info">
                        <div class="recruiter-avatar">👤</div>
                        <div class="recruiter-details">
                            <span class="recruiter-name">${groupBuy.hostUser?.nickname || groupBuy.hostUser?.name || '모집자'}</span>
                            <span class="recruiter-date">${createdDate}</span>
                        </div>
                    </div>
                </div>
                <div class="recruitment-content">
                    <h3>${groupBuy.title || '제목 없음'}</h3>
                    <p>${groupBuy.content || ''}</p>
                </div>
                <div class="recruitment-meta">
                    <span>상품명: ${groupBuy.product?.name || '상품명 없음'}</span>
                    <span>목표 인원: ${groupBuy.targetHeadcount || 0}명</span>
                    <span>마감일: ${dateStr}</span>
                </div>
            `;

            recruitmentList.appendChild(itemDiv);
        });

    } catch (error) {
        console.error('모집글 목록 로드 실패:', error);
        recruitmentList.innerHTML = `
            <div style="text-align: center; padding: 50px; color: #ff4444; background: #fff3cd; border-radius: 8px;">
                <p>모집글을 불러오지 못했습니다.</p>
                <p style="font-size: 0.9em; margin-top: 10px;">${error.message}</p>
            </div>`;
    }
}