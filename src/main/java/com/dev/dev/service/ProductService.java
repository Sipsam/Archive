package com.dev.dev.service;

import com.dev.dev.entity.Product;
import com.dev.dev.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLEncoder;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ProductService {

    private final ProductRepository productRepository;

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

    private final String NAVER_CLIENT_ID = "AN9TaXRlbzATdnmERqWg";
    private final String NAVER_CLIENT_SECRET = "WgV1Isj_ne";
    public String registerProduct(String productUrl) {
        try {
            String query = extractQueryFromUrl(productUrl);
            System.out.println( "Query : " + query );
            JSONObject item = callNaverApi(query);
            System.out.println("item: " + item);
            if (item == null) return "failed";
            Product product = new Product();
            product.setName(item.getString("title").replaceAll("<.*?>", ""));
            product.setPrice(item.getInt("lprice"));
            product.setAllQuantity(0);
            productRepository.save(product);
            return "success";
        } catch (Exception e) {
            e.printStackTrace();
            return "failed";
        }
    }
    private String extractQueryFromUrl(String url) throws MalformedURLException {
        String query = new URL(url).getQuery();
        Map<String, String> map = Arrays.stream(query.split("&"))
                .map(param -> param.split("=", 2))
                .collect(Collectors.toMap(a -> a[0], a -> a[1]));
        return map.get("n_query");
    }
    private JSONObject callNaverApi(String query) throws IOException {
        HttpURLConnection con = (HttpURLConnection) new URL(
                "https://openapi.naver.com/v1/search/shop.json?query=" + URLEncoder.encode(query, "UTF-8") + "&display=1"
        ).openConnection();
        con.setRequestMethod("GET");
        con.setRequestProperty("X-Naver-Client-Id", NAVER_CLIENT_ID);
        con.setRequestProperty("X-Naver-Client-Secret", NAVER_CLIENT_SECRET);
        int responseCode = con.getResponseCode();
        System.out.println("Response Code: " + responseCode);
        BufferedReader br = new BufferedReader(new InputStreamReader(
                responseCode == 200 ? con.getInputStream() : con.getErrorStream()
        ));
        StringBuilder response = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) response.append(line);
        br.close();
        try {
            JSONObject json = new JSONObject(response.toString());
            JSONArray items = json.getJSONArray("items");
            return items.length() == 0 ? null : items.getJSONObject(0);
        } catch (JSONException e) {
            return null;
        }
    }
}
