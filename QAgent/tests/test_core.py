import ast
import json
import inspect
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from pathlib import Path

import pandas as pd

from qagent_core.data_io import (
    DataLoadError,
    EXPECTED_DATA_FILES,
    REQUIRED_COLUMNS,
    clear_data_cache,
    create_dataset_summary,
    discover_data_folders,
    load_data_folder,
    summarize_battle_metrics,
    validate_data_folder,
)
from qagent_core.config import get_secret
from qagent_core.persistence import (
    DuplicateReviewError,
    ReviewPersistenceError,
    SQLiteReviewRepository,
    append_csv_record,
    save_review_with_mirrors,
)
from qagent_core.statistics import (
    analyze_balance_stages,
    benjamini_hochberg,
    binomial_upper_tail,
    detect_balance_candidates,
    normalize_win_results,
    project_patch_scenario,
    wilson_interval,
    win_rate,
)
from qagent_core.runtime import input_summary, new_run_id, output_summary, safe_for_log
from qagent_core.risk import assess_balance_risk, generate_retest_plan
from qagent_core.simulation import (
    SCENARIO_WARNINGS,
    project_patch_scenario as simulate_patch_scenario,
    project_patch_scenario_range,
)
from qagent_core.tool_executor import ToolExecutor
from qagent_core.tools import AnalysisContext, build_tool_functions


