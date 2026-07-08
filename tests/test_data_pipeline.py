import unittest

from qagent_core.data_pipeline.normalize_match import (
    compute_kda,
    extract_patch_version,
    extract_raw_patch_version,
    get_primary_perk,
    get_sub_style,
    map_game_version_to_patch_version,
    normalize_item_id,
    parse_riot_id,
    patch_version_mapping_rule,
    queue_to_battle_mode,
    safe_filename,
    timestamp_to_iso_kst,
    truthy_win,
)


class MatchNormalizationTests(unittest.TestCase):
    def test_parse_riot_id_uses_last_separator_and_validates_parts(self):
        self.assertEqual(parse_riot_id(" player#name#KR1 "), ("player#name", "KR1"))
        for invalid in ("missing-tag", "name#", "#tag"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_riot_id(invalid)

    def test_safe_filename_preserves_legacy_replacement_rules(self):
        self.assertEqual(safe_filename(' A/B:# C? '), "A_B___C_")

    def test_patch_mapping_contract(self):
        cases = {
            "14.10.123": ("14.10", "14.10", "game_version_1_to_14_same_as_patch_version"),
            "15.12.688.6522": ("15.12", "25.12", "game_version_15_plus_mapped_to_patch_version_25_plus"),
            "16.3.744.7656": ("16.3", "26.03", "game_version_15_plus_mapped_to_patch_version_25_plus"),
            None: (None, None, "unknown"),
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(extract_raw_patch_version(value), expected[0])
                self.assertEqual(map_game_version_to_patch_version(value), expected[1])
                self.assertEqual(extract_patch_version(value), expected[1])
                self.assertEqual(patch_version_mapping_rule(value), expected[2])

    def test_queue_win_item_and_kda_normalization(self):
        self.assertEqual(queue_to_battle_mode(420), "RANKED_SOLO")
        self.assertEqual(queue_to_battle_mode("999"), "QUEUE_999")
        self.assertEqual(queue_to_battle_mode("bad"), "UNKNOWN")
        self.assertTrue(all(truthy_win(value) for value in (True, "win", "YES", 1)))
        self.assertFalse(truthy_win("loss"))
        self.assertEqual(normalize_item_id("3001.0"), 3001)
        self.assertIsNone(normalize_item_id(0))
        self.assertIsNone(normalize_item_id("bad"))
        self.assertEqual(compute_kda(3, 0, 4), 7.0)
        self.assertEqual(compute_kda(3, 2, 4), 3.5)

    def test_timestamp_and_perk_helpers(self):
        self.assertEqual(timestamp_to_iso_kst(0), "1970-01-01 09:00:00")
        self.assertIsNone(timestamp_to_iso_kst(None))
        participant = {"perks": {"styles": [
            {"selections": [{"perk": 8005}]}, {"style": 8100},
        ]}}
        self.assertEqual(get_primary_perk(participant), 8005)
        self.assertEqual(get_sub_style(participant), 8100)
        self.assertIsNone(get_primary_perk({}))
        self.assertIsNone(get_sub_style({}))


if __name__ == "__main__":
    unittest.main()
