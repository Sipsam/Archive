package com.dev.dev.service;

import com.dev.dev.entity.UserReview;
import com.dev.dev.repository.UserReviewRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class UserReviewService {

    private final UserReviewRepository userReviewRepository;

    public List<UserReview> findAll() {
        return userReviewRepository.findAll();
    }

    public Optional<UserReview> findById(Long id) {
        return userReviewRepository.findById(id);
    }

    public UserReview save(UserReview userReview) {
        return userReviewRepository.save(userReview);
    }

    public void delete(Long id) {
        userReviewRepository.deleteById(id);
    }
}
