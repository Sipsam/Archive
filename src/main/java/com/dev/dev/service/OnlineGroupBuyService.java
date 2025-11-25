package com.dev.dev.service;

import com.dev.dev.entity.OnlineGroupBuy;
import com.dev.dev.repository.OnlineGroupBuyRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class OnlineGroupBuyService {

    private final OnlineGroupBuyRepository onlineGroupBuyRepository;

    public List<OnlineGroupBuy> findAll() {
        return onlineGroupBuyRepository.findAll();
    }

    public Optional<OnlineGroupBuy> findById(Long id) {
        return onlineGroupBuyRepository.findById(id);
    }

    public OnlineGroupBuy save(OnlineGroupBuy onlineGroupBuy) {
        return onlineGroupBuyRepository.save(onlineGroupBuy);
    }

    public void delete(Long id) {
        onlineGroupBuyRepository.deleteById(id);
    }
}
