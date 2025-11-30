package com.dev.dev.service;

import com.dev.dev.entity.Product;
import com.dev.dev.repository.ProductRepository;
import io.github.bonigarcia.wdm.WebDriverManager;
import jakarta.transaction.Transactional;
import lombok.extern.slf4j.Slf4j;
import org.json.JSONArray;
import org.json.JSONObject;
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Arrays;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@Service
public class ProductService {
    private final ProductRepository productRepository;
    @Value("${naver.client.id:7zALpPUHFLIUrlLhcFOi}")
    private String NAVER_CLIENT_ID;
    @Value("${naver.client.secret:4GfMwG3hWC}")
    private String NAVER_CLIENT_SECRET;

    public ProductService(ProductRepository productRepository) {
        this.productRepository = productRepository;
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
        WebDriverManager.chromedriver().setup();
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--disable-gpu");
        options.addArguments("--no-sandbox");
        options.addArguments("--disable-dev-shm-usage");
        options.addArguments("--window-size=1920,1080");
        options.addArguments("--disable-blink-features=AutomationControlled");
        options.addArguments("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36");
        options.setExperimentalOption("excludeSwitches", Arrays.asList("enable-automation"));
        options.setExperimentalOption("useAutomationExtension", false);
        WebDriver driver = new ChromeDriver(options);
        ((JavascriptExecutor) driver).executeScript(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        );
        ((JavascriptExecutor) driver).executeScript(
                "Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']})"
        );
        ((JavascriptExecutor) driver).executeScript(
                "Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]})"
        );
        Product product = null;
        try {
            // 1. 페이지 접속 후 og:title 추출
            driver.get(productUrl);
            log.info("페이지 로드 완료: {}", driver.getPageSource());
            WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
            wait.until(ExpectedConditions.presenceOfElementLocated(By.cssSelector("meta[property='og:title']")));
            String ogTitle = driver.findElement(By.cssSelector("meta[property='og:title']")).getAttribute("content");
            log.info("og:title: {}", ogTitle);
            // 2. ':' 기준으로 분리
            String[] parts = ogTitle.split(" : ");
            String productName = parts[0].trim();
            log.info("검색어로 사용할 상품명: {}", productName);
            // 3. Naver 쇼핑 API 반복 호출
            int display = 100;
            int start = 1;
            int total = Integer.MAX_VALUE;
            JSONObject matchedItem = null;
            while (start <= total && start <= 1000) {
                JSONObject response = callNaverApi(productName, display, start);
                log.info("API 호출 start={} display={}", start, display);
                log.info("response: {}", response.toString(2));
                total = response.optInt("total", 0);
                JSONArray items = response.optJSONArray("items");
                if (items != null) {
                    for (int i = 0; i < items.length(); i++) {
                        JSONObject item = items.getJSONObject(i);
                        String title = item.optString("title").replaceAll("<.*?>", "").trim();
                        log.info("상품 {}: {}", start + i, title);
                        if (title.contains(productName)) {
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
            if (matchedItem != null) {
                if (productRepository.existsById(matchedItem.optLong("productId"))) {
                    throw new IllegalStateException("EXISTS");
                }
                product = createProductFromItem(matchedItem);
                productRepository.save(product);
                log.info("생성된 Product: {}", product);
            } else {
                log.info("매칭된 상품 없음");
            }
        } catch (Exception e) {
            log.error("검색 및 Product 생성 실패", e);
        } finally {
            driver.quit();
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
