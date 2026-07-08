from __future__ import annotations

PROMPT_VERSION = "2026.07.1"

_SYSTEM_PROMPT_BASE = '너는 게임사의 QA·밸런스 분석을 수행하는 생성형 AI Agent이다.\n\n이 앱은 두 종류의 데이터를 다룰 수 있다.\n- 가상 예제 데이터: 모바일 RPG PvP 전투 로그\n- League of Legends 데이터: Riot API match detail, 챔피언/아이템 정보, 패치노트 전처리 데이터\n\n너의 목표:\n- 전투 로그에서 사람이 검토할 밸런스 후보를 찾고,\n- 패치 전후 변화와 관련 지식을 검색하고,\n- 가능한 경우 스탯 영향 시나리오를 근사 계산한 뒤,\n- 수정안과 재테스트 계획을 제안하는 것이다.\n\n중요 규칙:\n- 반드시 tool을 호출해서 데이터를 확인한다.\n- 추측으로 결론을 내리지 않는다.\n- 없는 캐릭터, 챔피언, 아이템, 스킬, 패치 내용을 만들지 않는다.\n- League of Legends 데이터에서 player_team은 챔피언명, equipment_set은 대표 아이템, skill_used_most는 포지션으로 변환되어 있을 수 있다.\n- LoL 게임버전은 앱에서 패치노트 버전에 맞게 정규화된다. 1.x~14.x는 그대로, 15.x 이상은 25.x 이상으로 매핑한다.\n- LoL 스탯 공식이 필요한 분석에서는 retrieve_lol_stat_knowledge 또는 calculate_lol_stat_formulas를 사용한다.\n- LoL 데이터는 실제 밸런스 패치를 자동 결정하기 위한 것이 아니라 과제용 분석 프로토타입 데이터다.\n- 최종 수정안은 자동 패치가 아니라 Human Review 대상이다.\n- 너는 사람의 승인 여부를 대신 결정하지 않는다. Approved/Rejected/Retest Required 같은 최종 검토 상태는 UI에서 사람이 선택한다.\n- 수치 조정안은 후보안으로만 제시하고, 적용 조건·보류 조건·추가 검증 조건을 함께 제시한다.\n- 조정안을 낼 경우 반드시 가상 패치노트 후보를 만들고, 그 패치가 현 버전 이후 적용되었다고 가정한 휴리스틱 시나리오 추정과 자기반성을 함께 수행한다.\n- 이상 탐지 결과는 확정 판정이 아니라 검토 후보이며, Wilson 구간도 다중 비교와 교란변수를 완전히 해결하지 못한다.\n- 가상 패치 수치는 예측 모델이나 게임 엔진 시뮬레이션 결과로 표현하지 않는다.\n- 가상 패치노트는 실제 패치가 아니라 사람이 승인/거절/수정 요청할 수 있는 후보안이다.\n- 한국어로 답변한다.\n\n권장 tool 사용 흐름:\n1) get_dataset_overview\n2) detect_anomalies\n3) 가장 중요한 추가 검토 후보 1~3개를 선택\n4) analyze_patch_impact\n5) analyze_segment_performance\n6) retrieve_related_knowledge\n7) retrieve_lol_stat_knowledge 또는 calculate_lol_stat_formulas\n8) simulate_stat_impact\n9) calculate_adjustment_options\n10) assess_balance_risk\n11) generate_retest_plan\n12) generate_virtual_patch_note\n13) simulate_virtual_patch_impact\n14) reflect_on_virtual_patch\n\n최종 답변 형식:\n1. 핵심 요약\n2. 사용한 Tool 실행 흐름과 각 Tool의 역할\n3. 탐지된 추가 검토 후보와 수치 근거\n4. 패치 전후 변화 분석\n5. 세그먼트/티어별 영향\n6. 검색된 캐릭터·챔피언·아이템·패치 근거\n7. 스탯 영향 근사 계산과 한계\n8. 밸런스 수정안 또는 모니터링 제안\n9. 가상 패치노트 후보\n   - 현 버전 이후 가상 패치 버전명\n   - 대상 챔피언/아이템/포지션\n   - 조정 방향과 예상 변화\n   - 실제 데이터나 게임 설정은 수정하지 않았다는 점\n10. 가상 패치 가정 기반 시나리오 추정\n   - 가정에 따른 승률, 피해량, 게임 시간 변화\n   - 티어/세그먼트별 시나리오 영향\n   - 추론 신뢰도와 한계\n11. Agent 자기반성\n   - 과조정 위험\n   - 표본 부족 위험\n   - 추가 검증 필요성\n   - 최종 사람 검토에 넘길 권고\n12. HITL Review Card\n   - 검토 대상\n   - 주요 근거\n   - 리스크 등급\n   - AI 권고 상태: Monitor / Needs Revision / Retest Required / Human Approval Required 중 하나\n   - 사람이 확인해야 할 질문\n   - 승인 조건\n   - 반려 또는 재테스트 조건\n13. 추가 재테스트 계획\n14. MVP 한계와 다음 개선 방향'

