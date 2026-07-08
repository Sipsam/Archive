"""Regenerate dataset summaries from the CSV files currently delivered with the app."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qagent_core.data_io import create_dataset_summary, load_data_folder


def csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.open("r", encoding="utf-8-sig", errors="replace")) - 1


def build_summary(dataset_dir: Path) -> dict:
    battle_path = dataset_dir / "battle_logs.csv"
    frames = load_data_folder(dataset_dir)
    battles = frames["battle_logs"]
    core_summary = create_dataset_summary(frames)
    required = [
        "battle_id", "patch_version", "player_team", "enemy_team", "result",
        "duration_sec", "total_damage", "skill_used_most", "equipment_set",
        "user_segment", "battle_mode",
    ]
    extras = dataset_dir / "extras"
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_of_truth": str(battle_path.as_posix()),
        "rows": {
            "battle_logs": int(len(battles)),
            "unique_matches": int(battles["match_id"].nunique()) if "match_id" in battles else None,
            "unique_battle_ids": int(battles["battle_id"].nunique()) if "battle_id" in battles else None,
            "app_columns": int(len(battles.columns)),
            "item_usage_long": csv_row_count(extras / "item_usage_long.csv"),
            "champion_performance_by_patch": csv_row_count(extras / "champion_performance_by_patch.csv"),
            "item_performance_by_patch": csv_row_count(extras / "item_performance_by_patch.csv"),
            "tier_patch_performance": csv_row_count(extras / "tier_patch_performance.csv"),
        },
        "patch_versions": sorted(battles["patch_version"].dropna().astype(str).unique().tolist()),
        "quality_checks": {
            "battle_id_unique": bool(battles["battle_id"].is_unique) if "battle_id" in battles else False,
            "duplicate_rows": int(battles.duplicated().sum()),
            "required_app_columns_present": all(column in battles for column in required),
            "required_column_nulls": {
                column: int(battles[column].isna().sum()) for column in required if column in battles
            },
        },
        "dataset": core_summary,
        "interpretation": (
            "This file is regenerated from the delivered battle_logs.csv. Historical conversion "
            "counts must not be treated as the current dataset size."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, default=Path("data/lol_assignment_dataset"))
    args = parser.parse_args()
    summary = build_summary(args.dataset_dir)
    output = args.dataset_dir / "dataset_summary.json"
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    conversion = {
        "status": "superseded_historical_conversion_metadata",
        "current_summary": "dataset_summary.json",
        "current_battle_logs_rows": summary["rows"]["battle_logs"],
        "current_unique_matches": summary["rows"]["unique_matches"],
        "note": (
            "The previous 13,990-row value described an earlier conversion source. "
            "It did not match the delivered CSV and has been superseded by the regenerated summary."
        ),
    }
    (args.dataset_dir / "app_conversion_summary.json").write_text(
        json.dumps(conversion, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {output} ({summary['rows']['battle_logs']} rows)")


if __name__ == "__main__":
    main()
