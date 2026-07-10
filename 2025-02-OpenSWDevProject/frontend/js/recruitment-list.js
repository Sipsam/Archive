// frontend/js/recruitment-list.js

document.addEventListener('DOMContentLoaded', async function() {
    await loadRecruitmentList();
});

// 모집글 목록 불러오기
async function loadRecruitmentList() {
    const recruitmentList = document.querySelector('.recruitment-list');
    if (!recruitmentList) return;

    try {
        const groupBuys = await apiFetch('/api/groupbuys/online');
        
        let myParticipations = [];
        if (checkAuth()) {
            try {
                const myData = await apiFetch('/api/users/me/participations');
                myParticipations = myData.onlineParticipations || [];
            } catch (e) {
                console.log('비로그인 상태 또는 내역 로드 실패 (무시 가능)');
            }
        }

        const myJoinedIds = myParticipations.map(p => p.onlineGroupBuy.id);

        recruitmentList.innerHTML = ''; 

        if (!groupBuys || groupBuys.length === 0) {
            recruitmentList.innerHTML = `
                <div style="text-align: center; padding: 50px; color: #666; background: #f9f9f9; border-radius: 8px;">
                    <p>등록된 모집글이 없습니다.</p>
                </div>`;
            return;
        }

        // 정렬
        groupBuys.sort((a, b) => {
            const aJoined = myJoinedIds.includes(a.id);
            const bJoined = myJoinedIds.includes(b.id);
            return (aJoined === bJoined) ? 0 : aJoined ? -1 : 1; 
        });

        // 리스트 렌더링
        groupBuys.forEach(groupBuy => {
            const isJoined = myJoinedIds.includes(groupBuy.id);
            const dateObj = new Date(groupBuy.recruitEndDate);
            const dateStr = dateObj.toLocaleDateString('ko-KR');
            const createdDate = groupBuy.createdAt ? new Date(groupBuy.createdAt).toLocaleDateString('ko-KR') : '-';
            
            const displayName = groupBuy.hostNickname || groupBuy.hostName || '모집자';
            const mannerTempVal = groupBuy.hostMannerTemp !== undefined ? groupBuy.hostMannerTemp : 36.5;
            const tempHtml = `<span style="color:#4a90e2; font-weight:bold; font-size:0.9em; margin-left:4px;">(${mannerTempVal.toFixed(1)}℃)</span>`;
            const productName = groupBuy.productName || '상품명 없음';

            // 이미지 처리
            let imageHtml = `<div class="recruitment-image-box" style="display:flex; align-items:center; justify-content:center; color:#999; font-size:12px;">이미지 없음</div>`;
            if (groupBuy.productImageUrl) {
                imageHtml = `
                    <div class="recruitment-image-box">
                        <img src="${groupBuy.productImageUrl}" alt="${productName}">
                    </div>
                `;
            }

            const itemDiv = document.createElement('div');
            itemDiv.className = 'recruitment-item';
            
            // 참여중 뱃지
            let badgeHtml = '';
            if (isJoined) {
                itemDiv.style.border = '2px solid #4a90e2'; 
                itemDiv.style.position = 'relative';
                badgeHtml = `
                    <div style="position:absolute; top:10px; right:10px; background:#4a90e2; color:white; padding:4px 10px; border-radius:15px; font-size:11px; font-weight:bold; box-shadow:0 1px 3px rgba(0,0,0,0.2); z-index: 10;">
                        참여중
                    </div>
                `;
            }

            itemDiv.onclick = () => navigateTo(`recruitment-detail.html?id=${groupBuy.id}`);
            
            // [구조 변경] 이미지(왼쪽) + 정보(오른쪽)
            itemDiv.innerHTML = `
                ${badgeHtml}
                
                ${imageHtml}

                <div class="recruitment-info-box">
                    <div class="recruitment-header">
                        <div class="recruiter-info">
                            <div class="recruiter-avatar">👤</div>
                            <div class="recruiter-details">
                                <span class="recruiter-name">${displayName} ${tempHtml}</span>
                                <span class="recruiter-date">${createdDate}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="recruitment-content">
                        <h3>${groupBuy.title || '제목 없음'}</h3>
                        <p>${groupBuy.content || ''}</p>
                    </div>
                    
                    <div class="recruitment-meta">
                        <span>상품: ${productName}</span>
                        <span>목표: ${groupBuy.targetHeadcount || 0}명</span>
                        <span>마감: ${dateStr}</span>
                    </div>
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