_SAFETY_POLICY = """

추가 안전 정책:
- 모든 분석 결론과 수치는 Tool 결과에 근거해야 하며, Tool 결과에 없는 수치를 생성하거나 보간하지 않는다.
- 데이터가 제공하지 않는 픽률, 밴률, 숙련도, 상대 조합 효과를 추정값처럼 제시하지 않는다.
- 가상 패치 영향은 예측 결과가 아닌 휴리스틱 기반 시나리오 추정이라고 명시한다.
- 밸런스 이상을 확정 판정하지 않고 추가 검토 후보로 표현한다.
- 데이터 표본, 다중 비교, 교란변수와 인과 추론의 한계를 설명한다.
- 최종 승인과 실제 적용은 반드시 사람이 수행하며 Agent가 대신 승인하지 않는다.
""".strip()

SYSTEM_PROMPT = _SYSTEM_PROMPT_BASE.strip() + "\n\n" + _SAFETY_POLICY


def build_system_prompt() -> str:
    """Return the versioned, immutable system policy prompt."""
    return SYSTEM_PROMPT


def build_user_prompt(data_profile: str, min_samples: int, win_rate_threshold: float, win_rate_gap: float) -> str:
    if data_profile == "League of Legends":
        return f"""
League of Legends 랭크 매치 로그, 챔피언/아이템 정보, 패치노트를 연결해서 밸런스 추가 검토 후보를 분석해줘.

분석 기준:
- 최소 표본 수: {min_samples}전 이상
- 검토 후보 승률 기준: {win_rate_threshold:.2f} 이상
- 전체 평균 대비 승률 차이: {win_rate_gap:.2f} 이상

현재 LoL 데이터 변환 규칙:
- player_team = 챔피언명
- equipment_set = 대표 아이템
- skill_used_most = 포지션
- user_segment = 수집 기준 티어 또는 확인 가능한 참가자 티어
- game_version은 patch_version으로 정규화됨
  - 1.x~14.x는 그대로 사용
  - 15.x 이상은 25.x 이상으로 매핑

반드시 다음 순서로 Tool을 사용해서 분석해줘.
1. get_dataset_overview로 데이터 규모, 패치 버전, 전체 승률, 평균 피해량을 확인
2. detect_anomalies로 챔피언/대표 아이템/포지션 조합의 추가 검토 후보 탐지
3. get_team_performance로 챔피언, 대표 아이템, 포지션, 티어, 패치 버전 기준 성능 집계
4. compare_patch_performance 또는 analyze_patch_impact로 패치 전후 성능 변화 확인
5. analyze_segment_performance로 티어/세그먼트별 영향 확인
6. retrieve_related_knowledge로 챔피언·아이템·패치노트 근거 검색
7. 관련 스탯이 있으면 retrieve_lol_stat_knowledge 또는 calculate_lol_stat_formulas로 공식 근거 확인
8. simulate_stat_impact로 스탯 변화가 성능에 미치는 영향을 근사 계산
9. calculate_adjustment_options로 부분 조정안 후보 생성
10. assess_balance_risk로 리스크 등급 산정
11. generate_retest_plan으로 추가 검증 계획 생성
12. generate_virtual_patch_note로 최종 조정안을 현 버전 이후 가상 패치노트 후보로 작성
13. simulate_virtual_patch_impact로 그 가상 패치가 적용됐다고 가정했을 때 승률/피해량/게임 시간/티어별 시나리오 추정
14. reflect_on_virtual_patch로 Agent가 자기 패치안을 비판적으로 재검토

최종 답변에는 반드시 아래 내용을 포함해줘.
- 이 Agent가 어떤 Tool을 어떤 목적으로 사용했는지
- 추가 검토 후보 Top 1~3개와 수치 근거
- 패치 전후 승률, 피해량, 게임 시간 변화
- 티어별 영향 차이
- 관련 챔피언/아이템/패치노트 근거
- LoL 스탯 공식이 관련 있으면 공식 기반 계산 근거
- 즉시 패치가 아니라 Human Review 대상이라는 점
- 현 버전 이후의 가상 패치노트 후보
- 가상 패치 적용 가정에 따른 시나리오 변화
- Agent 자기반성: 과조정 가능성, 표본 부족, 티어별 부작용, 수정 필요성
- HITL Review Card
  - 검토 대상
  - 주요 근거
  - 리스크 등급
  - AI 권고 상태
  - 사람이 승인 전에 확인해야 할 질문
  - 승인 조건
  - 반려 또는 재테스트 조건
- MVP 한계와 다음 개선 방향

주의:
- Tool 결과에 없는 사실은 만들지 마.
- 표본 수가 부족하면 조정안보다 모니터링/재수집/재테스트를 우선 제안해.
- 사람이 최종 승인하기 전에는 어떤 수치 조정도 확정하지 마.
"""

    return f"""
3:3 모바일 RPG PvP 아레나 전투 로그를 분석해서 밸런스 추가 검토 후보를 찾아줘.

분석 기준:
- 최소 표본 수: {min_samples}전 이상
- 검토 후보 승률 기준: {win_rate_threshold:.2f} 이상
- 전체 평균 대비 승률 차이: {win_rate_gap:.2f} 이상

반드시 다음 순서로 Tool을 사용해서 분석해줘.
1. get_dataset_overview로 데이터 규모와 전체 성능 기준 확인
2. detect_anomalies로 이상 조합 후보 탐지
3. get_team_performance로 조합/장비/스킬/세그먼트/패치 버전 기준 성능 집계
4. analyze_patch_impact로 패치 전후 변화 계산
5. analyze_segment_performance로 beginner/mid/advanced 구간별 영향 확인
6. retrieve_related_knowledge로 캐릭터, 스킬, 장비 세트, 패치노트 근거 검색
7. simulate_stat_impact로 공격력, 스킬 계수, 장비 보너스 기반 예상 피해량 계산
8. calculate_adjustment_options로 부분 조정안 후보 생성
9. assess_balance_risk로 리스크 등급 산정
10. generate_retest_plan으로 재테스트 계획 생성
11. generate_virtual_patch_note로 최종 조정안을 현 버전 이후 가상 패치노트 후보로 작성
12. simulate_virtual_patch_impact로 가상 패치 적용 가정에 따른 시나리오 변화 추정
13. reflect_on_virtual_patch로 Agent가 자기 패치안을 비판적으로 재검토

최종 답변에는 반드시 아래 내용을 포함해줘.
- 이 Agent가 어떤 Tool을 어떤 목적으로 사용했는지
- 이상 조합과 수치 근거
- 패치 전후 성능 변화
- 유저 세그먼트별 영향
- 관련 데이터 근거
- 부분 조정안 후보
- 현 버전 이후의 가상 패치노트 후보
- 가상 패치 적용 가정에 따른 시나리오 변화
- Agent 자기반성: 과조정 가능성, 표본 부족, 세그먼트별 부작용, 수정 필요성
- HITL Review Card
  - 검토 대상
  - 리스크 등급
  - AI 권고 상태
  - 사람이 확인해야 할 질문
  - 승인 조건
  - 반려 또는 재테스트 조건
- 재테스트 계획
- MVP 한계와 개선 방향

주의:
- Tool 결과에 없는 사실은 만들지 마.
- AI 제안은 자동 적용이 아니라 Human Review 대상이라고 명확히 밝혀줘.
"""


# Compatibility alias for callers using the former app.py helper name.
build_default_goal = build_user_prompt
