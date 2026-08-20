package com.dev.dev.dto.chat;

import lombok.Data;

@Data
public class ChatMessageDto {

    private Long roomId;
    private String message;
    private String type; // "CHAT" 등

}
