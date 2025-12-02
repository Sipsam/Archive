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

        // 정렬: 내가 참여한 글 우선
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
            
            // 기본값 설정 (API 호출 전)
            const defaultName = groupBuy.hostName || '모집자';
            
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recruitment-item';
            
            let badgeHtml = '';
            if (isJoined) {
                itemDiv.style.border = '3px solid #4a90e2'; 
                itemDiv.style.position = 'relative';
                badgeHtml = `
                    <div style="position:absolute; top:15px; right:15px; background:#4a90e2; color:white; padding:5px 12px; border-radius:20px; font-size:12px; font-weight:bold; box-shadow:0 2px 4px rgba(0,0,0,0.2); z-index: 10;">
                        참여중
                    </div>
                `;
            }

            itemDiv.onclick = () => navigateTo(`recruitment-detail.html?id=${groupBuy.id}`);
            
            itemDiv.innerHTML = `
                ${badgeHtml}
                <div class="recruitment-header">
                    <div class="recruiter-info">
                        <div class="recruiter-avatar">👤</div>
                        <div class="recruiter-details">
                            <span class="recruiter-name" id="host-info-${groupBuy.id}">
                                ${defaultName} <span style="font-size:0.9em; color:#888;">(로딩중...)</span>
                            </span>
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

            // [추가 API 호출] 방장 정보 가져와서 업데이트
            loadHostInfo(groupBuy.hostId, groupBuy.id, defaultName);
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

// 방장의 리뷰 목록을 조회해서 닉네임과 매너온도를 추출하는 함수
async function loadHostInfo(hostId, groupBuyId, defaultName) {
    try {
        const reviews = await apiFetch(`/api/users/${hostId}/reviews`);
        const targetEl = document.getElementById(`host-info-${groupBuyId}`);
        
        if (!targetEl) return;

        let nickname = defaultName;
        let mannerTemp = 36.5;

        // 리뷰가 하나라도 있으면 그 안의 유저 정보를 사용
        if (reviews && reviews.length > 0) {
            const info = reviews[0].reviewee; // 리뷰 대상자(방장) 정보
            if (info) {
                nickname = info.nickname || info.name || defaultName;
                mannerTemp = info.mannerTemp !== undefined ? info.mannerTemp : 36.5;
            }
        }

        // UI 업데이트
        targetEl.innerHTML = `${nickname} <span style="color:#4a90e2; font-weight:bold; font-size:0.9em;">(${mannerTemp.toFixed(1)}℃)</span>`;

    } catch (error) {
        // 에러 시(리뷰 없음 등) 기본값 유지
        const targetEl = document.getElementById(`host-info-${groupBuyId}`);
        if(targetEl) targetEl.innerHTML = `${defaultName} <span style="color:#4a90e2; font-weight:bold; font-size:0.9em;">(36.5℃)</span>`;
    }
}