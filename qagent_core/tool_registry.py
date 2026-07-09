# Centralized tool schemas for the Agent. Kept as a separate module so tests and the agent
# can load schemas from a single authoritative source.

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_dataset_overview",
            "description": "데이터셋의 전체 규모, 패치 버전, 평균 승률, 평균 피해량 등 기본 정보를 확인한다.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_team_performance",
            "description": "조합, 장비 세트, 딜러, 스킬, 세그먼트, 패치 버전 기준 성능 지표를 집계한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {
                        "type": "string",
                        "enum": [
                            "player_team",
                            "equipment_set",
                            "main_dealer",
                            "skill_used_most",
                            "user_segment",
                            "patch_version",
                        ],
                    },
                    "top_n": {"type": "integer", "minimum": 1, "maximum": 30},
                },
                "required": ["group_by"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_anomalies",
            "description": "전체 평균 대비 성능이 높은 조합 중 통계 기준을 통과한 추가 검토 후보를 탐지한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_samples": {"type": "integer", "minimum": 10, "maximum": 200},
                    "win_rate_threshold": {
                        "type": "number",
                        "minimum": 0.5,
                        "maximum": 0.99,
                    },
                    "win_rate_gap_threshold": {
                        "type": "number",
                        "minimum": 0.01,
                        "maximum": 0.6,
                    },
                    "wilson_lower_gap_threshold": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 0.3,
                    },
                    "segment_by": {
                        "type": "string",
                        "enum": ["", "none", "user_segment", "battle_mode"],
                    },
                    "fdr_alpha": {"type": "number", "minimum": 0.001, "maximum": 0.25},
                    "top_n": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "required": [
                    "min_samples",
                    "win_rate_threshold",
                    "win_rate_gap_threshold",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_patch_performance",
            "description": "특정 조합, 장비, 스킬의 패치 버전별 승률·피해량 변화를 비교한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_team": {"type": "string"},
                    "equipment_set": {"type": "string"},
                    "skill_used_most": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_patch_impact",
            "description": "특정 조합의 패치 전후 승률, 피해량, 전투 시간 변화량을 계산한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_team": {"type": "string"},
                    "equipment_set": {"type": "string"},
                    "skill_used_most": {"type": "string"},
                    "current_patch_version": {"type": "string"},
                },
                "required": ["player_team"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_segment_performance",
            "description": "특정 조합의 초보/중수/상위 유저 구간별 승률, 피해량, 전투 시간을 분석한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_team": {"type": "string"},
                    "equipment_set": {"type": "string"},
                    "skill_used_most": {"type": "string"},
                },
                "required": ["player_team"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_related_knowledge",
            "description": "특정 조합/스킬/패치에 관련된 캐릭터, 스킬, 아이템, 패치노트 매칭 정보를 검색한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_team": {"type": "string"},
                    "equipment_set": {"type": "string"},
                    "skill_used_most": {"type": "string"},
                    "patch_version": {"type": "string"},
                },
                "required": ["player_team", "patch_version"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_lol_stat_knowledge",
            "description": "LoL 스탯 설명과 계산 공식을 검색한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "stats": {"type": "array"},
                    "max_rows": {"type": "integer", "minimum": 1, "maximum": 50},
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_lol_stat_formulas",
            "description": "LoL 기본 스탯 공식으로 방어/마저/가속/공속 값을 계산한다.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_stat_impact",
            "description": "스킬 계수, 공격력, 세트 보너스, 버프성 패치가 피해량에 미치는 영향을 근사 계산한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_team": {"type": "string"},
                    "equipment_set": {"type": "string"},
                    "skill_used_most": {"type": "string"},
                    "patch_version": {"type": "string"},
                },
                "required": ["player_team", "patch_version"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_adjustment_options",
            "description": "패치노트 기반으로 완만한 조정(롤백) 제안 리스트를 생성한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_team": {"type": "string"},
                    "equipment_set": {"type": "string"},
                    "skill_used_most": {"type": "string"},
                    "patch_version": {"type": "string"},
                    "rollback_strength": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                },
                "required": ["player_team", "patch_version"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "assess_balance_risk",
            "description": "조합의 위험 점수를 산출하고 추천 의사결정(긴급/보수적/모니터)을 제시한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_team": {"type": "string"},
                    "win_rate": {"type": "number"},
                    "win_rate_gap": {"type": "number"},
                    "patch_win_rate_change": {"type": "number"},
                    "estimated_damage_increase_rate": {"type": "number"},
                },
                "required": ["player_team", "win_rate", "win_rate_gap"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_retest_plan",
            "description": "샘플 구간별 재테스트 계획을 생성한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_team": {"type": "string"},
                    "equipment_set": {"type": "string"},
                    "skill_used_most": {"type": "string"},
                    "risk_level": {"type": "string"},
                },
                "required": ["player_team"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_virtual_patch_note",
            "description": "Agent 제안 조정안을 가상 패치노트 형태로 구조화한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_team": {"type": "string"},
                    "equipment_set": {"type": "string"},
                    "skill_used_most": {"type": "string"},
                    "patch_version": {"type": "string"},
                    "risk_level": {"type": "string"},
                    "adjustment_direction": {"type": "string"},
                    "adjustment_intensity": {"type": "number"},
                    "reasoning": {"type": "string"},
                },
                "required": ["player_team", "patch_version"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_virtual_patch_impact",
            "description": "가정된 가상 패치가 적용되었을 때의 통계적 시나리오를 근사 추정한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_team": {"type": "string"},
                    "equipment_set": {"type": "string"},
                    "skill_used_most": {"type": "string"},
                    "base_patch_version": {"type": "string"},
                    "virtual_patch_version": {"type": "string"},
                    "expected_win_rate_delta_points": {"type": "number"},
                    "expected_damage_delta_percent": {"type": "number"},
                },
                "required": ["player_team"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reflect_on_virtual_patch",
            "description": "가상 패치 후보의 위험성/한계를 자기반성 형태로 정리한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_team": {"type": "string"},
                    "equipment_set": {"type": "string"},
                    "skill_used_most": {"type": "string"},
                    "base_patch_version": {"type": "string"},
                    "virtual_patch_version": {"type": "string"},
                    "projected_win_rate": {"type": "number"},
                    "projected_damage_delta_percent": {"type": "number"},
                    "human_decision_context": {"type": "string"},
                },
                "required": ["player_team"],
                "additionalProperties": False,
            },
        },
    },
]
