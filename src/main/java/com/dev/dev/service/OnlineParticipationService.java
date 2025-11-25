package com.dev.dev.service;

import com.dev.dev.entity.OnlineParticipation;
import com.dev.dev.repository.OnlineParticipationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class OnlineParticipationService {

    private final OnlineParticipationRepository onlineParticipationRepository;

    public List<OnlineParticipation> findAll() {
        return onlineParticipationRepository.findAll();
    }

    public Optional<OnlineParticipation> findById(Long id) {
        return onlineParticipationRepository.findById(id);
    }

    public OnlineParticipation save(OnlineParticipation onlineParticipation) {
        return onlineParticipationRepository.save(onlineParticipation);
    }

    public void delete(Long id) {
        onlineParticipationRepository.deleteById(id);
    }
}
