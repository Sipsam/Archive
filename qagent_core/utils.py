import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


LOL_STAT_KNOWLEDGE = [
    {"stat": "Health", "aliases": "hp, 체력, 생명력", "category": "survivability", "description": "유닛이 사망하기 전까지 버틸 수 있는 기본 생존 자원이다. 방어력/마법 저항력과 함께 유효 체력을 계산할 때 사용한다.", "formula": "effective_health_physical = health * (1 + armor / 100); effective_health_magic = health * (1 + magic_resist / 100)", "source_url": "https://wiki.leagueoflegends.com/en-us/Health"},
    {"stat": "Health regeneration", "aliases": "hp regen, 체력 재생", "category": "sustain", "description": "시간이 지남에 따라 체력을 회복하는 수치다. 라인 유지력과 장기 교전에 영향을 준다.", "formula": "healing_over_time ≈ health_regen_per_5s * seconds / 5", "source_url": "https://wiki.leagueoflegends.com/en-us/Health_regeneration"},
    {"stat": "Heal and shield power", "aliases": "heal power, shield power, 회복 및 보호막", "category": "sustain", "description": "회복량과 보호막량을 증폭하는 스탯이다.", "formula": "modified_heal_or_shield = base_value * (1 + heal_and_shield_power / 100)", "source_url": "https://wiki.leagueoflegends.com/en-us/Heal_and_shield_power"},
    {"stat": "Armor", "aliases": "방어력, armor", "category": "defense", "description": "물리 피해를 감소시키는 방어 스탯이다. 양수 방어력 기준으로 1 방어력은 물리 피해에 대한 유효 체력을 최대 체력의 1%만큼 증가시킨다.", "formula": "post_physical_damage = raw_physical_damage * 100 / (100 + armor); physical_damage_reduction = armor / (100 + armor); effective_health_physical = health * (1 + armor / 100)", "source_url": "https://wiki.leagueoflegends.com/en-us/Armor"},
    {"stat": "Magic resistance", "aliases": "mr, magic resist, 마법 저항력", "category": "defense", "description": "마법 피해를 감소시키는 방어 스탯이다. 양수 마법 저항력 기준으로 1 MR은 마법 피해에 대한 유효 체력을 최대 체력의 1%만큼 증가시킨다.", "formula": "post_magic_damage = raw_magic_damage * 100 / (100 + magic_resist); magic_damage_reduction = magic_resist / (100 + magic_resist); effective_health_magic = health * (1 + magic_resist / 100)", "source_url": "https://wiki.leagueoflegends.com/en-us/Magic_resistance"},
    {"stat": "Tenacity", "aliases": "강인함, cc reduction", "category": "crowd_control", "description": "일부 군중 제어 효과의 지속 시간을 줄이는 스탯이다. 모든 CC에 적용되는 것은 아니다.", "formula": "modified_cc_duration ≈ base_duration * (1 - tenacity / 100)", "source_url": "https://wiki.leagueoflegends.com/en-us/Tenacity"},
    {"stat": "Slow resist", "aliases": "slow resistance, 둔화 저항", "category": "crowd_control", "description": "둔화 효과의 강도를 줄이는 스탯이다.", "formula": "modified_slow_strength ≈ slow_strength * (1 - slow_resist / 100)", "source_url": "https://wiki.leagueoflegends.com/en-us/Slow_resist"},
    {"stat": "Attack speed", "aliases": "as, 공속, 공격 속도", "category": "offense", "description": "초당 기본 공격 횟수를 결정한다. 보너스 공격 속도는 공격 속도 비율에 가산되며 일반적으로 2.5 attacks/sec 상한을 가진다.", "formula": "total_attack_speed = base_attack_speed + attack_speed_ratio * (bonus_attack_speed_percent / 100); capped_attack_speed = min(max(total_attack_speed, 0.2), 2.5)", "source_url": "https://wiki.leagueoflegends.com/en-us/Attack_speed"},
    {"stat": "Attack damage", "aliases": "ad, 공격력", "category": "offense", "description": "기본 공격과 AD 계수를 가진 스킬의 피해량에 영향을 준다.", "formula": "physical_skill_damage ≈ base_damage + total_attack_damage * ad_ratio", "source_url": "https://wiki.leagueoflegends.com/en-us/Attack_damage"},
    {"stat": "Ability power", "aliases": "ap, 주문력", "category": "offense", "description": "AP 계수를 가진 스킬의 피해, 회복, 보호막 등에 영향을 준다.", "formula": "magic_skill_value ≈ base_value + ability_power * ap_ratio", "source_url": "https://wiki.leagueoflegends.com/en-us/Ability_power"},
    {"stat": "Critical strike", "aliases": "crit, 치명타", "category": "offense", "description": "기본 공격이나 일부 효과가 치명타로 적용될 확률과 피해량에 관련된다.", "formula": "expected_auto_damage ≈ normal_damage * (1 + crit_chance * (crit_damage_multiplier - 1))", "source_url": "https://wiki.leagueoflegends.com/en-us/Critical_strike"},
    {"stat": "Armor penetration", "aliases": "lethality, 방관, 물리 관통", "category": "penetration", "description": "물리 피해 계산 시 대상의 방어력 일부를 무시한다.", "formula": "effective_armor ≈ max(0, armor * (1 - percent_armor_pen) - flat_armor_pen)", "source_url": "https://wiki.leagueoflegends.com/en-us/Armor_penetration"},
    {"stat": "Magic penetration", "aliases": "마관, magic pen", "category": "penetration", "description": "마법 피해 계산 시 대상의 마법 저항력 일부를 무시한다.", "formula": "effective_mr ≈ max(0, magic_resist * (1 - percent_magic_pen) - flat_magic_pen)", "source_url": "https://wiki.leagueoflegends.com/en-us/Magic_penetration"},
    {"stat": "Life steal", "aliases": "lifesteal, 생명력 흡수", "category": "sustain", "description": "기본 공격 또는 해당되는 물리 피해의 일부를 체력으로 회복한다.", "formula": "heal ≈ eligible_damage_dealt * life_steal / 100", "source_url": "https://wiki.leagueoflegends.com/en-us/Life_steal"},
    {"stat": "Vamp", "aliases": "omnivamp, physical vamp, 흡혈", "category": "sustain", "description": "피해 유형이나 효과 조건에 따라 가한 피해 일부를 체력으로 회복한다.", "formula": "heal ≈ eligible_damage_dealt * vamp / 100", "source_url": "https://wiki.leagueoflegends.com/en-us/Vamp"},
    {"stat": "Haste", "aliases": "ability haste, item haste, 궁극기 가속, 스킬 가속", "category": "haste", "description": "스킬/아이템/소환사 주문 등의 사용 가능 빈도를 높이는 스탯이다. Ability Haste는 쿨다운 감소율로 환산할 수 있다.", "formula": "cooldown_multiplier = 100 / (100 + ability_haste); cooldown_reduction = ability_haste / (100 + ability_haste)", "source_url": "https://wiki.leagueoflegends.com/en-us/Haste"},
    {"stat": "Mana", "aliases": "마나", "category": "resource", "description": "많은 챔피언이 스킬 사용에 소비하는 자원이다.", "formula": "remaining_mana = current_mana - mana_cost", "source_url": "https://wiki.leagueoflegends.com/en-us/Mana"},
    {"stat": "Mana regeneration", "aliases": "mana regen, 마나 재생", "category": "resource", "description": "시간이 지남에 따라 마나를 회복하는 수치다.", "formula": "mana_restored ≈ mana_regen_per_5s * seconds / 5", "source_url": "https://wiki.leagueoflegends.com/en-us/Mana_regeneration"},
    {"stat": "Energy", "aliases": "기력", "category": "resource", "description": "일부 챔피언이 사용하는 빠르게 회복되는 스킬 자원이다.", "formula": "remaining_energy = current_energy - energy_cost + energy_restored", "source_url": "https://wiki.leagueoflegends.com/en-us/Energy"},
    {"stat": "Range", "aliases": "사거리, attack range", "category": "range", "description": "기본 공격 또는 스킬이 닿는 거리다.", "formula": "거리 조건: distance_to_target <= range", "source_url": "https://wiki.leagueoflegends.com/en-us/Range"},
    {"stat": "Movement speed", "aliases": "ms, 이속, 이동 속도", "category": "mobility", "description": "유닛의 이동 속도를 나타내며 로밍, 회피, 교전 진입/이탈에 영향을 준다.", "formula": "effective_movement_speed ≈ base_ms * (1 + bonus_ms_percent / 100) + flat_ms", "source_url": "https://wiki.leagueoflegends.com/en-us/Movement_speed"},
]


