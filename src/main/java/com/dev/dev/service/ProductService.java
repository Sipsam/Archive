package com.dev.dev.service;

import io.github.bonigarcia.wdm.WebDriverManager;
import lombok.extern.slf4j.Slf4j;
import org.json.JSONArray;
import org.json.JSONObject;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

@Slf4j
@Service
public class ProductService {

    @Value("${naver.client.id:7zALpPUHFLIUrlLhcFOi}")
    private String NAVER_CLIENT_ID;

    @Value("${naver.client.secret:4GfMwG3hWC}")
    private String NAVER_CLIENT_SECRET;

    /**
     * URL에서 n_query 추출
     */
    private String extractQueryFromUrl(String url) {
        try {
            String[] parts = url.split("[?&]");
            for (String part : parts) {
                if (part.startsWith("n_query=")) {
                    return java.net.URLDecoder.decode(part.substring(8), StandardCharsets.UTF_8);
                }
            }
        } catch (Exception e) {
            log.error("n_query 추출 실패: {}", e.getMessage());
        }
        return null;
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
    public void searchByUrl(String productUrl) {
        try {
            String query = extractQueryFromUrl(productUrl);
            if (query == null) {
                log.error("검색어 추출 실패");
                return;
            }
            log.info("추출된 검색어: {}", query);
            int display = 100; // 한 번에 100개씩 가져오기 (최대)
            int start = 1;
            int total = Integer.MAX_VALUE; // 총 검색 결과
            String targetTitle = "클라 섬유유연제 대용량 고농축 퍼퓸 라이프케어 플라워가든";
            JSONObject matchedItem = null;
            while (start <= total && start <= 1000) { // 최대 1000개까지만
                JSONObject response = callNaverApi(query, display, start);
                log.info("API 호출 start={} display={}", start, display);
                log.info("response: {}", response.toString(2));
                total = response.optInt("total", 0);
                JSONArray items = response.optJSONArray("items");
                if (items != null) {
                    for (int i = 0; i < items.length(); i++) {
                        JSONObject item = items.getJSONObject(i);
                        String title = item.optString("title").replaceAll("<.*?>", "").trim();
                        log.info("상품 {}: {}", start + i, title);
                        if (title.contains(targetTitle)) {
                            matchedItem = item;
                            break;
                        }
                    }
                }
                if (matchedItem != null) {
                    log.info("매칭된 상품 발견: {}", matchedItem.toString(2));
                    break;
                }
                start += display;
                Thread.sleep(200);
            }
            if (matchedItem == null) {
                log.info("매칭된 상품 없음");
            }
        } catch (Exception e) {
            log.error("검색 API 호출 실패: {}", e.getMessage());
        }
        WebDriverManager.chromedriver().setup();
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless=new");
        options.addArguments("--no-sandbox");
        options.addArguments("--disable-dev-shm-usage");
        options.addArguments("--disable-gpu");
        options.addArguments("--window-size=1920,1080");
        WebDriver driver = new ChromeDriver(options);
        try {
            driver.get(productUrl);
            Thread.sleep(3000);
            String html = driver.getPageSource();
            log.info("추출된 html: {}", html);
        } catch (Exception e) {
            e.printStackTrace();
            log.error("html 추출 실패");
        } finally {
            driver.quit();
        }
    }
}
