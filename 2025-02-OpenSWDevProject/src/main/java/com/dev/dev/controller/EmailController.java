package com.dev.dev.controller;

import com.dev.dev.dto.email.EmailQARequest;
import com.dev.dev.entity.User;
import com.dev.dev.repository.UserRepository;
import com.dev.dev.service.EmailService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;
import com.dev.dev.security.JwtUtil;

@RestController
@RequiredArgsConstructor
public class EmailController {
    private final EmailService emailService;
    private final UserRepository userRepository;
    private final JwtUtil jwtUtil;
    private static final String QA_TEMPLATE_ID = "d-3657637c55f64a91ab5594fd11394614";

    @PostMapping("/api/email")
    public ResponseEntity<?> sendMail(
            @RequestBody EmailQARequest req,
            @RequestHeader("Authorization") String authorizationHeader
    ) {
        String token = authorizationHeader.startsWith("Bearer ") ? authorizationHeader.substring(7) : authorizationHeader;
        Long userId = jwtUtil.getUserIdFromToken(token);
        if (userId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Invalid or missing token");
        }
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("유저 없음"));
        emailService.sendQAEmail(
                user.getName(),
                user.getEmail(),
                req.getTitle(),
                req.getMessage(),
                QA_TEMPLATE_ID
        );
        return ResponseEntity.ok("sent");
    }
}

