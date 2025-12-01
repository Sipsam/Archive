package com.dev.dev.controller;

import com.dev.dev.dto.community.PostDto;
import com.dev.dev.dto.community.ReviewRequestDto;
import com.dev.dev.security.JwtUtil;
import com.dev.dev.service.CommunityService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import java.util.List;  // 추가된 임포트
import javax.servlet.http.HttpServletRequest;  // 추가된 임포트

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class CommunityController {

    private final CommunityService communityService;
    private final JwtUtil jwtUtil;

    @GetMapping("/posts")
    public ResponseEntity<List<PostDto.Response>> getPost(@RequestParam String boardType) {
        return ResponseEntity.ok(communityService.getPostList(boardType));
    }

    @GetMapping("/posts/{id}")
    public ResponseEntity<PostDto.Response> getPost(@PathVariable Long id) {
        return ResponseEntity.ok(communityService.getPost(id));
    }

    @PostMapping("/posts")
    public ResponseEntity<PostDto.Response> createPost(
            @RequestBody PostDto.Request requestDto,
            @RequestHeader("Authorization") String authorizationHeader
    ) {
        String token = authorizationHeader.startsWith("Bearer ") ? authorizationHeader.substring(7) : authorizationHeader;
        Long userId = jwtUtil.getUserIdFromToken(token);
        if (userId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Invalid or missing token");
        }
        return ResponseEntity.ok(communityService.createPost(userId, requestDto));
    }

    @PostMapping("/reviews")
    public ResponseEntity<String> createReview(
            @RequestBody ReviewRequestDto requestDto,
            @RequestHeader("Authorization") String authorizationHeader
    ) {
        String token = authorizationHeader.startsWith("Bearer ") ? authorizationHeader.substring(7) : authorizationHeader;
        Long reviewerId = jwtUtil.getUserIdFromToken(token);
        if (reviewerId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Invalid or missing token");
        }
        communityService.createReview(reviewerId, requestDto);
        return ResponseEntity.ok("리뷰가 등록되었습니다.");
    }
}
