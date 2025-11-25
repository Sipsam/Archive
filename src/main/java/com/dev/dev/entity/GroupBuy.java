package com.dev.dev.entity;


import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;


@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "group_buys")
@Inheritance(strategy = InheritanceType.JOINED)
public abstract class GroupBuy {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;


    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "host_user_id", nullable = false)
    private User hostUser;


    private String title;


    @Lob
    private String content;


    @Enumerated(EnumType.STRING)
    @Column(length = 20)
    private GroupBuyType type;


    @Enumerated(EnumType.STRING)
    @Column(length = 20)
    private GroupBuyStatus status;


    @Column(name = "recruit_end_date")
    private LocalDateTime recruitEndDate;


    @Column(name = "location_info", length = 255)
    private String locationInfo;


    @Column(name = "chat_room_id")
    private Long chatRoomId;


    @Column(name = "created_at")
    private LocalDateTime createdAt;
}