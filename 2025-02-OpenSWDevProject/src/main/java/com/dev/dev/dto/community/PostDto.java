package com.dev.dev.dto.community;

import com.dev.dev.entity.Post;
import lombok.*;

import java.time.LocalDateTime;

public class PostDto {

    @Getter
    @Setter
    @AllArgsConstructor
    @Builder
    public static class Request {
        private String boardType;
        private String title;
        private String content;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class Response {
        private Long id;
        private String authorName;
        private String boardType;
        private String title;
        private String content;
        private LocalDateTime createdAt;

        public static Response from(Post post) {
            return Response.builder()
                    .id(post.getId())
                    .authorName(post.getAuthor().getNickname())
                    .boardType(post.getBoardType())
                    .title(post.getTitle())
                    .content(post.getContent())
                    .createdAt(post.getCreatedAt())
                    .build();
        }
    }
}
