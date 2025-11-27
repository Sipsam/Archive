package com.dev.dev.service;

import com.dev.dev.entity.Product;
import com.dev.dev.repository.ProductRepository;
import io.github.bonigarcia.wdm.WebDriverManager;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.json.JSONArray;
import org.json.JSONObject;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.support.ui.ExpectedCondition;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.*;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;

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
    private String extractOgTitle(String url) {
        WebDriverManager.chromedriver().setup();
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless=new");
        options.addArguments("--no-sandbox");
        options.addArguments("--disable-dev-shm-usage");
        options.addArguments("--disable-gpu");
        options.addArguments("--window-size=1920,1080");

        WebDriver driver = null;
        try {
            driver = new ChromeDriver(options);
            driver.get(url);
            boolean ogExists = false;
            for (int i = 0; i < 15; i++) {
                Object exists = ((JavascriptExecutor) driver)
                        .executeScript("return document.querySelector('meta[property=\"og:title\"]') !== null;");
                if (exists instanceof Boolean && (Boolean) exists) {
                    ogExists = true;
                    break;
                }
                Thread.sleep(1000);
            }
            String pageHtml = driver.getPageSource();
            System.out.println("===== Selenium 페이지 소스 =====");
            System.out.println(pageHtml);
            if (!ogExists) {
                log.error("meta[property='og:title'] 존재하지 않음");
                return null;
            }
            String html = driver.getPageSource();
            Document doc = Jsoup.parse(html);
            Element ogTag = doc.selectFirst("meta[property=og:title]");
            if (ogTag == null) {
                log.error("meta[property='og:title'] 파싱 실패");
                return null;
            }
            String fullOgTitle = ogTag.attr("content");
            if (fullOgTitle.contains(" : ")) {
                return fullOgTitle.split(" : ")[0].trim();
            }
            return fullOgTitle.trim();
        } catch (Exception e) {
            log.error("Selenium 크롤링 실패: {}", e.getMessage());
            return null;
        } finally {
            if (driver != null) {
                driver.quit();
            }
        }
    }
    private JSONObject searchInNaverShopping(String ogTitle) throws Exception {
        int display = 100;
        int start = 1;
        while (start <= 1000) {
            JSONObject res = callNaverApi(ogTitle, display, start);
            JSONArray items = res.getJSONArray("items");
            for (int i = 0; i < items.length(); i++) {
                JSONObject item = items.getJSONObject(i);
                String apiTitle = item.getString("title")
                        .replaceAll("<.*?>", "")
                        .trim();
                if (apiTitle.equals(ogTitle)) {
                    log.info("매칭 성공: {}", apiTitle);
                    return item;
                }
            }
            start += display;
            Thread.sleep(200);
        }
        return null;
    }
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
    public JSONObject findProductFromUrl(String productUrl) throws Exception {
        String ogTitle = extractOgTitle(productUrl);
        if (ogTitle == null) return null;
        return searchInNaverShopping(ogTitle);
    }
}