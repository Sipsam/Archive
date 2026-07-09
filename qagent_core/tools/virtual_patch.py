from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import pandas as pd

from qagent_core.data_io import summarize_battle_metrics
from qagent_core.config import (
    BALANCE_FDR_ALPHA,
    BALANCE_MIN_SAMPLES,
    BALANCE_MIN_WILSON_DIFF,
    BALANCE_MIN_WIN_RATE,
    BALANCE_MIN_WIN_RATE_DIFF,
)
from qagent_core.simulation import (
    SCENARIO_WARNINGS,
    project_patch_scenario,
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
    validate_choice,
    validation_error_dict,
)
from .context import AnalysisContext


def build_virtual_patch_tools(context: AnalysisContext) -> dict[str, Any]:
    """Build virtual patch proposal, simulation, and reflection tools."""
    battles = context.battles
    characters = context.characters
    skills = context.skills
    equipment_sets = context.equipment_sets
    patch_notes = context.patch_notes

    def _filter_target_rows(
        player_team: str = "",
        equipment_set: str = "",
        skill_used_most: str = "",
        patch_version: str = "",
    ) -> pd.DataFrame:
        """Filter battle rows to the candidate target population."""
        df = battles.copy()
        if player_team:
            df = df[df["player_team"].astype(str) == str(player_team)]
        if equipment_set:
            df = df[df["equipment_set"].astype(str) == str(equipment_set)]
        if skill_used_most:
            df = df[df["skill_used_most"].astype(str) == str(skill_used_most)]
        if patch_version:
            df = df[df["patch_version"].astype(str) == str(patch_version)]
        return df

    def _next_virtual_patch_version(base_patch: str = "") -> str:
        """Create the next virtual patch label from a base patch version."""
        if not base_patch:
            base_patch = get_latest_patch_version(battles)
        match = re.match(r"^(\d+)\.(\d+)", str(base_patch))
        if not match:
            return f"{base_patch}-agent-candidate"
        major = int(match.group(1))
        minor_text = match.group(2)
        minor = int(minor_text)
        next_minor = minor + 1
        width = max(len(minor_text), 2)
        return f"{major}.{next_minor:0{width}d}-agent-candidate"

    def generate_virtual_patch_note(
        player_team: str,
        equipment_set: str = "",
        skill_used_most: str = "",
        patch_version: str = "",
        risk_level: str = "Medium",
        adjustment_direction: str = "auto",
        adjustment_intensity: float = 0.5,
        reasoning: str = "",
    ) -> Dict[str, Any]:
        """
        Agent가 제안한 조정안을 현 버전 이후의 가상 패치노트 후보로 구조화한다.
        실제 CSV나 게임 데이터를 수정하지 않고 HITL 검토용 후보만 생성한다.
        """
        try:
            if not player_team or not isinstance(player_team, str):
                raise ToolValidationError(
                    "player_team은 비어있지 않은 문자열이어야 합니다"
                )
            risk_level = validate_choice(
                risk_level,
                ["Low", "Medium", "High", "Critical"],
                param_name="risk_level",
            )
            adjustment_intensity = validate_float_range(
                adjustment_intensity,
                min_val=0.1,
                max_val=1.0,
                param_name="adjustment_intensity",
            )
        except ToolValidationError as e:
            return validation_error_dict(e)

        if not patch_version:
            patch_version = get_latest_patch_version(battles)

        target_df = _filter_target_rows(
            player_team=player_team,
            equipment_set=equipment_set,
            skill_used_most=skill_used_most,
            patch_version=patch_version,
        )
        if target_df.empty:
            target_df = _filter_target_rows(
                player_team=player_team,
                equipment_set=equipment_set,
                skill_used_most=skill_used_most,
            )

        if target_df.empty:
            return {
                "status": "empty",
                "message": "가상 패치노트 후보를 만들 대상 전투 기록을 찾지 못했습니다.",
                "query": {
                    "player_team": player_team,
                    "equipment_set": equipment_set,
                    "skill_used_most": skill_used_most,
                    "patch_version": patch_version,
                },
            }

        overall_summary = summarize_battle_metrics(battles)
        target_summary = summarize_battle_metrics(target_df)
        overall_wr = float(overall_summary.get("win_rate") or 0)
        target_wr = float(target_summary.get("win_rate") or 0)
        win_rate_gap = target_wr - overall_wr
        intensity = max(0.1, min(float(adjustment_intensity), 1.0))

        direction_text = normalize_text(adjustment_direction)
        if direction_text in {"auto", "", "자동"}:
            if win_rate_gap >= 0.05 or risk_level in {"Medium", "High", "Critical"}:
                direction = "nerf"
            elif win_rate_gap <= -0.05:
                direction = "buff"
            else:
                direction = "monitor"
        elif any(token in direction_text for token in ["nerf", "down", "하향", "감소"]):
            direction = "nerf"
        elif any(token in direction_text for token in ["buff", "up", "상향", "증가"]):
            direction = "buff"
        else:
            direction = "monitor"

        # 데이터 기반 근사치. 실제 게임 공식 재현이 아니라 패치 후보 검토용 보수적 추정값이다.
        base_delta = min(0.10, max(0.025, abs(win_rate_gap) * 0.35 + 0.015)) * intensity
        if risk_level == "High":
            base_delta *= 1.25
        elif risk_level == "Low":
            base_delta *= 0.65

        if direction == "nerf":
            estimated_win_rate_delta_points = -round(min(base_delta, 0.08), 4)
            estimated_damage_delta_percent = -round(
                min(0.04 + intensity * 0.08, 0.14), 4
            )
            action_word = "하향"
            balance_intent = "과도한 성능 상승 완화"
        elif direction == "buff":
            estimated_win_rate_delta_points = round(min(base_delta, 0.06), 4)
            estimated_damage_delta_percent = round(
                min(0.03 + intensity * 0.06, 0.10), 4
            )
            action_word = "상향"
            balance_intent = "저조한 성능 보정"
        else:
            estimated_win_rate_delta_points = 0.0
            estimated_damage_delta_percent = 0.0
            action_word = "모니터링"
            balance_intent = "추가 데이터 확보 전 보류"

        target_parts = [player_team]
        if equipment_set:
            target_parts.append(f"대표 아이템: {equipment_set}")
        if skill_used_most:
            target_parts.append(f"포지션: {skill_used_most}")
        target_label = " / ".join(target_parts)

        virtual_patch_version = _next_virtual_patch_version(patch_version)
        patch_note_lines = [
            f"## Virtual Patch {virtual_patch_version}",
            "",
            f"### {target_label}",
            f"- 조정 방향: {action_word}",
            f"- 조정 의도: {balance_intent}",
            f"- 가정 승률 변화: {estimated_win_rate_delta_points * 100:.1f}%p",
            f"- 가정 평균 피해량 변화: {estimated_damage_delta_percent * 100:.1f}%",
            f"- 근거: 현재 승률 {target_wr * 100:.1f}%, 전체 평균 대비 {win_rate_gap * 100:.1f}%p, 표본 {target_summary['battles']:,}전",
            "- 적용 상태: 실제 반영 아님. Agent 후보안이며 Human Review 승인 전까지 보류.",
        ]
        if reasoning:
            patch_note_lines.append(f"- Agent 작성 사유: {reasoning}")

        return {
            "status": "ok",
            "virtual_patch_note": {
                "virtual_patch_version": virtual_patch_version,
                "base_patch_version": patch_version,
                "target": target_label,
                "player_team": player_team,
                "equipment_set": equipment_set,
                "skill_used_most": skill_used_most,
                "risk_level": risk_level,
                "action": action_word,
                "direction": direction,
                "balance_intent": balance_intent,
                "estimated_win_rate_delta_points": estimated_win_rate_delta_points,
                "estimated_damage_delta_percent": estimated_damage_delta_percent,
                "source_metrics": target_summary,
                "overall_metrics": overall_summary,
                "win_rate_gap": round(win_rate_gap, 4),
                "reasoning": reasoning,
            },
            "patch_note_markdown": "\n".join(patch_note_lines),
            "human_review_gate": {
                "required": True,
                "allowed_decisions": [
                    "Approve Virtual Patch",
                    "Reject Virtual Patch",
                    "Needs Revision",
                    "Retest Required",
                    "Save as Candidate",
                ],
                "control": "이 가상 패치노트는 실제 데이터나 게임 설정을 변경하지 않는다. 사람 승인 전까지 후보안으로만 취급한다.",
            },
        }

    def simulate_virtual_patch_impact(
        player_team: str,
        equipment_set: str = "",
        skill_used_most: str = "",
        base_patch_version: str = "",
        virtual_patch_version: str = "",
        expected_win_rate_delta_points: float = 0.0,
        expected_damage_delta_percent: float = 0.0,
    ) -> Dict[str, Any]:
        """
        가상 패치노트가 현 버전 이후 적용되었다고 가정하고 결과를 근사 추론한다.
        실제 게임 시뮬레이터가 아니라 통계 기반 counterfactual 추정이다.
        """
        try:
            if not player_team or not isinstance(player_team, str):
                raise ToolValidationError(
                    "player_team은 비어있지 않은 문자열이어야 합니다"
                )
            expected_win_rate_delta_points = validate_float_range(
                expected_win_rate_delta_points,
                min_val=-1.0,
                max_val=1.0,
                param_name="expected_win_rate_delta_points",
            )
            expected_damage_delta_percent = validate_float_range(
                expected_damage_delta_percent,
                min_val=-1.0,
                max_val=1.0,
                param_name="expected_damage_delta_percent",
            )
        except ToolValidationError as e:
            return validation_error_dict(e)

        if not base_patch_version:
            base_patch_version = get_latest_patch_version(battles)
        if not virtual_patch_version:
            virtual_patch_version = _next_virtual_patch_version(base_patch_version)

        target_df = _filter_target_rows(
            player_team=player_team,
            equipment_set=equipment_set,
            skill_used_most=skill_used_most,
            patch_version=base_patch_version,
        )
        if target_df.empty:
            target_df = _filter_target_rows(
                player_team=player_team,
                equipment_set=equipment_set,
                skill_used_most=skill_used_most,
            )

        if target_df.empty:
            return {
                "status": "empty",
                "message": "가상 패치 시나리오 추정 대상 전투 기록을 찾지 못했습니다.",
                "warnings": list(SCENARIO_WARNINGS),
                "query": {
                    "player_team": player_team,
                    "equipment_set": equipment_set,
                    "skill_used_most": skill_used_most,
                    "base_patch_version": base_patch_version,
                },
            }

        overall_summary = summarize_battle_metrics(battles)
        before = summarize_battle_metrics(target_df)

        wr_before = float(before.get("win_rate") or 0)
        dmg_before = float(before.get("avg_damage") or 0)
        duration_before = float(before.get("avg_duration_sec") or 0)

        wr_delta = float(expected_win_rate_delta_points)
        dmg_delta = float(expected_damage_delta_percent)

        projected = project_patch_scenario(
            wr_before, dmg_before, duration_before, wr_delta, dmg_delta
        )
        scenarios = project_patch_scenario_range(
            wr_before, dmg_before, duration_before, wr_delta, dmg_delta
        )

        is_valid, validation_warnings = validate_patch_scenario_result(scenarios)

        wr_after = projected["win_rate"]
        dmg_after = projected["avg_damage"]
        duration_after = projected["avg_duration_sec"]

        sample_size = int(before.get("battles") or 0)
        if sample_size >= 300:
            confidence = "Medium-High"
        elif sample_size >= 100:
            confidence = "Medium"
        elif sample_size >= 30:
            confidence = "Low-Medium"
        else:
            confidence = "Low"

        segment_rows = []
        if "user_segment" in target_df.columns:
            for segment, seg_df in target_df.groupby("user_segment"):
                seg_before = summarize_battle_metrics(seg_df)
                seg_wr = float(seg_before.get("win_rate") or 0)
                seg_dmg = float(seg_before.get("avg_damage") or 0)
                segment_rows.append(
                    {
                        "user_segment": str(segment),
                        "battles": seg_before.get("battles"),
                        "before_win_rate": seg_before.get("win_rate"),
                        "projected_win_rate": round(
                            min(max(seg_wr + wr_delta, 0.01), 0.99), 4
                        ),
                        "before_avg_damage": seg_before.get("avg_damage"),
                        "projected_avg_damage": round(
                            max(seg_dmg * (1 + dmg_delta), 0), 2
                        ),
                    }
                )

        return {
            "status": "ok",
            "method": (
                "휴리스틱 기반 시나리오 추정. 입력한 승률·피해량 변화 가정을 단순 계산한 결과이며, "
                "학습된 예측 모델·인과 추론·게임 엔진 시뮬레이션 또는 라이브 패치 결과가 아니다."
            ),
            "result_type": "assumption_based_scenario_estimate",
            "base_patch_version": base_patch_version,
            "virtual_patch_version": virtual_patch_version,
            "target": {
                "player_team": player_team,
                "equipment_set": equipment_set,
                "skill_used_most": skill_used_most,
            },
            "input_assumptions": {
                "expected_win_rate_delta_points": round(wr_delta, 4),
                "expected_damage_delta_percent": round(dmg_delta, 4),
            },
            "before": before,
            "projected_after": {
                "win_rate": round(wr_after, 4),
                "avg_damage": round(dmg_after, 2),
                "avg_duration_sec": round(duration_after, 2),
                "win_rate_vs_overall_after": round(
                    wr_after - float(overall_summary.get("win_rate") or 0), 4
                ),
            },
            "scenarios": scenarios,
            "warnings": list(SCENARIO_WARNINGS) + validation_warnings,
            "assumptions": [
                "휴리스틱 기반 시나리오 추정으로 실제 게임 패치 결과를 예측하지 못합니다.",
                "입력한 승률·피해량 변화 가정이 정확할수록 추정값의 신뢰도가 높아집니다.",
                "실제 패치 전 QA 테스트 및 검증이 필수입니다.",
            ],
            "segment_projection": segment_rows[:20],
            "confidence": confidence,
            "uncertainties": [
                "플레이어 숙련도, 챔피언 밴픽, 상대 조합, 아이템 빌드 변화는 완전히 통제하지 못함",
                "가상 패치 이후 실제 메타 적응 효과는 로그에 아직 존재하지 않음",
                "승률 변화는 피해량 변화와 선형 관계라고 단순화한 근사값임",
            ],
            "data_mutation": "없음. 실제 battle_logs.csv나 패치노트 파일은 수정하지 않음.",
        }

    def reflect_on_virtual_patch(
        player_team: str,
        equipment_set: str = "",
        skill_used_most: str = "",
        base_patch_version: str = "",
        virtual_patch_version: str = "",
        projected_win_rate: float = 0.0,
        projected_damage_delta_percent: float = 0.0,
        human_decision_context: str = "",
    ) -> Dict[str, Any]:
        """
        Agent가 자신이 만든 가상 패치노트의 위험성과 한계를 비판적으로 검토한다.
        최종 승인 여부는 사람이 판단한다.
        """
        if not base_patch_version:
            base_patch_version = get_latest_patch_version(battles)
        if not virtual_patch_version:
            virtual_patch_version = _next_virtual_patch_version(base_patch_version)

        target_df = _filter_target_rows(
            player_team=player_team,
            equipment_set=equipment_set,
            skill_used_most=skill_used_most,
            patch_version=base_patch_version,
        )
        if target_df.empty:
            target_df = _filter_target_rows(
                player_team=player_team,
                equipment_set=equipment_set,
                skill_used_most=skill_used_most,
            )

        if target_df.empty:
            return {
                "status": "empty",
                "message": "자기반성 대상 전투 기록을 찾지 못했습니다.",
            }

        overall = summarize_battle_metrics(battles)
        before = summarize_battle_metrics(target_df)
        overall_wr = float(overall.get("win_rate") or 0)
        before_wr = float(before.get("win_rate") or 0)
        projected_wr = float(projected_win_rate) if projected_win_rate else before_wr
        sample_size = int(before.get("battles") or 0)
        damage_delta = float(projected_damage_delta_percent)

        concerns = []
        positives = []
        revision_suggestions = []

        if sample_size < 30:
            concerns.append("표본 수가 30전 미만이라 가상 패치 추론 신뢰도가 낮음")
            revision_suggestions.append(
                "패치 후보 승인 전에 동일 조건 전투 로그를 추가 수집"
            )
        elif sample_size < 100:
            concerns.append(
                "표본 수가 충분하지 않아 티어별/포지션별 분리 검증이 필요함"
            )
        else:
            positives.append("표본 수가 최소 검토 기준을 어느 정도 충족함")

        if projected_wr < overall_wr - 0.05:
            concerns.append(
                "가상 패치 시나리오 승률이 전체 평균보다 5%p 이상 낮아질 수 있어 과조정 위험이 있음"
            )
            revision_suggestions.append("하향 폭을 줄이거나 단계적 조정안으로 분리")
        elif abs(projected_wr - overall_wr) <= 0.05:
            positives.append(
                "가상 패치 시나리오 승률이 전체 평균 근처로 수렴할 가능성이 있음"
            )
        elif projected_wr > overall_wr + 0.10:
            concerns.append(
                "가상 패치 후에도 전체 평균보다 10%p 이상 높게 남을 수 있음"
            )
            revision_suggestions.append(
                "조정폭을 재검토하거나 아이템/룬/포지션 원인을 추가 분석"
            )

        if abs(damage_delta) >= 0.12:
            concerns.append(
                "평균 피해량 변화 가정이 12% 이상으로 커서 체감 변화가 과도할 수 있음"
            )
            revision_suggestions.append(
                "피해량 조정보다 쿨다운, 성장값, 아이템 상호작용 등 대안을 비교"
            )
        else:
            positives.append("피해량 변화 가정이 비교적 보수적인 범위에 있음")

        if "|" in str(
            target_df.get("user_segment", pd.Series(dtype=str)).astype(str).iloc[0]
            if not target_df.empty and "user_segment" in target_df.columns
            else ""
        ):
            concerns.append(
                "source_tiers가 여러 티어로 묶여 있어 특정 티어 영향이 흐려질 수 있음"
            )

        if not revision_suggestions:
            revision_suggestions.append(
                "가상 패치 후보를 저장하고 QA/밸런스 담당자가 승인 여부를 검토"
            )

        if concerns and sample_size < 100:
            agent_recommendation = "Retest Required"
        elif any("과조정" in c for c in concerns):
            agent_recommendation = "Needs Revision"
        elif projected_wr > overall_wr + 0.10:
            agent_recommendation = "Needs Revision"
        else:
            agent_recommendation = "Human Approval Required"

        return {
            "status": "ok",
            "virtual_patch_version": virtual_patch_version,
            "target": {
                "player_team": player_team,
                "equipment_set": equipment_set,
                "skill_used_most": skill_used_most,
            },
            "self_reflection": {
                "positives": positives,
                "concerns": concerns,
                "revision_suggestions": revision_suggestions,
                "agent_recommendation": agent_recommendation,
                "human_decision_context": human_decision_context,
            },
            "comparison": {
                "overall_win_rate": round(overall_wr, 4),
                "before_win_rate": round(before_wr, 4),
                "projected_win_rate": round(projected_wr, 4),
                "sample_size": sample_size,
                "projected_damage_delta_percent": round(damage_delta, 4),
            },
            "hitl_gate": {
                "final_decision_owner": "Human reviewer",
                "allowed_decisions": [
                    "Approve Virtual Patch",
                    "Reject Virtual Patch",
                    "Needs Revision",
                    "Retest Required",
                    "Save as Candidate",
                ],
                "note": "Agent의 자기반성은 검토 보조 자료이며 최종 승인/거절은 사람이 선택한다.",
            },
        }

    return {
        "generate_virtual_patch_note": generate_virtual_patch_note,
        "simulate_virtual_patch_impact": simulate_virtual_patch_impact,
        "reflect_on_virtual_patch": reflect_on_virtual_patch,
    }
