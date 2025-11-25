package com.dev.dev.dto.auth;


import lombok.*;


@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LoginRequest {
    private String loginId;
    private String password;
}