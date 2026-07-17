"""Canonical clear scripts — one distinct tactical pattern per puzzle."""

from __future__ import annotations

from .game import Action, ActionType
from .grid import Pos


def solution_actions(puzzle_id: str) -> list[Action]:
    key = puzzle_id.upper()
    demos: dict[str, list[Action]] = {
        "D1": [
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.PASS, target_id="A3"),
            Action(ActionType.DRIBBLE, dest=Pos(0, 5)),
            Action(ActionType.PASS, target_id="A4"),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "D2": [
            Action(ActionType.MOVE, actor_id="A2", dest=Pos(6, 2)),
            Action(ActionType.END_TURN),
            Action(ActionType.MOVE, actor_id="A2", dest=Pos(6, 3)),
            Action(ActionType.END_TURN),
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.DRIBBLE, dest=Pos(5, 4)),
            Action(ActionType.END_TURN),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "D3": [
            Action(ActionType.MOVE, actor_id="A2", dest=Pos(4, 2)),
            Action(ActionType.END_TURN),
            Action(ActionType.MOVE, actor_id="A2", dest=Pos(4, 3)),
            Action(ActionType.END_TURN),
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.DRIBBLE, dest=Pos(5, 4)),
            Action(ActionType.END_TURN),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "D4": [
            Action(ActionType.DRIBBLE, dest=Pos(0, 3)),
            Action(ActionType.END_TURN),
            Action(ActionType.DRIBBLE, dest=Pos(0, 4)),
            Action(ActionType.MOVE, actor_id="A2", dest=Pos(5, 4)),
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "D5": [
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.END_TURN),
            Action(ActionType.MOVE, actor_id="A1", dest=Pos(1, 3)),
            Action(ActionType.PASS, target_id="A1"),
            Action(ActionType.PASS, target_id="A4"),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "D6": [
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.MOVE, actor_id="A1", dest=Pos(4, 3)),
            Action(ActionType.END_TURN),
            Action(ActionType.PASS, target_id="A1"),
            Action(ActionType.LOB, target_id="A3"),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "S1": [
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.PASS, target_id="A3"),
            Action(ActionType.DRIBBLE, dest=Pos(0, 5)),
            Action(ActionType.PASS, target_id="A4"),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "S2": [
            Action(ActionType.DRIBBLE, dest=Pos(0, 3)),
            Action(ActionType.END_TURN),
            Action(ActionType.DRIBBLE, dest=Pos(0, 4)),
            Action(ActionType.END_TURN),
            Action(ActionType.DRIBBLE, dest=Pos(0, 5)),
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "S3": [
            Action(ActionType.PASS, target_id="A3"),
            Action(ActionType.END_TURN),
            Action(ActionType.MOVE, actor_id="A2", dest=Pos(6, 1)),
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "S4": [
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.MOVE, actor_id="A1", dest=Pos(4, 3)),
            Action(ActionType.END_TURN),
            Action(ActionType.PASS, target_id="A1"),
            Action(ActionType.LOB, target_id="A3"),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "S5": [
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.MOVE, actor_id="A1", dest=Pos(4, 3)),
            Action(ActionType.END_TURN),
            Action(ActionType.PASS, target_id="A1"),
            Action(ActionType.LOB, target_id="A3"),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
    }
    if key not in demos:
        raise KeyError(f"No solution for {puzzle_id!r}")
    return demos[key]


def solution_steps(puzzle_id: str) -> list[dict]:
    labels: dict[str, list[str]] = {
        "D1": [
            "① 傳右衛 — 先離開逼搶壓力區",
            "② 傳左翼 — 換邊推進",
            "③ 盤帶下底 → (0,5)",
            "④ 回傳前鋒",
            "⑤ 射 (4,7)",
        ],
        "D2": [
            "① 邊衛套邊 → (6,2)",
            "② 結束回合（讓防守移動）",
            "③ 邊衛再套 → (6,3)",
            "④ 結束回合",
            "⑤ 傳給套上的邊衛",
            "⑥ 內切 → (5,4)",
            "⑦ 結束回合（盤帶後不能直接射）",
            "⑧ 遠柱射門 (4,7)",
        ],
        "D3": [
            "① 前腰內切 → (4,2)",
            "② 結束回合",
            "③ 再插肋部 → (4,3)",
            "④ 結束回合",
            "⑤ 直塞給內切的前腰",
            "⑥ 斜插 → (5,4)",
            "⑦ 結束回合",
            "⑧ 遠柱射門 (4,7)",
        ],
        "D4": [
            "① 盤帶 → (0,3)",
            "② 結束回合（防守才跟上）",
            "③ 盤帶 → (0,4)",
            "④ 前鋒插上 → (5,4)",
            "⑤ 倒三角回敲前鋒",
            "⑥ 射 (4,7)",
        ],
        "D5": [
            "① 傳給牆",
            "② 結束回合",
            "③ 插上 → (1,3)",
            "④ 接回傳（撞牆完成）",
            "⑤ 傳邊路拉開",
            "⑥ 射 (4,7)",
        ],
        "D6": [
            "① 傳給牆 — 不要直塞中路（後腰會斷）",
            "② 自己插上 → (4,3)",
            "③ 結束回合（讓後腰移位）",
            "④ 接回傳（繞過後腰）",
            "⑤ 高空吊給前鋒 A3",
            "⑥ 射 (4,7)",
        ],
        "S1": [
            "① 傳右衛 — 甩掉雙逼搶",
            "② 傳左翼 — 換邊推進",
            "③ 盤帶下底 → (0,5)",
            "④ 回傳前鋒",
            "⑤ 射 (4,7)",
        ],
        "S2": [
            "① 盤帶 → (0,3)",
            "② 結束回合",
            "③ 盤帶 → (0,4)",
            "④ 結束回合",
            "⑤ 下底 → (0,5)",
            "⑥ 倒三角回敲前鋒",
            "⑦ 射 (4,7)",
        ],
        "S3": [
            "① 傳左邊 — 先換邊",
            "② 結束回合（影子門側跟上）",
            "③ 右邊假跑 → (6,1) 拉開盯人",
            "④ 傳右邊",
            "⑤ 射 (4,7)",
        ],
        "S4": [
            "① 傳牆 — 別直塞後腰",
            "② 插上 → (4,3)",
            "③ 結束回合",
            "④ 接回傳",
            "⑤ 高空吊 A3",
            "⑥ 射 (4,7)",
        ],
        "S5": [
            "① 傳牆 — 別直塞雙后腰",
            "② 插上 → (4,3)",
            "③ 結束回合",
            "④ 接回傳",
            "⑤ 高空吊 A3",
            "⑥ 射 (4,7)",
        ],
    }
    key = puzzle_id.upper()
    if key not in labels:
        raise KeyError(f"No solution steps for {puzzle_id!r}")
    actions = solution_actions(key)
    steps = labels[key]
    if len(steps) != len(actions):
        raise RuntimeError(f"{key}: steps/actions length mismatch")
    out: list[dict] = []
    for text, action in zip(steps, actions):
        out.append(
            {
                "label": text,
                "type": action.type.value,
                "target_id": action.target_id,
                "actor_id": action.actor_id,
                "x": action.dest.x if action.dest else None,
                "y": action.dest.y if action.dest else None,
            }
        )
    return out
