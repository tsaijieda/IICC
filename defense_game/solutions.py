"""Canonical clear scripts — one distinct tactical pattern per puzzle."""

from __future__ import annotations

from .game import Action, ActionType
from .grid import Pos


def solution_actions(puzzle_id: str) -> list[Action]:
    key = puzzle_id.upper()
    demos: dict[str, list[Action]] = {
        "D1": [
            Action(ActionType.DRIBBLE, dest=Pos(0, 1)),
            Action(ActionType.PASS, target_id="A3"),
            Action(ActionType.MOVE, actor_id="A4", dest=Pos(5, 4)),
            Action(ActionType.PASS, target_id="A4"),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "D2": [
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.END_TURN),
            Action(ActionType.PASS, target_id="A3"),
            Action(ActionType.SHOOT, dest=Pos(2, 7)),
        ],
        "D3": [
            Action(ActionType.DRIBBLE, dest=Pos(6, 3)),
            Action(ActionType.END_TURN),
            Action(ActionType.DRIBBLE, dest=Pos(5, 4)),
            Action(ActionType.END_TURN),
            Action(ActionType.SHOOT, dest=Pos(2, 7)),
        ],
        "D4": [
            Action(ActionType.PASS, target_id="A4"),
            Action(ActionType.MOVE, actor_id="A2", dest=Pos(5, 4)),
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "D5": [
            Action(ActionType.DRIBBLE, dest=Pos(3, 3)),
            Action(ActionType.END_TURN),
            Action(ActionType.DRIBBLE, dest=Pos(3, 4)),
            Action(ActionType.END_TURN),
            Action(ActionType.SHOOT, dest=Pos(2, 7)),
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
            Action(ActionType.PASS, target_id="A4"),
            Action(ActionType.MOVE, actor_id="A3", dest=Pos(0, 5)),
            Action(ActionType.PASS, target_id="A3"),
            Action(ActionType.SHOOT, dest=Pos(2, 7)),
        ],
        "S2": [
            Action(ActionType.DRIBBLE, dest=Pos(0, 3)),
            Action(ActionType.MOVE, actor_id="A2", dest=Pos(3, 4)),
            Action(ActionType.MOVE, actor_id="A3", dest=Pos(5, 2)),
            Action(ActionType.END_TURN),
            Action(ActionType.DRIBBLE, dest=Pos(0, 4)),
            Action(ActionType.MOVE, actor_id="A2", dest=Pos(2, 4)),
            Action(ActionType.MOVE, actor_id="A3", dest=Pos(5, 3)),
            Action(ActionType.END_TURN),
            Action(ActionType.DRIBBLE, dest=Pos(0, 5)),
            Action(ActionType.MOVE, actor_id="A2", dest=Pos(1, 4)),
            Action(ActionType.MOVE, actor_id="A3", dest=Pos(5, 4)),
            Action(ActionType.PASS, target_id="A2"),
            Action(ActionType.PASS, target_id="A3"),
            Action(ActionType.SHOOT, dest=Pos(4, 7)),
        ],
        "S3": [
            Action(ActionType.DRIBBLE, dest=Pos(2, 4)),
            Action(ActionType.PASS, target_id="A4"),
            Action(ActionType.DRIBBLE, dest=Pos(3, 2)),
            Action(ActionType.MOVE, actor_id="A1", dest=Pos(1, 4)),
            Action(ActionType.PASS, target_id="A1"),
            Action(ActionType.SHOOT, dest=Pos(2, 7)),
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
            "① 盤帶拉開 → (0,1)",
            "② 傳左翼換邊",
            "③ 前鋒插上前場 → (5,4)",
            "④ 傳前鋒",
            "⑤ 前場射門 (4,7)",
        ],
        "D2": [
            "① 傳邊衛",
            "② 結束回合",
            "③ 傳前場前鋒",
            "④ 前場射門 (2,7)",
        ],
        "D3": [
            "① 盤帶推進 → (6,3)",
            "② 結束回合",
            "③ 內切前場 → (5,4)",
            "④ 結束回合",
            "⑤ 前場射門 (2,7)",
        ],
        "D4": [
            "① 傳拖後疏開",
            "② 前鋒插禁區前沿 → (5,4)",
            "③ 傳前鋒",
            "④ 前場射門 (4,7)",
        ],
        "D5": [
            "① 盤帶推進 → (3,3)",
            "② 結束回合",
            "③ 再推進前場 → (3,4)",
            "④ 結束回合",
            "⑤ 前場射門 (2,7)",
        ],
        "D6": [
            "① 傳給牆 — 不要直塞中路（後腰會斷）",
            "② 自己插上 → (4,3)",
            "③ 結束回合（讓後腰移位）",
            "④ 接回傳（繞過後腰）",
            "⑤ 高空吊給前鋒 A3",
            "⑥ 禁區射門 (4,7)",
        ],
        "S1": [
            "① 傳右衛甩掉逼搶",
            "② 傳前鋒轉移",
            "③ 左翼插上前場 → (0,5)",
            "④ 傳左翼",
            "⑤ 前場射門 (2,7)",
        ],
        "S2": [
            "① 左翼下底 → (0,3)",
            "② 前鋒插上 → (3,4)",
            "③ 右翼插上 → (5,2)",
            "④ 結束回合（防線被扯向邊路）",
            "⑤ 再推進 → (0,4)",
            "⑥ 前鋒續插 → (2,4)",
            "⑦ 右翼續插 → (5,3)",
            "⑧ 結束回合",
            "⑨ 下底 → (0,5)",
            "⑩ 前鋒到倒三角點 → (1,4)",
            "⑪ 右翼到對側 → (5,4)",
            "⑫ 倒三角回敲前鋒",
            "⑬ 橫傳到對側右翼",
            "⑭ 前場射門 (4,7)",
        ],
        "S3": [
            "① 前鋒盤帶前場 → (2,4)",
            "② 傳前腰拉開",
            "③ 前腰盤帶",
            "④ 前鋒再插 → (1,4)",
            "⑤ 傳回前鋒",
            "⑥ 前場射門 (2,7)",
        ],
        "S4": [
            "① 傳牆 — 別直塞後腰",
            "② 插上 → (4,3)",
            "③ 結束回合",
            "④ 接回傳",
            "⑤ 高空吊 A3",
            "⑥ 禁區射門 (4,7)",
        ],
        "S5": [
            "① 傳牆 — 別直塞雙后腰",
            "② 插上 → (4,3)",
            "③ 結束回合",
            "④ 接回傳",
            "⑤ 高空吊 A3",
            "⑥ 禁區射門 (4,7)",
        ],
    }
    key = puzzle_id.upper()
    if key not in labels:
        raise KeyError(f"No solution steps for {puzzle_id!r}")
    actions = solution_actions(key)
    steps = labels[key]
    if len(steps) != len(actions):
        raise RuntimeError(f"{key}: steps/actions length mismatch")
    out = []
    for label, act in zip(steps, actions):
        d: dict = {"label": label, "type": act.type.value}
        if act.dest is not None:
            d["x"], d["y"] = act.dest.x, act.dest.y
        if act.target_id is not None:
            d["target_id"] = act.target_id
        if act.actor_id is not None:
            d["actor_id"] = act.actor_id
        out.append(d)
    return out
