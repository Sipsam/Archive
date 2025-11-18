package com.dev.dev.service;

import com.dev.dev.entity.ChatRoom;
import com.dev.dev.repository.ChatRoomRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class ChatRoomService {

    private final ChatRoomRepository chatRoomRepository;

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
}