class DataIoTests(unittest.TestCase):
    @staticmethod
    def _write_dataset(folder, marker="first"):
        for name, filename in EXPECTED_DATA_FILES.items():
            values = {column: [marker] for column in REQUIRED_COLUMNS[name]}
            pd.DataFrame(values).to_csv(
                folder / filename, index=False, encoding="utf-8-sig"
            )

    def test_environment_secret_loading(self):
        os.environ["QAGENT_TEST_SECRET"] = " test-value "
        try:
            self.assertEqual(get_secret("QAGENT_TEST_SECRET"), "test-value")
        finally:
            os.environ.pop("QAGENT_TEST_SECRET", None)

    def test_runtime_log_redacts_secrets_and_user_input(self):
        safe = safe_for_log(
            {
                "api_key": "not-for-logs",
                "nested": {"authorization": "Bearer secret-value"},
                "message": "sk-example-secret-value",
            }
        )
        self.assertEqual(safe["api_key"], "[REDACTED]")
        self.assertEqual(safe["nested"]["authorization"], "[REDACTED]")
        self.assertNotIn("secret-value", safe["message"])
        user_log = safe_for_log({"role": "user", "content": "private goal"})
        self.assertEqual(user_log["content"], "[USER_INPUT_REDACTED]")

    def test_runtime_ids_and_summaries(self):
        first, second = new_run_id(), new_run_id()
        self.assertTrue(first.startswith("RUN-"))
        self.assertNotEqual(first, second)
        self.assertIn("fields=", input_summary({"player_team": "A"}))
        self.assertIn("status=ok", output_summary({"status": "ok", "rows": []}))

    def test_load_data_folder_and_clean_bom(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            self._write_dataset(folder)
            battles = pd.read_csv(folder / "battle_logs.csv")
            battles = battles.rename(columns={"patch_version": "\ufeffpatch_version"})
            battles.to_csv(
                folder / "battle_logs.csv", index=False, encoding="utf-8-sig"
            )
            loaded = load_data_folder(folder)
            self.assertEqual(set(loaded), set(EXPECTED_DATA_FILES))
            self.assertIn("patch_version", loaded["battle_logs"].columns)

    def test_missing_data_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(DataLoadError) as raised:
                load_data_folder(Path(temp))
            self.assertIn("[DATA_FILES_MISSING]", str(raised.exception))

    def test_missing_required_column_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            self._write_dataset(folder)
            pd.DataFrame({"battle_id": [1]}).to_csv(
                folder / "battle_logs.csv", index=False
            )
            with self.assertRaises(DataLoadError) as raised:
                load_data_folder(folder)
            self.assertIn("[DATA_COLUMNS_MISSING]", str(raised.exception))

    def test_cache_invalidates_when_file_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            clear_data_cache()
            folder = Path(temp)
            self._write_dataset(folder, "first")
            first = load_data_folder(folder)
            self._write_dataset(folder, "a-longer-second-value")
            second = load_data_folder(folder)
            self.assertEqual(first["battle_logs"].iloc[0]["battle_id"], "first")
            self.assertEqual(
                second["battle_logs"].iloc[0]["battle_id"], "a-longer-second-value"
            )

    def test_cached_frames_are_isolated_and_summary_uses_loaded_data(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            self._write_dataset(folder)
            loaded = load_data_folder(folder)
            loaded["battle_logs"].loc[0, "battle_id"] = "mutated"
            again = load_data_folder(folder)
            self.assertEqual(again["battle_logs"].loc[0, "battle_id"], "first")
            summary = create_dataset_summary(again)
            self.assertEqual(summary["rows"]["battle_logs"], 1)
            self.assertIn("first", summary["patch_versions"])

    @staticmethod
    def _touch_required_files(folder: Path):
        folder.mkdir(parents=True, exist_ok=True)
        for filename in EXPECTED_DATA_FILES.values():
            (folder / filename).touch()

    def test_bounded_discovery_finds_only_complete_datasets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            valid = root / "valid"
            incomplete = root / "incomplete"
            self._touch_required_files(valid)
            incomplete.mkdir()
            (incomplete / "battle_logs.csv").touch()

            self.assertEqual(discover_data_folders([root]), [valid.resolve()])

    def test_bounded_discovery_excludes_directories_beyond_max_depth(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            depth_two = root / "one" / "two"
            depth_three = depth_two / "three"
            self._touch_required_files(depth_two)
            self._touch_required_files(depth_three)

            self.assertEqual(
                discover_data_folders([root], max_depth=2), [depth_two.resolve()]
            )

    def test_explicit_folder_remains_directly_validatable(self):
        with tempfile.TemporaryDirectory() as temp:
            selected = Path(temp) / "outside_auto_root"
            self._touch_required_files(selected)

            self.assertEqual(validate_data_folder(selected), [])

    def test_bounded_discovery_finishes_quickly_with_many_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(1500):
                (root / f"unrelated-{index}.txt").touch()

            started = time.monotonic()
            result = discover_data_folders([root], max_depth=2)
            elapsed = time.monotonic() - started

            self.assertEqual(result, [])
            self.assertLess(elapsed, 2.0)

    def test_battle_metric_summary_keeps_virtual_patch_contract(self):
        frame = pd.DataFrame(
            {
                "result": ["win", " loss ", " Win "],
                "total_damage": [100, 200, 300],
                "duration_sec": [10, 20, 30],
                "kda": [1.0, 2.0, 3.0],
            }
        )
        summary = summarize_battle_metrics(frame)

        self.assertEqual(
            set(summary),
            {
                "battles",
                "wins",
                "win_rate",
                "avg_damage",
                "avg_duration_sec",
                "avg_kda",
            },
        )
        self.assertEqual(summary["wins"], 2)
        self.assertEqual(summary["win_rate"], round(2 / 3, 4))
        self.assertEqual(summary["avg_kda"], 2.0)


class StatisticsTests(unittest.TestCase):
    def test_win_rate_and_empty_input(self):
        self.assertEqual(win_rate(pd.Series(["win", "loss", "WIN"])), 2 / 3)
        self.assertEqual(win_rate(pd.Series(dtype=str)), 0.0)

    def test_result_normalization_handles_whitespace_case_missing_and_unknown(self):
        results = pd.Series(
            ["win", " win ", " Win ", " WIN ", "loss", " Loss ", None, pd.NA, "unknown"]
        )
        normalized = normalize_win_results(results)

        self.assertEqual(
            normalized.tolist(),
            [True, True, True, True, False, False, False, False, False],
        )
        self.assertAlmostEqual(win_rate(results), 4 / 9)

    def test_candidate_statistics_share_normalized_win_count(self):
        rows = []
        padded_wins = [" win ", " Win ", " WIN "]
        for index in range(40):
            rows.append(self._battle(index, "A", padded_wins[index % len(padded_wins)]))
        for index in range(40, 80):
            rows.append(self._battle(index, "B", " loss "))

        overall, candidates = detect_balance_candidates(
            pd.DataFrame(rows),
            min_samples=30,
            win_rate_threshold=0.75,
            win_rate_gap_threshold=0.20,
        )

        candidate = candidates.iloc[0]
        expected_low, expected_high = wilson_interval(40, 40)
        self.assertAlmostEqual(overall, 0.5)
        self.assertEqual(candidate["wins"], 40)
        self.assertAlmostEqual(
            candidate["win_rate"], candidate["wins"] / candidate["battles"]
        )
        self.assertAlmostEqual(candidate["win_rate_ci_low"], expected_low)
        self.assertAlmostEqual(candidate["win_rate_ci_high"], expected_high)
        self.assertAlmostEqual(
            candidate["p_value"], binomial_upper_tail(40, 40, overall)
        )

    def test_wilson_interval_narrows_with_sample_size(self):
        small = wilson_interval(8, 10)
        large = wilson_interval(80, 100)
        self.assertLess(large[1] - large[0], small[1] - small[0])
        self.assertLessEqual(small[0], 0.8)
        self.assertGreaterEqual(small[1], 0.8)

    def test_detect_balance_candidates_uses_confidence_bound(self):
        rows = []
        for index in range(100):
            rows.append(self._battle(index, "A", "win" if index < 90 else "loss"))
        for index in range(100, 200):
            rows.append(self._battle(index, "B", "win" if index < 130 else "loss"))
        overall, candidates = detect_balance_candidates(
            pd.DataFrame(rows),
            min_samples=30,
            win_rate_threshold=0.75,
            win_rate_gap_threshold=0.20,
        )
        self.assertAlmostEqual(overall, 0.60)
        self.assertEqual(candidates.iloc[0]["player_team"], "A")
        self.assertEqual(candidates.iloc[0]["battles"], 100)
        self.assertEqual(candidates.iloc[0]["wins"], 90)
        self.assertAlmostEqual(candidates.iloc[0]["win_rate"], 0.90)
        self.assertAlmostEqual(candidates.iloc[0]["global_win_rate"], 0.60)
        self.assertAlmostEqual(candidates.iloc[0]["win_rate_diff"], 0.30)
        self.assertGreater(candidates.iloc[0]["win_rate_ci_low"], overall)
        self.assertEqual(
            candidates.iloc[0]["anomaly_score"], candidates.iloc[0]["candidate_score"]
        )
        self.assertLessEqual(candidates.iloc[0]["fdr_q_value"], 0.05)
        self.assertEqual(candidates.iloc[0]["n"], candidates.iloc[0]["battles"])
        self.assertIn("검토 후보", candidates.iloc[0]["candidate_reason"])

    def test_fdr_adjustment_is_monotonic_and_not_below_p_value(self):
        binomial_upper_tail.cache_clear()
        p_values = [0.001, 0.01, 0.04, 0.20]
        q_values = benjamini_hochberg(p_values)
        self.assertEqual(len(q_values), len(p_values))
        self.assertTrue(all(q >= p for p, q in zip(p_values, q_values)))
        self.assertEqual(q_values, sorted(q_values))
        self.assertLess(binomial_upper_tail(9, 10, 0.5), 0.02)
        binomial_upper_tail(9, 10, 0.5)
        self.assertGreaterEqual(binomial_upper_tail.cache_info().hits, 1)

    def test_segment_comparison_adds_segment_to_entity(self):
        rows = []
        for index in range(100):
            row = self._battle(index, "A", "win" if index < 90 else "loss")
            row["user_segment"] = "HIGH"
            rows.append(row)
        for index in range(100, 200):
            row = self._battle(index, "B", "win" if index < 130 else "loss")
            row["user_segment"] = "LOW"
            rows.append(row)
        _, candidates = detect_balance_candidates(
            pd.DataFrame(rows),
            min_samples=30,
            win_rate_threshold=0.75,
            win_rate_gap_threshold=0.20,
            segment_by="user_segment",
        )
        self.assertIn("user_segment", candidates.iloc[0]["group_by"])
        self.assertIn("HIGH", candidates.iloc[0]["entity"])

    def test_candidate_entity_handles_missing_group_values(self):
        rows = []
        for index in range(10):
            row = self._battle(index, "A", "win")
            row["equipment_set"] = float("nan")
            rows.append(row)
        for index in range(10, 20):
            rows.append(self._battle(index, "B", "loss"))

        _, candidates = detect_balance_candidates(
            pd.DataFrame(rows),
            min_samples=1,
            win_rate_threshold=0.0,
            win_rate_gap_threshold=0.0,
            wilson_lower_gap_threshold=0.0,
            fdr_alpha=1.0,
        )

        self.assertTrue(any("(missing)" in value for value in candidates["entity"]))

    def test_staged_analysis_is_champion_first_and_preserves_review_language(self):
        rows = []
        for index in range(240):
            row = self._battle(index, "A", "win" if index % 10 < 8 else "loss")
            row["patch_version"] = "26.12" if index < 120 else "26.13"
            row["user_segment"] = "HIGH" if index % 2 == 0 else "LOW"
            row["skill_used_most"] = "MID" if index % 2 == 0 else "TOP"
            row["equipment_set"] = "item-a" if index % 3 else "item-b"
            rows.append(row)
        for index in range(240, 480):
            row = self._battle(index, "B", "win" if index % 10 < 2 else "loss")
            row["patch_version"] = "26.12" if index < 360 else "26.13"
            row["user_segment"] = "HIGH" if index % 2 == 0 else "LOW"
            rows.append(row)

        result = analyze_balance_stages(
            pd.DataFrame(rows),
            min_samples=60,
            win_rate_threshold=0.65,
            effect_size_threshold=0.15,
        )

        self.assertEqual(
            [stage["stage"] for stage in result["stages"]],
            [
                "1_champion_screening",
                "2_patch_reproducibility",
                "3_segment_check",
                "4_item_driver",
                "5_patch_review_candidate",
            ],
        )
        self.assertEqual(result["data_availability"]["pick_rate"], "not_available")
        self.assertEqual(result["data_availability"]["ban_rate"], "not_available")
        self.assertTrue(any("FDR" in warning for warning in result["warnings"]))
        self.assertTrue(any("표본" in warning for warning in result["warnings"]))
        candidate = result["candidates"][0]
        self.assertEqual(candidate["entity"], "A")
        self.assertEqual(candidate["stage"], "5_patch_review_candidate")
        self.assertEqual(candidate["recommendation_level"], "우선 검토 후보")
        self.assertIn("2/2", candidate["reproducibility_note"])
        self.assertIn("아이템", candidate["possible_driver"])
        self.assertEqual(
            set(candidate),
            {
                "stage",
                "entity",
                "n",
                "wins",
                "win_rate",
                "global_win_rate",
                "win_rate_diff",
                "wilson_low",
                "wilson_high",
                "reproducibility_note",
                "possible_driver",
                "recommendation_level",
                "warnings",
            },
        )

    def test_staged_analysis_empty_data_is_safe(self):
        columns = [
            "battle_id",
            "patch_version",
            "player_team",
            "equipment_set",
            "skill_used_most",
            "result",
        ]
        result = analyze_balance_stages(pd.DataFrame(columns=columns))
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["overall_win_rate"], 0.0)
        self.assertTrue(any("검토 후보" in warning for warning in result["warnings"]))

    def test_invalid_segment_is_rejected(self):
        frame = pd.DataFrame([self._battle(1, "A", "win")])
        with self.assertRaises(ValueError):
            detect_balance_candidates(frame, segment_by="unknown")

    def test_empty_and_missing_data_handling(self):
        columns = [
            "battle_id",
            "patch_version",
            "player_team",
            "equipment_set",
            "skill_used_most",
            "result",
            "total_damage",
            "duration_sec",
        ]
        overall, candidates = detect_balance_candidates(pd.DataFrame(columns=columns))
        self.assertEqual(overall, 0.0)
        self.assertTrue(candidates.empty)
        with self.assertRaises(ValueError):
            detect_balance_candidates(pd.DataFrame({"result": ["win"]}))

    def test_patch_scenario_is_bounded_and_identified_as_calculation(self):
        result = project_patch_scenario(0.98, 1000, 1200, 0.2, -0.1)
        self.assertEqual(result["win_rate"], 0.99)
        self.assertEqual(result["avg_damage"], 900)
        self.assertEqual(result["avg_duration_sec"], 1224)

    @staticmethod
    def _battle(index, champion, result):
        return {
            "battle_id": index,
            "patch_version": "26.13",
            "player_team": champion,
            "equipment_set": "item",
            "skill_used_most": "MID",
            "result": result,
            "total_damage": 1000,
            "duration_sec": 1200,
        }


class RiskAndSimulationTests(unittest.TestCase):
    def test_extracted_scenario_keeps_existing_bounds(self):
        self.assertEqual(
            simulate_patch_scenario(0.98, 1000, 1200, 0.2, -0.1),
            {"win_rate": 0.99, "avg_damage": 900.0, "avg_duration_sec": 1224.0},
        )

    def test_extracted_risk_contract_and_retest_plan(self):
        risk = assess_balance_risk("A", 0.90, 0.30, 0.20, 0.30)
        plan = generate_retest_plan("A", "item", "MID", risk["risk_level"])

        self.assertEqual(risk["status"], "ok")
        self.assertEqual(risk["risk_score"], 100)
        self.assertEqual(risk["risk_level"], "High")
        self.assertEqual(
            risk["recommended_decision"], "긴급 재테스트 및 부분 하향 검토"
        )
        self.assertEqual(plan["status"], "ok")
        self.assertEqual(plan["total_required_battles"], 900)
        self.assertEqual(len(plan["plan"]), 3)

    def test_three_scenario_range_preserves_baseline_and_required_fields(self):
        scenarios = project_patch_scenario_range(0.60, 1000, 1200, -0.04, -0.10)

        self.assertEqual(set(scenarios), {"conservative", "baseline", "aggressive"})
        required = {
            "assumed_effect_multiplier",
            "scenario_win_rate",
            "scenario_damage_change",
            "risk_note",
        }
        self.assertTrue(
            all(set(scenario) == required for scenario in scenarios.values())
        )
        self.assertEqual(scenarios["conservative"]["assumed_effect_multiplier"], 0.5)
        self.assertEqual(scenarios["baseline"]["assumed_effect_multiplier"], 1.0)
        self.assertEqual(scenarios["aggressive"]["assumed_effect_multiplier"], 1.5)
        self.assertEqual(scenarios["baseline"]["scenario_win_rate"], 0.56)
        self.assertEqual(scenarios["baseline"]["scenario_damage_change"], -0.10)
        self.assertGreater(
            scenarios["conservative"]["scenario_win_rate"],
            scenarios["aggressive"]["scenario_win_rate"],
        )

    def test_scenario_warnings_state_all_required_limitations(self):
        self.assertEqual(
            SCENARIO_WARNINGS,
            [
                "휴리스틱 기반 추정",
                "실제 예측 모델 아님",
                "게임 엔진 시뮬레이션 아님",
                "실제 패치 전 QA 테스트 필요",
            ],
        )


class ToolExecutorTests(unittest.TestCase):
    def _executor(self, tools=None, max_calls=3, timeout=60):
        trace = []
        state = {"tool_calls": 0}
        executor = ToolExecutor(
            tool_functions=tools or {"echo": lambda value="ok": {"value": value}},
            trace=trace,
            run_id="RUN-test",
            runtime_state=state,
            started_at=time.monotonic(),
            max_tool_calls=max_calls,
            timeout_seconds=timeout,
        )
        return executor, trace, state

    def test_normal_and_forced_calls_increment_shared_counter(self):
        executor, trace, state = self._executor()
        executor.execute("echo", {"value": "normal"}, turn=1)
        executor.execute("echo", {"value": "forced"}, turn=2, forced_by_app=True)

        self.assertEqual(state["tool_calls"], 2)
        self.assertEqual(len(trace), 2)
        self.assertFalse(trace[0]["forced_by_app"])
        self.assertTrue(trace[1]["forced_by_app"])

    def test_call_limit_blocks_additional_execution(self):
        calls = []
        executor, trace, state = self._executor(
            {"count": lambda: calls.append("called") or {"status": "ok"}}, max_calls=1
        )
        executor.execute("count", {}, turn=1)
        result = executor.execute("count", {}, turn=2, forced_by_app=True)

        self.assertEqual(calls, ["called"])
        self.assertEqual(state["tool_calls"], 1)
        self.assertEqual(result["error_type"], "tool_call_limit")
        self.assertFalse(trace[-1]["success"])
        self.assertFalse(trace[-1]["executed"])
        self.assertTrue(trace[0]["executed"])

    def test_exception_unknown_tool_and_malformed_arguments_are_traced(self):
        def fail():
            raise RuntimeError("sensitive implementation detail")

        executor, trace, state = self._executor({"fail": fail})
        failed = executor.execute("fail", {}, turn=1)
        unknown = executor.execute("missing", {}, turn=2)
        malformed = executor.execute_raw("fail", "{invalid", turn=3)

        self.assertEqual(state["tool_calls"], 1)
        self.assertEqual(failed["status"], "error")
        self.assertEqual(trace[0]["error_message"], failed["message"])
        self.assertEqual(unknown["error_type"], "unknown_tool")
        self.assertEqual(malformed["error_type"], "json_parse_error")
        self.assertTrue(all(not step["success"] for step in trace))
        self.assertTrue(all("result_summary" in step for step in trace))

    def test_timeout_blocks_tool_safely(self):
        executor, trace, state = self._executor(timeout=0)
        result = executor.execute("echo", {}, turn=1)

        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["error_type"], "timeout")
        self.assertEqual(state["tool_calls"], 0)
        self.assertFalse(trace[0]["executed"])
        self.assertFalse(trace[0]["success"])

    def test_fast_tool_completes_before_deadline(self):
        executor, trace, state = self._executor(timeout=1)
        result = executor.execute("echo", {"value": "fast"}, turn=1)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(state["tool_calls"], 1)
        self.assertTrue(trace[0]["success"])
        self.assertGreater(result["remaining_deadline_ms"], 0)

    def test_slow_tool_reports_timeout_without_false_cancellation(self):
        completed = threading.Event()

        def slow():
            time.sleep(0.15)
            completed.set()
            return {"status": "ok"}

        executor, trace, state = self._executor({"slow": slow}, timeout=0.03)
        result = executor.execute("slow", {}, turn=1)

        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["error_type"], "timeout")
        self.assertFalse(result["cancelled"])
        self.assertTrue(result["cancellation_attempted"])
        self.assertFalse(result["cancellation_succeeded"])
        self.assertTrue(result["underlying_task_may_complete_later"])
        self.assertIn("나중에 완료될 수 있습니다", result["user_safe_message"])
        self.assertEqual(state["tool_calls"], 1)
        self.assertTrue(trace[0]["executed"])
        self.assertEqual(trace[0]["status"], "timeout")
        self.assertEqual(trace[0]["remaining_deadline_ms"], 0.0)
        self.assertGreaterEqual(trace[0]["elapsed_ms"], 20)
        self.assertTrue(completed.wait(0.5))

    def test_expired_agent_deadline_blocks_additional_tool_without_counting(self):
        calls = []
        executor, trace, state = self._executor(
            {"count": lambda: calls.append("called") or {"status": "ok"}}, timeout=0.01
        )
        time.sleep(0.02)
        result = executor.execute("count", {}, turn=1)

        self.assertEqual(result["status"], "timeout")
        self.assertEqual(state["tool_calls"], 0)
        self.assertEqual(calls, [])
        self.assertFalse(trace[0]["executed"])
        self.assertFalse(result["underlying_task_may_complete_later"])

    def test_tool_raised_timeout_error_is_not_misreported_as_deadline(self):
        def fail_with_timeout():
            raise TimeoutError("tool-specific timeout")

        executor, trace, state = self._executor({"fail": fail_with_timeout}, timeout=1)
        result = executor.execute("fail", {}, turn=1)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "TimeoutError")
        self.assertEqual(state["tool_calls"], 1)
        self.assertEqual(trace[0]["status"], "error")

    def test_api_timeout_is_bounded_by_agent_deadline(self):
        executor, _, _ = self._executor(timeout=0.05)
        bounded = executor.deadline.bounded_timeout(60)

        self.assertGreater(bounded, 0)
        self.assertLessEqual(bounded, 0.05)
        time.sleep(0.06)
        self.assertEqual(executor.deadline.bounded_timeout(60), 0.0)


