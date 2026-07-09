"""
generate_battle_balance_v2_demo_data.py

Battle Balance Analyst Generative AI Agent v2용 예제 데이터 생성 스크립트입니다.

생성되는 각 시나리오 폴더에는 다음 파일이 들어갑니다.

- battle_logs.csv
- characters.csv
- skills.csv
- equipment_sets.csv
- patch_notes.csv
- agent_prompt_v2.txt
- README.md

실행:
    python generate_battle_balance_v2_demo_data.py

출력:
    ./battle_balance_v2_demo_data/
    ./battle_balance_v2_demo_data.zip
"""

from __future__ import annotations

import argparse
import csv
import random
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


BATTLE_COLUMNS = [
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

SEGMENTS = ["beginner", "mid", "advanced"]


@dataclass
class TeamProfile:
    """Synthetic team performance profile used to generate battle rows."""

    team: str
    equipment: str
    dealer: str
    skill: str

    pre_wr: float
    post_wr: float

    pre_damage: int
    post_damage: int

    pre_duration: int
    post_duration: int

    pre_weight: float
    post_weight: float

    damage_std: int = 26000
    duration_std: int = 14

    segment_bonus_name: Optional[str] = None
    segment_wr_delta: float = 0.0
    segment_damage_delta: int = 0
    segment_duration_delta: int = 0


@dataclass
class Scenario:
    """Definition of one generated demo dataset scenario."""

    folder_name: str
    title: str
    description: str
    problem_hint: str
    teams: List[TeamProfile]
    patch_notes: List[List[str]]
    skill_notes: Optional[Dict[str, str]] = None
    equipment_notes: Optional[Dict[str, str]] = None


def write_csv(path: Path, rows: List[List[object]]) -> None:
    """Write rows to a UTF-8-SIG CSV file, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def weighted_choice(items: List[TeamProfile], patch_version: str) -> TeamProfile:
    """Choose a team profile using pre/post patch sampling weights."""
    weights = [
        item.post_weight if patch_version == "1.2.0" else item.pre_weight
        for item in items
    ]

    total = sum(weights)
    r = random.random() * total
    current = 0.0

    for item, weight in zip(items, weights):
        current += weight
        if current >= r:
            return item

    return items[-1]


def make_characters() -> List[List[object]]:
    """Return the demo character master table rows."""
    return [
        [
            "character_id",
            "name",
            "role",
            "element",
            "base_attack",
            "base_hp",
            "main_skill",
            "design_intent",
        ],
        [
            "C001",
            "Luna",
            "Dealer",
            "Dark",
            920,
            4200,
            "Moon Slash",
            "광역 피해를 통해 중후반 전투를 마무리하는 딜러",
        ],
        [
            "C002",
            "Arthur",
            "Tank",
            "Light",
            610,
            7600,
            "Shield Break",
            "방어력 감소 디버프를 제공하는 탱커",
        ],
        [
            "C003",
            "Kain",
            "Support",
            "Dark",
            540,
            5100,
            "Critical Order",
            "치명타 확률 버프로 딜러를 보조하는 서포터",
        ],
        [
            "C004",
            "Noah",
            "Dealer",
            "Fire",
            870,
            4300,
            "Dark Pierce",
            "단일 대상 피해에 강한 딜러",
        ],
        [
            "C005",
            "Rin",
            "Healer",
            "Water",
            430,
            5900,
            "Healing Rain",
            "지속 회복을 통해 장기전을 지원하는 힐러",
        ],
        [
            "C006",
            "Evan",
            "Tank",
            "Earth",
            590,
            8000,
            "Stone Guard",
            "피해 감소 기반 방어형 탱커",
        ],
        [
            "C007",
            "Mira",
            "Dealer",
            "Fire",
            890,
            4100,
            "Flame Burst",
            "광역 화염 피해를 가진 딜러",
        ],
        [
            "C008",
            "Selene",
            "Support",
            "Light",
            510,
            5400,
            "Blessing Mark",
            "공격 속도와 행동 순서를 보조하는 서포터",
        ],
        [
            "C009",
            "Darius",
            "Tank",
            "Dark",
            640,
            7900,
            "Iron Wall",
            "실드와 도발로 아군을 보호하는 탱커",
        ],
        [
            "C010",
            "Iris",
            "Dealer",
            "Water",
            840,
            4400,
            "Frost Arrow",
            "감속과 단일 피해를 함께 제공하는 딜러",
        ],
    ]


def make_skills(skill_notes: Optional[Dict[str, str]] = None) -> List[List[object]]:
    """Return the demo skill master table rows with optional scenario notes."""
    rows = [
        [
            "skill_name",
            "character",
            "skill_type",
            "damage_multiplier",
            "cooldown_sec",
            "effect",
            "balance_note",
        ],
        ["Moon Slash", "Luna", "damage", 3.8, 8, "AOE damage", "광역 피해"],
        ["Shield Break", "Arthur", "debuff", 1.2, 10, "defense_down", "방어력 감소"],
        ["Critical Order", "Kain", "buff", 0.0, 12, "critical_rate_up", "치명타 증가"],
        [
            "Dark Pierce",
            "Noah",
            "damage",
            3.2,
            7,
            "single_target_damage",
            "단일 대상 피해",
        ],
        ["Healing Rain", "Rin", "heal", 0.0, 12, "team_heal", "팀 회복"],
        ["Stone Guard", "Evan", "defense", 0.0, 15, "damage_reduction", "피해 감소"],
        ["Flame Burst", "Mira", "damage", 3.5, 9, "AOE fire damage", "광역 화염 피해"],
        [
            "Blessing Mark",
            "Selene",
            "buff",
            0.0,
            13,
            "attack_speed_up",
            "공격 속도 증가",
        ],
        ["Iron Wall", "Darius", "defense", 0.0, 15, "shield", "실드"],
        ["Frost Arrow", "Iris", "damage", 3.3, 8, "slow_and_damage", "감속 및 피해"],
    ]

    if skill_notes:
        for row in rows[1:]:
            skill_name = str(row[0])
            if skill_name in skill_notes:
                row[-1] = skill_notes[skill_name]

    return rows


def make_equipment_sets(
    equipment_notes: Optional[Dict[str, str]] = None,
) -> List[List[object]]:
    """Return the demo equipment master table rows with optional notes."""
    rows = [
        [
            "set_name",
            "set_type",
            "bonus_type",
            "bonus_value",
            "condition",
            "balance_note",
        ],
        ["Vanguard", "attack", "attack_bonus", "12%", "2-set active", "공격 보너스"],
        ["Guardian", "defense", "damage_reduction", "14%", "2-set active", "피해 감소"],
        [
            "Arcane",
            "utility",
            "cooldown_reduction",
            "10%",
            "2-set active",
            "스킬 회전율 증가",
        ],
        [
            "Assassin",
            "attack",
            "critical_damage",
            "20%",
            "2-set active",
            "치명타 피해량 증가",
        ],
        ["Sanctuary", "support", "healing_bonus", "15%", "2-set active", "회복량 증가"],
    ]

    if equipment_notes:
        for row in rows[1:]:
            set_name = str(row[0])
            if set_name in equipment_notes:
                row[-1] = equipment_notes[set_name]

    return rows


def make_battle_row(
    battle_num: int,
    patch_version: str,
    team_profile: TeamProfile,
    enemy_team: str,
) -> List[object]:
    """Generate one synthetic battle log row for a team and patch."""
    is_post = patch_version == "1.2.0"

    wr = team_profile.post_wr if is_post else team_profile.pre_wr
    damage_mean = team_profile.post_damage if is_post else team_profile.pre_damage
    duration_mean = team_profile.post_duration if is_post else team_profile.pre_duration

    segment = random.choices(
        SEGMENTS,
        weights=[0.25, 0.45, 0.30],
        k=1,
    )[0]

    if (
        is_post
        and team_profile.segment_bonus_name
        and segment == team_profile.segment_bonus_name
    ):
        wr += team_profile.segment_wr_delta
        damage_mean += team_profile.segment_damage_delta
        duration_mean += team_profile.segment_duration_delta

    wr = min(max(wr, 0.05), 0.96)

    result = "win" if random.random() < wr else "lose"

    damage = int(
        max(
            60000,
            random.gauss(damage_mean, team_profile.damage_std),
        )
    )
    duration = int(
        max(
            35,
            random.gauss(duration_mean, team_profile.duration_std),
        )
    )

    if result == "lose":
        damage = int(damage * random.uniform(0.64, 0.88))
        duration = int(duration * random.uniform(1.05, 1.25))

    return [
        f"B{battle_num:05d}",
        patch_version,
        team_profile.team,
        enemy_team,
        result,
        duration,
        team_profile.dealer,
        damage,
        team_profile.skill,
        team_profile.equipment,
        segment,
        "arena",
    ]


def generate_battle_logs(
    teams: List[TeamProfile],
    n_pre: int = 360,
    n_post: int = 600,
) -> List[List[object]]:
    """Generate battle log CSV rows for one scenario."""
    rows = [BATTLE_COLUMNS]
    enemy_teams = [team.team for team in teams]

    battle_num = 1

    for _ in range(n_pre):
        selected = weighted_choice(teams, "1.1.0")
        enemy = random.choice([team for team in enemy_teams if team != selected.team])
        rows.append(make_battle_row(battle_num, "1.1.0", selected, enemy))
        battle_num += 1

    for _ in range(n_post):
        selected = weighted_choice(teams, "1.2.0")
        enemy = random.choice([team for team in enemy_teams if team != selected.team])
        rows.append(make_battle_row(battle_num, "1.2.0", selected, enemy))
        battle_num += 1

    return rows


def base_team_pool(problem_team: TeamProfile) -> List[TeamProfile]:
    """Return baseline control teams plus the scenario's problem team."""
    normal_teams = [
        TeamProfile(
            "Luna/Arthur/Kain",
            "Vanguard",
            "Luna",
            "Moon Slash",
            0.54,
            0.56,
            185000,
            190000,
            96,
            95,
            0.12,
            0.10,
        ),
        TeamProfile(
            "Noah/Rin/Evan",
            "Guardian",
            "Noah",
            "Dark Pierce",
            0.51,
            0.50,
            176000,
            174000,
            106,
            108,
            0.13,
            0.10,
        ),
        TeamProfile(
            "Mira/Noah/Rin",
            "Arcane",
            "Mira",
            "Flame Burst",
            0.52,
            0.53,
            180000,
            184000,
            101,
            98,
            0.13,
            0.10,
        ),
        TeamProfile(
            "Selene/Iris/Darius",
            "Assassin",
            "Iris",
            "Frost Arrow",
            0.53,
            0.55,
            184000,
            190000,
            100,
            97,
            0.13,
            0.10,
        ),
        TeamProfile(
            "Mira/Arthur/Selene",
            "Vanguard",
            "Mira",
            "Flame Burst",
            0.55,
            0.57,
            190000,
            197000,
            94,
            91,
            0.13,
            0.10,
        ),
        TeamProfile(
            "Luna/Rin/Darius",
            "Sanctuary",
            "Luna",
            "Moon Slash",
            0.52,
            0.54,
            179000,
            185000,
            104,
            101,
            0.13,
            0.10,
        ),
        TeamProfile(
            "Noah/Kain/Evan",
            "Guardian",
            "Noah",
            "Dark Pierce",
            0.50,
            0.50,
            172000,
            172000,
            109,
            110,
            0.12,
            0.10,
        ),
        TeamProfile(
            "Iris/Arthur/Rin",
            "Arcane",
            "Iris",
            "Frost Arrow",
            0.50,
            0.51,
            170000,
            173000,
            112,
            110,
            0.11,
            0.10,
        ),
    ]

    replaced = False
    for idx, team in enumerate(normal_teams):
        if team.team == problem_team.team:
            normal_teams[idx] = problem_team
            replaced = True
            break

    if not replaced:
        normal_teams.append(problem_team)

    return normal_teams


def make_scenarios() -> List[Scenario]:
    """Build all bundled synthetic demo scenarios."""
    scenarios: List[Scenario] = []

    # Scenario 1: 공격형 폭딜 메타
    burst_team = TeamProfile(
        team="Mira/Selene/Iris",
        equipment="Assassin",
        dealer="Mira",
        skill="Flame Burst",
        pre_wr=0.55,
        post_wr=0.89,
        pre_damage=196000,
        post_damage=305000,
        pre_duration=93,
        post_duration=64,
        pre_weight=0.12,
        post_weight=0.30,
        segment_bonus_name="advanced",
        segment_wr_delta=0.04,
        segment_damage_delta=18000,
        segment_duration_delta=-4,
    )

    scenarios.append(
        Scenario(
            folder_name="scenario_01_burst_meta",
            title="Scenario 01 - Burst Meta Overpower",
            description="Mira/Selene/Iris 조합이 패치 이후 과도한 순간 화력으로 높은 승률을 기록하는 시나리오입니다.",
            problem_hint="Mira/Selene/Iris + Assassin 조합의 순간 화력 과상승 여부를 중점적으로 확인하세요.",
            teams=base_team_pool(burst_team),
            skill_notes={
                "Flame Burst": "1.2.0 패치에서 피해 계수가 상향됨",
                "Blessing Mark": "1.2.0 패치에서 공격 속도 버프가 상향됨",
            },
            equipment_notes={
                "Assassin": "1.2.0 패치에서 치명타 피해량이 상향됨",
            },
            patch_notes=[
                [
                    "patch_version",
                    "date",
                    "change_target",
                    "before_value",
                    "after_value",
                    "description",
                ],
                ["1.1.0", "2026-06-20", "Baseline", "-", "-", "패치 전 기준 버전"],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Mira Flame Burst multiplier",
                    "3.2",
                    "3.9",
                    "Mira의 Flame Burst 피해 계수가 증가함",
                ],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Selene Blessing Mark attack speed",
                    "12%",
                    "22%",
                    "Selene의 Blessing Mark 공격 속도 증가량이 상승함",
                ],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Assassin set critical damage",
                    "20%",
                    "28%",
                    "Assassin 세트 치명타 피해량이 증가함",
                ],
            ],
        )
    )

    # Scenario 2: 방어/회복 장기전 메타
    stall_team = TeamProfile(
        team="Evan/Rin/Darius",
        equipment="Guardian",
        dealer="Darius",
        skill="Iron Wall",
        pre_wr=0.56,
        post_wr=0.86,
        pre_damage=150000,
        post_damage=178000,
        pre_duration=128,
        post_duration=154,
        pre_weight=0.12,
        post_weight=0.28,
        damage_std=18000,
        duration_std=22,
        segment_bonus_name="mid",
        segment_wr_delta=0.03,
        segment_damage_delta=6000,
        segment_duration_delta=8,
    )

    scenarios.append(
        Scenario(
            folder_name="scenario_02_stall_defense",
            title="Scenario 02 - Stall Defense Overpower",
            description="Evan/Rin/Darius 조합이 방어력과 회복량 상승으로 장기전에서 비정상적 승률을 보이는 시나리오입니다.",
            problem_hint="Evan/Rin/Darius + Guardian 조합이 전투 시간을 과도하게 늘리고 승률이 높아지는지 확인하세요.",
            teams=base_team_pool(stall_team),
            skill_notes={
                "Stone Guard": "1.2.0 패치에서 피해 감소량이 상향됨",
                "Healing Rain": "1.2.0 패치에서 회복량이 상향됨",
                "Iron Wall": "1.2.0 패치에서 실드량이 상향됨",
            },
            equipment_notes={
                "Guardian": "1.2.0 패치에서 피해 감소량이 상향됨",
            },
            patch_notes=[
                [
                    "patch_version",
                    "date",
                    "change_target",
                    "before_value",
                    "after_value",
                    "description",
                ],
                ["1.1.0", "2026-06-20", "Baseline", "-", "-", "패치 전 기준 버전"],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Evan Stone Guard damage reduction",
                    "12%",
                    "22%",
                    "Evan의 Stone Guard 피해 감소량이 증가함",
                ],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Rin Healing Rain healing bonus",
                    "10%",
                    "18%",
                    "Rin의 Healing Rain 회복량이 증가함",
                ],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Darius Iron Wall shield value",
                    "15%",
                    "25%",
                    "Darius의 Iron Wall 실드량이 증가함",
                ],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Guardian set damage reduction",
                    "12%",
                    "18%",
                    "Guardian 세트 피해 감소량이 증가함",
                ],
            ],
        )
    )

    # Scenario 3: 상위 유저 구간에서 과성능
    segment_team = TeamProfile(
        team="Noah/Kain/Evan",
        equipment="Vanguard",
        dealer="Noah",
        skill="Dark Pierce",
        pre_wr=0.53,
        post_wr=0.82,
        pre_damage=184000,
        post_damage=254000,
        pre_duration=98,
        post_duration=82,
        pre_weight=0.12,
        post_weight=0.27,
        segment_bonus_name="advanced",
        segment_wr_delta=0.08,
        segment_damage_delta=26000,
        segment_duration_delta=-7,
    )

    scenarios.append(
        Scenario(
            folder_name="scenario_03_advanced_segment",
            title="Scenario 03 - Advanced Segment Meta",
            description="Noah/Kain/Evan 조합이 특히 advanced 유저 구간에서 과성능을 보이는 시나리오입니다.",
            problem_hint="Noah/Kain/Evan + Vanguard 조합의 전체 이상 여부와 advanced 세그먼트 집중 여부를 확인하세요.",
            teams=base_team_pool(segment_team),
            skill_notes={
                "Dark Pierce": "1.2.0 패치에서 피해 계수가 상향됨",
                "Critical Order": "1.2.0 패치에서 치명타 증가량이 상향됨",
            },
            equipment_notes={
                "Vanguard": "1.2.0 패치에서 공격력 보너스가 상향됨",
            },
            patch_notes=[
                [
                    "patch_version",
                    "date",
                    "change_target",
                    "before_value",
                    "after_value",
                    "description",
                ],
                ["1.1.0", "2026-06-20", "Baseline", "-", "-", "패치 전 기준 버전"],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Noah Dark Pierce multiplier",
                    "3.1",
                    "3.8",
                    "Noah의 Dark Pierce 피해 계수가 증가함",
                ],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Kain Critical Order critical rate",
                    "15%",
                    "23%",
                    "Kain의 Critical Order 치명타 증가량이 증가함",
                ],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Vanguard set attack bonus",
                    "12%",
                    "20%",
                    "Vanguard 세트 공격력 보너스가 증가함",
                ],
            ],
        )
    )

    # Scenario 4: 원래 예시와 유사한 Luna/Kain/Vanguard 시나리오
    luna_team = TeamProfile(
        team="Luna/Arthur/Kain",
        equipment="Vanguard",
        dealer="Luna",
        skill="Moon Slash",
        pre_wr=0.58,
        post_wr=0.88,
        pre_damage=198000,
        post_damage=292000,
        pre_duration=91,
        post_duration=71,
        pre_weight=0.16,
        post_weight=0.30,
        segment_bonus_name="advanced",
        segment_wr_delta=0.04,
        segment_damage_delta=18000,
        segment_duration_delta=-3,
    )

    scenarios.append(
        Scenario(
            folder_name="scenario_04_luna_vanguard",
            title="Scenario 04 - Luna Vanguard Combo",
            description="Luna/Arthur/Kain 조합이 Moon Slash, Critical Order, Vanguard 상향이 중첩되어 과성능을 보이는 시나리오입니다.",
            problem_hint="Luna/Arthur/Kain + Vanguard 조합에서 스킬 계수, 치명타 버프, 공격 세트 효과가 중첩되는지 확인하세요.",
            teams=base_team_pool(luna_team),
            skill_notes={
                "Moon Slash": "1.2.0 패치에서 피해 계수가 상향됨",
                "Critical Order": "1.2.0 패치에서 치명타 증가량이 상향됨",
            },
            equipment_notes={
                "Vanguard": "1.2.0 패치에서 공격력 보너스가 상향됨",
            },
            patch_notes=[
                [
                    "patch_version",
                    "date",
                    "change_target",
                    "before_value",
                    "after_value",
                    "description",
                ],
                ["1.1.0", "2026-06-20", "Baseline", "-", "-", "패치 전 기준 버전"],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Luna Moon Slash multiplier",
                    "3.6",
                    "4.2",
                    "Luna의 Moon Slash 피해 계수가 증가함",
                ],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Kain Critical Order critical rate",
                    "15%",
                    "25%",
                    "Kain의 Critical Order 치명타 증가량이 증가함",
                ],
                [
                    "1.2.0",
                    "2026-07-01",
                    "Vanguard set attack bonus",
                    "10%",
                    "18%",
                    "Vanguard 장비 세트 공격력 보너스가 증가함",
                ],
            ],
        )
    )

    return scenarios


