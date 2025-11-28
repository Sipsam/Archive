package com.dev.dev.repository;

import com.dev.dev.entity.ChatMessage;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.time.LocalDateTime;
import java.util.List;

public interface ChatMessageRepository extends JpaRepository<ChatMessage, Long> {

    @Query("""
        SELECT COUNT(m)
        FROM ChatMessage m
        WHERE m.chatRoom.id = :roomId
          AND (:lastReadAt IS NULL OR m.sentAt > :lastReadAt)
          AND m.sender.id <> :userId
    """)
    int countUnreadMessages(Long roomId, Long userId, LocalDateTime lastReadAt);

    @Query("""
        SELECT m FROM ChatMessage m
        JOIN FETCH m.sender
        WHERE m.chatRoom.id = :roomId
        ORDER BY m.sentAt ASC
    """)
    List<ChatMessage> findByRoomId(Long roomId);

}
