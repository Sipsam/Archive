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
@Table(name = "offline_group_buys")
public class OfflineGroupBuy extends GroupBuy {
    @Column(name = "meet_at")
    private LocalDateTime meetAt;
}