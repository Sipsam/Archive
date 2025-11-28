package com.dev.dev.controller;

import com.dev.dev.dto.OnlineGroupBuyDto.OnlineParticipationDto;
import com.dev.dev.dto.OnlineGroupBuyDto.RequestOnlineGroupBuyDto;
import com.dev.dev.dto.OnlineGroupBuyDto.ResponseOnlineGroupByDto;
import com.dev.dev.service.OnlineGroupBuyService;
import com.dev.dev.service.ProductService; // [추가]
import com.dev.dev.security.JwtUtil;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/groupbuys")
@RequiredArgsConstructor
public class OnlineGroupBuyController {

    private final OnlineGroupBuyService groupBuyService;
    private final ProductService productService; // [추가] 상품 로직은 여기서 담당
    private final JwtUtil jwtUtil;

    private Long extractUserId(HttpServletRequest request) {
        String header = request.getHeader("Authorization");
        if (header == null) throw new IllegalArgumentException("Token Required");
        return jwtUtil.getUserIdFromToken(header);
    }

    // 1. [목록 조회]
    @GetMapping("/online")
    public ResponseEntity<List<ResponseOnlineGroupByDto>> getList(
            @RequestParam(required = false) String query) {
        return ResponseEntity.ok(groupBuyService.getGroupBuys(query));
    }

    // 2. [등록]
    @PostMapping("/online")
    public ResponseEntity<ResponseOnlineGroupByDto> create(
            HttpServletRequest request,
            @RequestBody RequestOnlineGroupBuyDto.Create req) {
        Long userId = extractUserId(request);
        return ResponseEntity.ok(groupBuyService.createGroupBuy(userId, req));
    }

    // 4. [상세 조회]
    @GetMapping("/online/{id}")
    public ResponseEntity<ResponseOnlineGroupByDto> getDetail(@PathVariable Long id) {
        return ResponseEntity.ok(groupBuyService.getGroupBuyDetail(id));
    }

    // 5. [참여]
    @PostMapping("/online/{id}/participate")
    public ResponseEntity<String> participate(
            HttpServletRequest request,
            @PathVariable Long id) {
        Long userId = extractUserId(request);
        groupBuyService.participate(userId, id);
        return ResponseEntity.ok("참여 완료 (수량 미정, 채팅방 입장)");
    }

    // 6. [상태 변경]
    @PutMapping("/online/{id}/status")
    public ResponseEntity<ResponseOnlineGroupByDto> updateStatus(
            HttpServletRequest request,
            @PathVariable Long id,
            @RequestBody RequestOnlineGroupBuyDto.UpdateStatus req) {
        Long userId = extractUserId(request);
        return ResponseEntity.ok(groupBuyService.updateGroupBuyStatus(userId, id, req));
    }

    // 7. [참여 정보 변경]
    @PutMapping("/participations/online/{partId}/tracking")
    public ResponseEntity<OnlineParticipationDto> updateTracking(
            HttpServletRequest request,
            @PathVariable Long partId,
            @RequestBody RequestOnlineGroupBuyDto.UpdateTracking req) {
        Long userId = extractUserId(request);
        return ResponseEntity.ok(groupBuyService.updateParticipation(userId, partId, req));
    }
}
