package com.dev.dev.controller;

import com.dev.dev.service.ProductService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/groupbuys")
@RequiredArgsConstructor
public class ProductController {

    private final ProductService productService;

    @GetMapping("/attempt")
    public String attemptRegister(@RequestParam String url) {
        return productService.registerProduct(url);
    }
}
