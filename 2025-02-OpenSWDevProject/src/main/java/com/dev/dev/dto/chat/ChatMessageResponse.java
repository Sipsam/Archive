package com.dev.dev.dto.chat;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
public class ChatMessageResponse {

    private Long messageId;
    private Long senderId;
    private String senderNickname;
    private String message;
    private LocalDateTime sentAt;
}
