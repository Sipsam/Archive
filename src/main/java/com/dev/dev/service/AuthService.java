package com.dev.dev.service;

import com.dev.dev.dto.auth.JoinRequest;
import com.dev.dev.dto.auth.LoginRequest;
import com.dev.dev.dto.auth.LoginResponse;
import com.dev.dev.dto.user.UserResponse;
import com.dev.dev.entity.Role;
import com.dev.dev.entity.User;
import com.dev.dev.repository.UserRepository;
import com.dev.dev.security.JwtUtil;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;


@Service
@RequiredArgsConstructor
public class AuthService {


    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;


    @Transactional
    public UserResponse join(JoinRequest req) {
        if (userRepository.findByLoginId(req.getLoginId()).isPresent()) {
            throw new IllegalArgumentException("이미 사용 중인 loginId 입니다.");
        }
        if (req.getNickname() != null && userRepository.findAll().stream().anyMatch(u -> req.getNickname().equals(u.getNickname()))) {
            throw new IllegalArgumentException("이미 사용 중인 닉네임입니다.");
        }


        User user = User.builder()
                .loginId(req.getLoginId())
                .password(passwordEncoder.encode(req.getPassword()))
                .name(req.getName())
                .nickname(req.getNickname())
                .email(req.getEmail())
                .phoneNumber(req.getPhoneNumber())
                .address(req.getAddress())
                .addressDetail(req.getAddressDetail())
                .zipCode(req.getZipCode())
                .points(1)
                .mannerTemp(36.5)
                .role(Role.USER)
                .build();


        User saved = userRepository.save(user);
        return UserResponse.from(saved);
    }


    public LoginResponse login(LoginRequest req) {
        User user = userRepository.findByLoginId(req.getLoginId())
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 사용자입니다."));


        if (!passwordEncoder.matches(req.getPassword(), user.getPassword())) {
            throw new IllegalArgumentException("비밀번호가 일치하지 않습니다.");
        }


        String token = jwtUtil.generateToken(user.getId());
        return new LoginResponse(token);
    }
}