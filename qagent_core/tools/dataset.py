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
from qagent_core.simulation import SCENARIO_WARNINGS, project_patch_scenario_range
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

from .context import AnalysisContext

REQUIRED_BATTLE_COLUMNS = [
    "battle_id",
    "patch_version",
    "player_team",
    "enemy_team",
    "result",
    "duration_sec",
    "main_dealer",
    "total_damage",
    "skill_used_most",
    "equipment_set",
    "user_segment",
    "battle_mode",
]


def build_dataset_tools(context: AnalysisContext) -> dict[str, Any]:
    """Build read-only dataset inspection tools for an Agent run."""
    battles = context.battles
    characters = context.characters
    skills = context.skills
    equipment_sets = context.equipment_sets
    patch_notes = context.patch_notes

    def get_dataset_overview() -> Dict[str, Any]:
        """Return row counts, key dimensions, columns, and global metrics."""
        missing = [c for c in REQUIRED_BATTLE_COLUMNS if c not in battles.columns]
        if missing:
            return {"status": "error", "missing_columns": missing}

        return {
            "status": "ok",
            "battle_rows": int(len(battles)),
            "patch_versions": sorted(
                [str(x) for x in battles["patch_version"].dropna().unique().tolist()]
            ),
            "battle_modes": sorted(
                [str(x) for x in battles["battle_mode"].dropna().unique().tolist()]
            ),
            "user_segments": sorted(
                [str(x) for x in battles["user_segment"].dropna().unique().tolist()]
            ),
            "unique_player_teams": int(battles["player_team"].nunique()),
            "unique_equipment_sets": int(battles["equipment_set"].nunique()),
            "overall_win_rate": round(win_rate(battles["result"]), 4),
            "avg_damage": round(float(battles["total_damage"].mean()), 2),
            "avg_duration_sec": round(float(battles["duration_sec"].mean()), 2),
            "master_rows": {
                "characters": int(len(characters)),
                "skills": int(len(skills)),
                "equipment_sets": int(len(equipment_sets)),
                "patch_notes": int(len(patch_notes)),
            },
            "loaded_columns": {
                "battle_logs": list(battles.columns),
                "characters": list(characters.columns),
                "skills": list(skills.columns),
                "equipment_sets": list(equipment_sets.columns),
                "patch_notes": list(patch_notes.columns),
            },
        }

    def get_team_performance(
        group_by: str = "player_team", top_n: int = 10
    ) -> Dict[str, Any]:
        """Aggregate win rate and damage by one allowed battle dimension."""
        allowed = [
            "player_team",
            "equipment_set",
            "main_dealer",
            "skill_used_most",
            "user_segment",
            "patch_version",
        ]
        if group_by not in allowed:
            return {"status": "error", "message": f"group_by must be one of {allowed}"}

        result = (
            battles.groupby(group_by)
            .agg(
                battles=("battle_id", "count"),
                wins=("result", lambda x: int((x == "win").sum())),
                win_rate=("result", win_rate),
                avg_damage=("total_damage", "mean"),
                avg_duration_sec=("duration_sec", "mean"),
            )
            .reset_index()
            .sort_values(["win_rate", "battles"], ascending=[False, False])
        )
        result["win_rate"] = result["win_rate"].round(4)
        result["avg_damage"] = result["avg_damage"].round(2)
        result["avg_duration_sec"] = result["avg_duration_sec"].round(2)
        return {
            "status": "ok",
            "group_by": group_by,
            "rows": to_jsonable_df(result, top_n),
        }

    return {
        "get_dataset_overview": get_dataset_overview,
        "get_team_performance": get_team_performance,
    }
