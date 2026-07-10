import json, re, shutil, zipfile
from pathlib import Path
from typing import Any

import pandas as pd

SRC = Path("/mnt/data/work_riot/riot_dataset")
OUT_ROOT = Path("/mnt/data/lol_assignment_ready")
DATA_DIR = OUT_ROOT / "data" / "lol_assignment_dataset"
EXTRA_DIR = DATA_DIR / "extras"
RAW_DIR = DATA_DIR / "raw_reference"

if OUT_ROOT.exists():
    shutil.rmtree(OUT_ROOT)
DATA_DIR.mkdir(parents=True, exist_ok=True)
EXTRA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with BOM and surrounding whitespace removed from columns."""
    df = df.copy()
    df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]
    return df


def as_int_or_none(x):
    """Convert a value to int when possible, otherwise return ``None``."""
    try:
        if pd.isna(x):
            return None
        return int(float(x))
    except Exception:
        return None


def extract_patch_version(game_version: Any):
    """Extract the major.minor patch prefix from a Riot game version."""
    if pd.isna(game_version):
        return ""
    parts = str(game_version).split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else str(game_version)


def join_names(vals):
    """Join non-empty values with slash separators for team composition labels."""
    return "/".join([str(x) for x in vals if str(x) and str(x) != "nan"])


def safe_numeric(s):
    """Convert a pandas object to numeric values with invalid entries coerced."""
    return pd.to_numeric(s, errors="coerce")


def first_number(value):
    """Extract the first numeric literal from a mixed text value."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    m = re.search(r"-?\d+(?:\.\s*\d+|\.\d+)?", str(value))
    if not m:
        return None
    try:
        return float(m.group(0).replace(" ", ""))
    except Exception:
        return None


