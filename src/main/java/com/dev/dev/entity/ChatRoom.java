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
@Table(name = "chat_rooms")
public class ChatRoom {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;


    @Column(name = "group_buy_id", unique = true)
    private Long groupBuyId;


    private String name;


    @Column(name = "created_at")
    private LocalDateTime createdAt;
}