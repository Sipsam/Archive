package com.dev.dev.entity;

import jakarta.persistence.*;
import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Entity
@Table(name = "products")
public class Product {
    @Id
    private Long id;

    private String name;
    private Integer price;

    @Column(name = "all_quantity")
    private Integer allQuantity;

    private String link;
    private String unit;

    private String imageUrl;   // ★ 추가됨
}

