package com.dev.dev.dto.chat;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class ChatRoomListResponse {

    private Long roomId;
    private String roomName;
    private int unreadCount;
}
