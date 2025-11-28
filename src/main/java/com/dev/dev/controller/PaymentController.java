// 기존 코드 유지
package com.dev.dev.controller;

import com.dev.dev.service.OnlineGroupBuyService;
import com.dev.dev.service.PaymentService;
import com.dev.dev.security.JwtUtil;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.json.simple.JSONObject;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/payment")
@RequiredArgsConstructor
public class PaymentController {

    private final PaymentService paymentService;
    private final OnlineGroupBuyService groupBuyService;
    private final JwtUtil jwtUtil;

    private Long extractUserId(HttpServletRequest request) {
        String header = request.getHeader("Authorization");
        if (header == null) throw new IllegalArgumentException("Token Required");
        return jwtUtil.getUserIdFromToken(header);
    }

    // 1. 결제 승인 요청
    @PostMapping("/confirm")
    public ResponseEntity<JSONObject> confirmPayment(@RequestBody String jsonBody) throws Exception {
        return ResponseEntity.ok(paymentService.confirmPayment(jsonBody));
    }

    // 2. 방장의 결제 시작
    @PostMapping("/start/{groupBuyId}")
    public ResponseEntity<String> startPaymentProcess(
            HttpServletRequest request,
            @PathVariable Long groupBuyId) {
        Long userId = extractUserId(request);
        groupBuyService.startPaymentProcess(userId, groupBuyId);
        return ResponseEntity.ok("결제 프로세스가 시작되었습니다. (참여자별 수량 계산 완료)");
    }
}
