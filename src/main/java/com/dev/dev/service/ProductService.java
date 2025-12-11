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
import java.util.ArrayList;
import java.util.List;
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
    public Product findById(Long id) {
        return productRepository.findById(id).orElse(null);
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

    private String executePythonCrawler(String productUrl) {
        try {
            ProcessBuilder pb = new ProcessBuilder(
                    "/opt/pyenv/bin/python",
                    "/app/crawler/crawler.py",
                    productUrl
            );
            pb.environment().put("PYTHONIOENCODING", "utf-8");
            pb.redirectErrorStream(true);
            Process process = pb.start();
            String lastLine = null;
            try (BufferedReader reader =
                         new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    lastLine = line;
                }
            }
            int exitCode = process.waitFor();
            if (exitCode != 0) throw new IllegalStateException("Python crawler exited with code: " + exitCode);
            return lastLine;
        } catch (Exception e) {
            throw new RuntimeException("Python crawler execution failed", e);
        }
    }

    private String normalizeTitleForSearch(String rawTitle) {
        if (rawTitle == null) return "";
        String t = rawTitle;
        t = removeOriginInfo(t);
        t = t.replace("<br>", " ")
                .replace("</br>", " ")
                .replace("<br/>", " ")
                .replace("<br />", " ");
        t = t.replaceAll("<[^>]*>", " ");
        t = t.replaceAll("\\s+", " ").trim();
        return t;
    }

    private String removeOriginInfo(String title) {
        if (title == null) return "";
        String t = title;
        t = t.replaceAll("\\[[^\\]]*원산지[^\\]]*\\]", " ");
        t = t.replaceAll("\\s+", " ").trim();
        t = t.split(" : ")[0].trim();
        t = t.split("\\s*\\|\\s*")[0].trim();
        t = t.replaceAll("\\s+", " ").trim();
        return t;
    }

    private Product searchAndCreateProduct(String productName, String extractedId) {
        if (productName == null || productName.isBlank()) return null;
        productName = productName.trim();
        productName = removeOriginInfo(productName);
        log.info("Trying search with product name: {}", productName);
        try {
            int display = 100;
            int start = 1;
            int total = Integer.MAX_VALUE;
            JSONObject matchedItem = null;
            while (start <= total && start <= 1000 && matchedItem == null) {
                JSONObject response = callNaverApi(productName, display, start);
                total = response.optInt("total", 0);
                JSONArray items = response.optJSONArray("items");
                if (items != null) {
                    for (int i = 0; i < items.length(); i++) {
                        JSONObject item = items.getJSONObject(i);
                        String rawTitle = item.optString("title", "").trim();
                        String link = item.optString("link", "").trim();
                        String normalizedTitle = normalizeTitleForSearch(rawTitle);
                        if (!link.isBlank() && link.contains(extractedId)) {
                            matchedItem = item;
                            log.info("URL match success (query={}, link={})", productName, link);
                            break;
                        }
                        if (normalizedTitle.contains(productName)) {
                            matchedItem = item;
                            log.info("Title match success (query={}, title={})", productName, normalizedTitle);
                            break;
                        }
                    }
                }
                if (matchedItem == null) {
                    start += display;
                    Thread.sleep(200);
                }
            }
            if (matchedItem != null) {
                long productId = matchedItem.optLong("productId");
                if (productRepository.existsById(productId)) throw new IllegalStateException("EXISTS");
                Product product = self.createProductFromItem(matchedItem);
                productRepository.save(product);
                return product;
            } else {
                log.info("No matched item for query: {}", productName);
            }
        } catch (Exception e) {
            log.error("Failed to search and create product for query: {}", productName, e);
        }
        return null;
    }

    public Product searchByUrl(String productUrl) {
        String extractedId = extractProductIdFromUrl(productUrl);
        if (extractedId == null) throw new RuntimeException("could not extract product id from url");
        log.info("extracted Id = {}", extractedId);
        String jsonStr = executePythonCrawler(productUrl);
        if (jsonStr == null) throw new RuntimeException("could not get json from Python crawler");
        JSONObject obj = new JSONObject(jsonStr);
        log.info("Crawling result : \n{}", obj.toString(2));
        String title_t = obj.optString("title", "").trim();
        String ogTitle = obj.optString("og_title", "").trim();
        List<String> candidateNames = new ArrayList<>();
        if (!title_t.isBlank()) candidateNames.add(title_t.split(" : ")[0].trim());
        if (!ogTitle.isBlank()) {
            String fromOg = ogTitle.split(" : ")[0].trim();
            if (candidateNames.stream().noneMatch(c -> c.equals(fromOg))) candidateNames.add(fromOg);
        }
        if (candidateNames.isEmpty()) throw new RuntimeException("no usable title from crawler");
        Product product = null;
        for (String candidate : candidateNames) {
            product = searchAndCreateProduct(candidate, extractedId);
            if (product != null) break;
        }
        if (product == null) log.info("do not find matched item for url: {}", productUrl);
        return product;
    }
    @Transactional
    public Product createProductFromItem(JSONObject item) {
        String title = item.optString("title").replaceAll("<.*?>", "").trim();
        Integer lprice = item.optInt("lprice", 0);
        Long productId = item.optLong("productId", 0L);

        String imageUrl = item.optString("image");  // ★ 추가

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
                .imageUrl(imageUrl)   // ★ 이미지 저장!
                .build();
    }
    private String extractProductIdFromUrl(String url) {
        Pattern pattern = Pattern.compile("/products/(\\d+)");
        Matcher matcher = pattern.matcher(url);
        if (matcher.find()) {
            return matcher.group(1);
        }
        return null;
    }
}
