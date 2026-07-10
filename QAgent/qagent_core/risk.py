"""Pure balance risk and QA retest policy functions."""

from __future__ import annotations

from typing import Any


def assess_balance_risk(
    player_team: str,
    win_rate: float,
    win_rate_gap: float,
    patch_win_rate_change: float = 0.0,
    estimated_damage_increase_rate: float = 0.0,
) -> dict[str, Any]:
    """Score balance risk from win-rate, patch impact, and damage signals."""
    score = 0
    reasons = []

    if win_rate >= 0.85:
        score += 35
        reasons.append("승률이 85% 이상으로 매우 높음")
    elif win_rate >= 0.75:
        score += 25
        reasons.append("승률이 75% 이상으로 높음")

    if win_rate_gap >= 0.25:
        score += 25
        reasons.append("전체 평균 대비 승률 차이가 25%p 이상")
    elif win_rate_gap >= 0.15:
        score += 15
        reasons.append("전체 평균 대비 승률 차이가 15%p 이상")

    if patch_win_rate_change >= 0.20:
        score += 25
        reasons.append("패치 전후 승률 상승 폭이 20%p 이상")
    elif patch_win_rate_change >= 0.10:
        score += 15
        reasons.append("패치 전후 승률 상승 폭이 10%p 이상")

    if estimated_damage_increase_rate >= 0.30:
        score += 15
        reasons.append("스탯 시뮬레이션상 피해량 증가율이 30% 이상")
    elif estimated_damage_increase_rate >= 0.15:
        score += 8
        reasons.append("스탯 시뮬레이션상 피해량 증가율이 15% 이상")

    score = min(score, 100)
    if score >= 75:
        level, decision = "High", "긴급 재테스트 및 부분 하향 검토"
    elif score >= 45:
        level, decision = "Medium", "추가 표본 수집 후 보수적 조정 검토"
    else:
        level, decision = "Low", "모니터링 유지"

    return {
        "status": "ok",
        "player_team": player_team,
        "risk_score": score,
        "risk_level": level,
        "reasons": reasons,
        "recommended_decision": decision,
        "control": "자동 패치 금지. QA 담당자와 밸런스 기획자의 Human Review 이후에만 반영.",
    }


def generate_retest_plan(
    player_team: str,
    equipment_set: str,
    skill_used_most: str,
    risk_level: str = "Medium",
) -> dict[str, Any]:
    """Build a segment-based QA retest plan for a balance candidate."""
    if risk_level == "High":
        battles_per_segment = 300
    elif risk_level == "Medium":
        battles_per_segment = 200
    else:
        battles_per_segment = 100

    segments = ["beginner", "mid", "advanced"]
    plan = [
        {
            "segment": segment,
            "required_battles": battles_per_segment,
            "conditions": {
                "player_team": player_team,
                "equipment_set": equipment_set,
                "skill_used_most": skill_used_most,
                "battle_mode": "arena",
            },
            "acceptance_criteria": [
                "승률이 허용 범위 내인지 확인",
                "평균 피해량이 전체 평균 대비 과도하게 높지 않은지 확인",
                "전투 시간이 지나치게 짧거나 길지 않은지 확인",
            ],
        }
        for segment in segments
    ]
    return {
        "status": "ok",
        "total_required_battles": battles_per_segment * len(segments),
        "plan": plan,
        "human_review_steps": [
            "QA 담당자: 로그 재현성과 표본 수 검토",
            "밸런스 기획자: 수치 조정안 검토",
            "데이터 분석 담당자: 패치 전후 변화량 검증",
            "리드 기획자: 최종 적용 여부 승인",
        ],
    }
