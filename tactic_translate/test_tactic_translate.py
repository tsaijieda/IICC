"""Tests for tactical board translation."""

from __future__ import annotations

import unittest

from tactic_translate import load_board, translate_board


class TranslateBoardTests(unittest.TestCase):
    def test_t001_pass_points_cross(self) -> None:
        board = load_board("examples/boards/T001_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        names = {t.name for it in result.intervals for t in it.tactics if t.score >= 0.67}
        self.assertIn("傳中", names)
        self.assertNotIn("套邊插上", names)

    def test_t003_switch_and_cutback(self) -> None:
        board = load_board("examples/boards/T003_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        names = {t.name for it in result.intervals for t in it.tactics if t.score >= 0.67}
        self.assertIn("強弱邊轉移", names)
        self.assertIn("倒三角傳球", names)

    def test_pass_points_only(self) -> None:
        board = load_board("examples/boards/T001_pass_points.yaml")
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
        board = load_board("examples/boards/T004_pass_points.yaml")
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
        board = load_board("examples/boards/T003_pass_points.yaml")
        result = translate_board(board)
        self.assertTrue(result.valid, result.invalid_reason)
        self.assertEqual(len(result.touches), 4)
        self.assertEqual(result.touches[0].receiver_id, "CM")
        self.assertEqual(result.touches[0].place, "右路中路")
        self.assertIsNone(result.touches[0].passer_id)
        self.assertEqual(result.touches[1].pass_action, "強弱邊轉移")
        self.assertEqual(result.touches[1].passer_id, "CM")
        self.assertEqual(result.touches[1].receiver_id, "LW")
        self.assertIn("CM在右路中路接球", result.description)
        self.assertIn("CM強弱邊轉移給LW", result.description)
        self.assertIn("強弱邊轉移", result.evaluation_points)
        self.assertIn("倒三角傳球", result.evaluation_points)
        self.assertIn("盤帶推進", result.evaluation_points)

    def test_load_question_yaml_pass_points(self) -> None:
        board = load_board("003.yaml")
        self.assertEqual(board.mode, "pass_points")
        self.assertEqual(len(board.frames), 4)
        self.assertEqual(board.frames[2].pass_action, "倒三角傳球")

    def test_invalid_zone_rejected(self) -> None:
        board = load_board("examples/boards/T001_pass_points.yaml")
        board.frames[0].ball_zone = 99
        result = translate_board(board)
        self.assertFalse(result.valid)


if __name__ == "__main__":
    unittest.main()
