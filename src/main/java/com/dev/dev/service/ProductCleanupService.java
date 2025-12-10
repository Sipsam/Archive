package com.dev.dev.service;

import com.dev.dev.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
public class ProductCleanupService {

    private final ProductRepository productRepository;

    /**
     * 모집글 생성 실패 시 상품을 삭제하는 보상 트랜잭션
     * (외부 트랜잭션 롤백과 상관 없이 별도로 커밋됨)
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void deleteProductInNewTx(Long productId) {
        try {
            productRepository.deleteById(productId);
        } catch (Exception ex) {
            log.error("Failed to delete product in compensation transaction. productId={}", productId, ex);
        }
    }
}

