// 모집글 목록 페이지 JavaScript
document.addEventListener('DOMContentLoaded', async function() {
    await loadRecruitmentList();
});

// 모집글 목록 불러오기
async function loadRecruitmentList() {
    const recruitmentList = document.querySelector('.recruitment-list');
    if (!recruitmentList) return;

    try {
        // 백엔드 API 호출: 온라인 모집글 목록 조회
        const groupBuys = await apiFetch('/api/groupbuys/online');
        
        recruitmentList.innerHTML = ''; // 기존 내용 초기화

        if (!groupBuys || groupBuys.length === 0) {
            recruitmentList.innerHTML = `
                <div style="text-align: center; padding: 50px; color: #666; background: #f9f9f9; border-radius: 8px;">
                    <p>등록된 모집글이 없습니다.</p>
                </div>`;
            return;
        }

        // 받아온 데이터로 HTML 생성
        groupBuys.forEach(groupBuy => {
            const dateObj = new Date(groupBuy.recruitEndDate);
            const dateStr = dateObj.toLocaleDateString('ko-KR');
            const createdDate = groupBuy.createdAt ? new Date(groupBuy.createdAt).toLocaleDateString('ko-KR') : '-';
            
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recruitment-item';
            itemDiv.onclick = () => navigateTo(`recruitment-detail.html?id=${groupBuy.id}`);
            
            itemDiv.innerHTML = `
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

