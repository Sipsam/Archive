package com.dev.dev.service;

import com.dev.dev.entity.OfflineGroupBuy;
import com.dev.dev.repository.OfflineGroupBuyRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class OfflineGroupBuyService {

    private final OfflineGroupBuyRepository offlineGroupBuyRepository;

    public List<OfflineGroupBuy> findAll() {
        return offlineGroupBuyRepository.findAll();
    }

    public Optional<OfflineGroupBuy> findById(Long id) {
        return offlineGroupBuyRepository.findById(id);
    }

    public OfflineGroupBuy save(OfflineGroupBuy offlineGroupBuy) {
        return offlineGroupBuyRepository.save(offlineGroupBuy);
    }

    public void delete(Long id) {
        offlineGroupBuyRepository.deleteById(id);
    }
}
