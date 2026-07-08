import json
import unittest
from pathlib import Path

from qagent_core.evaluation import evaluate_agent_response
from tests.fakes import FakeAgentClient


FIXTURE_DIR = Path(__file__).parent / "fixtures"


class AgentEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((FIXTURE_DIR / "agent_eval_cases.json").read_text(encoding="utf-8"))
        cls.traces = json.loads((FIXTURE_DIR / "agent_tool_results.json").read_text(encoding="utf-8"))
        cls.client = FakeAgentClient({case["id"]: case["fake_response"] for case in cls.cases})

    def test_dataset_has_required_fields_and_minimum_case_count(self):
        required = {
            "user_query", "expected_tools", "forbidden_claims",
            "required_output_keywords", "expected_limitations",
        }
        self.assertGreaterEqual(len(self.cases), 5)
        self.assertEqual(len({case["id"] for case in self.cases}), len(self.cases))
        for case in self.cases:
            self.assertTrue(required.issubset(case))
            self.assertTrue(case["user_query"].strip())

    def test_canned_agent_responses_pass_all_quality_rules(self):
        failures = []
        for case in self.cases:
            response = self.client.generate(case["id"])
            result = evaluate_agent_response(case, response, self.traces[case["id"]])
            if not result.passed:
                failures.append(result)
        self.assertEqual(failures, [])

    def test_unsupported_number_is_detected(self):
        case = next(case for case in self.cases if case["id"] == "missing_pick_ban")
        response = case["fake_response"] + " 픽률은 72.3%입니다."
        result = evaluate_agent_response(case, response, self.traces[case["id"]])

        self.assertFalse(result.passed)
        self.assertIn("72.3%", result.unsupported_numbers)

    def test_missing_tool_and_dangerous_claim_are_detected(self):
        case = next(case for case in self.cases if case["id"] == "forced_verdict")
        response = case["fake_response"] + " 사기 챔피언으로 확정합니다."
        result = evaluate_agent_response(case, response, [])

        self.assertIn("detect_anomalies", result.missing_tools)
        self.assertIn("사기 챔피언으로 확정", result.forbidden_claims)

    def test_fake_client_never_requires_api_credentials(self):
        self.assertFalse(hasattr(self.client, "api_key"))
        self.assertGreaterEqual(len(self.client.calls), len(self.cases))


if __name__ == "__main__":
    unittest.main()
