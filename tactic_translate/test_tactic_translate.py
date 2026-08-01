"""Tests for tactical board translation."""

from __future__ import annotations

import unittest

from tactic_translate import load_board, translate_board


class TranslateBoardTests(unittest.TestCase):
    def test_t001_pass_points_cross(self) -> None:
        board = load_board("examples/boards/A001_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        names = {t.name for it in result.intervals for t in it.tactics if t.score >= 0.67}
        self.assertIn("傳中", names)
        self.assertNotIn("套邊插上", names)

    def test_t003_switch_and_cutback(self) -> None:
        board = load_board("examples/boards/A002_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        names = {t.name for it in result.intervals for t in it.tactics if t.score >= 0.67}
        self.assertIn("強弱邊轉移", names)
        self.assertIn("倒三角傳球", names)

    def test_pass_points_only(self) -> None:
        board = load_board("examples/boards/A001_pass_points.yaml")
        self.assertEqual(board.mode, "pass_points")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        names = {t.name for it in result.intervals for t in it.tactics if t.score >= 0.67}
        self.assertIn("傳中", names)

    def test_pass_points_layoff(self) -> None:
        board = load_board("examples/boards/T007_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        names = {t.name for it in result.intervals for t in it.tactics if t.score >= 0.67}
        self.assertIn("回做球", names)

    def test_pass_points_escape_switch(self) -> None:
        board = load_board("examples/boards/T011_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        self.assertIn("強弱邊轉移", result.evaluation_points)

    def test_pass_points_cutback_switch(self) -> None:
        board = load_board("examples/boards/T012_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        self.assertIn("倒三角傳球", result.evaluation_points)
        self.assertIn("強弱邊轉移", result.evaluation_points)

    def test_t004_layoff_and_through(self) -> None:
        board = load_board("examples/boards/A003_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        names = {t.name for it in result.intervals for t in it.tactics if t.score >= 0.67}
        self.assertIn("回做球", names)
        self.assertIn("直塞", names)

    def test_t005_cutback_dummy(self) -> None:
        board = load_board("examples/boards/T005_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        self.assertIn("倒三角傳球", result.evaluation_points)

    def test_t006_lob_and_layoff(self) -> None:
        board = load_board("examples/boards/T006_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        self.assertIn("過頂長傳", result.evaluation_points)
        self.assertIn("回做球", result.evaluation_points)
        names = {t.pass_action for t in result.touches if t.pass_action}
        self.assertIn("過頂長傳", names)
        self.assertIn("回做球", names)

    def test_t003_touch_timeline(self) -> None:
        board = load_board("examples/boards/A002_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        self.assertEqual(len(result.touches), 4)
        self.assertEqual(result.touches[0].receiver_id, "CM")
        self.assertEqual(result.touches[0].place, "右路中路")
        self.assertIsNone(result.touches[0].passer_id)
        self.assertEqual(result.touches[1].pass_action, "強弱邊轉移")
        self.assertEqual(result.touches[1].passer_id, "CM")
        self.assertEqual(result.touches[1].receiver_id, "LW")
        self.assertEqual(result.touches[2].pass_action, "倒三角傳球")
        self.assertEqual(result.touches[2].receiver_id, "ST")
        self.assertEqual(result.touches[3].pass_action, "傳球")
        self.assertEqual(result.touches[3].passer_id, "ST")
        self.assertEqual(result.touches[3].receiver_id, "LW")
        self.assertEqual(result.touches[3].outcome, "得分")
        self.assertIn("CM在右路中路接球", result.description)
        self.assertIn("CM強弱邊轉移給LW", result.description)
        self.assertIn("強弱邊轉移", result.evaluation_points)
        self.assertIn("倒三角傳球", result.evaluation_points)
        self.assertIn("傳球", result.evaluation_points)

    def test_load_question_yaml_pass_points(self) -> None:
        board = load_board("final_document/a002.yaml")
        self.assertEqual(board.mode, "pass_points")
        self.assertEqual(len(board.frames), 4)
        self.assertEqual(board.frames[2].pass_action, "倒三角傳球")
        self.assertEqual(board.frames[3].receiver_id, "LW")

    def test_invalid_zone_rejected(self) -> None:
        board = load_board("examples/boards/A001_pass_points.yaml")
        board.frames[0].ball_zone = 99
        result = translate_board(board)
        self.assertFalse(result.valid)

    def test_t013_third_man_escape_press(self) -> None:
        board = load_board("examples/boards/A004_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        self.assertEqual(len(result.touches), 4)
        self.assertEqual(result.touches[0].receiver_id, "CB")
        self.assertEqual(result.touches[1].passer_id, "CB")
        self.assertEqual(result.touches[1].receiver_id, "DM")
        self.assertEqual(result.touches[2].passer_id, "DM")
        self.assertEqual(result.touches[2].receiver_id, "FB")
        self.assertEqual(result.touches[2].pass_action, "第三人出球")
        self.assertEqual(result.touches[2].place, "右邊路（後段）")
        self.assertEqual(result.touches[3].receiver_id, "AM")
        self.assertEqual(result.touches[3].place, "禁區中央")
        self.assertEqual(result.touches[3].pass_action, "直塞")
        self.assertEqual(result.touches[3].outcome, "射正")
        self.assertIn("第三人出球", result.evaluation_points)
        self.assertIn("直塞", result.evaluation_points)
        self.assertIn("CB在後場禁區接球", result.description)

    def test_t014_triangle_rotation(self) -> None:
        board = load_board("examples/boards/A005_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        self.assertEqual(len(result.touches), 8)
        zones = [t.zone for t in result.touches]
        self.assertEqual(zones, [10, 3, 7, 16, 14, 7, 17, 14])
        receivers = [t.receiver_id for t in result.touches]
        self.assertEqual(receivers, ["RW", "FB", "CM", "RW", "CM", "FB", "CM", "RW"])
        self.assertEqual(result.touches[5].pass_action, "回做球")
        self.assertEqual(result.touches[7].outcome, "射正")
        self.assertIn("回做球", result.evaluation_points)
        self.assertIn("RW在右邊路（中段）接球", result.description)

    def test_t015_interchange_runs(self) -> None:
        board = load_board("examples/boards/T015_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        self.assertEqual(len(result.touches), 6)
        self.assertEqual([t.zone for t in result.touches], [14, 11, 14, 13, 18, 20])
        self.assertEqual(
            [t.receiver_id for t in result.touches],
            ["AM", "LW", "ST", "AM", "LW", "ST"],
        )
        self.assertEqual(result.touches[5].pass_action, "傳中")
        self.assertEqual(result.touches[5].outcome, "得分")
        self.assertIn("傳中", result.evaluation_points)
        self.assertIn("AM在弧頂前緣接球", result.description)

    def test_t016_wing_shot_zone17(self) -> None:
        board = load_board("examples/boards/A006_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        self.assertEqual(len(result.touches), 5)
        self.assertEqual([t.zone for t in result.touches], [7, 13, 5, 14, 12])
        self.assertEqual(result.touches[2].receiver_id, "LW")
        self.assertEqual(result.touches[2].zone, 5)
        self.assertEqual(result.touches[-1].receiver_id, "LW")
        self.assertEqual(result.touches[-1].place, "左邊路（前段）")
        self.assertEqual(result.touches[-1].outcome, "射正")
        self.assertIn("LW在左邊路（前段）射正", result.description)

    def test_a000_example_wing_cross(self) -> None:
        board = load_board("examples/boards/A000_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        self.assertEqual([t.zone for t in result.touches], [9, 15, 20])
        names = {t.name for it in result.intervals for t in it.tactics if t.score >= 0.67}
        self.assertIn("傳球", names)
        self.assertIn("傳中", names)


if __name__ == "__main__":
    unittest.main()
