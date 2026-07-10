import unittest

from qagent_core.agent.prompts import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    build_system_prompt,
    build_user_prompt,
)


class PromptContractTests(unittest.TestCase):
    def test_prompt_version_has_stable_date_revision_format(self):
        self.assertRegex(PROMPT_VERSION, r"^\d{4}\.\d{2}\.\d+$")

    def test_system_prompt_builder_returns_versioned_constant(self):
        self.assertEqual(build_system_prompt(), SYSTEM_PROMPT)
        self.assertEqual(build_system_prompt(), build_system_prompt())
        self.assertGreater(len(SYSTEM_PROMPT), 1000)

    def test_system_prompt_requires_tool_grounding_and_forbids_fabricated_numbers(self):
        prompt = build_system_prompt()
        self.assertIn("반드시 tool을 호출", prompt)
        self.assertIn("Tool 결과에 근거", prompt)
        self.assertIn("Tool 결과에 없는 수치를 생성하거나 보간하지 않는다", prompt)

    def test_system_prompt_labels_virtual_patch_as_heuristic_not_prediction(self):
        prompt = build_system_prompt()
        self.assertIn("휴리스틱 기반 시나리오 추정", prompt)
        self.assertIn("예측 결과가 아닌", prompt)
        self.assertIn("게임 엔진 시뮬레이션 결과로 표현하지 않는다", prompt)

    def test_system_prompt_forbids_final_balance_verdict(self):
        prompt = build_system_prompt()
        self.assertIn("확정 판정하지 않고 추가 검토 후보", prompt)
        self.assertIn("사람이 수행", prompt)
        self.assertIn("Agent가 대신 승인하지 않는다", prompt)

    def test_system_prompt_requires_data_limitations(self):
        prompt = build_system_prompt()
        for limitation in (
            "표본",
            "다중 비교",
            "교란변수",
            "인과 추론",
            "픽률",
            "밴률",
        ):
            self.assertIn(limitation, prompt)

    def test_system_prompt_preserves_required_tool_flow(self):
        prompt = build_system_prompt()
        required_tools = [
            "get_dataset_overview",
            "detect_anomalies",
            "analyze_patch_impact",
            "analyze_segment_performance",
            "retrieve_related_knowledge",
            "simulate_stat_impact",
            "calculate_adjustment_options",
            "assess_balance_risk",
            "generate_retest_plan",
            "generate_virtual_patch_note",
            "simulate_virtual_patch_impact",
            "reflect_on_virtual_patch",
        ]
        self.assertTrue(all(tool in prompt for tool in required_tools))

    def test_user_prompt_builder_preserves_profile_and_thresholds(self):
        lol = build_user_prompt("League of Legends", 42, 0.73, 0.17)
        rpg = build_user_prompt("Sample RPG", 42, 0.73, 0.17)

        for prompt in (lol, rpg):
            self.assertIn("42전 이상", prompt)
            self.assertIn("0.73 이상", prompt)
            self.assertIn("0.17 이상", prompt)
            self.assertIn("Tool 결과에 없는 사실은 만들지 마", prompt)
        self.assertIn("League of Legends", lol)
        self.assertIn("3:3 모바일 RPG", rpg)


if __name__ == "__main__":
    unittest.main()
