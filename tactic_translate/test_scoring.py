"""Tests for rubric scoring."""

from __future__ import annotations

import unittest

from tactic_translate.io import board_from_dict
from tactic_translate.scoring import load_rubric_for_play_id
from tactic_translate.translator import translate_board


class ScoringTests(unittest.TestCase):
    def test_a001_perfect_score(self) -> None:
        board = board_from_dict(
            {
                "play_id": "A001",
                "mode": "pass_points",
                "frames": [
                    {"zone": 9, "receiver": "FB"},
                    {"zone": 15, "receiver": "AM"},
                    {"zone": 19, "receiver": "FB"},
                    {"zone": 20, "receiver": "ST"},
                ],
            }
        )
        result = translate_board(board)
        self.assertTrue(result.valid)
        self.assertIsNotNone(result.scoring)
        assert result.scoring is not None
        self.assertEqual(result.scoring.earned, 15.0)
        self.assertEqual(result.scoring.max_points, 15.0)

    def test_a001_partial_wrong_place(self) -> None:
        board = board_from_dict(
            {
                "play_id": "A001",
                "mode": "pass_points",
                "frames": [
                    {"zone": 9, "receiver": "FB"},
                    {"zone": 15, "receiver": "AM"},
                    {"zone": 17, "receiver": "FB"},  # 右邊路 not 右路底線
                    {"zone": 20, "receiver": "ST"},
                ],
            }
        )
        result = translate_board(board)
        assert result.scoring is not None
        self.assertLess(result.scoring.earned, 15.0)
        self.assertGreater(result.scoring.earned, 10.0)

    def test_a001_run_tactic_perfect_score(self) -> None:
        board = board_from_dict(
            {
                "play_id": "A001",
                "mode": "pass_points",
                "grading_mode": "run_tactic",
                "frames": [
                    {"zone": 9, "receiver": "FB"},
                    {"zone": 15, "receiver": "AM"},
                    {"zone": 19, "receiver": "FB"},
                    {"zone": 20, "receiver": "ST"},
                ],
            }
        )
        result = translate_board(board)
        assert result.scoring is not None
        self.assertEqual(result.scoring.earned, 30.0)
        self.assertEqual(result.scoring.max_points, 30.0)
        self.assertEqual(result.scoring.grading_mode, "run_tactic")

    def test_rubric_loads_from_a001_yaml(self) -> None:
        rubric = load_rubric_for_play_id("A001")
        self.assertIsNotNone(rubric)
        assert rubric is not None
        self.assertEqual(rubric.total, 15.0)
        self.assertEqual(len(rubric.items), 3)


if __name__ == "__main__":
    unittest.main()
