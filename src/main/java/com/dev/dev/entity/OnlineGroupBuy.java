package com.dev.dev.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder // 빌더 패턴 사용을 위해 추가
@Entity
@Table(name = "online_group_buys") // 테이블 명은 프로젝트 규칙에 따라 수정 가능 (예: group_buys)
public class OnlineGroupBuy {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id; // 온라인 모집글 고유 id

    // --- 기존 GroupBuy(부모)에서 가져온 필드들 ---

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "host_user_id", nullable = false)
    private User hostUser;//모집글 방장 id, User테이블 참조 FK

    private String title;//모집글 제목

    @Lob
    private String content;//모집글 상세 내용

    @Enumerated(EnumType.STRING)
    @Column(length = 20)
    private GroupBuyStatus status;//모집글 참여 상태

    @Column(name = "recruit_end_date")
    private LocalDateTime recruitEndDate;//모집글 마감 일시

    @Column(name = "chat_room_id")
    private Long chatRoomId;//ChatRoom테이블 참조 FK

    @Column(name = "created_at")
    private LocalDateTime createdAt;//모집글 생성 일시

    // --- 기존 OnlineGroupBuy(자식)에 있던 필드 ---

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "product_id", nullable = false)
    private Product productId;//Product테이블 참조 FK

    // 1. mappedBy: OnlineParticipation 엔터티 내의 변수명("onlineGroupBuy")과 일치해야 함
    // 2. CascadeType.ALL: 공동구매 글이 삭제되면 참여 내역도 같이 삭제됨 (필요에 따라 조절)
    // 3. orphanRemoval: 리스트에서 제거하면 DB에서도 삭제됨
    @OneToMany(mappedBy = "onlineGroupBuy", fetch = FetchType.LAZY, cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default // @Builder 사용 시 리스트가 null이 아닌 빈 리스트로 초기화되도록 함
    private List<OnlineParticipation> participationList = new ArrayList<>();


    // 생성일자 자동 주입을 위한 메서드 (JPA Auditing을 안 쓴다면 필요)
    @PrePersist
    public void prePersist() {
        this.createdAt = LocalDateTime.now();//생성일자 자동 주입.
    }
}