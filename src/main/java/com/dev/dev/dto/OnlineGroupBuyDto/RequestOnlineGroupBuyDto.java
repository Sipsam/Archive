package com.dev.dev.dto.OnlineGroupBuyDto;

import com.dev.dev.entity.GroupBuyStatus;
import com.dev.dev.entity.PaymentStatus;
import lombok.*;
import java.time.LocalDateTime;

public class RequestOnlineGroupBuyDto {

        // [등록] 공구 모집글 생성용 Dto
        @Getter
        @Setter
        @NoArgsConstructor
        @AllArgsConstructor
        @Builder
        public static class Create {
            private Long productId;
            private String title;
            private String content;
            private Integer targetHeadcount;
            private LocalDateTime recruitEndDate;
        }

        // [상태 변경] 공구 모집글 정보 수정용 Dto
        @Getter
        @Setter
        @NoArgsConstructor
        @AllArgsConstructor
        @Builder
        public static class UpdateStatus {
            private String title;
            private String content;
            private GroupBuyStatus status;
            private LocalDateTime recruitEndDate;
        }

        // [참여 정보 수정] 공구 참여자 개인별 정보 수정용 Dto. 수량, 결제상태 등
        @Getter
        @Setter
        @NoArgsConstructor
        @AllArgsConstructor
        @Builder
        public static class UpdateTracking {
            private Integer quantity;
            private PaymentStatus paymentStatus;
        }
}

