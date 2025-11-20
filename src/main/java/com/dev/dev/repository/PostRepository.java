package com.dev.dev.repository;

import com.dev.dev.entity.Post;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface PostRepository extends JpaRepository<Post,Long> {
    List<Post> findAllByBoardTypeOrderByCreatedAtDesc(String boardType);
}
