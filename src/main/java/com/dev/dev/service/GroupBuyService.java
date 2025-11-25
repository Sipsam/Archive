package com.dev.dev.service;

import com.dev.dev.entity.GroupBuy;
import com.dev.dev.repository.GroupBuyRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class GroupBuyService {

    private final GroupBuyRepository groupBuyRepository;

    public List<GroupBuy> findAll() {
        return groupBuyRepository.findAll();
    }

    public Optional<GroupBuy> findById(Long id) {
        return groupBuyRepository.findById(id);
    }

    public GroupBuy save(GroupBuy groupBuy) {
        return groupBuyRepository.save(groupBuy);
    }

    public void delete(Long id) {
        groupBuyRepository.deleteById(id);
    }
}