def make_agent_prompt(problem_hint: str) -> str:
    """Create the default Agent prompt stored beside each scenario."""
    return f"""3:3 모바일 RPG PvP 아레나 전투 로그를 분석해 밸런스 이상 조합을 찾아줘.
권장 기준은 최소 표본 수 30전, 승률 0.75 이상, 전체 평균 대비 승률 차이 0.20 이상이야.

이상 조합이 있다면 다음을 반드시 수행해줘.
1. 패치 전후 승률·피해량·전투 시간 변화 분석
2. beginner/mid/advanced 세그먼트별 영향 분석
3. 캐릭터, 스킬, 장비 세트, 패치노트 근거 검색
4. 스탯 시뮬레이터로 예상 피해량 증가율 계산
5. 부분 조정안 제안
6. 리스크 등급과 Human Review 절차 제안
7. 재테스트 계획 제안

이번 데이터의 시나리오 힌트:
{problem_hint}

반드시 Tool을 호출해서 데이터를 확인한 뒤 답변해줘.
"""


def write_scenario_files(
    root_dir: Path, scenario: Scenario, n_pre: int, n_post: int
) -> None:
    """Write all CSV, prompt, and README files for one scenario."""
    scenario_dir = root_dir / scenario.folder_name
    scenario_dir.mkdir(parents=True, exist_ok=True)

    write_csv(
        scenario_dir / "battle_logs.csv",
        generate_battle_logs(scenario.teams, n_pre=n_pre, n_post=n_post),
    )
    write_csv(scenario_dir / "characters.csv", make_characters())
    write_csv(scenario_dir / "skills.csv", make_skills(scenario.skill_notes))
    write_csv(
        scenario_dir / "equipment_sets.csv",
        make_equipment_sets(scenario.equipment_notes),
    )
    write_csv(scenario_dir / "patch_notes.csv", scenario.patch_notes)

    (scenario_dir / "agent_prompt_v2.txt").write_text(
        make_agent_prompt(scenario.problem_hint),
        encoding="utf-8",
    )

    readme = f"""# {scenario.title}

{scenario.description}

## 예상 분석 포인트

{scenario.problem_hint}

## 포함 파일

- battle_logs.csv
- characters.csv
- skills.csv
- equipment_sets.csv
- patch_notes.csv
- agent_prompt_v2.txt

## 사용 방법

1. Battle Balance Analyst Generative AI Agent v2 실행
2. 이 폴더의 CSV 5개를 각각 업로드
3. agent_prompt_v2.txt 내용을 Agent 목표 입력창에 붙여넣기
4. OpenAI API Key 입력
5. 생성형 AI Agent 실행

## 기대되는 Tool 호출 흐름

- get_dataset_overview
- detect_anomalies
- analyze_patch_impact
- analyze_segment_performance
- retrieve_related_knowledge
- simulate_stat_impact
- calculate_adjustment_options
- assess_balance_risk
- generate_retest_plan
"""
    (scenario_dir / "README.md").write_text(readme, encoding="utf-8")