def first_existing_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    normalized = {str(c).replace("\ufeff", "").strip().lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]
    return None


def ensure_column(df: pd.DataFrame, target: str, candidates: List[str], default_value: Any = "") -> pd.DataFrame:
    if target in df.columns:
        return df
    found = first_existing_column(df, candidates)
    if found is not None:
        df[target] = df[found]
    else:
        df[target] = default_value
    return df


def normalize_master_tables(characters: pd.DataFrame, skills: pd.DataFrame, equipment_sets: pd.DataFrame, patch_notes: pd.DataFrame):
    characters = ensure_column(characters if not characters is None else pd.DataFrame(), "name", ["name", "character", "character_name", "캐릭터명", "이름", "hero_name"], "")
    # reuse clean columns behavior from qagent_core.data_io if caller wants full cleaning
    characters = characters
    skills = ensure_column(skills if not skills is None else pd.DataFrame(), "skill_name", ["skill_name", "skill", "name", "스킬명", "스킬"], "")
    equipment_sets = ensure_column(equipment_sets if not equipment_sets is None else pd.DataFrame(), "set_name", ["set_name", "equipment_set", "name", "세트명", "장비세트"], "")
    patch_notes = ensure_column(patch_notes if not patch_notes is None else pd.DataFrame(), "patch_version", ["patch_version", "version", "패치버전"], "")
    return characters, skills, equipment_sets, patch_notes


