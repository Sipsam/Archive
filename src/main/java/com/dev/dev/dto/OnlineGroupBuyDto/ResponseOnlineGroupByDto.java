package com.dev.dev.dto.OnlineGroupBuyDto;

import com.dev.dev.entity.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class ResponseOnlineGroupByDto {
    // 1. 공구 기본 정보
    private Long id;
    private String title;
    private String content;
    private GroupBuyStatus status;
    private Integer targetHeadcount; // 목표 인원
    private int currentHeadcount;    // 현재 인원 (계산됨)
    private LocalDateTime recruitEndDate;
    private LocalDateTime createdAt;
    private Long chatRoomId;

    // 2. 상품 정보
    private Long productId;
    private String productName;
    private Integer productPrice;
    private Integer productAllQuantity;

    // 3. 방장 정보
    private Long hostId;
    private String hostName;

    // 4. 참여자 리스트 (순환 참조 방지를 위해 전용 DTO 사용)
    private List<OnlineParticipationDto> participationList;

    // ★ Entity -> Full DTO 변환 메서드. from은 특별한 거 없이 단순 매서드다. 서비스에서 직접 호출 해야함.
    public static ResponseOnlineGroupByDto from(OnlineGroupBuy entity) {
        return ResponseOnlineGroupByDto.builder()
                .id(entity.getId())
                .title(entity.getTitle())
                .content(entity.getContent())
                .status(entity.getStatus())
                .targetHeadcount(entity.getTargetHeadcount())
                .currentHeadcount(entity.getParticipationList().size()) // 현재 인원
                .recruitEndDate(entity.getRecruitEndDate())
                .createdAt(entity.getCreatedAt())
                .chatRoomId(entity.getChatRoomId())

                // 상품 정보 평탄화
                .productId(entity.getProductId().getId())
                .productName(entity.getProductId().getName())
                .productPrice(entity.getProductId().getPrice())
                .productAllQuantity(entity.getProductId().getAllQuantity())

                // 방장 정보
                .hostId(entity.getHostUser().getId())
                .hostName(entity.getHostUser().getName())

                // 참여자 리스트 변환
                .participationList(entity.getParticipationList().stream()//참여자 리스트에서 참여자들을 하나씩 스트림으로 흘려보냄
                        .map(OnlineParticipationDto::from)//그 참여자를 잡아서 OnlineParticipationDto의 from메소드에 하나씩 넣어서 Dto로 변환된 참여자를 반환 받음.
                        .collect(Collectors.toList()))//반환 받은 참여자 Dto들을 다시 List로 묶음.
                .build();
    }
}