from __future__ import annotations

import math
from functools import lru_cache
from typing import Iterable

import pandas as pd

from .simulation import project_patch_scenario

from .config import (
    BALANCE_FDR_ALPHA, BALANCE_MIN_SAMPLES, BALANCE_MIN_WILSON_DIFF,
    BALANCE_MIN_WIN_RATE, BALANCE_MIN_WIN_RATE_DIFF,
)


def normalize_win_results(results: Iterable[object]) -> pd.Series:
    """Return one boolean win flag per result using the canonical result rule.

    Only the case-insensitive, whitespace-trimmed value ``win`` is a win.
    Losses, missing values, and unknown values are all non-wins.  Keeping this
    rule in one function prevents descriptive and inferential statistics from
    counting the same row differently.
    """
    series = pd.Series(results, copy=False)
    return (
        series.astype("string")
        .str.strip()
        .str.lower()
        .eq("win")
        .fillna(False)
        .astype(bool)
    )


def win_rate(results: Iterable[object]) -> float:
    normalized_wins = normalize_win_results(results)
    if normalized_wins.empty:
        return 0.0
    return float(normalized_wins.mean())


def build_entity_labels(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    """Build stable labels even when pandas StringDtype contains float NaN values."""
    values = frame.loc[:, columns].apply(
        lambda column: column.map(lambda value: "(missing)" if pd.isna(value) else str(value))
    )
    return values.apply(lambda row: " | ".join(row.tolist()), axis=1)


def wilson_interval(wins: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Two-sided Wilson score interval; returns (0, 1) for no observations."""
    if total <= 0:
        return 0.0, 1.0
    wins = min(max(int(wins), 0), int(total))
    p = wins / total
    z2 = z * z
    denominator = 1 + z2 / total
    center = (p + z2 / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z2 / (4 * total)) / total) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def add_wilson_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    intervals = [wilson_interval(w, n) for w, n in zip(result["wins"], result["battles"])]
    result["win_rate_ci_low"] = [low for low, _ in intervals]
    result["win_rate_ci_high"] = [high for _, high in intervals]
    result["ci_width"] = result["win_rate_ci_high"] - result["win_rate_ci_low"]
    return result


@lru_cache(maxsize=100_000)
def binomial_upper_tail(wins: int, total: int, null_rate: float) -> float:
    """Exact one-sided P(X >= wins) under Binomial(total, null_rate)."""
    if total <= 0:
        return 1.0
    if null_rate <= 0:
        return 1.0 if wins <= 0 else 0.0
    if null_rate >= 1:
        return 1.0
    start = min(max(int(wins), 0), int(total))
    logs = [
        math.lgamma(total + 1) - math.lgamma(k + 1) - math.lgamma(total - k + 1)
        + k * math.log(null_rate) + (total - k) * math.log1p(-null_rate)
        for k in range(start, total + 1)
    ]
    maximum = max(logs)
    return min(1.0, math.exp(maximum) * sum(math.exp(value - maximum) for value in logs))


def benjamini_hochberg(p_values: Iterable[float]) -> list[float]:
    values = [min(max(float(value), 0.0), 1.0) for value in p_values]
    count = len(values)
    if not count:
        return []
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    adjusted = [1.0] * count
    running = 1.0
    for rank_index in range(count - 1, -1, -1):
        original_index, value = ordered[rank_index]
        rank = rank_index + 1
        running = min(running, value * count / rank)
        adjusted[original_index] = min(running, 1.0)
    return adjusted


def detect_balance_candidates(
    battles: pd.DataFrame,
    min_samples: int = BALANCE_MIN_SAMPLES,
    win_rate_threshold: float = BALANCE_MIN_WIN_RATE,
    win_rate_gap_threshold: float = BALANCE_MIN_WIN_RATE_DIFF,
    wilson_lower_gap_threshold: float = BALANCE_MIN_WILSON_DIFF,
    segment_by: str = "",
    fdr_alpha: float = BALANCE_FDR_ALPHA,
) -> tuple[float, pd.DataFrame]:
    required = {
        "battle_id", "patch_version", "player_team", "equipment_set",
        "skill_used_most", "result", "total_damage", "duration_sec",
    }
    missing = sorted(required - set(battles.columns))
    if missing:
        raise ValueError(f"밸런스 검토 후보 탐지 필수 컬럼 누락: {missing}")
    if battles.empty:
        return 0.0, pd.DataFrame(columns=[
            "patch_version", "player_team", "equipment_set", "skill_used_most",
            "battles", "wins", "win_rate", "avg_damage", "avg_duration_sec",
            "win_rate_ci_low", "win_rate_ci_high", "ci_width", "win_rate_gap",
            "damage_index", "sample_confidence", "candidate_score", "anomaly_score",
            "entity", "group_by", "n", "global_win_rate", "win_rate_diff",
            "wilson_low", "wilson_high", "p_value", "fdr_q_value",
            "candidate_reason", "interpretation_warning",
        ])

    overall = win_rate(battles["result"])
    allowed_segments = {"": "", "none": "", "user_segment": "user_segment", "battle_mode": "battle_mode"}
    if segment_by not in allowed_segments:
        raise ValueError("segment_by는 none, user_segment, battle_mode 중 하나여야 합니다.")
    segment_column = allowed_segments[segment_by]
    if segment_column and segment_column not in battles.columns:
        raise ValueError(f"세그먼트 비교 컬럼이 없습니다: {segment_column}")
    group_columns = ["patch_version", "player_team", "equipment_set", "skill_used_most"]
    if segment_column:
        group_columns.append(segment_column)
    working_columns = list(dict.fromkeys(
        group_columns + ["battle_id", "result", "total_damage", "duration_sec"]
    ))
    working = battles.loc[:, working_columns].copy()
    # This single flag feeds wins, win rate, Wilson intervals, and p-values.
    working["_win"] = normalize_win_results(working["result"]).astype("int8")
    grouped = (
        working.groupby(
            group_columns,
            dropna=False,
        )
        .agg(
            battles=("battle_id", "count"),
            wins=("_win", "sum"),
            avg_damage=("total_damage", "mean"),
            avg_duration_sec=("duration_sec", "mean"),
        )
        .reset_index()
    )
    grouped["win_rate"] = grouped["wins"] / grouped["battles"]
    grouped = add_wilson_columns(grouped)
    grouped["win_rate_gap"] = grouped["win_rate"] - overall
    grouped["p_value"] = [
        binomial_upper_tail(int(wins), int(total), overall)
        for wins, total in zip(grouped["wins"], grouped["battles"])
    ]
    grouped["fdr_q_value"] = benjamini_hochberg(grouped["p_value"])
    mean_damage = pd.to_numeric(battles["total_damage"], errors="coerce").mean()
    grouped["damage_index"] = grouped["avg_damage"] / max(float(mean_damage or 0), 1.0)
    grouped["sample_confidence"] = grouped["battles"].apply(
        lambda count: min(1.0, count / max(min_samples * 3, 1))
    )
    # CI lower bound makes small, noisy groups less likely to rank highly.
    grouped["candidate_score"] = (
        (grouped["win_rate_ci_low"] - overall) * 100
        + grouped["damage_index"].clip(upper=3) * 5
        + grouped["sample_confidence"] * 8
    )
    # Backward-compatible alias for clients built against the v2.7 Tool response.
    grouped["anomaly_score"] = grouped["candidate_score"]
    grouped["entity"] = build_entity_labels(grouped, group_columns)
    grouped["group_by"] = " + ".join(group_columns)
    grouped["n"] = grouped["battles"]
    grouped["global_win_rate"] = overall
    grouped["win_rate_diff"] = grouped["win_rate_gap"]
    grouped["wilson_low"] = grouped["win_rate_ci_low"]
    grouped["wilson_high"] = grouped["win_rate_ci_high"]
    grouped["candidate_reason"] = (
        "최소 표본·승률 차이·Wilson 하한·FDR 기준을 모두 통과한 추가 검토 후보"
    )
    grouped["interpretation_warning"] = (
        "밸런스 이상 확정이 아님. 다중 비교는 FDR로 보정했지만 픽률/밴률, 숙련도, 상대 조합과 인과효과는 통제하지 않음."
    )
    candidates = grouped[
        (grouped["battles"] >= min_samples)
        & (grouped["win_rate"] >= win_rate_threshold)
        & (grouped["win_rate_gap"] >= win_rate_gap_threshold)
        & (grouped["win_rate_ci_low"] > overall + wilson_lower_gap_threshold)
        & (grouped["fdr_q_value"] <= fdr_alpha)
    ].copy()
    return overall, candidates.sort_values(
        ["candidate_score", "win_rate"], ascending=[False, False]
    )


def analyze_balance_stages(
    battles: pd.DataFrame,
    min_samples: int = BALANCE_MIN_SAMPLES,
    win_rate_threshold: float = BALANCE_MIN_WIN_RATE,
    effect_size_threshold: float = BALANCE_MIN_WIN_RATE_DIFF,
    wilson_lower_gap_threshold: float = BALANCE_MIN_WILSON_DIFF,
    fdr_alpha: float = BALANCE_FDR_ALPHA,
    top_n: int = 20,
) -> dict[str, object]:
    """Build a champion-first, exploratory QA balance review pipeline."""
    required = {
        "battle_id", "patch_version", "player_team", "equipment_set",
        "skill_used_most", "result",
    }
    missing = sorted(required - set(battles.columns))
    if missing:
        raise ValueError(f"단계형 밸런스 분석 필수 컬럼 누락: {missing}")

    global_warnings = [
        "결과는 통계적으로 이상이 확정된 판정이 아니라 밸런스 검토 후보입니다.",
        "1차 챔피언 비교에는 Benjamini-Hochberg FDR 보정을 적용했지만 후속 단계는 탐색적 분석입니다.",
        "세부 패치·세그먼트·아이템 그룹은 표본 수가 작아질수록 신뢰구간이 넓어질 수 있습니다.",
        "픽률과 밴률 데이터가 없어 계산하거나 추정하지 않았습니다.",
    ]
    empty_result = {
        "status": "ok",
        "overall_win_rate": 0.0,
        "data_availability": {"pick_rate": "not_available", "ban_rate": "not_available"},
        "warnings": global_warnings,
        "stages": [],
        "candidates": [],
    }
    if battles.empty:
        return empty_result

    working = battles.copy()
    working["_win"] = normalize_win_results(working["result"]).astype("int8")
    overall = float(working["_win"].mean())

    def aggregate(group_columns: list[str], stage: str) -> pd.DataFrame:
        grouped = (
            working.groupby(group_columns, dropna=False)
            .agg(n=("battle_id", "count"), wins=("_win", "sum"))
            .reset_index()
        )
        grouped["win_rate"] = grouped["wins"] / grouped["n"]
        intervals = [wilson_interval(int(w), int(n)) for w, n in zip(grouped["wins"], grouped["n"])]
        grouped["wilson_low"] = [item[0] for item in intervals]
        grouped["wilson_high"] = [item[1] for item in intervals]
        grouped["global_win_rate"] = overall
        grouped["win_rate_diff"] = grouped["win_rate"] - overall
        grouped["stage"] = stage
        grouped["entity"] = build_entity_labels(grouped, group_columns)
        return grouped

    champion_rows = aggregate(["player_team"], "1_champion_screening")
    champion_rows["p_value"] = [
        binomial_upper_tail(int(w), int(n), overall)
        for w, n in zip(champion_rows["wins"], champion_rows["n"])
    ]
    champion_rows["fdr_q_value"] = benjamini_hochberg(champion_rows["p_value"])
    champion_rows["reproducibility_note"] = "후속 패치별 재현성 확인 필요"
    champion_rows["possible_driver"] = "후속 세그먼트·아이템 분석 필요"
    champion_rows["recommendation_level"] = "모니터링"
    champion_rows["warnings"] = [list(global_warnings) for _ in range(len(champion_rows))]

    primary_mask = (
        (champion_rows["n"] >= min_samples)
        & (champion_rows["win_rate"] >= win_rate_threshold)
        & (champion_rows["win_rate_diff"] >= effect_size_threshold)
        & (champion_rows["wilson_low"] > overall + wilson_lower_gap_threshold)
        & (champion_rows["fdr_q_value"] <= fdr_alpha)
    )
    champion_rows.loc[primary_mask, "recommendation_level"] = "후속 분석"
    candidate_champions = champion_rows.loc[primary_mask, "player_team"].astype(str).tolist()
    candidate_data = working[working["player_team"].astype(str).isin(candidate_champions)].copy()

    patch_rows = aggregate(["player_team", "patch_version"], "2_patch_reproducibility")
    patch_rows = patch_rows[patch_rows["player_team"].astype(str).isin(candidate_champions)].copy()
    patch_min_samples = max(10, min_samples // 2)
    patch_rows["_supports"] = (
        (patch_rows["n"] >= patch_min_samples)
        & (patch_rows["win_rate_diff"] >= effect_size_threshold)
        & (patch_rows["wilson_low"] > overall)
    )
    support_counts = patch_rows.groupby("player_team")["_supports"].sum().to_dict()
    patch_counts = patch_rows.groupby("player_team").size().to_dict()
    patch_rows["reproducibility_note"] = patch_rows["player_team"].map(
        lambda name: (
            f"{int(support_counts.get(name, 0))}/{int(patch_counts.get(name, 0))}개 패치에서 효과 방향 재현"
        )
    )
    patch_rows["possible_driver"] = "패치별 표본 구성 차이 확인 필요"
    patch_rows["recommendation_level"] = patch_rows["_supports"].map(
        {True: "재현성 근거", False: "추가 표본 필요"}
    )
    patch_rows["warnings"] = [list(global_warnings) for _ in range(len(patch_rows))]

    segment_frames = []
    for dimension in ["user_segment", "skill_used_most"]:
        if dimension not in candidate_data.columns:
            continue
        frame = aggregate(["player_team", dimension], "3_segment_check")
        frame = frame[frame["player_team"].astype(str).isin(candidate_champions)].copy()
        frame["entity"] = frame["player_team"].astype(str) + f" | {dimension}=" + frame[dimension].astype(str)
        frame["reproducibility_note"] = "티어/포지션별 효과 방향과 표본 차이 확인"
        frame["possible_driver"] = f"{dimension} 구성 차이"
        frame["recommendation_level"] = frame["n"].map(
            lambda n: "세그먼트 검토" if n >= patch_min_samples else "추가 표본 필요"
        )
        frame["warnings"] = [list(global_warnings) for _ in range(len(frame))]
        segment_frames.append(frame)
    segment_rows = pd.concat(segment_frames, ignore_index=True) if segment_frames else pd.DataFrame()

    item_rows = aggregate(["player_team", "equipment_set"], "4_item_driver")
    item_rows = item_rows[item_rows["player_team"].astype(str).isin(candidate_champions)].copy()
    item_rows["reproducibility_note"] = "아이템은 원인 확정이 아닌 연관 후보"
    item_rows["possible_driver"] = item_rows.apply(
        lambda row: (
            f"아이템 조합 후보: {row['equipment_set']}"
            if row["n"] >= patch_min_samples and row["win_rate_diff"] >= effect_size_threshold
            else "아이템 원인 후보 근거 약함"
        ),
        axis=1,
    )
    item_rows["recommendation_level"] = item_rows["possible_driver"].map(
        lambda value: "원인 후보 검토" if value.startswith("아이템 조합 후보") else "모니터링"
    )
    item_rows["warnings"] = [list(global_warnings) for _ in range(len(item_rows))]

    final_rows = champion_rows[primary_mask].copy()
    for index, row in final_rows.iterrows():
        champion = str(row["player_team"])
        supporting = int(support_counts.get(champion, 0))
        total_patches = int(patch_counts.get(champion, 0))
        items = item_rows[item_rows["player_team"].astype(str) == champion]
        driver = "아이템 원인 후보 없음"
        if not items.empty:
            driver = str(items.sort_values(["win_rate_diff", "n"], ascending=False).iloc[0]["possible_driver"])
        final_rows.at[index, "stage"] = "5_patch_review_candidate"
        final_rows.at[index, "reproducibility_note"] = f"{supporting}/{total_patches}개 패치에서 효과 방향 재현"
        final_rows.at[index, "possible_driver"] = driver
        final_rows.at[index, "recommendation_level"] = (
            "우선 검토 후보" if supporting >= 2 else "조건부 검토 후보"
        )

    def records(frame: pd.DataFrame, limit: int = top_n) -> list[dict[str, object]]:
        if frame.empty:
            return []
        fields = [
            "stage", "entity", "n", "wins", "win_rate", "global_win_rate",
            "win_rate_diff", "wilson_low", "wilson_high", "reproducibility_note",
            "possible_driver", "recommendation_level", "warnings",
        ]
        output = []
        ordered = frame.sort_values(["win_rate_diff", "n"], ascending=[False, False]).head(limit)
        for _, row in ordered.iterrows():
            item = {}
            for field in fields:
                value = row.get(field)
                if field in {"n", "wins"}:
                    value = int(value)
                elif field in {"win_rate", "global_win_rate", "win_rate_diff", "wilson_low", "wilson_high"}:
                    value = round(float(value), 4)
                item[field] = value
            output.append(item)
        return output

    stages = [
        {
            "stage": "1_champion_screening",
            "interpretation": "챔피언 단위로 최소 효과 크기·Wilson 구간·FDR을 확인합니다.",
            "rows": records(champion_rows),
        },
        {
            "stage": "2_patch_reproducibility",
            "interpretation": "1차 후보가 여러 패치에서 같은 방향으로 관찰되는지 확인합니다.",
            "rows": records(patch_rows),
        },
        {
            "stage": "3_segment_check",
            "interpretation": "티어와 포지션별 표본 및 효과 차이를 탐색합니다.",
            "rows": records(segment_rows),
        },
        {
            "stage": "4_item_driver",
            "interpretation": "아이템 조합을 인과 원인이 아닌 가능한 연관 요인으로 확인합니다.",
            "rows": records(item_rows),
        },
        {
            "stage": "5_patch_review_candidate",
            "interpretation": "최소 효과 크기와 신뢰구간을 통과한 사람 검토용 후보입니다.",
            "rows": records(final_rows),
        },
    ]
    return {
        "status": "ok",
        "overall_win_rate": round(overall, 4),
        "data_availability": {"pick_rate": "not_available", "ban_rate": "not_available"},
        "warnings": global_warnings,
        "stages": stages,
        "candidates": records(final_rows),
    }
