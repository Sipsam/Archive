package com.dev.dev.websocket;

import com.dev.dev.dto.chat.ChatMessageDto;
import com.dev.dev.entity.ChatMessage; // [중요] import 추가
import com.dev.dev.entity.User;
import com.dev.dev.service.ChatMessageService;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.Collections;
import java.util.HashMap; // [중요] import 추가
import java.util.HashSet;
import java.util.Map;     // [중요] import 추가
import java.util.Set;

@Slf4j
@Component
@RequiredArgsConstructor
public class ChatWebSocketHandler extends TextWebSocketHandler {

    private final ChatMessageService chatMessageService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    // 연결된 세션들 관리
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
                // [수정 핵심] DB에 메시지 저장 후, 반환된 엔티티를 savedMsg 변수에 저장해야 함
                ChatMessage savedMsg = chatMessageService.saveFromDto(dto, user.getId());

                // 2. 채팅방에 있는 모든 클라이언트에게 '메시지 내용' 전송 (Type: CHAT)
                Map<String, Object> chatPayload = new HashMap<>();
                chatPayload.put("type", "CHAT");
                chatPayload.put("roomId", dto.getRoomId());
                chatPayload.put("senderId", user.getId());
                chatPayload.put("senderNickname", user.getNickname());
                chatPayload.put("message", dto.getMessage());
                // savedMsg 변수를 여기서 사용
                chatPayload.put("sentAt", savedMsg.getSentAt().toString());

                String jsonPayload = objectMapper.writeValueAsString(chatPayload);
                TextMessage textMessage = new TextMessage(jsonPayload);

                synchronized (sessions) {
                    for (WebSocketSession s : sessions) {
                        if (s.isOpen()) {
                            try {
                                s.sendMessage(textMessage);
                            } catch (Exception e) {
                                log.error("Error sending message", e);
                            }
                        }
                    }
                }

                // 3. 사이드바 알림용 NEW_MESSAGE 이벤트 전송
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
