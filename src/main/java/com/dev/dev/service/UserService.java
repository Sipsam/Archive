package com.dev.dev.service;


import com.dev.dev.dto.user.UpdateUserRequest;
import com.dev.dev.dto.user.UserResponse;
import com.dev.dev.entity.*;
import com.dev.dev.repository.*;
import lombok.Builder;
import lombok.Getter;
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


    // [수정된 메서드] 엔터티를 그대로 반환하지 않고 DTO로 변환하여 반환
    public MyParticipationsDTO getMyParticipations(Long userId) {
        List<MyParticipationItemDto> online = onlineParticipationRepository.findAll().stream()
                .filter(op -> op.getUser() != null && op.getUser().getId().equals(userId))
                .map(MyParticipationItemDto::from) // Entity -> DTO 변환
                .collect(Collectors.toList());
        
        return new MyParticipationsDTO(online);
    }

    // [수정] 응답용 DTO 클래스들 (순환 참조 방지)
    @Getter
    public static class MyParticipationsDTO {
        private List<MyParticipationItemDto> onlineParticipations;

        public MyParticipationsDTO(List<MyParticipationItemDto> online) {
            this.onlineParticipations = online;
        }
    }

    @Getter
    @Builder
    public static class MyParticipationItemDto {
        private Long id;
        private SimpleGroupBuyDto onlineGroupBuy; // 프론트엔드가 이 필드명을 기대함

        public static MyParticipationItemDto from(OnlineParticipation entity) {
            return MyParticipationItemDto.builder()
                    .id(entity.getId())
                    // 여기서 필요한 공구 정보만 쏙 뽑아서 DTO로 만듦
                    .onlineGroupBuy(SimpleGroupBuyDto.from(entity.getOnlineGroupBuy()))
                    .build();
        }
    }

    @Getter
    @Builder
    public static class SimpleGroupBuyDto {
        private Long id;
        private String title;
        private Long chatRoomId; // 채팅방 ID 필수

        public static SimpleGroupBuyDto from(OnlineGroupBuy entity) {
            return SimpleGroupBuyDto.builder()
                    .id(entity.getId())
                    .title(entity.getTitle())
                    .chatRoomId(entity.getChatRoomId())
                    .build();
        }
    }
}
