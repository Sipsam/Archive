package com.dev.dev.dto.auth;


import lombok.*;


@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class JoinRequest {
    private String loginId;
    private String password;
    private String name;
    private String nickname;
    private String email;
    private String phoneNumber;
    private String address;
    private String addressDetail;
    private String zipCode;
}