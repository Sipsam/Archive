package com.dev.dev.dto.participation;

import com.dev.dev.entity.OnlineParticipation;
import lombok.Data;

@Data
public class ParticipationResponse {
    private Long id;
    private OnlineGroupBuySimpleDto onlineGroupBuy;  // ★ 프론트가 반드시 요구함

    public ParticipationResponse(OnlineParticipation p) {
        this.id = p.getId();
        this.onlineGroupBuy = new OnlineGroupBuySimpleDto(p.getOnlineGroupBuy());
    }
}