def parse_first_damage_ratio(value):
    """Extract the first percent ratio from skill or item text."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value)
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if not m:
        return None
    try:
        return round(float(m.group(1)) / 100, 4)
    except Exception:
        return None


battles = clean_columns(pd.read_csv(SRC / "processed" / "battle_logs.csv"))
accounts = clean_columns(pd.read_csv(SRC / "processed" / "accounts.csv"))
player_match_ids = clean_columns(
    pd.read_csv(SRC / "processed" / "player_match_ids.csv")
)
collect_logs = clean_columns(pd.read_csv(SRC / "processed" / "collect_logs.csv"))
champions = clean_columns(
    pd.read_csv(SRC / "champsanditems" / "champions_processed.csv")
)
champion_map = clean_columns(
    pd.read_csv(SRC / "champsanditems" / "champion_id_map.csv")
)
items = clean_columns(pd.read_csv(SRC / "champsanditems" / "items_processed.csv"))
item_map = clean_columns(pd.read_csv(SRC / "champsanditems" / "item_id_map.csv"))
patch = clean_columns(pd.read_csv(SRC / "patch" / "lol_patch.csv"))

item_map2 = item_map.copy()
item_map2["item_id_int"] = pd.to_numeric(item_map2["item_id"], errors="coerce").astype(
    "Int64"
)
item_name_by_id = dict(
    zip(
        item_map2["item_id_int"].dropna().astype(int),
        item_map2.loc[item_map2["item_id_int"].notna(), "item_name"],
    )
)
item_buy_by_id = {}
if "buy" in item_map2.columns:
    for _, r in item_map2.iterrows():
        iid = as_int_or_none(r.get("item_id"))
        if iid is not None:
            item_buy_by_id[iid] = first_number(r.get("buy")) or 0

acc_ok = accounts[accounts.get("status", "") == "success"].copy()
puuid_tier = dict(zip(acc_ok["puuid"], acc_ok["tier"]))
puuid_riot = dict(zip(acc_ok["puuid"], acc_ok["riot_id"]))

battles["battle_id"] = (
    battles["match_id"].astype(str) + "_" + battles["participant_id"].astype(str)
)
battles["result"] = (
    battles["win"]
    .map({True: "win", False: "loss", "True": "win", "False": "loss"})
    .fillna(battles["win"].apply(lambda x: "win" if bool(x) else "loss"))
)
battles["duration_sec"] = battles["game_duration"]
battles["main_dealer"] = battles["champion_name"]
battles["total_damage"] = battles["total_damage_dealt_to_champions"]
battles["battle_mode"] = (
    battles["queue_id"]
    .map({420: "Ranked Solo/Duo", 440: "Ranked Flex", 450: "ARAM"})
    .fillna(battles["game_mode"].astype(str))
)
battles["user_segment"] = (
    battles["puuid"].map(puuid_tier).fillna(battles["source_tiers"].astype(str))
)
battles["source_player_riot_id"] = battles["source_riot_ids"]
battles["is_seed_player"] = battles["puuid"].isin(set(puuid_tier))

# item names for item0~item6
for c in [f"item{i}" for i in range(7)]:
    if c in battles.columns:
        battles[f"{c}_name"] = battles[c].apply(
            lambda x: (
                item_name_by_id.get(as_int_or_none(x), "")
                if as_int_or_none(x) not in (None, 0)
                else ""
            )
        )


# choose main item: highest buy among item0~item5, excluding trinket slot item6
def choose_main_item(row):
    """Choose the highest-price non-trinket item as the representative item."""
    candidates = []
    for c in [f"item{i}" for i in range(6)]:
        iid = as_int_or_none(row.get(c))
        if iid is None or iid == 0:
            continue
        name = item_name_by_id.get(iid, str(iid))
        price = item_buy_by_id.get(iid, 0)
        candidates.append((price, iid, name))
    if not candidates:
        return "No Main Item"
    candidates.sort(reverse=True)
    return candidates[0][2]


battles["equipment_set"] = battles.apply(choose_main_item, axis=1)
battles["skill_used_most"] = battles["team_position"].fillna("").replace("", "UNKNOWN")
battles["player_team"] = battles["champion_name"]


# Enemy team composition per participant
def make_enemy_team_map(df):
    """Build enemy team composition labels keyed by match and participant."""
    maps = {}
    for mid, g in df.groupby("match_id"):
        comps = (
            g.groupby("team_id")["champion_name"]
            .apply(lambda s: "/".join(s.astype(str).tolist()))
            .to_dict()
        )
        for _, r in g.iterrows():
            enemy_team_id = 200 if r["team_id"] == 100 else 100
            maps[(r["match_id"], r["participant_id"])] = comps.get(enemy_team_id, "")
    return maps


enemy_map = make_enemy_team_map(battles)
battles["enemy_team"] = battles.apply(
    lambda r: enemy_map.get((r["match_id"], r["participant_id"]), ""), axis=1
)

# Core item build string excluding empty and trinket
item_name_cols = [
    f"item{i}_name" for i in range(6) if f"item{i}_name" in battles.columns
]
battles["item_build"] = (
    battles[item_name_cols]
    .fillna("")
    .apply(lambda r: "|".join([x for x in r.astype(str).tolist() if x]), axis=1)
)

# ensure patch_version from game_version
battles["patch_version"] = battles["game_version"].apply(extract_patch_version)

# Reorder columns: app-required first + LoL extras
required_first = [
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
extra_priority = [
    "source_tiers",
    "source_riot_ids",
    "source_puuids",
    "source_player_riot_id",
    "is_seed_player",
    "match_id",
    "game_id",
    "game_version",
    "queue_id",
    "map_id",
    "game_mode",
    "game_type",
    "game_duration",
    "game_start_kst",
    "game_end_kst",
    "participant_id",
    "puuid",
    "riot_id_game_name",
    "riot_id_tagline",
    "team_id",
    "team_position",
    "individual_position",
    "lane",
    "role",
    "win",
    "champion_id",
    "champion_name",
    "champ_level",
    "kills",
    "deaths",
    "assists",
    "kda",
    "gold_earned",
    "gold_spent",
    "total_cs",
    "total_damage_dealt_to_champions",
    "total_damage_taken",
    "vision_score",
    "damage_per_minute",
    "gold_per_minute",
    "vision_score_per_minute",
    "team_damage_percentage",
    "item_build",
    "item0",
    "item0_name",
    "item1",
    "item1_name",
    "item2",
    "item2_name",
    "item3",
    "item3_name",
    "item4",
    "item4_name",
    "item5",
    "item5_name",
    "item6",
    "item6_name",
    "primary_perk",
    "sub_style",
]
cols = []
for c in required_first + extra_priority + list(battles.columns):
    if c in battles.columns and c not in cols:
        cols.append(c)
battle_ready = battles[cols].copy()
battle_ready.to_csv(DATA_DIR / "battle_logs.csv", index=False, encoding="utf-8-sig")

chars = pd.DataFrame()
chars["name"] = champions["champion_name"]
chars["role"] = champions.get("role", "")
chars["element"] = champions.get("adaptivetype", champions.get("damage_type", ""))
chars["base_attack"] = champions.get("stat_dam_base", 0)
chars["base_hp"] = champions.get("stat_hp_base", 0)
chars["main_skill"] = champions.get("skill_q", "")
for c in [
    "id",
    "apiname",
    "title",
    "difficulty",
    "herotype",
    "alttype",
    "resource",
    "rangetype",
    "client_positions",
    "external_positions",
    "skill_passive",
    "skill_q",
    "skill_w",
    "skill_e",
    "skill_r",
    "stat_hp_base",
    "stat_hp_lvl",
    "stat_dam_base",
    "stat_dam_lvl",
    "stat_arm_base",
    "stat_mr_base",
    "stat_range",
    "stat_ms",
    "patch",
    "changes",
]:
    if c in champions.columns:
        name = "champion_id" if c == "id" else c
        chars[name] = champions[c]
chars.to_csv(DATA_DIR / "characters.csv", index=False, encoding="utf-8-sig")

skills_rows = []
sk_json_path = SRC / "champion_skills.json"
if sk_json_path.exists():
    sk = json.load(open(sk_json_path, encoding="utf-8"))
    for champ_name, data in sk.items():
        for slot in ["passive", "q", "w", "e", "r"]:
            v = data.get(slot, {}) if isinstance(data, dict) else {}
            if not isinstance(v, dict):
                continue
            skills_rows.append(
                {
                    "skill_name": v.get("name") or "",
                    "character": data.get("champion") or champ_name,
                    "skill_slot": slot.upper(),
                    "skill_type": slot.upper(),
                    "damage_multiplier": parse_first_damage_ratio(
                        v.get("damage_ratio")
                    ),
                    "cooldown_sec": first_number(v.get("cooldown")),
                    "effect": "buffs="
                    + "|".join(v.get("buffs") or [])
                    + "; debuffs="
                    + "|".join(v.get("debuffs") or []),
                    "cooldown_raw": v.get("cooldown"),
                    "cost_raw": v.get("cost"),
                    "range_raw": v.get("range"),
                    "cast_time_raw": v.get("cast_time"),
                    "damage_raw": v.get("damage"),
                    "damage_ratio_raw": "|".join(v.get("damage_ratio") or [])
                    if isinstance(v.get("damage_ratio"), list)
                    else v.get("damage_ratio"),
                    "buffs": "|".join(v.get("buffs") or []),
                    "debuffs": "|".join(v.get("debuffs") or []),
                    "description": v.get("description") or "",
                }
            )
skills = pd.DataFrame(skills_rows)
if skills.empty:
    # fallback using skill columns in champions_processed
    rows = []
    for _, r in champions.iterrows():
        for slot, col in [
            ("PASSIVE", "skill_passive"),
            ("Q", "skill_q"),
            ("W", "skill_w"),
            ("E", "skill_e"),
            ("R", "skill_r"),
        ]:
            rows.append(
                {
                    "skill_name": r.get(col, ""),
                    "character": r.get("champion_name", ""),
                    "skill_slot": slot,
                    "skill_type": slot,
                    "damage_multiplier": None,
                    "cooldown_sec": None,
                    "effect": "",
                    "description": "",
                }
            )
    skills = pd.DataFrame(rows)
skills.to_csv(DATA_DIR / "skills.csv", index=False, encoding="utf-8-sig")

equip = pd.DataFrame()
equip["set_name"] = items["item_name"]
equip["set_type"] = items.get("type", "")
equip["bonus_type"] = items.get("effect_names", "")
equip["bonus_value"] = items.get("buy", "")
equip["condition"] = items.get("availability", "")
# add item extras
for c in [
    "id",
    "tier",
    "buy",
    "sell",
    "type",
    "recipe",
    "builds_into",
    "stat_ad",
    "stat_ah",
    "stat_ap",
    "stat_armor",
    "stat_as",
    "stat_crit",
    "stat_hp",
    "stat_mana",
    "stat_mr",
    "stat_ms",
    "effect_names",
    "effect_text",
]:
    if c in items.columns:
        name = "item_id" if c == "id" else c
        equip[name] = items[c]
equip.to_csv(DATA_DIR / "equipment_sets.csv", index=False, encoding="utf-8-sig")

patch_ready = pd.DataFrame()
patch_ready["patch_version"] = patch["patch_version"].astype(str)
patch_ready["date"] = ""
patch_ready["change_target"] = patch["target"].fillna("")
patch_ready["before_value"] = patch.get("old_value", "")
patch_ready["after_value"] = patch.get("new_value", "")
patch_ready["description"] = patch["change_text"].fillna("")
for c in [
    "page_name",
    "section",
    "target",
    "subtarget",
    "change_text",
    "change_type",
    "old_value",
    "new_value",
]:
    if c in patch.columns:
        patch_ready[c] = patch[c]
patch_ready.to_csv(DATA_DIR / "patch_notes.csv", index=False, encoding="utf-8-sig")

accounts.to_csv(EXTRA_DIR / "accounts.csv", index=False, encoding="utf-8-sig")
player_match_ids.to_csv(
    EXTRA_DIR / "player_match_ids.csv", index=False, encoding="utf-8-sig"
)
collect_logs.to_csv(EXTRA_DIR / "collect_logs.csv", index=False, encoding="utf-8-sig")
champion_map.to_csv(
    EXTRA_DIR / "champion_id_map.csv", index=False, encoding="utf-8-sig"
)
item_map.to_csv(EXTRA_DIR / "item_id_map.csv", index=False, encoding="utf-8-sig")
champions.to_csv(
    EXTRA_DIR / "champions_processed.csv", index=False, encoding="utf-8-sig"
)
items.to_csv(EXTRA_DIR / "items_processed.csv", index=False, encoding="utf-8-sig")
patch.to_csv(EXTRA_DIR / "lol_patch_raw.csv", index=False, encoding="utf-8-sig")

# performance summary tables
perf = (
    battle_ready.groupby(["patch_version", "champion_name"], dropna=False)
    .agg(
        games=("battle_id", "count"),
        wins=("result", lambda s: int((s == "win").sum())),
        win_rate=("result", lambda s: round(float((s == "win").mean()), 4)),
        avg_kills=("kills", "mean"),
        avg_deaths=("deaths", "mean"),
        avg_assists=("assists", "mean"),
        avg_kda=("kda", "mean"),
        avg_damage=("total_damage_dealt_to_champions", "mean"),
        avg_gold=("gold_earned", "mean"),
        avg_cs=("total_cs", "mean"),
        avg_vision=("vision_score", "mean"),
    )
    .reset_index()
)
for c in [
    "avg_kills",
    "avg_deaths",
    "avg_assists",
    "avg_kda",
    "avg_damage",
    "avg_gold",
    "avg_cs",
    "avg_vision",
]:
    perf[c] = perf[c].round(2)
perf.to_csv(
    EXTRA_DIR / "champion_performance_by_patch.csv", index=False, encoding="utf-8-sig"
)

item_rows = []
for i in range(6):
    sub = battle_ready[
        [
            "battle_id",
            "patch_version",
            "champion_name",
            "result",
            "user_segment",
            "team_position",
            "total_damage_dealt_to_champions",
            "gold_earned",
            "kda",
            f"item{i}",
            f"item{i}_name",
        ]
    ].copy()
    sub = sub.rename(columns={f"item{i}": "item_id", f"item{i}_name": "item_name"})
    sub["item_slot"] = i
    item_rows.append(sub)
item_usage = pd.concat(item_rows, ignore_index=True)
item_usage = item_usage[
    (item_usage["item_id"].fillna(0).astype(float) != 0)
    & (item_usage["item_name"].astype(str) != "")
]
item_usage.to_csv(EXTRA_DIR / "item_usage_long.csv", index=False, encoding="utf-8-sig")
item_perf = (
    item_usage.groupby(["patch_version", "item_id", "item_name"], dropna=False)
    .agg(
        uses=("battle_id", "count"),
        wins=("result", lambda s: int((s == "win").sum())),
        win_rate=("result", lambda s: round(float((s == "win").mean()), 4)),
        avg_damage=("total_damage_dealt_to_champions", "mean"),
        avg_gold=("gold_earned", "mean"),
        avg_kda=("kda", "mean"),
    )
    .reset_index()
)
for c in ["avg_damage", "avg_gold", "avg_kda"]:
    item_perf[c] = item_perf[c].round(2)
item_perf.to_csv(
    EXTRA_DIR / "item_performance_by_patch.csv", index=False, encoding="utf-8-sig"
)

tier_perf = (
    battle_ready.groupby(["user_segment", "patch_version"], dropna=False)
    .agg(
        participant_rows=("battle_id", "count"),
        unique_matches=("match_id", "nunique"),
        win_rate=("result", lambda s: round(float((s == "win").mean()), 4)),
        avg_damage=("total_damage_dealt_to_champions", "mean"),
        avg_gold=("gold_earned", "mean"),
        avg_kda=("kda", "mean"),
    )
    .reset_index()
)
for c in ["avg_damage", "avg_gold", "avg_kda"]:
    tier_perf[c] = tier_perf[c].round(2)
tier_perf.to_csv(
    EXTRA_DIR / "tier_patch_performance.csv", index=False, encoding="utf-8-sig"
)

# summary JSON
summary = {
    "dataset_name": "lol_assignment_dataset",
    "purpose": "LoL patch note + Riot match detail dataset for battle balance AI agent assignment",
    "rows": {
        "battle_logs": int(len(battle_ready)),
        "characters": int(len(chars)),
        "skills": int(len(skills)),
        "equipment_sets": int(len(equip)),
        "patch_notes": int(len(patch_ready)),
        "accounts": int(len(accounts)),
        "player_match_ids": int(len(player_match_ids)),
    },
    "source_summary": json.load(
        open(SRC / "processed" / "summary.json", encoding="utf-8")
    ),
    "notes": [
        "battle_logs.csv is transformed to the app canonical schema while retaining LoL-specific columns.",
        "player_team is champion_name, equipment_set is the highest-price completed/current item found in item0~item5, skill_used_most is team_position.",
        "user_segment uses the known source player tier when the participant is one of the seed accounts; otherwise it uses source_tiers of the match.",
        "timeline data is not included because the current assignment app focuses on match-level balance analysis.",
    ],
}
save_json = lambda data, path: Path(path).write_text(
    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
)
save_json(summary, DATA_DIR / "dataset_summary.json")

# README
readme = f"""# LoL Assignment Dataset

