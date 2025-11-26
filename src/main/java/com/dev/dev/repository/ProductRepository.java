package com.dev.dev.repository;

import com.dev.dev.entity.Product;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ProductRepository extends JpaRepository<Product, Long> {
    boolean existsByName(String name); // 중복 체크용
}
