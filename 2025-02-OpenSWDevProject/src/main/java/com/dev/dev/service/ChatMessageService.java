package com.dev.dev.service;

import com.dev.dev.dto.chat.ChatMessageDto;
import com.dev.dev.dto.chat.ChatMessageResponse;
import com.dev.dev.entity.ChatMessage;
import com.dev.dev.entity.ChatRoom;
import com.dev.dev.entity.User;
import com.dev.dev.repository.ChatMessageRepository;
import com.dev.dev.repository.ChatRoomRepository;
import com.dev.dev.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class ChatMessageService {

    private final ChatMessageRepository chatMessageRepository;
    private final ChatRoomRepository chatRoomRepository;
    private final UserRepository userRepository;

    // 기존 CRUD
    public List<ChatMessage> findAll() {
        return chatMessageRepository.findAll();
    }

    public Optional<ChatMessage> findById(Long id) {
        return chatMessageRepository.findById(id);
    }

    public ChatMessage save(ChatMessage chatMessage) {
        return chatMessageRepository.save(chatMessage);
    }

    public void delete(Long id) {
        chatMessageRepository.deleteById(id);
    }

    public ChatMessage saveFromDto(ChatMessageDto dto, Long senderId) {
        ChatRoom room = chatRoomRepository.findById(dto.getRoomId())
                .orElseThrow(() -> new IllegalArgumentException("ChatRoom not found: " + dto.getRoomId()));

        User sender = userRepository.findById(senderId)
                .orElseThrow(() -> new IllegalArgumentException("User not found: " + senderId));

        ChatMessage message = ChatMessage.builder()
                .chatRoom(room)
                .sender(sender)
                .message(dto.getMessage())
                .sentAt(LocalDateTime.now())
                .build();

        return chatMessageRepository.save(message);
    }

    public List<ChatMessage> findByRoomId(Long roomId) {
        return chatMessageRepository.findByRoomId(roomId);
    }
    public List<ChatMessageResponse> getMessagesByRoomId(Long roomId) {

        List<ChatMessage> messages = chatMessageRepository.findByRoomId(roomId);

        return messages.stream()
                .map(m -> new ChatMessageResponse(
                        m.getId(),
                        m.getSender().getId(),
                        m.getSender().getNickname(),
                        m.getMessage(),
                        m.getSentAt()
                ))
                .toList();
    }
}
