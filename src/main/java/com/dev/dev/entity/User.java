package com.dev.dev.entity;


import jakarta.persistence.*;
import lombok.*;


@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;


    @Column(name = "login_id", length = 50, nullable = false, unique = true)
    private String loginId;


    @Column(length = 255, nullable = false)
    private String password;


    @Column(length = 50)
    private String name;


    @Column(length = 50, unique = true)
    private String nickname;


    @Column(length = 100, unique = true)
    private String email;


    @Column(name = "phone_number", length = 20, unique = true)
    private String phoneNumber;


    @Column(length = 255)
    private String address;


    @Column(name = "address_detail", length = 255)
    private String addressDetail;


    @Column(name = "zip_code", length = 10)
    private String zipCode;


    @Column(nullable = false)
    private Integer points = 1;


    @Column(name = "manner_temp", nullable = false)
    private Double mannerTemp = 36.5;


    @Enumerated(EnumType.STRING)
    @Column(length = 20)
    private Role role = Role.USER;
}