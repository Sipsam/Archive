package com.dev.dev.service;

import com.dev.dev.dto.chat.ChatRoomListResponse;
import com.dev.dev.entity.ChatMessage;
import com.dev.dev.entity.ChatParticipant;
import com.dev.dev.entity.ChatRoom;
import com.dev.dev.entity.User;
import com.dev.dev.repository.ChatMessageRepository;
import com.dev.dev.repository.ChatParticipantRepository;
import com.dev.dev.repository.ChatRoomRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class ChatRoomService {

    private final ChatRoomRepository chatRoomRepository;
    private final ChatParticipantRepository chatParticipantRepository;
    private final ChatMessageRepository chatMessageRepository;

    // 기존 CRUD
    public List<ChatRoom> findAll() {
        return chatRoomRepository.findAll();
    }

    public Optional<ChatRoom> findById(Long id) {
        return chatRoomRepository.findById(id);
    }

    public ChatRoom save(ChatRoom chatRoom) {
        return chatRoomRepository.save(chatRoom);
    }

    public void delete(Long id) {
        chatRoomRepository.deleteById(id);
    }

    public List<ChatRoomListResponse> getRoomsForUser(Long userId) {
        List<ChatParticipant> participants = chatParticipantRepository.findByUserId(userId);
        List<ChatRoomListResponse> result = new ArrayList<>();

        for (ChatParticipant cp : participants) {
            ChatRoom room = cp.getChatRoom();
            int unread = chatMessageRepository.countUnreadMessages(
                    room.getId(),
                    userId,
                    cp.getLastReadAt()
            );
            result.add(new ChatRoomListResponse(
                    room.getId(),
                    room.getName(),
                    unread
            ));
        }

        return result;
    }

    public void validateParticipant(Long roomId, Long userId) {
        chatParticipantRepository.findByChatRoomIdAndUserId(roomId, userId)
                .orElseThrow(() -> new IllegalArgumentException("해당 방에 참여자가 아닙니다."));
    }

    public ChatRoom createRoomForGroupBuy(Long groupBuyId, String title) {
        ChatRoom room = ChatRoom.builder()
                .groupBuyId(groupBuyId)
                .name("공동구매: " + title)  // 방 이름
                .createdAt(LocalDateTime.now())
                .build();

        return chatRoomRepository.save(room);
    }

    public Optional<ChatRoom> findByGroupBuyId(Long groupBuyId) {
        return chatRoomRepository.findByGroupBuyId(groupBuyId);
    }

    public void addParticipant(ChatRoom room, User user) {
        boolean exists = chatParticipantRepository
                .findByChatRoomIdAndUserId(room.getId(), user.getId())
                .isPresent();
        if (!exists) {
            ChatParticipant cp = ChatParticipant.builder()
                    .chatRoom(room)
                    .user(user)
                    .lastReadAt(LocalDateTime.now())
                    .build();

            chatParticipantRepository.save(cp);
        }
    }

}
