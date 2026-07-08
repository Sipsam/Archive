from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from qagent_core.config import (
    BALANCE_FDR_ALPHA, BALANCE_MIN_SAMPLES, BALANCE_MIN_WILSON_DIFF,
    BALANCE_MIN_WIN_RATE, BALANCE_MIN_WIN_RATE_DIFF,
)
from qagent_core.simulation import SCENARIO_WARNINGS, project_patch_scenario_range
from qagent_core.statistics import analyze_balance_stages, detect_balance_candidates, win_rate
from qagent_core.utils import (
    apply_lol_patch_version_mapping, ensure_column, first_existing_column,
    format_value, get_latest_patch_version, get_previous_patch_version,
    normalize_text, parse_number, patch_sort_key, pct, search_lol_stat_knowledge,
    split_team, to_jsonable_df,
)

from .context import AnalysisContext


def build_patch_tools(context: AnalysisContext) -> dict[str, Any]:
    battles = context.battles
    characters = context.characters
    skills = context.skills
    equipment_sets = context.equipment_sets
    patch_notes = context.patch_notes

    def compare_patch_performance(
        player_team: str = "",
        equipment_set: str = "",
        skill_used_most: str = ""
    ) -> Dict[str, Any]:
        df = battles.copy()
        filters = {}

        if player_team:
            df = df[df["player_team"].astype(str) == player_team]
            filters["player_team"] = player_team
        if equipment_set:
            df = df[df["equipment_set"].astype(str) == equipment_set]
            filters["equipment_set"] = equipment_set
        if skill_used_most:
            df = df[df["skill_used_most"].astype(str) == skill_used_most]
            filters["skill_used_most"] = skill_used_most

        if df.empty:
            return {"status": "empty", "filters": filters}

        result = (
            df.groupby("patch_version")
            .agg(
                battles=("battle_id", "count"),
                wins=("result", lambda x: int((x == "win").sum())),
                win_rate=("result", win_rate),
                avg_damage=("total_damage", "mean"),
                avg_duration_sec=("duration_sec", "mean")
            )
            .reset_index()
            .sort_values("patch_version")
        )

        result["win_rate"] = result["win_rate"].round(4)
        result["avg_damage"] = result["avg_damage"].round(2)
        result["avg_duration_sec"] = result["avg_duration_sec"].round(2)

        return {"status": "ok", "filters": filters, "rows": to_jsonable_df(result, 20)}

    def analyze_patch_impact(
        player_team: str,
        equipment_set: str = "",
        skill_used_most: str = "",
        current_patch_version: str = ""
    ) -> Dict[str, Any]:
        """패치 전후 성능 변화량을 직접 계산하는 핵심 개선 Tool."""
        if not current_patch_version:
            current_patch_version = get_latest_patch_version(battles)
        previous_patch_version = get_previous_patch_version(battles, current_patch_version)

        df = battles[battles["player_team"].astype(str) == player_team].copy()
        if equipment_set:
            df = df[df["equipment_set"].astype(str) == equipment_set]
        if skill_used_most:
            df = df[df["skill_used_most"].astype(str) == skill_used_most]

        if df.empty:
            return {"status": "empty", "message": "matching battle logs not found"}

        patch_summary = (
            df.groupby("patch_version")
            .agg(
                battles=("battle_id", "count"),
                win_rate=("result", win_rate),
                avg_damage=("total_damage", "mean"),
                avg_duration_sec=("duration_sec", "mean")
            )
            .reset_index()
        )

        current = patch_summary[patch_summary["patch_version"].astype(str) == str(current_patch_version)]
        previous = patch_summary[patch_summary["patch_version"].astype(str) == str(previous_patch_version)]

        impact = {}
        if not current.empty and not previous.empty:
            c = current.iloc[0]
            p = previous.iloc[0]
            impact = {
                "previous_patch": previous_patch_version,
                "current_patch": current_patch_version,
                "win_rate_change": round(float(c["win_rate"] - p["win_rate"]), 4),
                "damage_change_rate": round(float(c["avg_damage"] / max(p["avg_damage"], 1) - 1), 4),
                "duration_change_rate": round(float(c["avg_duration_sec"] / max(p["avg_duration_sec"], 1) - 1), 4),
                "previous_battles": int(p["battles"]),
                "current_battles": int(c["battles"])
            }

        return {
            "status": "ok",
            "query": {
                "player_team": player_team,
                "equipment_set": equipment_set,
                "skill_used_most": skill_used_most,
                "current_patch_version": current_patch_version
            },
            "patch_summary": to_jsonable_df(patch_summary.sort_values("patch_version"), 20),
            "impact": impact
        }

    def retrieve_related_knowledge(
        player_team: str,
        equipment_set: str,
        skill_used_most: str,
        patch_version: str
    ) -> Dict[str, Any]:
        team_members = split_team(player_team)
        skill_tokens = [x for x in str(skill_used_most).replace("/", " ").split() if len(x) >= 3]
        equipment_tokens = [x for x in str(equipment_set).replace("/", " ").split() if len(x) >= 3]
        keywords = sorted(set(team_members + skill_tokens + equipment_tokens))

        char_rows = characters[characters["name"].astype(str).isin(team_members)]
        skill_rows = skills[
            (skills["character"].astype(str).isin(team_members))
            | (skills["skill_name"].astype(str).str.lower() == str(skill_used_most).lower())
        ]
        equip_rows = equipment_sets[
            equipment_sets["set_name"].astype(str).str.lower() == str(equipment_set).lower()
        ]

        patch_matches = []
        for _, patch in patch_notes.iterrows():
            if str(patch.get("patch_version", "")) != str(patch_version):
                continue
            text = normalize_text(str(patch.get("change_target", "")) + " " + str(patch.get("description", "")))
            matched = [kw for kw in keywords if normalize_text(kw) in text]
            if matched:
                patch_matches.append({
                    "patch_version": str(patch.get("patch_version", "")),
                    "date": str(patch.get("date", "")),
                    "change_target": str(patch.get("change_target", "")),
                    "before_value": str(patch.get("before_value", "")),
                    "after_value": str(patch.get("after_value", "")),
                    "description": str(patch.get("description", "")),
                    "matched_keywords": matched
                })

        return {
            "status": "ok",
            "query": {
                "player_team": player_team,
                "equipment_set": equipment_set,
                "skill_used_most": skill_used_most,
                "patch_version": patch_version
            },
            "keywords": keywords,
            "characters": to_jsonable_df(char_rows, 20),
            "skills": to_jsonable_df(skill_rows, 20),
            "equipment_sets": to_jsonable_df(equip_rows, 20),
            "patch_matches": patch_matches
        }

    return {
        "compare_patch_performance": compare_patch_performance,
        "analyze_patch_impact": analyze_patch_impact,
        "retrieve_related_knowledge": retrieve_related_knowledge,
    }
