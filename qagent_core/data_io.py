"""Canonical, Streamlit-independent loading for application datasets."""
from __future__ import annotations

import os
from collections import deque
from functools import lru_cache
from pathlib import Path
from typing import IO, Any, Mapping

import pandas as pd

from .statistics import normalize_win_results

EXPECTED_DATA_FILES = {
    "battle_logs": "battle_logs.csv",
    "characters": "characters.csv",
    "skills": "skills.csv",
    "equipment_sets": "equipment_sets.csv",
    "patch_notes": "patch_notes.csv",
}

REQUIRED_COLUMNS = {
    "battle_logs": frozenset({
        "battle_id", "patch_version", "player_team", "enemy_team", "result",
        "duration_sec", "main_dealer", "total_damage", "skill_used_most",
        "equipment_set", "user_segment", "battle_mode",
    }),
    "characters": frozenset({"name", "role", "element", "base_attack", "base_hp", "main_skill"}),
    "skills": frozenset({"skill_name", "character", "skill_type", "damage_multiplier", "cooldown_sec", "effect"}),
    "equipment_sets": frozenset({"set_name", "set_type", "bonus_type", "bonus_value", "condition"}),
    "patch_notes": frozenset({"patch_version", "date", "change_target", "before_value", "after_value", "description"}),
}


