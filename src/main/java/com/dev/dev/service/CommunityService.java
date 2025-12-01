package com.dev.dev.service;

import com.dev.dev.dto.community.PostDto;
import com.dev.dev.dto.community.ReviewRequestDto;
import com.dev.dev.entity.*;
import com.dev.dev.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class CommunityService {

    private final PostRepository postRepository;
    private final UserRepository userRepository;
    private final UserService userService;

    public List<PostDto.Response> getPostList(String boardType){
        return postRepository.findAllByBoardTypeOrderByCreatedAtDesc(boardType).stream()
                .map(PostDto.Response::from)
                .collect(Collectors.toList());
    }

    public PostDto.Response getPost(Long postId){
        Post post = postRepository.findById(postId).orElseThrow(() -> new IllegalArgumentException("해당 게시글이 없습니다. id=" + postId));
        return PostDto.Response.from(post);
    }

    @Transactional
    public PostDto.Response createPost(Long userId, PostDto.Request requestDto){
        User author = userRepository.findById(userId).orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));

        Post post = Post.builder()
                .author(author)
                .boardType(requestDto.getBoardType())
                .title(requestDto.getTitle())
                .content(requestDto.getContent())
                .createdAt(LocalDateTime.now())
                .build();
        postRepository.save(post);

        if("REVIEW".equalsIgnoreCase(requestDto.getBoardType())){
            int rewardPoints = 100;

            author.setPoints(author.getPoints() + rewardPoints);

        }

        return PostDto.Response.from(post);

    }

    @Transactional
    public void createReview(Long reviewerId, ReviewRequestDto requestDto){
        User reviewer = userRepository.findById(reviewerId).orElseThrow(()-> new IllegalArgumentException("작성자를 찾을 수 없습니다."));
        User reviewee = userRepository.findById(requestDto.getRevieweeId()).orElseThrow(() -> new IllegalArgumentException("평가 대상자를 찾을 수 없습니다."));

        UserReview review = UserReview.builder()
                .groupBuyId(requestDto.getGroupBuyId())
                .reviewer(reviewer)
                .reviewee(reviewee)
                .rating(requestDto.getRating())
                .comment(requestDto.getComment())
                .createdAt(LocalDateTime.now())
                .build();
        userRepository.save(reviewer);

        double tempChange = (requestDto.getRating() - 3.0) * 0.1;
        double newTemp = reviewee.getMannerTemp() +  tempChange;

        review.setRating(newTemp);

    }
}
