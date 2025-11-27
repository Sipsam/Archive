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
            JSONObject product = productService.findProductFromUrl(url);
            if (product == null) {
                System.out.println("매칭되는 상품을 찾을 수 없음");
                return ResponseEntity.ok(createErrorResponse("매칭되는 상품을 찾을 수 없습니다."));
            }
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("message", "상품 정보를 성공적으로 가져왔습니다.");
            result.put("title", removeHtmlTags(product.optString("title", "")));
            result.put("link", product.optString("link", ""));
            result.put("image", product.optString("image", ""));
            result.put("lprice", product.optString("lprice", "0"));
            result.put("hprice", product.optString("hprice", "0"));
            result.put("mallName", product.optString("mallName", ""));
            result.put("productId", product.optString("productId", ""));
            result.put("brand", product.optString("brand", ""));
            result.put("maker", product.optString("maker", ""));
            result.put("category1", product.optString("category1", ""));
            result.put("category2", product.optString("category2", ""));
            result.put("category3", product.optString("category3", ""));
            result.put("category4", product.optString("category4", ""));
            System.out.println("상품 정보 추출 성공: " + result.get("title"));
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            System.out.println("상품 등록 실패: " + e.getMessage());
            return ResponseEntity.status(500)
                    .body(createErrorResponse("상품 정보를 가져오는데 실패했습니다: " + e.getMessage()));
        }
    }
    private String removeHtmlTags(String html) {
        if (html == null || html.isEmpty()) {
            return "";
        }
        return html.replaceAll("<[^>]*>", "").trim();
    }
    private Map<String, Object> createErrorResponse(String message) {
        Map<String, Object> error = new HashMap<>();
        error.put("success", false);
        error.put("message", message);
        return error;
    }
}
