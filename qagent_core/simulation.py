"""Pure, deterministic balance scenario calculations."""
from __future__ import annotations

from typing import Any


def project_patch_scenario(
    win_rate_before: float,
    avg_damage_before: float,
    avg_duration_before: float,
    win_rate_delta_points: float,
    damage_delta_percent: float,
) -> dict[str, float]:
    """Calculate a bounded heuristic scenario; this is not a prediction."""
    return {
        "win_rate": min(max(float(win_rate_before) + float(win_rate_delta_points), 0.01), 0.99),
        "avg_damage": max(float(avg_damage_before) * (1 + float(damage_delta_percent)), 0.0),
        "avg_duration_sec": max(
            float(avg_duration_before) * (1 - float(damage_delta_percent) * 0.20), 1.0
        ),
    }


SCENARIO_WARNINGS = [
    "휴리스틱 기반 추정",
    "실제 예측 모델 아님",
    "게임 엔진 시뮬레이션 아님",
    "실제 패치 전 QA 테스트 필요",
]


def project_patch_scenario_range(
    win_rate_before: float,
    avg_damage_before: float,
    avg_duration_before: float,
    win_rate_delta_points: float,
    damage_delta_percent: float,
) -> dict[str, dict[str, float | str]]:
    """Return three bounded sensitivity scenarios around the input assumptions."""
    definitions = {
        "conservative": (0.5, "효과를 절반만 반영한 보수적 시나리오 추정입니다."),
        "baseline": (1.0, "입력 가정을 그대로 반영한 기준 시나리오 추정입니다."),
        "aggressive": (1.5, "효과가 더 크게 나타나는 경우를 확인하는 공격적 시나리오 추정입니다."),
    }
    scenarios: dict[str, dict[str, float | str]] = {}
    for name, (multiplier, risk_note) in definitions.items():
        scenario_damage_change = float(damage_delta_percent) * multiplier
        projected = project_patch_scenario(
            win_rate_before=win_rate_before,
            avg_damage_before=avg_damage_before,
            avg_duration_before=avg_duration_before,
            win_rate_delta_points=float(win_rate_delta_points) * multiplier,
            damage_delta_percent=scenario_damage_change,
        )
        scenarios[name] = {
            "assumed_effect_multiplier": multiplier,
            "scenario_win_rate": round(projected["win_rate"], 4),
            "scenario_damage_change": round(scenario_damage_change, 4),
            "risk_note": risk_note,
        }
    return scenarios


def validate_patch_scenario_result(result: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate virtual patch scenario result for data integrity and warnings.
    
    Checks:
    - Win rate values are in [0.0, 1.0]
    - Damage delta is not excessive (warn if >0.5 or <-0.5)
    - Required fields (warnings, assumptions) exist
    - Scenario estimates include heuristic limitation notice
    
    Args:
        result: Virtual patch scenario result dict
        
    Returns:
        Tuple of (is_valid: bool, warnings: list[str])
    """
    warnings: list[str] = []
    
    # Check win_rate values
    for scenario_key in ["conservative", "baseline", "aggressive"]:
        if scenario_key in result:
            scenario = result[scenario_key]
            if isinstance(scenario, dict):
                win_rate = scenario.get("scenario_win_rate")
                if win_rate is not None:
                    try:
                        wr = float(win_rate)
                        if not (0.0 <= wr <= 1.0):
                            warnings.append(
                                f"[SANITY_CHECK] {scenario_key} 시나리오의 win_rate가 범위를 벗어남: {wr}"
                            )
                    except (ValueError, TypeError):
                        warnings.append(
                            f"[SANITY_CHECK] {scenario_key} 시나리오의 win_rate가 숫자가 아님: {win_rate}"
                        )
                
                # Check damage delta
                damage_delta = scenario.get("scenario_damage_change")
                if damage_delta is not None:
                    try:
                        dd = float(damage_delta)
                        if abs(dd) > 0.5:
                            warnings.append(
                                f"[SANITY_CHECK] {scenario_key} 시나리오의 damage 변화율이 과도함: {dd:.2%}"
                            )
                    except (ValueError, TypeError):
                        pass
    
    # Check required fields
    if "warnings" not in result:
        warnings.append("[STRUCTURE] 'warnings' 필드가 없습니다. 추가되어야 합니다.")
    if "assumptions" not in result:
        warnings.append("[STRUCTURE] 'assumptions' 필드가 없습니다. 추가되어야 합니다.")
    
    # Check heuristic limitation notice in warnings or assumptions
    all_warnings_text = str(result.get("warnings", "")) + str(result.get("assumptions", ""))
    has_heuristic_notice = (
        "휴리스틱" in all_warnings_text or 
        "근사" in all_warnings_text or
        "예측" in all_warnings_text or
        "검증" in all_warnings_text
    )
    if not has_heuristic_notice:
        warnings.append(
            "[STRUCTURE] 휴리스틱 기반 추정이라는 한계 문구가 결과에 포함되어야 합니다."
        )
    
    return (len(warnings) == 0, warnings)

