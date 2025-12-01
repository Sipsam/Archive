package com.dev.dev.dto.participation;

import com.dev.dev.entity.OnlineGroupBuy;
import lombok.Data;

@Data
public class OnlineGroupBuySimpleDto {

    private Long id;
    private String title;
    private Long chatRoomId;
    private int targetHeadcount;

    private ProductSimpleDto product;
    private String productImageUrl;  // ★ 프론트에서 groupBuy.productImageUrl 로 접근 예정

    public OnlineGroupBuySimpleDto(OnlineGroupBuy ogb) {
        this.id = ogb.getId();
        this.title = ogb.getTitle();
        this.chatRoomId = ogb.getChatRoomId();
        this.targetHeadcount = ogb.getTargetHeadcount();

        this.product = new ProductSimpleDto(ogb.getProductId());
        this.productImageUrl = ogb.getProductId().getImageUrl(); // ★ 추가됨
    }
}


