package com.dev.dev.websocket;

import com.dev.dev.dto.chat.ChatMessageDto;
import com.dev.dev.entity.ChatMessage;
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
                ChatMessage savedMessage = chatMessageService.saveFromDto(dto, user.getId());
                // 모든 클라이언트에게 NEW_MESSAGE 알림
                broadcastNewMessageEvent(dto.getRoomId());
            }

        } catch (Exception e) {
            log.error("WebSocket message handling error", e);
        }
    }

    private void broadcastNewMessageEvent(Long roomId) {
        // 프론트엔드(chat.js)가 기대하는 포맷으로 맵 구성
            Map<String, Object> response = new HashMap<>();
            response.put("type", "CHAT");
            response.put("roomId", message.getChatRoom().getId());
            response.put("senderId", message.getSender().getId());
            response.put("senderNickname", message.getSender().getNickname());
            response.put("message", message.getMessage());
            response.put("sentAt", message.getSentAt().toString());

            String payload = objectMapper.writeValueAsString(response);
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
}

    // 내부용 이벤트 DTO
    @lombok.Data
    @lombok.AllArgsConstructor
    static class WebSocketEvent {
        private String type;
        private Long roomId;
    }
}
