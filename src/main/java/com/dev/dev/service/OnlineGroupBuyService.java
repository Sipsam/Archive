package com.dev.dev.service;

import com.dev.dev.dto.OnlineGroupBuyDto.OnlineParticipationDto;
import com.dev.dev.dto.OnlineGroupBuyDto.RequestOnlineGroupBuyDto;
import com.dev.dev.dto.OnlineGroupBuyDto.ResponseOnlineGroupByDto;
import com.dev.dev.entity.*;
import com.dev.dev.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor// private final 키워드가 붙은 필드들의 생성자를 자동으로 만들어줌. 생성자 호출은 Service에너테이션이 알아서 new를 통해 만듦.
@Transactional(readOnly = true)
public class OnlineGroupBuyService {

    private final OnlineGroupBuyRepository groupBuyRepository;
    private final OnlineParticipationRepository participationRepository;
    private final UserRepository userRepository;
    private final ProductRepository productRepository;
    private final ChatRoomService chatRoomService;

    // 1. 목록 조회. 객체들을 Dto로 감싸고 List에 담는 로직은 ResponseOnlineGroupByDto의 참여자 Dto가 담긴 리스트 필드를 생성하는 것과 동일하지만, 범위가 이것은 모집글이 담긴 리스트 이다. 저건 참여자 Dto를 담는 리스트 이고
    // 더 큰 범위의 리스트. 이 리스트 안에 모집글 Dto가 있고 그 모집글 Dto안에 참여자 리스트  필드가 있고, 그 참여자 리스트 필드에 참여자 Dto들이 각각 담겨 있는 구조이다.
    public List<ResponseOnlineGroupByDto> getGroupBuys(String query) {
        List<OnlineGroupBuy> list;
        if (query == null || query.isBlank()) {
            list = groupBuyRepository.findAll();
        } else {
            list = groupBuyRepository.findAllByQuery(query);
        }
        return list.stream()
                .map(ResponseOnlineGroupByDto::from)
                .collect(Collectors.toList());
    }

    // 2. 공구 생성
    @Transactional
    public ResponseOnlineGroupByDto createGroupBuy(Long userId, RequestOnlineGroupBuyDto.Create req) {
        User host = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found"));
        Product product = productRepository.findById(req.getProductId())
                .orElseThrow(() -> new IllegalArgumentException("Product not found"));

        // 포인트 차감
        int deposit = 1000;
        int currentPoint = host.getPoints() == null ? 0 : host.getPoints();

        if (currentPoint < deposit) {
            throw new IllegalStateException("공구 생성을 위한 포인트가 부족합니다. (보유: " + currentPoint + ", 필요: " + deposit + ")");
        }

        // 차감 수행
        host.setPoints(currentPoint - deposit);

        OnlineGroupBuy groupBuy = OnlineGroupBuy.builder()//엔터티 생성. 바디를 통해 전달된 req를 반영하여 객체 생성(req는 Dto다)
                .hostUser(host)
                .productId(product) // 엔터티 변수명이 productId라면 맞음 (보통 product 권장)
                .title(req.getTitle())
                .content(req.getContent())
                .targetHeadcount(req.getTargetHeadcount())
                .recruitEndDate(req.getRecruitEndDate())
                .status(GroupBuyStatus.RECRUITING)
                .build();

        OnlineGroupBuy saved = groupBuyRepository.save(groupBuy);//생성된 객체를 데이터베이스 테이블에 저장
        ChatRoom room = chatRoomService.createRoomForGroupBuy(saved.getId(), saved.getTitle());
        saved.setChatRoomId(room.getId());
        chatRoomService.addParticipant(room, host);

        return ResponseOnlineGroupByDto.from(saved);//생성된 객체를 다시 ResponseOnlineGroupByDto형식으로 변환하여 반환
    }

    // [삭제됨] registerProductFromUrl 메서드
    // 이유: 상품 등록 로직은 이제 ProductService에서 전담합니다.