class ContractAndPersistenceTests(unittest.TestCase):
    @staticmethod
    def _review(review_id="review-one"):
        return {
            "review_id": review_id,
            "created_at": "2026-07-07T15:00:00+09:00",
            "model": "test-model",
            "target": "champion-a",
            "decision": "Retest Required",
            "reviewer": "QA",
            "reviewer_note": "표본 추가 필요",
            "final_answer": "검토 후보",
            "tool_trace_json": [{"tool": "detect_anomalies"}],
            "virtual_patch_json": {"action": "monitor"},
            "self_reflection_json": {"risk": "sample-size"},
            "dataset_name": "test-dataset",
            "app_version": "2.8.0",
        }

    def test_sqlite_review_create_save_and_list(self):
        with tempfile.TemporaryDirectory() as temp:
            db_path = Path(temp) / "nested" / "reviews.sqlite3"
            repository = SQLiteReviewRepository(db_path)
            self.assertTrue(db_path.exists())
            repository.save_review(self._review())
            rows = repository.list_reviews()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows.iloc[0]["review_id"], "review-one")
            self.assertEqual(rows.iloc[0]["review_status"], "Retest Required")

    def test_sqlite_duplicate_review_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            repository = SQLiteReviewRepository(Path(temp) / "reviews.sqlite3")
            repository.save_review(self._review())
            with self.assertRaises(DuplicateReviewError):
                repository.save_review(self._review())

    def test_sqlite_invalid_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            repository = SQLiteReviewRepository(Path(temp) / "reviews.sqlite3")
            record = self._review()
            record["tool_trace_json"] = "{invalid-json"
            with self.assertRaises(ReviewPersistenceError):
                repository.save_review(record)
            self.assertTrue(repository.list_reviews().empty)

    def test_tool_schema_contracts_are_closed_and_map_to_functions(self):
        # Load tool schemas from centralized registry module
        source = Path("qagent_core/tool_registry.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        schemas = None
        for node in ast.walk(module):
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "TOOL_SCHEMAS"
                for target in node.targets
            ):
                schemas = ast.literal_eval(node.value)

        empty = pd.DataFrame()
        returned_tools = set(
            build_tool_functions(
                AnalysisContext(
                    battles=empty,
                    characters=empty,
                    skills=empty,
                    equipment_sets=empty,
                    patch_notes=empty,
                )
            )
        )

        self.assertIsNotNone(schemas)
        schema_names = set()
        for tool in schemas:
            function = tool["function"]
            schema_names.add(function["name"])
            self.assertFalse(function["parameters"].get("additionalProperties", True))
            self.assertEqual(function["parameters"]["type"], "object")
        self.assertEqual(schema_names, returned_tools)

    def test_review_log_rejects_duplicate_id(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "reviews.csv"
            append_csv_record(
                path, {"review_id": "one", "status": "approved"}, "review_id"
            )
            with self.assertRaises(ValueError):
                append_csv_record(
                    path, {"review_id": "one", "status": "rejected"}, "review_id"
                )
            self.assertEqual(len(pd.read_csv(path)), 1)

    def _save_with_mirrors(self, temp: str, **overrides):
        repository = overrides.pop(
            "repository", SQLiteReviewRepository(Path(temp) / "reviews.sqlite3")
        )
        options = {
            "csv_path": Path(temp) / "review_logs.csv",
            "csv_row": {"review_id": "review-one", "status": "saved"},
            "json_path": Path(temp) / "records" / "review-one.json",
            "json_artifact": {"review_id": "review-one", "detail": {"value": 1}},
        }
        options.update(overrides)
        db_record = {**self._review(), "artifact_json": options["json_artifact"]}
        result = save_review_with_mirrors(repository, db_record, **options)
        return repository, result, options

    def test_authoritative_save_exports_both_mirrors(self):
        with tempfile.TemporaryDirectory() as temp:
            repository, result, options = self._save_with_mirrors(temp)

            self.assertEqual(result["status"], "saved")
            self.assertTrue(result["db_saved"])
            self.assertTrue(result["csv_exported"])
            self.assertTrue(result["json_exported"])
            self.assertEqual(result["mirror_warning"], "")
            self.assertEqual(len(repository.list_reviews()), 1)
            self.assertTrue(options["csv_path"].exists())
            self.assertTrue(options["json_path"].exists())
            connection = sqlite3.connect(repository.db_path)
            try:
                artifact_json = connection.execute(
                    "SELECT artifact_json FROM hitl_reviews WHERE review_id = ?",
                    ("review-one",),
                ).fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(json.loads(artifact_json)["detail"]["value"], 1)

    def test_json_export_failure_keeps_database_record(self):
        def fail_json(path, artifact):
            raise OSError("disk unavailable")

        with tempfile.TemporaryDirectory() as temp:
            repository, result, options = self._save_with_mirrors(
                temp,
                json_exporter=fail_json,
            )

            self.assertEqual(result["status"], "partial")
            self.assertTrue(result["db_saved"])
            self.assertFalse(result["json_exported"])
            self.assertTrue(result["csv_exported"])
            self.assertIn("JSON mirror 실패", result["mirror_warning"])
            self.assertEqual(len(repository.list_reviews()), 1)
            self.assertFalse(options["json_path"].exists())

    def test_csv_export_failure_keeps_database_record(self):
        def fail_csv(path, row, unique_key):
            raise PermissionError("read only")

        with tempfile.TemporaryDirectory() as temp:
            repository, result, options = self._save_with_mirrors(
                temp,
                csv_exporter=fail_csv,
            )

            self.assertEqual(result["status"], "partial")
            self.assertTrue(result["db_saved"])
            self.assertTrue(result["json_exported"])
            self.assertFalse(result["csv_exported"])
            self.assertIn("CSV mirror 실패", result["mirror_warning"])
            self.assertEqual(len(repository.list_reviews()), 1)
            self.assertFalse(options["csv_path"].exists())

    def test_database_failure_does_not_start_exports(self):
        class FailingRepository:
            def save_review(self, record):
                raise ReviewPersistenceError("database unavailable")

        exports = []

        def record_json(path, artifact):
            exports.append("json")

        def record_csv(path, row, unique_key):
            exports.append("csv")

        with tempfile.TemporaryDirectory() as temp:
            csv_path = Path(temp) / "review_logs.csv"
            json_path = Path(temp) / "record.json"
            with self.assertRaises(ReviewPersistenceError) as raised:
                save_review_with_mirrors(
                    FailingRepository(),
                    self._review(),
                    csv_path=csv_path,
                    csv_row={"review_id": "review-one"},
                    json_path=json_path,
                    json_artifact={"review_id": "review-one"},
                    csv_exporter=record_csv,
                    json_exporter=record_json,
                )

            self.assertEqual(raised.exception.storage_result["status"], "failed")
            self.assertFalse(raised.exception.storage_result["db_saved"])
            self.assertFalse(raised.exception.storage_result["csv_exported"])
            self.assertFalse(raised.exception.storage_result["json_exported"])
            self.assertEqual(exports, [])
            self.assertFalse(csv_path.exists())
            self.assertFalse(json_path.exists())

    def test_duplicate_database_record_does_not_create_new_exports(self):
        with tempfile.TemporaryDirectory() as temp:
            repository = SQLiteReviewRepository(Path(temp) / "reviews.sqlite3")
            repository.save_review(self._review())
            csv_path = Path(temp) / "duplicate.csv"
            json_path = Path(temp) / "duplicate.json"

            with self.assertRaises(DuplicateReviewError):
                save_review_with_mirrors(
                    repository,
                    self._review(),
                    csv_path=csv_path,
                    csv_row={"review_id": "review-one"},
                    json_path=json_path,
                    json_artifact={"review_id": "review-one"},
                )

            self.assertFalse(csv_path.exists())
            self.assertFalse(json_path.exists())


class ExtractedToolIntegrationTests(unittest.TestCase):
    def test_all_registered_tools_execute_after_module_extraction(self):
        frames = load_data_folder(Path("data"), use_cache=False)
        row = frames["battle_logs"].iloc[0]
        tools = build_tool_functions(
            AnalysisContext(
                battles=frames["battle_logs"],
                characters=frames["characters"],
                skills=frames["skills"],
                equipment_sets=frames["equipment_sets"],
                patch_notes=frames["patch_notes"],
            )
        )
        values = {
            "player_team": str(row["player_team"]),
            "equipment_set": str(row["equipment_set"]),
            "skill_used_most": str(row["skill_used_most"]),
            "patch_version": str(row["patch_version"]),
            "current_patch_version": str(row["patch_version"]),
            "win_rate": 0.6,
            "win_rate_gap": 0.1,
        }

        results = {}
        for name, function in tools.items():
            arguments = {
                parameter.name: values.get(parameter.name, "test")
                for parameter in inspect.signature(function).parameters.values()
                if parameter.default is inspect.Parameter.empty
            }
            results[name] = function(**arguments)

        self.assertEqual(len(results), 16)
        self.assertTrue(all(isinstance(result, dict) for result in results.values()))
        self.assertTrue(
            all(result.get("status", "ok") != "error" for result in results.values())
        )


if __name__ == "__main__":
    unittest.main()
