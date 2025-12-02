package com.dev.dev.websocket;

import com.dev.dev.dto.chat.ChatMessageDto;
import com.dev.dev.entity.User;
import com.dev.dev.service.ChatMessageService;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.*;
import java.util.HashMap;
import java.util.Map;
import com.dev.dev.entity.ChatMessage;

import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

@Slf4j
@Component
@RequiredArgsConstructor
public class ChatWebSocketHandler extends TextWebSocketHandler {

    private final ChatMessageService chatMessageService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    // 연결된 세션들 관리 (사이드바는 NEW_MESSAGE 신호만 받으면 되기 때문에 전체 브로드캐스트)
    private final Set<WebSocketSession> sessions = Collections.synchronizedSet(new HashSet<>());

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        sessions.add(session);
        log.info("WebSocket connected: {}", session.getId());
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessions.remove(session);
        log.info("WebSocket disconnected: {}", session.getId());
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws IOException {
        try {
            ChatMessageDto dto = objectMapper.readValue(message.getPayload(), ChatMessageDto.class);

            // 핸드셰이크에서 저장한 user 꺼내기
            User user = (User) session.getAttributes().get("user");
            if (user == null) {
                log.warn("Unauthenticated WebSocket message");
                session.close();
                return;
            }

            if ("CHAT".equalsIgnoreCase(dto.getType())) {
                // DB에 메시지 저장
                chatMessageService.saveFromDto(dto, user.getId());
		// ================= [수정된 부분 시작] =================
                // 2. 채팅방에 있는 모든 클라이언트에게 '메시지 내용' 전송 (Type: CHAT)
                Map<String, Object> chatPayload = new HashMap<>();
                chatPayload.put("type", "CHAT");
                chatPayload.put("roomId", dto.getRoomId());
                chatPayload.put("senderId", user.getId());
                chatPayload.put("senderNickname", user.getNickname());
                chatPayload.put("message", dto.getMessage());
                chatPayload.put("sentAt", savedMsg.getSentAt().toString()); // 시간 정보 포함

                String jsonPayload = objectMapper.writeValueAsString(chatPayload);
                TextMessage textMessage = new TextMessage(jsonPayload);

                synchronized (sessions) {
                    for (WebSocketSession s : sessions) {
                        if (s.isOpen()) {
                            // 간단한 구현을 위해 전체 브로드캐스트 (프론트에서 roomId로 필터링함)
                            try {
                                s.sendMessage(textMessage);
                            } catch (Exception e) {
                                log.error("Error sending message", e);
                            }
                        }
                    }
                }

                // 모든 클라이언트에게 NEW_MESSAGE 알림
                broadcastNewMessageEvent(dto.getRoomId());
            }

        } catch (Exception e) {
            log.error("WebSocket message handling error", e);
        }
    }

    private void broadcastNewMessageEvent(Long roomId) {
        try {
            String payload = objectMapper.writeValueAsString(
                    new WebSocketEvent("NEW_MESSAGE", roomId)
            );
            TextMessage textMessage = new TextMessage(payload);

            synchronized (sessions) {
                for (WebSocketSession session : sessions) {
                    if (session.isOpen()) {
                        session.sendMessage(textMessage);
                    }
                }
            }
        } catch (Exception e) {
            log.error("Broadcast error", e);
        }
    }

    // 내부용 이벤트 DTO
    @lombok.Data
    @lombok.AllArgsConstructor
    static class WebSocketEvent {
        private String type;
        private Long roomId;
    }
}
