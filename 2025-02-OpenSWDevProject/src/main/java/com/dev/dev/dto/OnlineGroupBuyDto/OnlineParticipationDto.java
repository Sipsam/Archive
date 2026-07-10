package com.dev.dev.dto.OnlineGroupBuyDto;

import com.dev.dev.entity.*;
import lombok.*;
import java.time.LocalDateTime;

@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class OnlineParticipationDto {
    private Long id;
    private Long userId;
    private String userName;
    private Integer quantity;
    private PaymentStatus paymentStatus;
    private String trackingNumber;
    private LocalDateTime createdAt;

    //아래 메서드를 사용하여 참여자 Dto를 생성. 참여자 객체를 넣어야함.
    //ResponseOnlineGroupByDto에서 참여자 Dto를 담는 리스트를 만들 때, 이 메서드를 통해 스트림에서 하나씩 흘러나오는 참여자 객체를 참여자 Dto로 만듬.
    public static OnlineParticipationDto from(OnlineParticipation entity) {
        return OnlineParticipationDto.builder()
                .id(entity.getId())
                .userId(entity.getUser().getId())
                .userName(entity.getUser().getName())
                .quantity(entity.getQuantity())
                .paymentStatus(entity.getPaymentStatus())
                .createdAt(entity.getCreatedAt())
                .build();
    }
}