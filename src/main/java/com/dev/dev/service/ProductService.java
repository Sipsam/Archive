package com.dev.dev.service;

import com.dev.dev.entity.Product;
import com.dev.dev.repository.ProductRepository;
import lombok.extern.slf4j.Slf4j;
import org.json.JSONArray;
import org.json.JSONObject;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;


import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CompletableFuture;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@Service
public class ProductService {
    private final ProductService self;
    private final ProductRepository productRepository;
    @Value("${naver.client.id:7zALpPUHFLIUrlLhcFOi}")
    private String NAVER_CLIENT_ID;
    @Value("${naver.client.secret:4GfMwG3hWC}")
    private String NAVER_CLIENT_SECRET;

    public ProductService(ProductRepository productRepository,
                          @Lazy ProductService self) {
        this.productRepository = productRepository;
        this.self = self;
    }

    /**
     * 네이버 쇼핑 검색 API 호출
     */
    private JSONObject callNaverApi(String query, int display, int start) throws Exception {
        String encoded = URLEncoder.encode(query, StandardCharsets.UTF_8);
        String apiURL =
                "https://openapi.naver.com/v1/search/shop.json?query=" + encoded
                        + "&display=" + display
                        + "&start=" + start;
        HttpURLConnection con = (HttpURLConnection) new URL(apiURL).openConnection();
        con.setRequestMethod("GET");
        con.setRequestProperty("X-Naver-Client-Id", NAVER_CLIENT_ID);
        con.setRequestProperty("X-Naver-Client-Secret", NAVER_CLIENT_SECRET);
        BufferedReader br = new BufferedReader(
                new InputStreamReader(con.getInputStream(), StandardCharsets.UTF_8)
        );
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) sb.append(line);
        br.close();
        con.disconnect();
        return new JSONObject(sb.toString());
    }
    /**
     * URL 기반으로 검색 API 호출 후 결과 로깅
     */
    public Product searchByUrl(String productUrl) {
        CompletableFuture<String> ret_val = CompletableFuture.supplyAsync(() -> {
            try {
                ProcessBuilder pb = new ProcessBuilder(
                        "/opt/pyenv/bin/python",
                        "/app/crawler/crawler.py",
                        productUrl
                );
                pb.environment().put("PYTHONIOENCODING", "utf-8");
                pb.redirectErrorStream(true);
                Process process = pb.start();
                BufferedReader reader =
                        new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8));
                String line;
                String result = null;
                while ((line = reader.readLine()) != null) {
                    result = line;
                }
                process.waitFor();
                return result;

            } catch (Exception e) {
                e.printStackTrace();
                return null;
            }
        });
        System.out.println(ret_val);
        String jsonStr;
        try {
            jsonStr = ret_val.get();
        } catch (Exception e) {
            throw new RuntimeException("Python 실행 실패", e);
        }
        if (jsonStr == null) throw new RuntimeException("Python 크롤러 JSON을 받지 못했습니다.");
        JSONObject obj = new JSONObject(jsonStr);
        String ogTitle = obj.optString("og_title");
        log.info("og:title = {}", ogTitle);
        if (ogTitle == null || ogTitle.isBlank()) throw new RuntimeException("og:title 파싱 실패");
        String productName = ogTitle.split(" : ")[0].trim();
        log.info("검색어로 사용할 상품명: {}", productName);
        Product product = null;
        try {
            int display = 100;
            int start = 1;
            int total = Integer.MAX_VALUE;
            JSONObject matchedItem = null;
            while (start <= total && start <= 1000) {
                JSONObject response = callNaverApi(productName, display, start);
                total = response.optInt("total", 0);
                JSONArray items = response.optJSONArray("items");
                if (items != null) {
                    for (int i = 0; i < items.length(); i++) {
                        JSONObject item = items.getJSONObject(i);
                        String title = item.optString("title").replaceAll("<.*?>", "").trim();
                        if (title.contains(productName)) {
                            matchedItem = item;
                            break;
                        }
                    }
                }
                if (matchedItem != null) break;
                start += display;
                Thread.sleep(200);
            }
            if (matchedItem != null) {
                long productId = matchedItem.optLong("productId");
                if (productRepository.existsById(productId)) {
                    throw new IllegalStateException("EXISTS");
                }
                product = self.createProductFromItem(matchedItem);
                productRepository.save(product);
            } else {
                log.info("매칭된 상품 없음");
            }
        } catch (Exception e) {
            log.error("검색 및 Product 생성 실패", e);
        }
        return product;
    }
    @Transactional
    public Product createProductFromItem(JSONObject item) {
        String title = item.optString("title").replaceAll("<.*?>", "").trim();
        Integer lprice = item.optInt("lprice", 0);
        Long productId = item.optLong("productId", 0L);
        Pattern pattern = Pattern.compile("(\\d+(?:\\.\\d+)?)\\s*(kg|g|개|팩)");
        Matcher matcher = pattern.matcher(title);
        int quantity = 1;
        String unit = null;
        while (matcher.find()) {
            String qtyStr = matcher.group(1);
            String matchedUnit = matcher.group(2);
            try {
                double qty = Double.parseDouble(qtyStr);
                if ("kg".equals(matchedUnit)) {
                    qty = qty * 1000;
                    matchedUnit = "g";
                }
                if (unit != null && ("개".equals(unit) || "팩".equals(unit))) {
                    continue;
                }
                Pattern afterPattern = Pattern.compile("g\\s*(개|팩)");
                Matcher afterMatcher = afterPattern.matcher(title);
                if ("g".equals(matchedUnit) && afterMatcher.find()) {
                    matchedUnit = afterMatcher.group(1);
                    qty = 1;
                }
                quantity = (int) Math.ceil(qty);
                unit = matchedUnit;
            } catch (NumberFormatException e) {
                quantity = 1;
            }
        }
        return Product.builder()
                .id(productId)
                .name(title)
                .price(lprice)
                .allQuantity(quantity)
                .link(item.optString("link"))
                .unit(unit)
                .build();
    }
}
