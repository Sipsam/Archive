package com.dev.dev.dto.user;


import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;


@Getter
@Setter
@NoArgsConstructor
public class UpdateUserRequest {
    private String nickname;
    private String address;
    private String addressDetail;
    private String zipCode;
}