"""Measure local QAgent core performance without calling external APIs."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qagent_core.data_io import EXPECTED_DATA_FILES, clean_columns, load_data_folder
from qagent_core.persistence import SQLiteReviewRepository, append_csv_record
from qagent_core.statistics import (
    detect_balance_candidates,
    project_patch_scenario,
    win_rate,
)


@dataclass
class Measurement:
    """One timed local profile measurement."""

    name: str
    seconds: float
    status: str
    note: str = ""


def measure(
    name: str, action: Callable[[], object], note: str = ""
) -> tuple[Measurement, object | None]:
    """Run an action and capture its elapsed time and success status."""
    started = time.perf_counter()
    try:
        value = action()
        return Measurement(name, time.perf_counter() - started, "SUCCESS", note), value
    except Exception as error:
        return (
            Measurement(
                name,
                time.perf_counter() - started,
                "FAIL",
                f"{type(error).__name__}: {error}",
            ),
            None,
        )


def raw_load(dataset_dir: Path) -> dict[str, pd.DataFrame]:
    """Load dataset CSV files through the production loader without cache."""
    return load_data_folder(dataset_dir, use_cache=False)


def normalize_frames(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Normalize numeric and result columns for local profiling."""
    normalized = {name: clean_columns(frame) for name, frame in frames.items()}
    battles = normalized["battle_logs"]
    for column in ("total_damage", "duration_sec"):
        battles[column] = pd.to_numeric(battles[column], errors="coerce")
    battles["result"] = battles["result"].astype(str).str.strip().str.lower()
    return normalized


def patch_comparison(battles: pd.DataFrame) -> pd.DataFrame:
    """Profile a patch comparison aggregation for the most common team."""
    entity = battles["player_team"].astype(str).value_counts().index[0]
    target = battles[battles["player_team"].astype(str) == entity]
    return (
        target.groupby("patch_version")
        .agg(
            battles=("battle_id", "count"),
            wins=("result", lambda values: int((values == "win").sum())),
            win_rate=("result", win_rate),
            avg_damage=("total_damage", "mean"),
            avg_duration_sec=("duration_sec", "mean"),
        )
        .reset_index()
    )


def segment_analysis(battles: pd.DataFrame) -> pd.DataFrame:
    """Profile segment-level aggregation by patch and user segment."""
    return (
        battles.groupby(["patch_version", "user_segment"], dropna=False)
        .agg(
            battles=("battle_id", "count"),
            win_rate=("result", win_rate),
            avg_damage=("total_damage", "mean"),
        )
        .reset_index()
    )


def scenario_estimate(battles: pd.DataFrame) -> dict[str, float]:
    """Profile virtual patch scenario projection on aggregate battle metrics."""
    return project_patch_scenario(
        win_rate(battles["result"]),
        float(battles["total_damage"].mean()),
        float(battles["duration_sec"].mean()),
        -0.02,
        -0.05,
    )


def hitl_save() -> None:
    """Profile SQLite and CSV HITL persistence in a temporary directory."""
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        review_id = "PROFILE-LOCAL-1"
        record = {
            "review_id": review_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": "local-profile",
            "target": "profile-target",
            "decision": "Retest Required",
            "reviewer": "performance-profile",
            "reviewer_note": "local measurement",
            "final_answer": "local-only",
            "tool_trace_json": [],
            "virtual_patch_json": {},
            "self_reflection_json": {},
            "dataset_name": "profile",
            "app_version": "2.8.0",
        }
        SQLiteReviewRepository(root / "reviews.sqlite3").save_review(record)
        append_csv_record(
            root / "review_logs.csv", {"review_id": review_id}, "review_id"
        )
        (root / "record.json").write_text(
            json.dumps(record, ensure_ascii=False), encoding="utf-8"
        )


