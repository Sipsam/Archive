package com.dev.dev.controller;

import com.dev.dev.entity.Product;
import com.dev.dev.service.ProductService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/groupbuys")
@RequiredArgsConstructor
@Slf4j
public class ProductController {

    private final ProductService productService;

    @GetMapping("/attempt")
    public ResponseEntity<Map<String, Object>> attemptRegister(@RequestParam String url) {
        log.info("상품 등록 시도: {}", url);
        try {
            Product product = productService.searchByUrl(url);
            Map<String, Object> result = new HashMap<>();
            if (product != null) {
                result.put("success", true);
                result.put("message", "success"); // 성공 시
                result.put("productNumber", product.getId());
                log.info("상품 정보 추출 성공: {}", product);
            } else {
                result.put("success", false);
                result.put("message", "failed"); // 매칭된 상품 없을 때
                log.info("매칭된 상품 없음");
            }
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("상품 등록 실패", e);
            Map<String, Object> result = new HashMap<>();
            result.put("success", false);
            result.put("message", "failed");
            return ResponseEntity.ok(result);
        }
    }
    // 상품 ID로 상품 조회
    @GetMapping("/{productId}")
    public ResponseEntity<?> getProduct(@PathVariable Long productId) {
        Product product = productService.findById(productId);

        if (product == null) {
            return ResponseEntity
                    .status(404)
                    .body("Product not found: " + productId);
        }

        return ResponseEntity.ok(product);
    }
    private Map<String, Object> createErrorResponse(String message) {
        Map<String, Object> error = new HashMap<>();
        error.put("success", false);
        error.put("message", message);
        return error;
    }
}
