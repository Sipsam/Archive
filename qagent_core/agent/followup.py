from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from qagent_core.config import AGENT_TIMEOUT_SECONDS, MAX_AGENT_ITERATIONS, MAX_TOOL_CALLS
from qagent_core.runtime import new_run_id, safe_error_message, safe_for_log
from qagent_core.tool_executor import ToolExecutor
from qagent_core.tool_registry import TOOL_SCHEMAS

from .presentation import TOOL_DISPLAY_INFO, summarize_tool_result



def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default

def _build_simulation_args_from_virtual_patch(virtual_patch: Dict[str, Any]) -> Dict[str, Any]:
    note = virtual_patch.get("virtual_patch_note", {}) if isinstance(virtual_patch, dict) else {}
    return {
        "player_team": str(note.get("player_team", "") or ""),
        "equipment_set": str(note.get("equipment_set", "") or ""),
        "skill_used_most": str(note.get("skill_used_most", "") or ""),
        "base_patch_version": str(note.get("base_patch_version", "") or ""),
        "virtual_patch_version": str(note.get("virtual_patch_version", "") or ""),
        "expected_win_rate_delta_points": _safe_float(note.get("estimated_win_rate_delta_points"), 0.0),
        "expected_damage_delta_percent": _safe_float(note.get("estimated_damage_delta_percent"), 0.0),
    }

def _build_reflection_args_from_virtual_patch_and_simulation(
    virtual_patch: Dict[str, Any],
    virtual_simulation: Dict[str, Any],
) -> Dict[str, Any]:
    note = virtual_patch.get("virtual_patch_note", {}) if isinstance(virtual_patch, dict) else {}
    after = virtual_simulation.get("projected_after", {}) if isinstance(virtual_simulation, dict) else {}
    return {
        "player_team": str(note.get("player_team", "") or ""),
        "equipment_set": str(note.get("equipment_set", "") or ""),
        "skill_used_most": str(note.get("skill_used_most", "") or ""),
        "base_patch_version": str(note.get("base_patch_version", "") or ""),
        "virtual_patch_version": str(note.get("virtual_patch_version", "") or ""),
        "projected_win_rate": _safe_float(after.get("win_rate"), 0.0),
        "projected_damage_delta_percent": _safe_float(note.get("estimated_damage_delta_percent"), 0.0),
        "human_decision_context": "가상 패치노트 생성 이후 필수 후속 검증 단계로 자동 실행됨",
    }

def _append_forced_tool_step(
    trace: List[Dict[str, Any]],
    tool_name: str,
    args: Dict[str, Any],
    tool_executor: ToolExecutor,
    update_live=None,
) -> Dict[str, Any]:
    info = TOOL_DISPLAY_INFO.get(tool_name, {"label": tool_name, "analysis": ""})
    if update_live is not None:
        update_live(f"{info.get('label', tool_name)} 자동 보완 실행 중")
    next_turn = max([int(step.get("turn", 0) or 0) for step in trace] + [0]) + 1
    result = tool_executor.execute(
        tool_name, args, turn=next_turn, forced_by_app=True
    )
    if update_live is not None:
        update_live(f"{info.get('label', tool_name)} 자동 보완 완료")
    return result

def ensure_virtual_patch_followup_tools(
    final_answer: str,
    trace: List[Dict[str, Any]],
    tool_functions: Dict[str, Any],
    update_live=None,
    tool_executor: Optional[ToolExecutor] = None,
) -> str:
    """
    LLM이 generate_virtual_patch_note까지만 호출하고 멈추는 경우가 있다.
    이 함수는 가상 패치노트가 존재하면 simulate_virtual_patch_impact와
    reflect_on_virtual_patch를 앱 레벨에서 반드시 실행해 HITL 검토 자료가 비지 않도록 보장한다.
    """
    virtual_patch = get_latest_tool_result(trace, "generate_virtual_patch_note")
    if not virtual_patch or virtual_patch.get("status") != "ok":
        return final_answer
    if tool_executor is None:
        # Compatibility path for direct callers; all Agent paths pass their
        # existing executor so forced calls share the same counter and timeout.
        tool_executor = ToolExecutor(
            tool_functions=tool_functions,
            trace=trace,
            run_id=str(trace[0].get("run_id", "")) if trace else new_run_id(),
            runtime_state={"tool_calls": sum(bool(step.get("success")) for step in trace)},
            started_at=time.monotonic(),
            max_tool_calls=MAX_TOOL_CALLS,
            timeout_seconds=AGENT_TIMEOUT_SECONDS,
            result_summarizer=summarize_tool_result,
        )

    auto_messages = []

    virtual_simulation = get_latest_tool_result(trace, "simulate_virtual_patch_impact")
    if not virtual_simulation:
        sim_args = _build_simulation_args_from_virtual_patch(virtual_patch)
        if sim_args.get("player_team"):
            virtual_simulation = _append_forced_tool_step(
                trace=trace,
                tool_name="simulate_virtual_patch_impact",
                args=sim_args,
                tool_executor=tool_executor,
                update_live=update_live,
            )
            if virtual_simulation.get("status") == "ok":
                auto_messages.append("- `simulate_virtual_patch_impact`를 앱이 자동 실행해 가상 적용 시나리오 추정을 보완했습니다.")
            else:
                auto_messages.append("- `simulate_virtual_patch_impact` 자동 실행은 안전 제한 또는 오류로 완료되지 않았습니다.")

    virtual_reflection = get_latest_tool_result(trace, "reflect_on_virtual_patch")
    if not virtual_reflection:
        # 방금 자동 실행한 simulation 또는 기존 simulation을 사용한다.
        virtual_simulation = get_latest_tool_result(trace, "simulate_virtual_patch_impact") or virtual_simulation or {}
        reflection_args = _build_reflection_args_from_virtual_patch_and_simulation(virtual_patch, virtual_simulation)
        if reflection_args.get("player_team"):
            reflection_result = _append_forced_tool_step(
                trace=trace,
                tool_name="reflect_on_virtual_patch",
                args=reflection_args,
                tool_executor=tool_executor,
                update_live=update_live,
            )
            if reflection_result.get("status") == "ok":
                auto_messages.append("- `reflect_on_virtual_patch`를 앱이 자동 실행해 Agent 자기반성 자료를 보완했습니다.")
            else:
                auto_messages.append("- `reflect_on_virtual_patch` 자동 실행은 안전 제한 또는 오류로 완료되지 않았습니다.")

    if auto_messages:
        final_answer = (final_answer or "") + "\n\n---\n\n## 앱 자동 보완: Virtual Patch 후속 검증\n"
        final_answer += "\n".join(auto_messages)
        final_answer += "\n\n위 자동 보완 결과는 아래 `Virtual Patch Scenario Estimate & HITL Review Gate`에 구조화 데이터로 표시됩니다."

    return final_answer

def get_latest_tool_result(trace: List[Dict[str, Any]], tool_name: str) -> Dict[str, Any]:
    for step in reversed(trace or []):
        if step.get("tool") == tool_name and isinstance(step.get("result"), dict):
            return step.get("result", {})
    return {}
