package com.dev.dev.controller;


import com.dev.dev.dto.user.UpdateUserRequest;
import com.dev.dev.dto.user.UserResponse;
import com.dev.dev.entity.UserReview;
import com.dev.dev.entity.Post;
import com.dev.dev.service.UserService;
import com.dev.dev.security.JwtUtil;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;


import java.util.List;


@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {


    private final UserService userService;
    private final JwtUtil jwtUtil;


    private Long extractUserId(HttpServletRequest request) {
        String header = request.getHeader("Authorization");
        if (header == null) throw new IllegalArgumentException("토큰 필요");
        return jwtUtil.getUserIdFromToken(header);
    }


    @GetMapping("/me")
    public ResponseEntity<UserResponse> getMe(HttpServletRequest request) {
        Long userId = extractUserId(request);
        return ResponseEntity.ok(userService.getMyInfo(userId));
    }


    @PutMapping("/me")
    public ResponseEntity<UserResponse> updateMe(HttpServletRequest request,
                                                 @RequestBody UpdateUserRequest req) {
        Long userId = extractUserId(request);
        return ResponseEntity.ok(userService.updateUser(userId, req));
    }


    @GetMapping("/{userId}/reviews")
    public ResponseEntity<List<UserReview>> getReviews(@PathVariable Long userId) {
        return ResponseEntity.ok(userService.getUserReviews(userId));
    }


    @GetMapping("/me/posts")
    public ResponseEntity<List<Post>> getMyPosts(HttpServletRequest request) {
        Long userId = extractUserId(request);
        return ResponseEntity.ok(userService.getMyPosts(userId));
    }


    @GetMapping("/me/participations")
    public ResponseEntity<?> getMyParticipations(HttpServletRequest request) {
        Long userId = extractUserId(request);
        return ResponseEntity.ok(userService.getMyParticipations(userId));
    }
}