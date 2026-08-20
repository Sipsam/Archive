package com.dev.dev.dto.community;

import lombok.*;

@Getter
@Setter
@AllArgsConstructor
@Builder
public class ReviewRequestDto {
    private Long groupBuyId;
    private Long revieweeId;
    private String comment;
    private Double rating;
}
