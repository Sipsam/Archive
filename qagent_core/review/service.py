from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from qagent_core.agent.followup import get_latest_tool_result
from qagent_core.config import APP_VERSION
from qagent_core.persistence import (
    ReviewPersistenceError, SQLiteReviewRepository, export_json_record,
    save_review_with_mirrors,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
HITL_DIR = DATA_DIR / "human_review"
REVIEW_LOG_PATH = HITL_DIR / "review_logs.csv"
REVIEW_RECORDS_DIR = HITL_DIR / "records"
REVIEW_DB_PATH = HITL_DIR / "reviews.sqlite3"


def now_kst_iso() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")

def safe_json_dump(data: Any, path: Path) -> None:
    """Backward-compatible JSON export helper; SQLite remains authoritative."""
    export_json_record(path, data)

def load_review_logs() -> pd.DataFrame:
    repository = SQLiteReviewRepository(REVIEW_DB_PATH)
    sqlite_logs = repository.list_reviews()
    try:
        legacy_logs = pd.read_csv(REVIEW_LOG_PATH) if REVIEW_LOG_PATH.exists() else pd.DataFrame()
    except Exception:
        legacy_logs = pd.DataFrame()

    frames = [frame for frame in (sqlite_logs, legacy_logs) if not frame.empty]
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    if "review_id" in combined.columns:
        combined = combined.drop_duplicates(subset=["review_id"], keep="first")
    if "created_at_kst" in combined.columns:
        combined = combined.assign(
            _created_sort=pd.to_datetime(combined["created_at_kst"], errors="coerce", utc=True)
        ).sort_values("_created_sort", kind="stable", na_position="first").drop(columns="_created_sort")
    return combined

def append_review_log(row: Dict[str, Any], artifact: Dict[str, Any]) -> Dict[str, Any]:
    """Persist to authoritative SQLite, then export best-effort compatibility mirrors."""
    repository = SQLiteReviewRepository(REVIEW_DB_PATH)
    artifact_path = Path(row.get("artifact_path", ""))
    return save_review_with_mirrors(repository, {
        "review_id": row.get("review_id", ""),
        "created_at": row.get("created_at_kst", ""),
        "model": row.get("model", ""),
        "target": row.get("review_target", ""),
        "decision": row.get("review_status", ""),
        "reviewer": row.get("reviewer", ""),
        "reviewer_note": row.get("human_comment", ""),
        "final_answer": artifact.get("final_answer", ""),
        "tool_trace_json": artifact.get("tool_trace", []),
        "virtual_patch_json": {
            "note": artifact.get("virtual_patch_note", {}),
            "scenario": artifact.get("virtual_patch_simulation", {}),
        },
        "self_reflection_json": artifact.get("agent_self_reflection", {}),
        "dataset_name": row.get("data_profile", ""),
        "app_version": APP_VERSION,
        "artifact_path": row.get("artifact_path", ""),
        "artifact_json": artifact,
    }, csv_path=REVIEW_LOG_PATH, csv_row=row,
       json_path=artifact_path, json_artifact=artifact)

def summarize_trace_for_review(trace: List[Dict[str, Any]]) -> str:
    if not trace:
        return ""
    names = []
    for step in trace:
        tool_name = str(step.get("tool", ""))
        if tool_name and tool_name not in names:
            names.append(tool_name)
    return " → ".join(names)

def summarize_virtual_patch_for_log(virtual_patch: Dict[str, Any]) -> Dict[str, str]:
    note = virtual_patch.get("virtual_patch_note", {}) if isinstance(virtual_patch, dict) else {}
    return {
        "virtual_patch_version": str(note.get("virtual_patch_version", "")),
        "virtual_patch_target": str(note.get("target", "")),
        "virtual_patch_action": str(note.get("action", "")),
        "virtual_patch_expected_wr_delta": str(note.get("estimated_win_rate_delta_points", "")),
        "virtual_patch_expected_damage_delta": str(note.get("estimated_damage_delta_percent", "")),
    }

def summarize_simulation_for_log(simulation: Dict[str, Any]) -> str:
    if not isinstance(simulation, dict) or simulation.get("status") != "ok":
        return ""
    after = simulation.get("projected_after", {})
    return (
        f"projected_win_rate={after.get('win_rate')}, "
        f"projected_avg_damage={after.get('avg_damage')}, "
        f"confidence={simulation.get('confidence')}"
    )

def summarize_reflection_for_log(reflection: Dict[str, Any]) -> str:
    if not isinstance(reflection, dict) or reflection.get("status") != "ok":
        return ""
    body = reflection.get("self_reflection", {})
    return (
        f"recommendation={body.get('agent_recommendation')}, "
        f"concerns={len(body.get('concerns', []))}, "
        f"suggestions={len(body.get('revision_suggestions', []))}"
    )

def build_review_record(
    agent_state: Dict[str, Any],
    data_profile: str,
    selected_data_folder: Optional[Path],
    reviewer: str,
    review_status: str,
    human_risk_level: str,
    review_target: str,
    human_comment: str,
    next_action: str,
    followup_owner: str,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    review_id = f"HITL-{datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    trace = agent_state.get("trace", [])
    final_answer = agent_state.get("final_answer", "")
    virtual_patch = get_latest_tool_result(trace, "generate_virtual_patch_note")
    virtual_simulation = get_latest_tool_result(trace, "simulate_virtual_patch_impact")
    virtual_reflection = get_latest_tool_result(trace, "reflect_on_virtual_patch")
    virtual_log_fields = summarize_virtual_patch_for_log(virtual_patch)

    artifact = {
        "review_id": review_id,
        "run_id": agent_state.get("run_id", ""),
        "created_at_kst": now_kst_iso(),
        "reviewer": reviewer,
        "review_status": review_status,
        "human_risk_level": human_risk_level,
        "review_target": review_target,
        "human_comment": human_comment,
        "next_action": next_action,
        "followup_owner": followup_owner,
        "data_profile": data_profile,
        "selected_data_folder": str(selected_data_folder) if selected_data_folder else "",
        "model": agent_state.get("model", ""),
        "user_goal": agent_state.get("user_goal", ""),
        "final_answer": final_answer,
        "tool_trace": trace,
        "messages": agent_state.get("messages", []),
        "virtual_patch_note": virtual_patch,
        "virtual_patch_simulation": virtual_simulation,
        "agent_self_reflection": virtual_reflection,
    }

    artifact_path = REVIEW_RECORDS_DIR / f"{review_id}.json"
    log_row = {
        "review_id": review_id,
        "run_id": artifact["run_id"],
        "created_at_kst": artifact["created_at_kst"],
        "reviewer": reviewer,
        "review_status": review_status,
        "human_risk_level": human_risk_level,
        "review_target": review_target,
        "next_action": next_action,
        "followup_owner": followup_owner,
        "data_profile": data_profile,
        "selected_data_folder": str(selected_data_folder) if selected_data_folder else "",
        "model": agent_state.get("model", ""),
        "tool_count": sum(bool(step.get("executed")) for step in trace),
        "tool_flow": summarize_trace_for_review(trace),
        **virtual_log_fields,
        "virtual_patch_simulation_summary": summarize_simulation_for_log(virtual_simulation),
        "agent_self_reflection_summary": summarize_reflection_for_log(virtual_reflection),
        "human_comment": human_comment,
        "artifact_path": str(artifact_path),
    }
    storage_result = append_review_log(log_row, artifact)
    log_row["storage_result"] = storage_result
    if storage_result.get("mirror_warning"):
        log_row["storage_warning"] = storage_result["mirror_warning"]
    return log_row, artifact
