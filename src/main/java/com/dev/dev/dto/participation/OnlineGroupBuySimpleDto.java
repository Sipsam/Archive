package com.dev.dev.dto.participation;

import com.dev.dev.entity.OnlineGroupBuy;
import lombok.Data;

@Data
public class OnlineGroupBuySimpleDto {

    private Long id;
    private String title;
    private Long chatRoomId;
    private int targetHeadcount;

    private ProductSimpleDto product; // product 정보도 포함해야 프론트 확장에 대비

    public OnlineGroupBuySimpleDto(OnlineGroupBuy ogb) {
        this.id = ogb.getId();
        this.title = ogb.getTitle();
        this.chatRoomId = ogb.getChatRoomId();
        this.targetHeadcount = ogb.getTargetHeadcount();
        this.product = new ProductSimpleDto(ogb.getProductId());
    }
}

