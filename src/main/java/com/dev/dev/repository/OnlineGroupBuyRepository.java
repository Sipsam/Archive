package com.dev.dev.repository;

import com.dev.dev.entity.OnlineGroupBuy;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface OnlineGroupBuyRepository extends JpaRepository<OnlineGroupBuy, Long> {
    @Query("SELECT g FROM OnlineGroupBuy g WHERE (:query IS NULL OR g.title LIKE %:query%) ORDER BY g.createdAt DESC")
    List<OnlineGroupBuy> findAllByQuery(@Param("query") String query);

}