def streamlit_initial_render():
    """Render the Streamlit app once using Streamlit's testing harness."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    if app.exception:
        raise RuntimeError(f"Streamlit exceptions={len(app.exception)}")
    return app


def render_table(measurements: list[Measurement]) -> str:
    """Render profile measurements as a Markdown table."""
    lines = ["| 구간 | 실행 시간(초) | 상태 | 비고 |", "|---|---:|---|---|"]
    for item in measurements:
        note = item.note.replace("|", "/")
        lines.append(f"| {item.name} | {item.seconds:.6f} | {item.status} | {note} |")
    return "\n".join(lines)


def main() -> int:
    """CLI entry point for local performance profiling."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-dir", type=Path, default=ROOT / "data" / "lol_assignment_dataset"
    )
    parser.add_argument(
        "--output", type=Path, help="Optional Markdown baseline output path"
    )
    args = parser.parse_args()
    dataset_dir = args.dataset_dir.resolve()
    missing = [
        filename
        for filename in EXPECTED_DATA_FILES.values()
        if not (dataset_dir / filename).is_file()
    ]
    if missing:
        print(f"[ERROR] 데이터 파일이 없습니다: {missing}", file=sys.stderr)
        return 2

    total_started = time.perf_counter()
    measurements: list[Measurement] = []

    item, raw = measure(
        "CSV 데이터 로딩", lambda: raw_load(dataset_dir), "필수 CSV 5개"
    )
    measurements.append(item)
    if raw is None:
        print(render_table(measurements))
        return 1

    item, normalized = measure(
        "데이터 정규화", lambda: normalize_frames(raw), "컬럼/BOM, 숫자형, 결과값 정리"
    )
    measurements.append(item)
    if normalized is None:
        print(render_table(measurements))
        return 1
    battles = normalized["battle_logs"]

    item, _ = measure(
        "이상 후보 탐지",
        lambda: detect_balance_candidates(battles),
        "Wilson + 이항검정 + FDR",
    )
    measurements.append(item)
    item, _ = measure(
        "패치 전후 비교", lambda: patch_comparison(battles), "최빈 entity의 패치별 집계"
    )
    measurements.append(item)
    item, _ = measure(
        "세그먼트 분석", lambda: segment_analysis(battles), "패치 × user_segment 집계"
    )
    measurements.append(item)
    item, _ = measure(
        "가상 패치 영향 추정",
        lambda: scenario_estimate(battles),
        "휴리스틱 시나리오 계산",
    )
    measurements.append(item)
    item, _ = measure("HITL 저장", hitl_save, "임시 SQLite + CSV + JSON")
    measurements.append(item)

    tool = lambda: project_patch_scenario(0.55, 20000, 1800, -0.02, -0.05)
    item, _ = measure("Agent Tool 1회 실행", tool, "외부 API 없는 순수 Tool 호출")
    measurements.append(item)
    item, streamlit_app = measure(
        "Streamlit 초기 렌더링",
        streamlit_initial_render,
        "AppTest, 기본 데이터 로딩 포함",
    )
    measurements.append(item)
    comparable_total_seconds = time.perf_counter() - total_started
    if streamlit_app is not None:
        item, _ = measure(
            "Streamlit 캐시 재렌더링", streamlit_app.run, "동일 파일, 동일 세션 재실행"
        )
        measurements.append(item)
    measurements.append(
        Measurement(
            "전체 실행",
            comparable_total_seconds,
            "SUCCESS",
            f"battle rows={len(battles)}, 캐시 재렌더링 벤치마크 제외",
        )
    )

    table = render_table(measurements)
    print(table)
    if args.output:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        header = (
            "# Core 성능 기준값\n\n"
            f"- 측정 시각(UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
            f"- Python: {platform.python_version()}\n"
            f"- OS: {platform.platform()}\n"
            f"- 데이터: `{dataset_dir}` ({len(battles):,} rows)\n"
            "- 측정 방식: 각 항목 1회 wall-clock 측정, 외부 API 호출 없음\n\n"
        )
        measured_steps = [item for item in measurements if item.name != "전체 실행"]
        slowest = max(measured_steps, key=lambda item: item.seconds)
        notes = (
            "\n## 해석 주의사항\n\n"
            f"- 이번 실행에서 가장 느린 독립 측정 항목은 `{slowest.name}` ({slowest.seconds:.6f}초)입니다.\n"
            "- 각 항목은 워밍업 없이 1회 측정했으므로 작은 값의 순위는 반복 실행 시 달라질 수 있습니다.\n"
            "- Streamlit 초기 렌더링은 데이터 로딩을 다시 포함하므로 위 항목을 단순 합산해 비율을 계산하면 안 됩니다.\n"
            "- OpenAI/Riot 네트워크 지연과 LLM 응답 시간은 측정하지 않았습니다.\n"
            "- 이 문서는 해당 실행의 측정값이며 성능 보증 수치가 아닙니다.\n"
        )
        output.write_text(header + table + "\n" + notes, encoding="utf-8")
        print(f"[OK] 기준 문서 저장: {output}")
    return 1 if any(item.status == "FAIL" for item in measurements) else 0


if __name__ == "__main__":
    raise SystemExit(main())
