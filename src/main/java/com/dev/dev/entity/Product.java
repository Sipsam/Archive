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
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;


    private String name;
    private Integer price;


    @Column(name = "all_quantity")
    private Integer allQuantity;


    @Column(name = "image_url", length = 500)
    private String imageUrl;


    @Column(name = "source_url", length = 500)
    private String sourceUrl;
}