    // 4. 상세 조회
    public ResponseOnlineGroupByDto getGroupBuyDetail(Long id) {
        OnlineGroupBuy groupBuy = groupBuyRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("GroupBuy not found"));
        return ResponseOnlineGroupByDto.from(groupBuy);//상세 조회는 공구 생성 로직에서 결과적으로 반환해서 보여주는 거랑 동일한 반환
    }



    // 5. 참여
    @Transactional
    public void participate(Long userId, Long groupBuyId) {
        User user = userRepository.findById(userId).orElseThrow();
        OnlineGroupBuy groupBuy = groupBuyRepository.findById(groupBuyId).orElseThrow();

        //이미 해당 공구 모집에 참여 중이면 이미 참여 중이라는 예외처리
        boolean exists = groupBuy.getParticipationList().stream()
                .anyMatch(p -> p.getUser().getId().equals(userId));
        if (exists) throw new IllegalStateException("이미 참여함");

        OnlineParticipation participation = OnlineParticipation.builder()
                .user(user)
                .onlineGroupBuy(groupBuy)
                .quantity(null) // 이건 프론트에서 안 넘긴다고 함.
                .paymentStatus(PaymentStatus.PENDING)//PENDING = "결제 대기"라는 의미의 enum요소
                .build();

        participationRepository.save(participation);
        ChatRoom room = chatRoomService.findByGroupBuyId(groupBuyId)
                .orElseThrow(() -> new IllegalStateException("채팅방을 찾을 수 없습니다."));
        chatRoomService.addParticipant(room, user);
    }

    // 6. 공구 상태 변경
    @Transactional
    public ResponseOnlineGroupByDto updateGroupBuyStatus(Long userId, Long groupBuyId, RequestOnlineGroupBuyDto.UpdateStatus req) {
        OnlineGroupBuy groupBuy = groupBuyRepository.findById(groupBuyId).orElseThrow();

        if (!groupBuy.getHostUser().getId().equals(userId)) {
            throw new SecurityException("방장만 수정 가능");
        }

        if (req.getStatus() != null) groupBuy.setStatus(req.getStatus());
        if (req.getTitle() != null) groupBuy.setTitle(req.getTitle());
        if (req.getContent() != null) groupBuy.setContent(req.getContent());

        return ResponseOnlineGroupByDto.from(groupBuy);
    }

    // 7. 참여 정보 수정
    @Transactional
    public OnlineParticipationDto updateParticipation(Long userId,Long partId, RequestOnlineGroupBuyDto.UpdateTracking req) {
        OnlineParticipation participation = participationRepository.findById(partId).orElseThrow();

        if (req.getQuantity() != null) participation.setQuantity(req.getQuantity());

        if (req.getPaymentStatus() != null) participation.setPaymentStatus(req.getPaymentStatus());
        //이거 결제로직이랑 연동해서 해야하므로 수정해야 할 것 같음. 이대로 하면 사용자가 직접 수정 가능한데 말이 안됌.

        return OnlineParticipationDto.from(participation);
    }

    @Transactional
    public void startPaymentProcess(Long userId, Long groupBuyId) {
        OnlineGroupBuy groupBuy = groupBuyRepository.findById(groupBuyId)
                .orElseThrow(() -> new IllegalArgumentException("공구 정보를 찾을 수 없습니다."));

        // 1. 방장 권한 체크
        if (!groupBuy.getHostUser().getId().equals(userId)) {
            throw new SecurityException("방장만 결제를 시작할 수 있습니다.");
        }

        // 2. 인원 수 체크 (목표 인원과 현재 인원이 정확히 일치해야 함)
        if (groupBuy.getParticipationList().size() != groupBuy.getTargetHeadcount()) {
            throw new IllegalStateException("목표 인원이 정확히 채워져야 결제를 시작할 수 있습니다.");
        }

        Product product = groupBuy.getProductId();
        int targetHeadcount = groupBuy.getTargetHeadcount();

        // 3. 계산 로직 (N분의 1)
        // 요청 사항: 참여자별 Quantity = 상품 총 수량 / 목표 인원
        int individualQuantity = product.getAllQuantity() / targetHeadcount;

        // 4. 모든 참여자의 수량(Quantity) 일괄 업데이트
        // 금액은 백엔드에서 계산하지 않고, 프론트엔드가 product 정보를 보고 처리하도록 둠
        List<OnlineParticipation> participations = groupBuy.getParticipationList();
        for (OnlineParticipation participation : participations) {
            participation.setQuantity(individualQuantity);
        }

        // 5. 공구 상태 변경 (RECRUITING -> PAYING)
        groupBuy.setStatus(GroupBuyStatus.IN_PROGRESS);

        // Dirty Checking에 의해 트랜잭션 종료 시 자동 Update
    }
}