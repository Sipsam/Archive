package com.dev.dev.repository;

import com.dev.dev.entity.ChatParticipant;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface ChatParticipantRepository extends JpaRepository<ChatParticipant, Long> {

    List<ChatParticipant> findByUserId(Long userId);

    Optional<ChatParticipant> findByChatRoomIdAndUserId(Long roomId, Long userId);
}