class DataLoadError(ValueError):
    """A dataset could not be loaded or did not satisfy its contract."""


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove transport artifacts only; source column names are otherwise preserved."""
    result = df.copy()
    result.columns = [str(column).replace("\ufeff", "").strip() for column in result.columns]
    return result


def validate_data_folder(folder: Path | str) -> list[str]:
    path = Path(folder)
    if not path.exists() or not path.is_dir():
        raise DataLoadError(f"[DATA_FOLDER_INVALID] 데이터 폴더가 없거나 폴더가 아닙니다: {path}")
    return [filename for filename in EXPECTED_DATA_FILES.values() if not (path / filename).is_file()]


def discover_data_folders(
    search_roots: list[Path | str] | tuple[Path | str, ...],
    *,
    max_depth: int = 2,
) -> list[Path]:
    """Find valid datasets below explicit roots without unbounded recursion.

    The root itself is depth 0. Symlinked directories are not followed, and a
    candidate is returned only when all canonical CSV files are regular files.
    """
    safe_depth = min(max(int(max_depth), 0), 3)
    required_files = tuple(EXPECTED_DATA_FILES.values())
    found: dict[str, Path] = {}
    visited: set[str] = set()

    for root_value in search_roots:
        root = Path(root_value).expanduser()
        try:
            root = root.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if not root.is_dir():
            continue

        queue = deque([(root, 0)])
        while queue:
            candidate, depth = queue.popleft()
            key = os.path.normcase(str(candidate))
            if key in visited:
                continue
            visited.add(key)

            if all((candidate / filename).is_file() for filename in required_files):
                found[key] = candidate

            if depth >= safe_depth:
                continue
            try:
                with os.scandir(candidate) as entries:
                    children = sorted(
                        (
                            Path(entry.path)
                            for entry in entries
                            if entry.is_dir(follow_symlinks=False)
                        ),
                        key=lambda path: os.path.normcase(str(path)),
                    )
            except OSError:
                continue
            queue.extend((child, depth + 1) for child in children)

    return sorted(found.values(), key=lambda path: os.path.normcase(str(path)))


def validate_required_columns(name: str, frame: pd.DataFrame) -> None:
    required = REQUIRED_COLUMNS.get(name, frozenset())
    missing = sorted(required.difference(frame.columns))
    if missing:
        filename = EXPECTED_DATA_FILES.get(name, name)
        raise DataLoadError(f"[DATA_COLUMNS_MISSING] {filename} 필수 컬럼 누락: {', '.join(missing)}")


def file_signature(path: Path | str) -> tuple[str, int, int]:
    resolved = Path(path).resolve()
    try:
        stat = resolved.stat()
    except OSError as error:
        raise DataLoadError(f"[DATA_FILE_UNREADABLE] CSV 파일을 확인할 수 없습니다: {resolved}") from error
    return str(resolved), stat.st_mtime_ns, stat.st_size


def folder_signature(folder: Path | str) -> tuple[tuple[str, int, int], ...]:
    path = Path(folder).resolve()
    missing = validate_data_folder(path)
    if missing:
        raise DataLoadError(f"[DATA_FILES_MISSING] 필수 CSV 누락: {', '.join(missing)} (폴더: {path})")
    return tuple(file_signature(path / filename) for filename in EXPECTED_DATA_FILES.values())


def load_csv(source: Path | str | IO[Any], *, name: str | None = None) -> pd.DataFrame:
    """Read and normalize one CSV without relying on Streamlit."""
    try:
        frame = clean_columns(pd.read_csv(source, dtype={"patch_version": str}, low_memory=False))
    except Exception as error:
        raise DataLoadError(f"[DATA_CSV_READ_FAILED] CSV 읽기 실패: {source}") from error
    if name is not None:
        validate_required_columns(name, frame)
    return frame


@lru_cache(maxsize=16)
def _load_data_folder_cached(
    signature: tuple[tuple[str, int, int], ...],
) -> tuple[pd.DataFrame, ...]:
    frames = []
    for name, item in zip(EXPECTED_DATA_FILES, signature):
        frames.append(load_csv(item[0], name=name))
    return tuple(frames)


def load_data_folder(folder: Path | str, *, use_cache: bool = True) -> dict[str, pd.DataFrame]:
    """Load the canonical five-file dataset; cache identity includes mtime and size."""
    signature = folder_signature(folder)
    if use_cache:
        frames = _load_data_folder_cached(signature)
    else:
        frames = tuple(load_csv(item[0], name=name) for name, item in zip(EXPECTED_DATA_FILES, signature))
    # Callers receive isolated frames, so mutation cannot corrupt the process cache.
    return {name: frame.copy(deep=True) for name, frame in zip(EXPECTED_DATA_FILES, frames)}


def clear_data_cache() -> None:
    _load_data_folder_cached.cache_clear()


def create_dataset_summary(frames: Mapping[str, pd.DataFrame]) -> dict[str, Any]:
    """Create a cheap, JSON-serializable summary from already-loaded frames."""
    battles = frames["battle_logs"]
    return {
        "rows": {name: int(len(frame)) for name, frame in frames.items()},
        "columns": {name: list(frame.columns) for name, frame in frames.items()},
        "patch_versions": sorted(battles["patch_version"].dropna().astype(str).unique().tolist()),
        "battle_id_unique": bool(battles["battle_id"].is_unique),
        "duplicate_battles": int(battles.duplicated().sum()),
        "required_column_nulls": {
            column: int(battles[column].isna().sum()) for column in sorted(REQUIRED_COLUMNS["battle_logs"])
        },
    }


def summarize_battle_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    """Return the stable metric shape used by virtual patch tools."""
    if frame.empty:
        return {
            "battles": 0,
            "wins": 0,
            "win_rate": None,
            "avg_damage": None,
            "avg_duration_sec": None,
            "avg_kda": None,
        }
    wins = normalize_win_results(frame["result"])
    summary = {
        "battles": int(len(frame)),
        "wins": int(wins.sum()),
        "win_rate": round(float(wins.mean()), 4),
        "avg_damage": round(float(pd.to_numeric(frame["total_damage"], errors="coerce").mean()), 2),
        "avg_duration_sec": round(
            float(pd.to_numeric(frame["duration_sec"], errors="coerce").mean()), 2
        ),
    }
    summary["avg_kda"] = (
        round(float(pd.to_numeric(frame["kda"], errors="coerce").mean()), 2)
        if "kda" in frame.columns
        else None
    )
    return summary
