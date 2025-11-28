package com.dev.dev.security;

import com.dev.dev.entity.User;
import com.dev.dev.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.server.HandshakeInterceptor;

import java.net.URI;
import java.util.Map;
import java.util.Optional;

@Component
@RequiredArgsConstructor
public class JwtHandshakeInterceptor implements HandshakeInterceptor {

    private final JwtUtil jwtUtil;
    private final UserRepository userRepository;

    @Override
    public boolean beforeHandshake(ServerHttpRequest request, ServerHttpResponse response,
                                   WebSocketHandler wsHandler, Map<String, Object> attributes) {

        URI uri = request.getURI();
        String query = uri.getQuery(); // token=xxx 형식

        if (query == null || !query.startsWith("token=")) {
            return false;
        }

        String token = query.substring("token=".length());

        if (!jwtUtil.validateToken(token)) { // JwtUtil에 맞게 메서드명 맞춰줘
            return false;
        }

        String loginId = String.valueOf(jwtUtil.getUserIdFromToken(token)); // 토큰 subject가 loginId라고 가정

        Optional<User> userOpt = userRepository.findByLoginId(loginId);
        if (userOpt.isEmpty()) {
            return false;
        }

        User user = userOpt.get();
        attributes.put("user", user);

        return true;
    }

    @Override
    public void afterHandshake(ServerHttpRequest request, ServerHttpResponse response,
                               WebSocketHandler wsHandler, Exception exception) {
    }
}
