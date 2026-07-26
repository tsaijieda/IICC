"""Tests for rubric scoring."""

from __future__ import annotations

import unittest

from tactic_translate.io import board_from_dict
from tactic_translate.scoring import load_rubric
from tactic_translate.translator import translate_board


class ScoringTests(unittest.TestCase):
    def test_t001_perfect_score(self) -> None:
        board = board_from_dict(
            {
                "play_id": "T001",
                "mode": "pass_points",
                "frames": [
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

    def test_t001_partial_wrong_place(self) -> None:
        board = board_from_dict(
            {
                "play_id": "T001",
                "mode": "pass_points",
                "frames": [
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

    def test_rubric_loads_from_001_yaml(self) -> None:
        rubric = load_rubric("001.yaml")
        self.assertIsNotNone(rubric)
        assert rubric is not None
        self.assertEqual(rubric.total, 15.0)
        self.assertEqual(len(rubric.items), 2)


if __name__ == "__main__":
    unittest.main()
