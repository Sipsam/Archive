from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from qagent_core.config import (
    BALANCE_FDR_ALPHA,
    BALANCE_MIN_SAMPLES,
    BALANCE_MIN_WILSON_DIFF,
    BALANCE_MIN_WIN_RATE,
    BALANCE_MIN_WIN_RATE_DIFF,
)
from qagent_core.simulation import (
    SCENARIO_WARNINGS,
    project_patch_scenario_range,
    validate_patch_scenario_result,
)
from qagent_core.statistics import (
    analyze_balance_stages,
    detect_balance_candidates,
    win_rate,
)
from qagent_core.utils import (
    apply_lol_patch_version_mapping,
    ensure_column,
    first_existing_column,
    format_value,
    get_latest_patch_version,
    get_previous_patch_version,
    normalize_text,
    parse_number,
    patch_sort_key,
    pct,
    search_lol_stat_knowledge,
    split_team,
    to_jsonable_df,
)
from .validators import (
    ToolValidationError,
    validate_float_range,
    validate_int_range,
    validate_top_n,
    validation_error_dict,
)
from .context import AnalysisContext
from .patch import build_patch_tools


def build_balance_tools(context: AnalysisContext) -> dict[str, Any]:
    """Build statistical balance, formula, and adjustment proposal tools."""
    battles = context.battles
    characters = context.characters
    skills = context.skills
    equipment_sets = context.equipment_sets
    patch_notes = context.patch_notes
    retrieve_related_knowledge = build_patch_tools(context)[
        "retrieve_related_knowledge"
    ]

    def detect_anomalies(
        min_samples: int = BALANCE_MIN_SAMPLES,
        win_rate_threshold: float = BALANCE_MIN_WIN_RATE,
        win_rate_gap_threshold: float = BALANCE_MIN_WIN_RATE_DIFF,
        wilson_lower_gap_threshold: float = BALANCE_MIN_WILSON_DIFF,
        segment_by: str = "",
        fdr_alpha: float = BALANCE_FDR_ALPHA,
        top_n: int = 10,
    ) -> Dict[str, Any]:
        """Detect balance anomalies with input validation."""
        try:
            min_samples = validate_int_range(
                min_samples, min_val=1, max_val=10000, param_name="min_samples"
            )
            win_rate_threshold = validate_float_range(
                win_rate_threshold,
                min_val=0.0,
                max_val=1.0,
                param_name="win_rate_threshold",
            )
            win_rate_gap_threshold = validate_float_range(
                win_rate_gap_threshold,
                min_val=0.0,
                max_val=1.0,
                param_name="win_rate_gap_threshold",
            )
            wilson_lower_gap_threshold = validate_float_range(
                wilson_lower_gap_threshold,
                min_val=0.0,
                max_val=1.0,
                param_name="wilson_lower_gap_threshold",
            )
            fdr_alpha = validate_float_range(
                fdr_alpha, min_val=0.0, max_val=1.0, param_name="fdr_alpha"
            )
            top_n = validate_top_n(top_n, max_top_n=100, default_top_n=10)
        except ToolValidationError as e:
            return validation_error_dict(e)

        try:
            overall_wr, anomalies = detect_balance_candidates(
                battles,
                min_samples=min_samples,
                win_rate_threshold=win_rate_threshold,
                win_rate_gap_threshold=win_rate_gap_threshold,
                wilson_lower_gap_threshold=wilson_lower_gap_threshold,
                segment_by=segment_by,
                fdr_alpha=fdr_alpha,
            )
            staged_analysis = analyze_balance_stages(
                battles,
                min_samples=min_samples,
                win_rate_threshold=win_rate_threshold,
                effect_size_threshold=win_rate_gap_threshold,
                wilson_lower_gap_threshold=wilson_lower_gap_threshold,
                fdr_alpha=fdr_alpha,
                top_n=top_n,
            )
            for col in [
                "win_rate",
                "win_rate_gap",
                "damage_index",
                "sample_confidence",
                "candidate_score",
                "anomaly_score",
                "win_rate_ci_low",
                "win_rate_ci_high",
                "ci_width",
                "global_win_rate",
                "win_rate_diff",
                "wilson_low",
                "wilson_high",
                "p_value",
                "fdr_q_value",
            ]:
                anomalies[col] = anomalies[col].round(4)
            anomalies["avg_damage"] = anomalies["avg_damage"].round(2)
            anomalies["avg_duration_sec"] = anomalies["avg_duration_sec"].round(2)

            return {
                "status": "ok",
                "overall_win_rate": round(overall_wr, 4),
                "criteria": {
                    "min_samples": min_samples,
                    "win_rate_threshold": win_rate_threshold,
                    "win_rate_gap_threshold": win_rate_gap_threshold,
                    "confidence_interval": "95% Wilson score interval",
                    "wilson_lower_gap_threshold": wilson_lower_gap_threshold,
                    "segment_by": segment_by or "none",
                    "fdr_method": "Benjamini-Hochberg",
                    "fdr_alpha": fdr_alpha,
                },
                "data_availability": {
                    "pick_rate": "not_available",
                    "ban_rate": "not_available",
                },
                "interpretation": (
                    "결과는 밸런스 이상 확정이 아니라 사람의 추가 검토가 필요한 후보 목록이다. "
                    "다중 비교는 FDR로 보정했지만 픽률/밴률 데이터는 없으며, 플레이어 숙련도와 상대 조합은 완전히 통제하지 않는다."
                ),
                "anomalies": to_jsonable_df(anomalies, top_n),
                "candidates": to_jsonable_df(anomalies, top_n),
                "staged_analysis": staged_analysis,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"detect_anomalies 실행 중 오류: {str(e)[:200]}",
            }

    def analyze_segment_performance(
        player_team: str, equipment_set: str = "", skill_used_most: str = ""
    ) -> Dict[str, Any]:
        """초보/중수/상위 유저 구간별로 문제가 특정 세그먼트에 집중되는지 확인."""
        try:
            if not player_team or not isinstance(player_team, str):
                raise ToolValidationError(
                    "player_team은 비어있지 않은 문자열이어야 합니다"
                )
        except ToolValidationError as e:
            return validation_error_dict(e)

        df = battles[battles["player_team"].astype(str) == player_team].copy()
        if equipment_set:
            df = df[df["equipment_set"].astype(str) == equipment_set]
        if skill_used_most:
            df = df[df["skill_used_most"].astype(str) == skill_used_most]

        if df.empty:
            return {"status": "empty", "message": "matching battle logs not found"}

        result = (
            df.groupby(["patch_version", "user_segment"])
            .agg(
                battles=("battle_id", "count"),
                win_rate=("result", win_rate),
                avg_damage=("total_damage", "mean"),
                avg_duration_sec=("duration_sec", "mean"),
            )
            .reset_index()
            .sort_values(["patch_version", "win_rate"], ascending=[True, False])
        )
        result["win_rate"] = result["win_rate"].round(4)
        result["avg_damage"] = result["avg_damage"].round(2)
        result["avg_duration_sec"] = result["avg_duration_sec"].round(2)

        return {
            "status": "ok",
            "query": {
                "player_team": player_team,
                "equipment_set": equipment_set,
                "skill_used_most": skill_used_most,
            },
            "rows": to_jsonable_df(result, 30),
        }

    def simulate_stat_impact(
        player_team: str, equipment_set: str, skill_used_most: str, patch_version: str
    ) -> Dict[str, Any]:
        """스킬 계수, 공격력, 세트 보너스, 버프성 패치가 피해량에 미치는 영향을 근사 계산."""
        team_members = split_team(player_team)

        dealer_name = None
        dealer_row = characters[
            characters["main_skill"].astype(str).str.lower()
            == str(skill_used_most).lower()
        ]
        if not dealer_row.empty:
            dealer_name = str(dealer_row.iloc[0]["name"])
        else:
            skill_row = skills[
                skills["skill_name"].astype(str).str.lower()
                == str(skill_used_most).lower()
            ]
            if not skill_row.empty:
                dealer_name = str(skill_row.iloc[0]["character"])

        if not dealer_name and team_members:
            dealer_name = team_members[0]

        char_row = characters[characters["name"].astype(str) == str(dealer_name)]
        skill_row = skills[
            skills["skill_name"].astype(str).str.lower() == str(skill_used_most).lower()
        ]
        equip_row = equipment_sets[
            equipment_sets["set_name"].astype(str).str.lower()
            == str(equipment_set).lower()
        ]

        base_attack = (
            float(char_row.iloc[0]["base_attack"])
            if not char_row.empty
            and str(char_row.iloc[0]["base_attack"]).replace(".", "", 1).isdigit()
            else 0
        )
        current_multiplier = (
            float(skill_row.iloc[0]["damage_multiplier"])
            if not skill_row.empty
            and str(skill_row.iloc[0]["damage_multiplier"])
            .replace(".", "", 1)
            .isdigit()
            else 1.0
        )

        current_set_bonus = 0.0
        if not equip_row.empty:
            current_set_bonus_number, suffix = parse_number(
                equip_row.iloc[0].get("bonus_value", "0")
            )
            if current_set_bonus_number is not None:
                current_set_bonus = (
                    current_set_bonus_number / 100
                    if suffix == "%"
                    else current_set_bonus_number
                )

        knowledge = retrieve_related_knowledge(
            player_team, equipment_set, skill_used_most, patch_version
        )
        before_multiplier = current_multiplier
        after_multiplier = current_multiplier
        before_set_bonus = current_set_bonus
        after_set_bonus = current_set_bonus
        before_buff = 0.0
        after_buff = 0.0

        for patch in knowledge["patch_matches"]:
            target = normalize_text(patch["change_target"])
            before, before_suffix = parse_number(patch["before_value"])
            after, after_suffix = parse_number(patch["after_value"])

            if before is None or after is None:
                continue

            if normalize_text(skill_used_most) in target and (
                "multiplier" in target or "계수" in target
            ):
                before_multiplier = before
                after_multiplier = after

            if normalize_text(equipment_set) in target and (
                "bonus" in target or "set" in target or "세트" in target
            ):
                before_set_bonus = before / 100 if before_suffix == "%" else before
                after_set_bonus = after / 100 if after_suffix == "%" else after

            if (
                "critical" in target
                or "crit" in target
                or "치명" in target
                or "attack speed" in target
            ):
                before_buff += before / 100 if before_suffix == "%" else before
                after_buff += after / 100 if after_suffix == "%" else after

        estimated_before_damage = (
            base_attack * before_multiplier * (1 + before_set_bonus) * (1 + before_buff)
        )
        estimated_after_damage = (
            base_attack * after_multiplier * (1 + after_set_bonus) * (1 + after_buff)
        )
        increase_rate = estimated_after_damage / max(estimated_before_damage, 1) - 1

        return {
            "status": "ok",
            "query": {
                "player_team": player_team,
                "dealer_name": dealer_name,
                "equipment_set": equipment_set,
                "skill_used_most": skill_used_most,
                "patch_version": patch_version,
            },
            "assumptions": [
                "실제 게임 전투 공식이 아닌 MVP용 근사 계산이다.",
                "base_attack × skill_multiplier × set_bonus × buff_bonus 형태로 단순화했다.",
                "방어력, 속성 상성, 랜덤 치명타, 회피, 피해 감소는 제외했다.",
            ],
            "before": {
                "base_attack": base_attack,
                "skill_multiplier": before_multiplier,
                "set_bonus": round(before_set_bonus, 4),
                "buff_bonus": round(before_buff, 4),
                "estimated_damage_index": round(estimated_before_damage, 2),
            },
            "after": {
                "base_attack": base_attack,
                "skill_multiplier": after_multiplier,
                "set_bonus": round(after_set_bonus, 4),
                "buff_bonus": round(after_buff, 4),
                "estimated_damage_index": round(estimated_after_damage, 2),
            },
            "estimated_increase_rate": round(increase_rate, 4),
            "retrieved_patch_matches": knowledge["patch_matches"],
        }

    def calculate_adjustment_options(
        player_team: str,
        equipment_set: str,
        skill_used_most: str,
        patch_version: str,
        rollback_strength: float = 0.5,
    ) -> Dict[str, Any]:
        """Create rollback-style adjustment options from related patch notes."""
        knowledge = retrieve_related_knowledge(
            player_team, equipment_set, skill_used_most, patch_version
        )
        actions = []

        for patch in knowledge["patch_matches"]:
            before, suffix_before = parse_number(patch["before_value"])
            after, suffix_after = parse_number(patch["after_value"])

            if before is None or after is None:
                actions.append(
                    {
                        "target": patch["change_target"],
                        "proposal": "수치형 변경이 아니므로 직접 조정보다 추가 재테스트를 우선 수행",
                        "basis": "before/after 값이 숫자로 해석되지 않음",
                    }
                )
                continue

            suffix = suffix_after or suffix_before
            if after > before:
                proposed = after - (after - before) * rollback_strength
                direction = "하향"
            elif after < before:
                proposed = after + (before - after) * rollback_strength
                direction = "상향 복구"
            else:
                proposed = after
                direction = "유지"

            actions.append(
                {
                    "target": patch["change_target"],
                    "before": format_value(before, suffix),
                    "current": format_value(after, suffix),
                    "proposal": f"{format_value(after, suffix)} → {format_value(proposed, suffix)} {direction} 검토",
                    "basis": "이상 조합과 연결된 최근 패치 변경사항의 일부를 되돌리는 완만한 조정안",
                }
            )

        if not actions:
            actions.append(
                {
                    "target": "추가 분석",
                    "proposal": "패치노트 직접 근거가 부족하므로 스킬별 피해량, 버프 중첩, 장비 옵션 로그를 추가 수집",
                    "basis": "검색된 patch_matches가 없어 수치 조정안을 계산할 수 없음",
                }
            )

        return {
            "status": "ok",
            "rollback_strength": rollback_strength,
            "actions": actions,
        }

    def retrieve_lol_stat_knowledge(
        query: str = "", stats: Optional[List[str]] = None, max_rows: int = 10
    ) -> Dict[str, Any]:
        """LoL 스탯 설명과 계산 공식을 검색한다."""
        rows = search_lol_stat_knowledge(query=query, stats=stats, max_rows=max_rows)
        return {
            "status": "ok",
            "query": query,
            "stats": stats or [],
            "rows": rows,
            "note": "공식은 과제용 근사 계산에 사용하며, 실제 게임 내부 처리와 예외 효과는 챔피언/아이템별로 다를 수 있습니다.",
        }

    def calculate_lol_stat_formulas(
        raw_damage: float = 1000,
        health: float = 1000,
        armor: float = 0,
        magic_resist: float = 0,
        ability_haste: float = 0,
        base_attack_speed: float = 0.625,
        attack_speed_ratio: float = 0.625,
        bonus_attack_speed_percent: float = 0,
    ) -> Dict[str, Any]:
        """LoL 기본 스탯 공식으로 방어/마저/가속/공속 값을 계산한다."""

        def positive_resist_damage(raw: float, resist: float) -> float:
            """Approximate post-mitigation damage for positive or negative resist."""
            if resist >= 0:
                return raw * 100 / (100 + resist)
            return raw * (2 - 100 / (100 - resist))

        physical_post = positive_resist_damage(float(raw_damage), float(armor))
        magic_post = positive_resist_damage(float(raw_damage), float(magic_resist))
        physical_reduction = 1 - physical_post / max(float(raw_damage), 1)
        magic_reduction = 1 - magic_post / max(float(raw_damage), 1)
        effective_health_physical = (
            float(health) * (1 + float(armor) / 100) if armor >= 0 else None
        )
        effective_health_magic = (
            float(health) * (1 + float(magic_resist) / 100)
            if magic_resist >= 0
            else None
        )

        cooldown_multiplier = 100 / (100 + max(float(ability_haste), 0))
        cooldown_reduction = 1 - cooldown_multiplier

        total_attack_speed = float(base_attack_speed) + float(attack_speed_ratio) * (
            float(bonus_attack_speed_percent) / 100
        )
        capped_attack_speed = min(max(total_attack_speed, 0.2), 2.5)

        return {
            "status": "ok",
            "input": {
                "raw_damage": raw_damage,
                "health": health,
                "armor": armor,
                "magic_resist": magic_resist,
                "ability_haste": ability_haste,
                "base_attack_speed": base_attack_speed,
                "attack_speed_ratio": attack_speed_ratio,
                "bonus_attack_speed_percent": bonus_attack_speed_percent,
            },
            "defense": {
                "post_physical_damage": round(physical_post, 2),
                "physical_damage_reduction": round(physical_reduction, 4),
                "effective_health_vs_physical": round(effective_health_physical, 2)
                if effective_health_physical is not None
                else None,
                "post_magic_damage": round(magic_post, 2),
                "magic_damage_reduction": round(magic_reduction, 4),
                "effective_health_vs_magic": round(effective_health_magic, 2)
                if effective_health_magic is not None
                else None,
            },
            "haste": {
                "cooldown_multiplier": round(cooldown_multiplier, 4),
                "cooldown_reduction": round(cooldown_reduction, 4),
                "example_10s_cooldown_after_haste": round(10 * cooldown_multiplier, 2),
            },
            "attack_speed": {
                "total_attack_speed_before_cap": round(total_attack_speed, 4),
                "capped_attack_speed": round(capped_attack_speed, 4),
                "cap_note": "일반적으로 2.5 attacks/sec 상한을 적용합니다. 일부 효과는 예외적으로 상한을 바꿀 수 있습니다.",
            },
            "formula_references": search_lol_stat_knowledge(
                stats=["Armor", "Magic resistance", "Haste", "Attack speed"],
                max_rows=10,
            ),
        }

    return {
        "detect_anomalies": detect_anomalies,
        "analyze_segment_performance": analyze_segment_performance,
        "simulate_stat_impact": simulate_stat_impact,
        "calculate_adjustment_options": calculate_adjustment_options,
        "retrieve_lol_stat_knowledge": retrieve_lol_stat_knowledge,
        "calculate_lol_stat_formulas": calculate_lol_stat_formulas,
    }
