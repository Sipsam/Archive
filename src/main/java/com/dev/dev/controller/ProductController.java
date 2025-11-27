package com.dev.dev.controller;

import com.dev.dev.service.ProductService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.json.JSONObject;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/groupbuys")
@RequiredArgsConstructor
public class ProductController {

    private final ProductService productService;

    @GetMapping("/attempt")
    public ResponseEntity<Map<String, Object>> attemptRegister(@RequestParam String url) {
        System.out.println("상품 등록 시도: " + url);
        try {
            productService.searchByUrl(url);
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("message", "상품 정보를 성공적으로 가져왔습니다.");
            System.out.println("상품 정보 추출 성공: ");
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            System.out.println("상품 등록 실패: " + e.getMessage());
            return ResponseEntity.status(500)
                    .body(createErrorResponse("상품 정보를 가져오는데 실패했습니다: " + e.getMessage()));
        }
    }
    private Map<String, Object> createErrorResponse(String message) {
        Map<String, Object> error = new HashMap<>();
        error.put("success", false);
        error.put("message", message);
        return error;
    }
}
