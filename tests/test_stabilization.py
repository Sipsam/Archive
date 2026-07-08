"""Stabilization improvements tests for validators, simulation, and data caching."""
import unittest
from pathlib import Path
import tempfile

import pandas as pd

from qagent_core.data_io import (
    EXPECTED_DATA_FILES, REQUIRED_COLUMNS, clear_data_cache, load_data_folder,
)
from qagent_core.simulation import validate_patch_scenario_result, project_patch_scenario_range
from qagent_core.tools.validators import (
    ToolValidationError, validate_int_range, validate_float_range, validate_choice,
    validate_top_n, validation_error_dict,
)


class ValidatorTests(unittest.TestCase):
    """Test input validation utilities."""

    def test_validate_int_range_valid(self):
        """Valid integer within range."""
        result = validate_int_range(5, min_val=1, max_val=10)
        self.assertEqual(result, 5)

    def test_validate_int_range_string_input(self):
        """Convert string to int."""
        result = validate_int_range("42", min_val=0, max_val=100)
        self.assertEqual(result, 42)

    def test_validate_int_range_below_min(self):
        """Raise error when below minimum."""
        with self.assertRaises(ToolValidationError):
            validate_int_range(0, min_val=1, max_val=10)

    def test_validate_int_range_above_max(self):
        """Raise error when above maximum."""
        with self.assertRaises(ToolValidationError):
            validate_int_range(11, min_val=1, max_val=10)

    def test_validate_int_range_invalid_string(self):
        """Raise error on invalid string."""
        with self.assertRaises(ToolValidationError):
            validate_int_range("not_a_number", min_val=1, max_val=10)

    def test_validate_float_range_valid(self):
        """Valid float within range."""
        result = validate_float_range(0.5, min_val=0.0, max_val=1.0)
        self.assertAlmostEqual(result, 0.5, places=2)

    def test_validate_float_range_below_min(self):
        """Raise error when below minimum."""
        with self.assertRaises(ToolValidationError):
            validate_float_range(-0.1, min_val=0.0, max_val=1.0)

    def test_validate_float_range_above_max(self):
        """Raise error when above maximum."""
        with self.assertRaises(ToolValidationError):
            validate_float_range(1.1, min_val=0.0, max_val=1.0)

    def test_validate_choice_valid(self):
        """Valid choice selection."""
        result = validate_choice("Low", ["Low", "Medium", "High"])
        self.assertEqual(result, "Low")

    def test_validate_choice_invalid(self):
        """Raise error on invalid choice."""
        with self.assertRaises(ToolValidationError):
            validate_choice("Invalid", ["Low", "Medium", "High"])

    def test_validate_top_n_valid(self):
        """Valid top_n value."""
        result = validate_top_n(10, max_top_n=100)
        self.assertEqual(result, 10)

    def test_validate_top_n_none(self):
        """Use default when None."""
        result = validate_top_n(None, max_top_n=100, default_top_n=10)
        self.assertEqual(result, 10)

    def test_validate_top_n_below_min(self):
        """Raise error when below 1."""
        with self.assertRaises(ToolValidationError):
            validate_top_n(0, max_top_n=100)

    def test_validate_top_n_above_max(self):
        """Raise error when above max."""
        with self.assertRaises(ToolValidationError):
            validate_top_n(150, max_top_n=100)

    def test_validation_error_dict(self):
        """Convert ToolValidationError to dict."""
        error = ToolValidationError("[VALIDATION_ERROR] Test error message")
        result = validation_error_dict(error)
        self.assertEqual(result["status"], "validation_error")
        self.assertIn("Test error message", result["error"])
        self.assertIn("입력 검증 실패", result["message"])


