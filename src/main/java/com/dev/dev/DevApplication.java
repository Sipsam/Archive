package com.dev.dev;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages = "com.dev.dev")
public class DevApplication {
    public static void main(String[] args) {
        SpringApplication.run(DevApplication.class, args);
    }
}

