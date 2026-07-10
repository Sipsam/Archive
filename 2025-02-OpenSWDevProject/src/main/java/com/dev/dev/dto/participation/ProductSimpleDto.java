package com.dev.dev.dto.participation;

import com.dev.dev.entity.Product;
import lombok.Data;

@Data
public class ProductSimpleDto {
    private Long id;
    private String name;
    private String imageUrl;  // ★ 추가

    public ProductSimpleDto(Product p) {
        this.id = p.getId();
        this.name = p.getName();
        this.imageUrl = p.getImageUrl();  // ★ 추가
    }
}


