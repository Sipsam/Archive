package com.dev.dev.service;

import com.dev.dev.entity.GroupBuyStatus;
import com.dev.dev.entity.OnlineGroupBuy;
import com.dev.dev.entity.OnlineParticipation;
import com.dev.dev.entity.PaymentStatus;
import com.dev.dev.repository.OnlineParticipationRepository;
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

    private String widgetSecretKey = "test_sk_LlDJaYngro1dl0enY2bn3ezGdRpX";

    @Transactional
    public JSONObject confirmPayment(String jsonBody) throws Exception {
        // ... (1. 파싱 로직 기존과 동일) ...
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

        // ... (2. API 호출 준비 기존과 동일) ...
        JSONObject obj = new JSONObject();
        obj.put("orderId", orderId);
        obj.put("amount", amount);
        obj.put("paymentKey", paymentKey);

        Base64.Encoder encoder = Base64.getEncoder();
        byte[] encodedBytes = encoder.encode((widgetSecretKey + ":").getBytes(StandardCharsets.UTF_8));
        String authorizations = "Basic " + new String(encodedBytes);

        // ... (3. API 호출 기존과 동일) ...
        URL url = new URL("https://api.tosspayments.com/v1/payments/confirm");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestProperty("Authorization", authorizations);
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);

        try (OutputStream outputStream = connection.getOutputStream()) {
            outputStream.write(obj.toString().getBytes(StandardCharsets.UTF_8));
        }

        int code = connection.getResponseCode();
        boolean isSuccess = code == 200;

        InputStream responseStream = isSuccess ? connection.getInputStream() : connection.getErrorStream();
        Reader reader = new InputStreamReader(responseStream, StandardCharsets.UTF_8);
        JSONObject jsonObject = (JSONObject) parser.parse(reader);
        responseStream.close();

        // 4. 결제 성공 시 비즈니스 로직 처리
        if (isSuccess) {
            updateParticipationStatus(orderId);
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
                // throw new IllegalStateException("결제 진행 중인 공구가 아닙니다.");
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
            // GroupBuyStatus에 COMPLETED가 있다고 가정
            groupBuy.setStatus(GroupBuyStatus.COMPLETED);
        }
    }
}
