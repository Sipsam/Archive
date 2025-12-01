package com.dev.dev.dto.participation;

import com.dev.dev.entity.OnlineParticipation;
import lombok.Data;

@Data
public class ParticipationResponse {
    private Long id;
    private String groupTitle;
    private String productName;
    private int targetHeadcount;

    public ParticipationResponse(OnlineParticipation p) {
        this.id = p.getId();
        this.groupTitle = p.getOnlineGroupBuy().getTitle();

        // ★ 여기 수정됨: product → productId
        this.productName = p.getOnlineGroupBuy().getProductId().getName();

        this.targetHeadcount = p.getOnlineGroupBuy().getTargetHeadcount();
    }
}
