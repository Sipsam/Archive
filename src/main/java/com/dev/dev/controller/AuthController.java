package com.dev.dev.controller;


import com.dev.dev.dto.auth.JoinRequest;
import com.dev.dev.dto.auth.LoginRequest;
import com.dev.dev.dto.auth.LoginResponse;
import com.dev.dev.dto.user.UserResponse;
import com.dev.dev.service.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;


@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {


    private final AuthService authService;


    @PostMapping("/join")
    public ResponseEntity<UserResponse> join(@RequestBody JoinRequest req) {
        System.out.println(req);
        return ResponseEntity.ok(authService.join(req));
    }


    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@RequestBody LoginRequest req) {
        return ResponseEntity.ok(authService.login(req));
    }
}