package com.dev.dev.service;


import com.dev.dev.dto.user.UpdateUserRequest;
import com.dev.dev.dto.user.UserResponse;
import com.dev.dev.entity.*;
import com.dev.dev.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;


import java.util.List;
import java.util.stream.Collectors;


@Service
@RequiredArgsConstructor
public class UserService {


    private final UserRepository userRepository;
    private final UserReviewRepository userReviewRepository;
    private final PostRepository postRepository;
    private final OnlineParticipationRepository onlineParticipationRepository;
    private final OfflineParticipationRepository offlineParticipationRepository;


    public UserResponse getMyInfo(Long userId) {
        User u = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("사용자 없음"));
        return UserResponse.from(u);
    }


    public UserResponse updateUser(Long userId, UpdateUserRequest req) {
        User u = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("사용자 없음"));


        if (req.getNickname() != null) u.setNickname(req.getNickname());
        if (req.getAddress() != null) u.setAddress(req.getAddress());
        if (req.getAddressDetail() != null) u.setAddressDetail(req.getAddressDetail());
        if (req.getZipCode() != null) u.setZipCode(req.getZipCode());


        userRepository.save(u);
        return UserResponse.from(u);
    }


    public List<UserReview> getUserReviews(Long userId) {
        return userReviewRepository.findAll().stream()
                .filter(r -> r.getReviewee() != null && r.getReviewee().getId().equals(userId))
                .collect(Collectors.toList());
    }


    public List<Post> getMyPosts(Long userId) {
        return postRepository.findAll().stream()
                .filter(p -> p.getAuthor() != null && p.getAuthor().getId().equals(userId))
                .collect(Collectors.toList());
    }


    public MyParticipationsDTO getMyParticipations(Long userId) {
        List<OnlineParticipation> online = onlineParticipationRepository.findAll().stream()
                .filter(op -> op.getUser() != null && op.getUser().getId().equals(userId))
                .collect(Collectors.toList());


        List<OfflineParticipation> offline = offlineParticipationRepository.findAll().stream()
                .filter(op -> op.getUser() != null && op.getUser().getId().equals(userId))
                .collect(Collectors.toList());


        return new MyParticipationsDTO(online, offline);
    }
    public static class MyParticipationsDTO {
        public final List<OnlineParticipation> onlineParticipations;
        public final List<OfflineParticipation> offlineParticipations;


        public MyParticipationsDTO(List<OnlineParticipation> online, List<OfflineParticipation> offline) {
            this.onlineParticipations = online;
            this.offlineParticipations = offline;
        }
    }
}