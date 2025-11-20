package com.dev.dev.controller;

import com.dev.dev.dto.community.PostDto;
import com.dev.dev.dto.community.ReviewRequestDto;
import com.dev.dev.service.CommunityService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class CommunityController {

    private final CommunityService communityService;

    @GetMapping("/posts")
    public ResponseEntity<List<PostDto.Response>> getPost(@RequestParam String boardType) {
        return ResponseEntity.ok(communityService.getPostList(boardType));
    }

    @GetMapping("/posts/{id}")
    public ResponseEntity<PostDto.Response> getPost(@PathVariable Long id){
        return ResponseEntity.ok(communityService.getPost(id));
    }

    @PostMapping("/posts")
    public ResponseEntity<PostDto.Response> createPost(
            @RequestBody PostDto.Request requestDto,
            @AuthenticationPrincipal UserDetails userDetails
    ){
        Long userId = Long.parseLong(userDetails.getUsername());

        return ResponseEntity.ok(communityService.createPost(userId, requestDto));
    }

    @PostMapping("/reviews")
    public ResponseEntity<String> createReview(
            @RequestBody ReviewRequestDto requestDto,
            @AuthenticationPrincipal UserDetails userDetails
    ){
        Long reviewerId = Long.parseLong(userDetails.getUsername());

        communityService.createReview(reviewerId, requestDto);
        return ResponseEntity.ok("리뷰가 등록되었습니다.");
    }
}