def to_jsonable_df(df: pd.DataFrame, max_rows: int = 20) -> List[Dict[str, Any]]:
    if df is None or df.empty:
        return []
    safe = df.head(max_rows).copy()
    for col in safe.columns:
        if pd.api.types.is_float_dtype(safe[col]):
            safe[col] = safe[col].round(4)
    return safe.to_dict(orient="records")


def split_team(team: str) -> List[str]:
    return [x.strip() for x in str(team).split("/") if x.strip()]


def normalize_text(value: Any) -> str:
    return str(value).lower().strip()


def parse_number(value: Any) -> Tuple[Optional[float], str]:
    text = str(value).strip()
    match = re.search(r"(-?\d+(\.\d+)?)", text)
    if not match:
        return None, ""
    number = float(match.group(1))
    suffix = "%" if "%" in text else ""
    return number, suffix


def format_value(number: float, suffix: str) -> str:
    if suffix == "%":
        return f"{number:.1f}%".replace(".0%", "%")
    return f"{number:.2f}".rstrip("0").rstrip(".")


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def patch_sort_key(version: Any) -> tuple:
    text = str(version).strip().replace("V", "")
    nums = [int(x) for x in re.findall(r"\d+", text)]
    if not nums:
        return (9999, 9999, text)
    while len(nums) < 3:
        nums.append(0)
    return (nums[0], nums[1], nums[2], text)


def map_game_version_to_patch_version(game_version: Any) -> str:
    if game_version is None or pd.isna(game_version):
        return ""
    text = str(game_version).strip().replace("V", "")
    match = re.search(r"(\d+)\.(\d+)", text)
    if not match:
        return ""
    major = int(match.group(1))
    minor = int(match.group(2))
    if major >= 15:
        return f"{major + 10}.{minor:02d}"
    return f"{major}.{minor}"


def normalize_existing_patch_version(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().replace("V", "")
    match = re.fullmatch(r"(\d+)\.(\d+)", text)
    if not match:
        return text
    major = int(match.group(1))
    minor = int(match.group(2))
    if 15 <= major <= 19:
        return f"{major + 10}.{minor:02d}"
    if major >= 25:
        return f"{major}.{minor:02d}"
    return f"{major}.{minor}"


def apply_lol_patch_version_mapping(battles: pd.DataFrame) -> pd.DataFrame:
    df = battles.copy()
    if "game_version" not in df.columns:
        if "patch_version" in df.columns:
            df["patch_version"] = df["patch_version"].apply(normalize_existing_patch_version)
        return df
    if "patch_version" in df.columns and "original_patch_version" not in df.columns:
        df["original_patch_version"] = df["patch_version"].astype(str)
    mapped = df["game_version"].apply(map_game_version_to_patch_version)
    if "patch_version" not in df.columns:
        df["patch_version"] = mapped
    else:
        df["patch_version"] = mapped.where(mapped.astype(str).str.len() > 0, df["patch_version"].astype(str))
        df["patch_version"] = df["patch_version"].apply(normalize_existing_patch_version)
    df["patch_version_mapping_rule"] = "game 1.x~14.x => patch same; game 15.x+ => patch 25.x+"
    return df


def get_latest_patch_version(battles: pd.DataFrame) -> str:
    versions = sorted([str(v) for v in battles["patch_version"].dropna().unique()], key=patch_sort_key)
    return versions[-1] if versions else ""


def get_previous_patch_version(battles: pd.DataFrame, current_version: str) -> str:
    versions = sorted([str(v) for v in battles["patch_version"].dropna().unique()], key=patch_sort_key)
    if current_version in versions:
        idx = versions.index(current_version)
        if idx > 0:
            return versions[idx - 1]
    return versions[0] if versions else ""


def search_lol_stat_knowledge(query: str = "", stats: Optional[List[str]] = None, max_rows: int = 10) -> List[Dict[str, Any]]:
    query_text = normalize_text(query)
    stat_filters = {normalize_text(s) for s in stats or [] if str(s).strip()}
    rows = []
    for row in LOL_STAT_KNOWLEDGE:
        haystack = normalize_text(" ".join([row.get("stat", ""), row.get("aliases", ""), row.get("category", ""), row.get("description", ""), row.get("formula", "")]))
        stat_name = normalize_text(row.get("stat", ""))
        if stat_filters and not any(f in stat_name or f in haystack for f in stat_filters):
            continue
        if query_text and query_text not in haystack and not any(token in haystack for token in query_text.split() if len(token) >= 2):
            continue
        rows.append(row)
    return rows[:max_rows]
