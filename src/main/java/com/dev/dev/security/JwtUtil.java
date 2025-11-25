package com.dev.dev.security;


import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Component;


import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;


@Component
public class JwtUtil {
    private static final String SECRET = "Z9fS8x!2uN3@aPq7RwLm48#DhQp29zF6KsTnBvQ4@UzpWmX8"; // 예시키
    private static final long EXPIRATION_MS = 1000L * 60 * 60 * 24 * 7; // 7일


    private Key getSigningKey() {
        return Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8));
    }


    public String generateToken(Long userId) {
        Date now = new Date();
        Date exp = new Date(now.getTime() + EXPIRATION_MS);


        return Jwts.builder()
                .setSubject(String.valueOf(userId))
                .setIssuedAt(now)
                .setExpiration(exp)
                .signWith(getSigningKey(), SignatureAlgorithm.HS256)
                .compact();
    }


    public Long getUserIdFromToken(String token) {
        if (token == null) return null;
        if (token.startsWith("Bearer ")) token = token.substring(7);


        Claims claims = Jwts.parserBuilder()
                .setSigningKey(getSigningKey())
                .build()
                .parseClaimsJws(token)
                .getBody();


        return Long.valueOf(claims.getSubject());
    }


    public boolean validateToken(String token) {
        try {
            if (token == null) return false;
            if (token.startsWith("Bearer ")) token = token.substring(7);
            Jwts.parserBuilder().setSigningKey(getSigningKey()).build().parseClaimsJws(token);
            return true;
        } catch (Exception ex) {
            return false;
        }
    }
}