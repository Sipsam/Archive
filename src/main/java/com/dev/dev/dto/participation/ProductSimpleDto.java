package com.dev.dev.dto.participation;

import com.dev.dev.entity.Product;
import lombok.Data;

@Data
public class ProductSimpleDto {
    private Long id;
    private String name;

    public ProductSimpleDto(Product p) {
        this.id = p.getId();
        this.name = p.getName();
    }
}