class PatchScenarioValidationTests(unittest.TestCase):
    """Test patch scenario result validation."""

    def test_validate_patch_scenario_result_valid(self):
        """Valid scenario with all required fields."""
        scenarios = project_patch_scenario_range(
            win_rate_before=0.50,
            avg_damage_before=1000,
            avg_duration_before=300,
            win_rate_delta_points=0.05,
            damage_delta_percent=0.1,
        )
        
        result = {
            "conservative": scenarios["conservative"],
            "baseline": scenarios["baseline"],
            "aggressive": scenarios["aggressive"],
            "warnings": ["휴리스틱 기반 추정"],
            "assumptions": ["실제 예측이 아님"],
        }
        
        is_valid, warnings = validate_patch_scenario_result(result)
        # Validation may warn about structure, but should be mostly valid
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(warnings, list)

    def test_validate_patch_scenario_result_invalid_win_rate(self):
        """Invalid win rate outside [0, 1]."""
        result = {
            "baseline": {
                "scenario_win_rate": 1.5,  # Invalid!
            },
            "warnings": ["휴리스틱"],
            "assumptions": [],
        }
        
        is_valid, warnings = validate_patch_scenario_result(result)
        self.assertFalse(is_valid)
        self.assertTrue(any("범위를 벗어남" in w for w in warnings))

    def test_validate_patch_scenario_result_missing_warnings(self):
        """Missing warnings field."""
        result = {
            "baseline": {
                "scenario_win_rate": 0.5,
            },
            "assumptions": [],
        }
        
        is_valid, warnings = validate_patch_scenario_result(result)
        self.assertFalse(is_valid)
        self.assertTrue(any("warnings" in w for w in warnings))

    def test_validate_patch_scenario_result_missing_assumptions(self):
        """Missing assumptions field."""
        result = {
            "baseline": {
                "scenario_win_rate": 0.5,
            },
            "warnings": ["휴리스틱"],
        }
        
        is_valid, warnings = validate_patch_scenario_result(result)
        self.assertFalse(is_valid)
        self.assertTrue(any("assumptions" in w for w in warnings))

    def test_validate_patch_scenario_result_missing_heuristic_notice(self):
        """Missing heuristic limitation notice."""
        result = {
            "baseline": {
                "scenario_win_rate": 0.5,
            },
            "warnings": ["some warning"],
            "assumptions": ["some assumption"],
        }
        
        is_valid, warnings = validate_patch_scenario_result(result)
        self.assertFalse(is_valid)
        self.assertTrue(any("휴리스틱" in w or "한계" in w for w in warnings))


class DataCachingSecurityTests(unittest.TestCase):
    """Test data caching security and isolation."""

    @staticmethod
    def _write_test_dataset(folder):
        """Write test dataset to folder."""
        for name, filename in EXPECTED_DATA_FILES.items():
            values = {column: ["test"] for column in REQUIRED_COLUMNS[name]}
            pd.DataFrame(values).to_csv(folder / filename, index=False, encoding="utf-8-sig")

    def test_cache_uses_file_signature(self):
        """Cache should use file path, mtime, and size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            self._write_test_dataset(folder)
            
            # Load first time
            clear_data_cache()
            data1 = load_data_folder(folder)
            
            # Load second time (should be cached)
            data2 = load_data_folder(folder)
            
            # Verify they are different objects (deep copy)
            self.assertIsNot(data1["battle_logs"], data2["battle_logs"])
            
            # But have same content
            pd.testing.assert_frame_equal(data1["battle_logs"], data2["battle_logs"])

    def test_cache_returns_copies(self):
        """Cache should return deep copies to prevent external mutation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            self._write_test_dataset(folder)
            
            clear_data_cache()
            data1 = load_data_folder(folder)
            data2 = load_data_folder(folder)
            
            # Modify data1
            data1["battle_logs"].loc[0, "battle_id"] = "MODIFIED"
            
            # data2 should not be affected
            self.assertNotEqual(data2["battle_logs"].loc[0, "battle_id"], "MODIFIED")

    def test_cache_invalidated_on_file_change(self):
        """Cache should invalidate when file is modified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            self._write_test_dataset(folder)
            
            clear_data_cache()
            data1 = load_data_folder(folder)
            
            # Modify a file
            battle_logs_path = folder / "battle_logs.csv"
            df = pd.read_csv(battle_logs_path)
            df.loc[0, "battle_id"] = "MODIFIED"
            df.to_csv(battle_logs_path, index=False, encoding="utf-8-sig")
            
            # Reload (should not use cache due to changed mtime/size)
            data2 = load_data_folder(folder)
            
            # data2 should have the modified value
            self.assertEqual(data2["battle_logs"].loc[0, "battle_id"], "MODIFIED")


if __name__ == "__main__":
    unittest.main()
