package com.dev.dev.service;

import com.dev.dev.entity.*;
import com.dev.dev.repository.OnlineParticipationRepository;
import com.dev.dev.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

@Service
@RequiredArgsConstructor
public class PaymentService {

    private final OnlineParticipationRepository participationRepository;
    private final UserRepository userRepository; // [추가] 포인트 업데이트를 위해 필요

    private String widgetSecretKey = "test_GROQ_API_KEY_REMOVED";

    @Transactional
    public JSONObject confirmPayment(String jsonBody) throws Exception {
        // 공구 결제는 포인트 충전이 아니므로(false), userId는 null로 넘김 (orderId로 식별 가능)
        return processPayment(jsonBody, false, null);
    }

    /**
     * 2. 포인트 충전 결제 승인 (추가된 기능)
     * 프론트엔드에서 포인트 충전창을 통해 결제했을 때 호출됨
     */
    @Transactional
    public JSONObject chargePoint(String jsonBody, Long userId) throws Exception {
        // 포인트 충전이므로(true), userId를 넘겨서 해당 유저의 포인트를 증가시킴
        return processPayment(jsonBody, true, userId);
    }


    /**
     * [핵심 로직] 토스 페이먼츠 API 호출 및 결과 처리 공통 메서드
     */
    private JSONObject processPayment(String jsonBody, boolean isPointCharge, Long userId) throws Exception {
        // 1. JSON 파싱
        JSONParser parser = new JSONParser();
        String orderId;
        String amount;
        String paymentKey;

        try {
            JSONObject requestData = (JSONObject) parser.parse(jsonBody);
            paymentKey = (String) requestData.get("paymentKey");
            orderId = (String) requestData.get("orderId");
            amount = (String) requestData.get("amount");
        } catch (ParseException e) {
            throw new RuntimeException("JSON 파싱 에러", e);
        }

        // 2. 토스 API 호출 준비
        JSONObject obj = new JSONObject();
        obj.put("orderId", orderId);
        obj.put("amount", amount);
        obj.put("paymentKey", paymentKey);

        Base64.Encoder encoder = Base64.getEncoder();
        byte[] encodedBytes = encoder.encode((widgetSecretKey + ":").getBytes(StandardCharsets.UTF_8));
        String authorizations = "Basic " + new String(encodedBytes);

        URL url = new URL("https://api.tosspayments.com/v1/payments/confirm");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestProperty("Authorization", authorizations);
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);

        try (OutputStream outputStream = connection.getOutputStream()) {
            outputStream.write(obj.toString().getBytes(StandardCharsets.UTF_8));
        }

        // 3. API 응답 처리
        int code = connection.getResponseCode();
        boolean isSuccess = code == 200;

        InputStream responseStream = isSuccess ? connection.getInputStream() : connection.getErrorStream();
        Reader reader = new InputStreamReader(responseStream, StandardCharsets.UTF_8);
        JSONObject jsonObject = (JSONObject) parser.parse(reader);
        responseStream.close();

        // 4. 결제 성공 시 DB 업데이트 (분기 처리)
        if (isSuccess) {
            if (isPointCharge) {
                // A. 포인트 충전인 경우 -> 유저 포인트 증가
                updateUserPoint(userId, Integer.parseInt(amount));
            } else {
                // B. 공구 결제인 경우 -> 참여 상태 변경 및 공구 마감 체크
                updateParticipationStatus(orderId);
            }
        } else {
            throw new RuntimeException("결제 승인 실패: " + jsonObject.toString());
        }

        return jsonObject;
    }


    private void updateParticipationStatus(String orderId) {
        try {
            // orderId 파싱 (예: "PART_123")
            String[] parts = orderId.split("_");
            Long participationId = Long.parseLong(parts[1]);

            OnlineParticipation participation = participationRepository.findById(participationId)
                    .orElseThrow(() -> new IllegalArgumentException("참여 정보를 찾을 수 없습니다."));

            // [추가된 검증] 공구가 현재 결제 진행 중인지 확인 (안전장치)
            if (participation.getOnlineGroupBuy().getStatus() != GroupBuyStatus.IN_PROGRESS) {
                // 이미 끝났거나 시작 안 한 공구에 결제 시도 시 예외 처리 (혹은 로그)
                throw new IllegalStateException("결제 진행 중인 공구가 아닙니다.");
            }

            // 1. 개인 상태 변경 (PENDING -> COMPLETED)
            participation.setPaymentStatus(PaymentStatus.PAID);

            // 2. [핵심 추가] 모든 참여자가 결제했는지 확인 후 공구 상태 변경
            checkAndCompleteGroupBuy(participation.getOnlineGroupBuy());

        } catch (Exception e) {
            e.printStackTrace();
            throw new RuntimeException("결제 후 상태 업데이트 실패");
        }
    }

    // [새로 추가된 메서드]
    private void checkAndCompleteGroupBuy(OnlineGroupBuy groupBuy) {
        // 모든 참여자의 결제 상태가 PAID인지 확인
        boolean allPaid = groupBuy.getParticipationList().stream()
                .allMatch(p -> p.getPaymentStatus() == PaymentStatus.PAID);

        if (allPaid) {
            // 모두 결제했다면 공구 상태를 '완료(COMPLETED)' 또는 '배송준비(PREPARING)' 등으로 변경
            // GroupBuyStatus에 COMPLETED
            groupBuy.setStatus(GroupBuyStatus.COMPLETED);
        }
    }

    // [NEW] 유저 포인트 증가 로직
    private void updateUserPoint(Long userId, int amount) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));

        int currentPoint = user.getPoints() == null ? 0 : user.getPoints();
        user.setPoints(currentPoint + amount);

        // Dirty Checking으로 자동 저장됨
    }
}
