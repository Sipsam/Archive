package com.dev.dev.service;

import com.dev.dev.entity.Product;
import com.dev.dev.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.json.JSONArray;
import org.json.JSONObject;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class ProductService {

    private final ProductRepository productRepository;

    // application.yml에서 주입 (보안 강화)
    @Value("${naver.client.id:7zALpPUHFLIUrlLhcFOi}")
    private String NAVER_CLIENT_ID;

    @Value("${naver.client.secret:4GfMwG3hWC}")
    private String NAVER_CLIENT_SECRET;

    public List<Product> findAll() {
        return productRepository.findAll();
    }

    public Optional<Product> findById(Long id) {
        return productRepository.findById(id);
    }

    public Product save(Product product) {
        return productRepository.save(product);
    }

    public void delete(Long id) {
        productRepository.deleteById(id);
    }

    // ===== 상품 URL에서 정보 추출 =====
    public JSONObject findProductFromUrl(String productUrl) throws Exception {
        log.info("상품 URL 분석 시작: {}", productUrl);
        String ogTitle = extractOgTitle(productUrl);
        if (ogTitle == null || ogTitle.isEmpty()) {
            log.warn("OG Title을 찾을 수 없습니다.");
            return null;
        }
        log.info("OG Title 추출 성공: {}", ogTitle);
        JSONObject matchedProduct = searchInNaverShopping(ogTitle);
        if (matchedProduct != null) {
            log.info("매칭된 상품 찾기 성공!");
        } else {
            log.warn("매칭된 상품을 찾지 못했습니다.");
        }
        return matchedProduct;
    }
    private String extractOgTitle(String url) throws IOException {
        int maxRetries = 3;
        int retryDelay = 2000;
        int attempt = 1;
        for (; attempt <= maxRetries; attempt++) {
            try {
                System.out.println("크롤링 시도 #" + attempt + ": " + url);
                Document doc = Jsoup.connect(url)
                        .userAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                        .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8")
                        .header("Accept-Language", "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7")
                        .header("Accept-Encoding", "gzip, deflate, br")
                        .header("Connection", "keep-alive")
                        .header("Upgrade-Insecure-Requests", "1")
                        .header("Sec-Fetch-Dest", "document")
                        .header("Sec-Fetch-Mode", "navigate")
                        .header("Sec-Fetch-Site", "none")
                        .header("Sec-Fetch-User", "?1")
                        .header("Cache-Control", "max-age=0")
                        .referrer("https://www.google.com/")
                        .timeout(15000)
                        .ignoreHttpErrors(true)
                        .followRedirects(true)
                        .get();
                log.debug("크롤링 성공: {}", doc);
                Element ogTitleTag = doc.selectFirst("meta[property=og:title]");
                if (ogTitleTag == null) {
                    log.warn("og:title 메타 태그가 없습니다. 일반 title 태그 사용.");
                    return doc.title();
                }
                String fullOgTitle = ogTitleTag.attr("content");
                log.debug("원본 OG Title: {}", fullOgTitle);
                if (fullOgTitle.contains(" : ")) {
                    return fullOgTitle.split(" : ")[0].trim();
                }
                return fullOgTitle.trim();
            } catch (IOException e) {
                log.error("크롤링 실패: {}", e.getMessage());
                throw e;
            }
        }
        return "";
    }
    private JSONObject searchInNaverShopping(String ogTitle) throws Exception {
        int display = 100;
        int start = 1;
        int maxStart = 1000;
        log.info("네이버 쇼핑 검색 시작: 검색어=[{}]", ogTitle);
        while (start <= maxStart) {
            log.debug("페이지 요청: start={}, display={}", start, display);
            JSONObject response = callNaverApi(ogTitle, display, start);
            JSONArray items = response.getJSONArray("items");
            log.debug("응답 상품 수: {}", items.length());
            for (int i = 0; i < items.length(); i++) {
                JSONObject item = items.getJSONObject(i);
                String apiTitle = item.getString("title")
                        .replaceAll("<[^>]*>", "")
                        .trim();
                log.trace("[{}] API Title: {}", i + 1, apiTitle);
                if (apiTitle.equals(ogTitle)) {
                    log.info("정확히 일치하는 상품 발견! (start={})", start);
                    return item;
                }
            }
            start += display;
            Thread.sleep(200);
        }
        log.warn("1000개 상품 검색 완료, 매칭 실패");
        return null;
    }
    public JSONObject callNaverApi(String query, int display, int start) throws Exception {
        String encodedQuery = URLEncoder.encode(query, StandardCharsets.UTF_8);
        String apiURL = String.format(
                "https://openapi.naver.com/v1/search/shop.json?query=%s&display=%d&start=%d",
                encodedQuery, display, start
        );
        log.debug("API 요청: {}", apiURL);
        HttpURLConnection con = (HttpURLConnection) new URL(apiURL).openConnection();
        con.setRequestMethod("GET");
        con.setRequestProperty("X-Naver-Client-Id", NAVER_CLIENT_ID);
        con.setRequestProperty("X-Naver-Client-Secret", NAVER_CLIENT_SECRET);
        int responseCode = con.getResponseCode();
        if (responseCode != 200) {
            log.error("API 오류: HTTP {}", responseCode);
            throw new RuntimeException("네이버 API 오류: " + responseCode);
        }
        BufferedReader br = new BufferedReader(
                new InputStreamReader(con.getInputStream(), StandardCharsets.UTF_8)
        );
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) {
            sb.append(line);
        }
        br.close();
        con.disconnect();
        JSONObject jsonResponse = new JSONObject(sb.toString());
        log.debug("API 응답 성공");
        return jsonResponse;
    }
    public JSONObject findProductWithSimilarity(String productUrl) throws Exception {
        String ogTitle = extractOgTitle(productUrl);
        if (ogTitle == null || ogTitle.isEmpty()) {
            return null;
        }
        log.info("유사도 기반 검색 시작: {}", ogTitle);
        JSONObject response = callNaverApi(ogTitle, 100, 1);
        JSONArray items = response.getJSONArray("items");
        JSONObject bestMatch = null;
        double highestSimilarity = 0.0;
        for (int i = 0; i < items.length(); i++) {
            JSONObject item = items.getJSONObject(i);
            String apiTitle = item.getString("title")
                    .replaceAll("<[^>]*>", "")
                    .trim();

            double similarity = calculateSimilarity(ogTitle, apiTitle);

            if (similarity > highestSimilarity) {
                highestSimilarity = similarity;
                bestMatch = item;
            }
        }
        log.info("최고 유사도: {} (상품: {})",
                highestSimilarity,
                bestMatch != null ? bestMatch.getString("title") : "없음");
        return bestMatch;
    }
    private double calculateSimilarity(String str1, String str2) {
        Set<String> set1 = new HashSet<>(Arrays.asList(str1.toLowerCase().split("\\s+")));
        Set<String> set2 = new HashSet<>(Arrays.asList(str2.toLowerCase().split("\\s+")));
        Set<String> intersection = new HashSet<>(set1);
        intersection.retainAll(set2);
        Set<String> union = new HashSet<>(set1);
        union.addAll(set2);
        return union.isEmpty() ? 0.0 : (double) intersection.size() / union.size();
    }
}