package com.dev.dev.service;

import com.dev.dev.entity.OfflineParticipation;
import com.dev.dev.repository.OfflineParticipationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class OfflineParticipationService {

    private final OfflineParticipationRepository offlineParticipationRepository;

    public List<OfflineParticipation> findAll() {
        return offlineParticipationRepository.findAll();
    }

    public Optional<OfflineParticipation> findById(Long id) {
        return offlineParticipationRepository.findById(id);
    }

    public OfflineParticipation save(OfflineParticipation offlineParticipation) {
        return offlineParticipationRepository.save(offlineParticipation);
    }

    public void delete(Long id) {
        offlineParticipationRepository.deleteById(id);
    }
}