def make_zip(root_dir: Path, zip_path: Path) -> None:
    """Create a zip archive containing generated demo data."""
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for file in root_dir.rglob("*"):
            z.write(file, file.relative_to(root_dir.parent))


def main() -> None:
    """CLI entry point for generating demo datasets."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", default="battle_balance_v2_demo_data", help="출력 폴더"
    )
    parser.add_argument("--seed", type=int, default=20260702, help="난수 시드")
    parser.add_argument(
        "--n-pre", type=int, default=360, help="1.1.0 패치 전 전투 로그 수"
    )
    parser.add_argument(
        "--n-post", type=int, default=600, help="1.2.0 패치 후 전투 로그 수"
    )
    parser.add_argument("--no-zip", action="store_true", help="ZIP 파일을 만들지 않음")
    args = parser.parse_args()

    random.seed(args.seed)

    root_dir = Path(args.output)
    if root_dir.exists():
        shutil.rmtree(root_dir)
    root_dir.mkdir(parents=True, exist_ok=True)

    scenarios = make_scenarios()

    for scenario in scenarios:
        write_scenario_files(root_dir, scenario, n_pre=args.n_pre, n_post=args.n_post)

    summary = "# Battle Balance Agent v2 예제 데이터\n\n"
    summary += "생성된 시나리오:\n\n"
    for scenario in scenarios:
        summary += f"- `{scenario.folder_name}`: {scenario.title}\n"
        summary += f"  - {scenario.description}\n"
    summary += "\n각 시나리오 폴더의 CSV 5개를 Agent v2 앱에 업로드해서 실행하세요.\n"

    (root_dir / "README.md").write_text(summary, encoding="utf-8")

    print(f"[OK] Generated scenario data at: {root_dir.resolve()}")

    if not args.no_zip:
        zip_path = root_dir.with_suffix(".zip")
        make_zip(root_dir, zip_path)
        print(f"[OK] Created ZIP: {zip_path.resolve()}")


if __name__ == "__main__":
    main()