이 폴더는 `app.py`에서 바로 사용할 수 있도록 정리한 LoL 데이터셋입니다.

## 필수 CSV 5개
- battle_logs.csv: 앱 분석용 핵심 전투 로그. 기존 RPG 샘플 앱의 필수 컬럼을 맞추면서 LoL 컬럼을 추가 보존했습니다.
- characters.csv: 챔피언 마스터 정보.
- skills.csv: 챔피언 스킬 정보.
- equipment_sets.csv: 아이템 마스터 정보. 기존 앱 호환을 위해 아이템을 equipment_set 형식으로 변환했습니다.
- patch_notes.csv: LoL Wiki 패치노트 중 Champions/Items 섹션 중심 전처리 결과.

## 추가 분석 파일
`extras/` 폴더에 계정, 매치 ID, 아이템/챔피언 매핑, 챔피언 성능 집계, 아이템 사용 집계가 들어 있습니다.

## 주요 변환 규칙
- battle_logs.player_team = champion_name
- battle_logs.equipment_set = item0~item5 중 가격이 가장 높은 아이템 이름
- battle_logs.skill_used_most = team_position
- battle_logs.result = win/loss
- battle_logs.total_damage = total_damage_dealt_to_champions
- battle_logs.duration_sec = game_duration

## 규모
- battle_logs: {len(battle_ready):,} rows
- characters: {len(chars):,} rows
- skills: {len(skills):,} rows
- equipment_sets/items: {len(equip):,} rows
- patch_notes: {len(patch_ready):,} rows
"""
(DATA_DIR / "README.md").write_text(readme, encoding="utf-8")

print(json.dumps(summary, ensure_ascii=False, indent=2))
