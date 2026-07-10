package com.dev.dev.controller;

import com.dev.dev.dto.chat.ChatMessageResponse;
import com.dev.dev.dto.chat.ChatRoomListResponse;
import com.dev.dev.entity.ChatMessage;
import com.dev.dev.entity.User;
import com.dev.dev.service.ChatMessageService;
import com.dev.dev.service.ChatRoomService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatRoomController {

    private final ChatRoomService chatRoomService;
    private final ChatMessageService chatMessageService;

    @GetMapping("/rooms")
    public List<ChatRoomListResponse> getMyChatRooms(@AuthenticationPrincipal User user) {
        return chatRoomService.getRoomsForUser(user.getId());
    }

    @GetMapping("/rooms/{roomId}/messages")
    public List<ChatMessageResponse> getRoomMessages(
            @PathVariable Long roomId,
            @AuthenticationPrincipal User user
    ) {
        // 1. 유저가 이 방의 참여자인지 검증
        chatRoomService.validateParticipant(roomId, user.getId());

        // [추가] 2. 메시지 목록을 조회했으므로 '읽음' 처리 (시간 업데이트)
        chatRoomService.updateLastReadAt(roomId, user.getId());

        // 3. 메시지 목록 반환 (DTO 형태)
        return chatMessageService.getMessagesByRoomId(roomId);
    }
}
