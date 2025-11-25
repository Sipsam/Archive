package com.dev.dev.repository;

import com.dev.dev.entity.UserReview;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserReviewRepository extends JpaRepository<UserReview,Long> {
}
