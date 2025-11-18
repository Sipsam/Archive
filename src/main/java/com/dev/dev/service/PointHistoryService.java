package com.dev.dev.service;

import com.dev.dev.entity.PointHistory;
import com.dev.dev.repository.PointHistoryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class PointHistoryService {

    private final PointHistoryRepository pointHistoryRepository;

    public List<PointHistory> findAll() {
        return pointHistoryRepository.findAll();
    }

    public Optional<PointHistory> findById(Long id) {
        return pointHistoryRepository.findById(id);
    }

    public PointHistory save(PointHistory pointHistory) {
        return pointHistoryRepository.save(pointHistory);
    }

    public void delete(Long id) {
        pointHistoryRepository.deleteById(id);
    }
}
