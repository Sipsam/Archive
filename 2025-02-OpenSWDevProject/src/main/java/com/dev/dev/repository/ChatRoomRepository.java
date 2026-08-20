package com.dev.dev.repository;

import com.dev.dev.entity.ChatRoom;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface ChatRoomRepository extends JpaRepository<ChatRoom, Long> {

    Optional<ChatRoom> findByGroupBuyId(Long groupBuyId);
}

