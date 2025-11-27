package com.dev.dev.service;

import lombok.extern.slf4j.Slf4j;
import org.json.JSONArray;
import org.json.JSONObject;
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

            JSONObject response = callNaverApi(query, 10, 1);
            log.info("네이버 쇼핑 검색 API response: {}", response.toString(2));

            // 결과 items 배열 로그
            JSONArray items = response.optJSONArray("items");
            if (items != null) {
                for (int i = 0; i < items.length(); i++) {
                    JSONObject item = items.getJSONObject(i);
                    log.info("상품 {}: {}", i + 1, item.toString());
                }
            }
        } catch (Exception e) {
            log.error("검색 API 호출 실패: {}", e.getMessage());
        }
    }
}
