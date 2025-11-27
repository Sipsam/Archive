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
    private Long id; // 쇼핑 API의 productId를 그대로 사용

    private String name;
    private Integer price;

    @Column(name = "all_quantity")
    private Integer allQuantity;
    private String link;
    private String unit; // g, kg, 개, 팩 등
}
