"""Pure normalization helpers for Riot match collection.

These functions perform no network or filesystem I/O and preserve the legacy
fetchMatch.py contracts.
"""

from __future__ import annotations

import re
import time
from typing import Any, Optional

import pandas as pd


def parse_riot_id(riot_id: str) -> tuple[str, str]:
    """Split a ``gameName#tagLine`` Riot ID into validated parts."""
    riot_id = riot_id.strip()

    if "#" not in riot_id:
        raise ValueError(f"Riot ID 형식 오류: {riot_id}")

    game_name, tag_line = riot_id.rsplit("#", 1)

    game_name = game_name.strip()
    tag_line = tag_line.strip()

    if not game_name or not tag_line:
        raise ValueError(f"Riot ID 형식 오류: {riot_id}")

    return game_name, tag_line


def safe_filename(text: str) -> str:
    """Return a filesystem-safe filename fragment for Riot identifiers."""
    text = text.strip()
    text = text.replace("#", "_")
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = re.sub(r"\s+", "_", text)
    return text


def timestamp_to_iso_kst(ms: Optional[int]) -> Optional[str]:
    """Convert a Riot millisecond timestamp to a KST datetime string."""
    if ms is None or pd.isna(ms):
        return None

    return time.strftime(
        "%Y-%m-%d %H:%M:%S",
        time.gmtime(float(ms) / 1000 + 9 * 3600),
    )


def compute_kda(kills: int, deaths: int, assists: int) -> float:
    """Compute a rounded KDA ratio using kills, deaths, and assists."""
    if deaths == 0:
        return float(kills + assists)

    return round((kills + assists) / deaths, 2)


def extract_raw_patch_version(game_version: Optional[str]) -> Optional[str]:
    """
    Riot gameVersion에서 앞의 major.minor만 추출한다.

    예:
    16.13.791.5903 -> 16.13
    15.12.688.6522 -> 15.12
    14.10.x -> 14.10
    """
    if game_version is None or pd.isna(game_version):
        return None

    parts = str(game_version).strip().split(".")

    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"

    return str(game_version).strip()


def map_game_version_to_patch_version(game_version: Optional[str]) -> Optional[str]:
    """
    과제용 패치노트 버전 매핑 규칙.

    1.x ~ 14.x  : 게임버전과 패치버전 그대로 매핑
    15.x 이상  : 게임버전 major에 +10을 해서 25.x, 26.x 패치노트와 매핑
                  이때 minor는 두 자리로 패딩한다.

    예:
    14.10.0000      -> 14.10
    15.12.688.6522 -> 25.12
    16.3.744.7656  -> 26.03
    16.13.791.5903 -> 26.13
    """
    raw = extract_raw_patch_version(game_version)

    if not raw:
        return None

    match = re.match(r"^(\d+)\.(\d+)", str(raw))
    if not match:
        return raw

    major = int(match.group(1))
    minor_text = match.group(2)
    minor = int(minor_text)

    if major <= 14:
        return f"{major}.{minor_text}"

    return f"{major + 10}.{minor:02d}"


def patch_version_mapping_rule(game_version: Optional[str]) -> str:
    """Describe which assignment patch mapping rule applies to a gameVersion."""
    raw = extract_raw_patch_version(game_version)

    if not raw:
        return "unknown"

    match = re.match(r"^(\d+)\.", str(raw))
    if not match:
        return "unknown"

    major = int(match.group(1))

    if major <= 14:
        return "game_version_1_to_14_same_as_patch_version"

    return "game_version_15_plus_mapped_to_patch_version_25_plus"


def queue_to_battle_mode(queue_id: Any) -> str:
    """Map Riot queue IDs to stable battle mode labels."""
    try:
        q = int(float(queue_id))
    except Exception:
        return "UNKNOWN"

    queue_map = {
        400: "NORMAL_DRAFT",
        420: "RANKED_SOLO",
        430: "NORMAL_BLIND",
        440: "RANKED_FLEX",
        450: "ARAM",
        490: "QUICKPLAY",
        700: "CLASH",
        1700: "ARENA",
    }

    return queue_map.get(q, f"QUEUE_{q}")


def truthy_win(value: Any) -> bool:
    """Normalize varied win flags to a boolean."""
    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()
    return text in {"true", "1", "win", "w", "yes"}


def normalize_item_id(value: Any) -> Optional[int]:
    """Convert a Riot item value to a positive item ID or ``None``."""
    if value is None or pd.isna(value):
        return None

    try:
        item_id = int(float(value))
    except Exception:
        return None

    if item_id <= 0:
        return None

    return item_id


def extract_patch_version(game_version: Optional[str]) -> Optional[str]:
    """Compatibility wrapper for assignment patch version extraction."""
    return map_game_version_to_patch_version(game_version)


def get_primary_perk(participant: dict[str, Any]) -> Optional[int]:
    """Return the participant's primary keystone perk ID when present."""
    styles = participant.get("perks", {}).get("styles", [])

    if not styles:
        return None

    selections = styles[0].get("selections", [])

    if not selections:
        return None

    return selections[0].get("perk")


def get_sub_style(participant: dict[str, Any]) -> Optional[int]:
    """Return the participant's secondary rune style ID when present."""
    styles = participant.get("perks", {}).get("styles", [])

    if len(styles) < 2:
        return None

    return styles[1].get("style")
