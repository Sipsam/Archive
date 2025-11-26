package com.dev.dev.entity;


import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;


@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Entity
@Table(name = "online_participations")
public class OnlineParticipation {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id; //참여 고유 id


    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user; //User 테이블 참조 FK , 참여자 id


    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "online_group_buy_id", nullable = false)
    private OnlineGroupBuy onlineGroupBuy;//온라인 모집글 고유id, OnlineGroupBuy 테이블 참조 FK


    private Integer quantity; // 수량


    @Enumerated(EnumType.STRING)
    @Column(name = "payment_status", length = 20)
    private PaymentStatus paymentStatus; //결제 상태

    @Column(name = "created_at")
    private LocalDateTime createdAt;//참여 일시
}