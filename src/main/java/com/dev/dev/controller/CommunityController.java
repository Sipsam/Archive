package com.dev.dev.controller;

import com.dev.dev.dto.community.PostDto;
import com.dev.dev.dto.community.ReviewRequestDto;
import com.dev.dev.security.JwtUtil;  // JwtUtil 임포트
import com.dev.dev.service.CommunityService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import javax.servlet.http.HttpServletRequest;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class CommunityController {

    private final CommunityService communityService;
    private final JwtUtil jwtUtil;  // JwtUtil 의존성 주입

    // Get 요청은 그대로
    @GetMapping("/posts")
    public ResponseEntity<List<PostDto.Response>> getPost(@RequestParam String boardType) {
        return ResponseEntity.ok(communityService.getPostList(boardType));
    }

    @GetMapping("/posts/{id}")
    public ResponseEntity<PostDto.Response> getPost(@PathVariable Long id) {
        return ResponseEntity.ok(communityService.getPost(id));
    }

    // Post 요청에서 UserDetails 대신 JWT로 userId 가져오기
    @PostMapping("/posts")
    public ResponseEntity<PostDto.Response> createPost(
            @RequestBody PostDto.Request requestDto,
            @RequestHeader("Authorization") String authorizationHeader // 헤더에서 Authorization 추출
    ) {
        // JWT 토큰 추출 (Bearer <token>)
        String token = authorizationHeader.startsWith("Bearer ") ? authorizationHeader.substring(7) : authorizationHeader;

        // JWT 토큰에서 userId 추출
        Long userId = jwtUtil.getUserIdFromToken(token);
        if (userId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Invalid or missing token");
        }

        // service 호출
        return ResponseEntity.ok(communityService.createPost(userId, requestDto));
    }

    // Review 생성 API도 JWT로 userId 가져오기
    @PostMapping("/reviews")
    public ResponseEntity<String> createReview(
            @RequestBody ReviewRequestDto requestDto,
            @RequestHeader("Authorization") String authorizationHeader // 헤더에서 Authorization 추출
    ) {
        // JWT 토큰 추출 (Bearer <token>)
        String token = authorizationHeader.startsWith("Bearer ") ? authorizationHeader.substring(7) : authorizationHeader;

        // JWT 토큰에서 userId 추출
        Long reviewerId = jwtUtil.getUserIdFromToken(token);
        if (reviewerId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Invalid or missing token");
        }

        // service 호출
        communityService.createReview(reviewerId, requestDto);
        return ResponseEntity.ok("리뷰가 등록되었습니다.");
    }
}
