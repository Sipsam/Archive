package com.dev.dev.dto.user;


import com.dev.dev.entity.User;
import lombok.*;


@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserResponse {
    private Long id;
    private String loginId;
    private String name;
    private String nickname;
    private String email;
    private String phoneNumber;
    private String address;
    private String addressDetail;
    private String zipCode;
    private Integer points;
    private Double mannerTemp;
    private String role;


    public static UserResponse from(User u) {
        return UserResponse.builder()
                .id(u.getId())
                .loginId(u.getLoginId())
                .name(u.getName())
                .nickname(u.getNickname())
                .email(u.getEmail())
                .phoneNumber(u.getPhoneNumber())
                .address(u.getAddress())
                .addressDetail(u.getAddressDetail())
                .zipCode(u.getZipCode())
                .points(u.getPoints())
                .mannerTemp(u.getMannerTemp())
                .role(u.getRole() == null ? null : u.getRole().name())
                .build();
    }
}