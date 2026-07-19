"""Tactical puzzles (D1–D6) and defense-style puzzles (S1–S5).

Blocks slide on the ball→goal-centre corridor (original low-block). Each clears in 5 turns.
"""

from __future__ import annotations

from .entities import DefenderKind, Player, Puzzle, Side
from .grid import Pos


def _atk(pid: str, label: str, x: int, y: int) -> Player:
    return Player(id=pid, label=label, side=Side.ATTACK, pos=Pos(x, y))


def _def(
    pid: str,
    label: str,
    kind: DefenderKind,
    x: int,
    y: int,
    *,
    block_max_y: int | None = None,
    cover_ball: bool = False,
) -> Player:
    return Player(
        id=pid,
        label=label,
        side=Side.DEFENSE,
        pos=Pos(x, y),
        kind=kind,
        block_max_y=block_max_y,
        block_hold_channel=cover_ball,
        anchored=False,
    )


def _block(
    pid: str, label: str, x: int, y: int, *, cover_ball: bool = True
) -> Player:
    """Low-block — lateral slide on ball→goal line only."""
    return _def(
        pid,
        label,
        DefenderKind.BLOCK,
        x,
        y,
        block_max_y=y,
        cover_ball=cover_ball,
    )


def _anchor_block(pid: str, label: str, x: int, y: int) -> Player:
    """Stationary block — holds a cell (e.g. far-post cover)."""
    return Player(
        id=pid,
        label=label,
        side=Side.DEFENSE,
        pos=Pos(x, y),
        kind=DefenderKind.BLOCK,
        block_max_y=y,
        block_hold_channel=True,
        anchored=True,
    )


def _shadow(pid: str, label: str, x: int, y: int, mark_id: str) -> Player:
    return Player(
        id=pid,
        label=label,
        side=Side.DEFENSE,
        pos=Pos(x, y),
        kind=DefenderKind.SHADOW,
        mark_id=mark_id,
    )


PUZZLE_CATEGORIES: list[dict[str, str]] = [
    {"id": "tactical", "label": "進攻戰術"},
    {"id": "defense", "label": "防守體系"},
]


PUZZLES: list[Puzzle] = [
    Puzzle(
        id="D1",
        title="破逼搶 — Break the Press",
        description=(
            "戰術單元：破逼搶。"
            "逼搶員已經貼身——結束回合或硬盤會被斷；先傳出壓力區，換邊推進，再回傳射門。"
            "大閘只沿球→門走廊橫移。"
        ),
        tip="盤 (0,1) → 傳左翼 → 前鋒插 (5,4) → 傳前鋒 → 射 (4,7)。",
        attackers=[
            _atk("A1", "中場", 1, 2),
            _atk("A2", "右衛", 6, 0),
            _atk("A3", "左翼", 0, 4),
            _atk("A4", "前鋒", 4, 3),
        ],
        defenders=[
            _def("G1", "門將", DefenderKind.GOALKEEPER, 3, 7),
            _def("P1", "逼搶", DefenderKind.PRESSER, 1, 3),
            _block("B1", "左閘", 0, 5),
            _block("B2", "中閘", 2, 5),
            _block("B3", "右閘", 4, 5),
            _block("B4", "拖後閘", 3, 6),
        ],
        ball_holder_id="A1",
        max_turns=8,
        allow_lob=False,
    ),
    Puzzle(
        id="D2",
        title="套邊 — Overlap",
        description=(
            "戰術單元：套邊插上（Overlap）。"
            "前腰持球——右邊衛無球套到外側高位，接球後內切遠柱射門。"
            "大閘會跟著球橫移，邊衛必須先跑到位。"
        ),
        tip="傳邊衛 → 結束 → 傳前鋒（y=4）→ 射 (2,7)。",
        attackers=[
            _atk("A1", "前腰", 3, 2),
            _atk("A2", "邊衛", 6, 1),
            _atk("A3", "前鋒", 1, 4),
            _atk("A4", "左翼", 0, 2),
        ],
        defenders=[
            _def("G1", "門將", DefenderKind.GOALKEEPER, 2, 7),
            _block("B1", "邊閘", 4, 3),
            _block("B2", "中閘", 2, 4),
            _block("B3", "近線", 1, 5),
            _block("B4", "肋閘", 3, 4),
            _def("S1", "影子", DefenderKind.SHADOW, 1, 3),
        ],
        ball_holder_id="A1",
        max_turns=8,
        allow_lob=False,
    ),
    Puzzle(
        id="D3",
        title="內切 — Underlap",
        description=(
            "戰術單元：內切／套內（Underlap）。"
            "邊鋒持球——前腰從內側肋部插上接直塞，再斜插遠柱射門。"
        ),
        tip="盤 (6,3) 結束 → 內切 (5,4) 結束 → 射 (2,7)。",
        attackers=[
            _atk("A1", "邊鋒", 6, 2),
            _atk("A2", "前腰", 4, 1),
            _atk("A3", "前鋒", 0, 3),
            _atk("A4", "拖後", 2, 0),
        ],
        defenders=[
            _def("G1", "門將", DefenderKind.GOALKEEPER, 2, 7),
            _block("B1", "邊閘", 5, 3),
            _block("B2", "中閘", 2, 4),
            _block("B3", "肋閘", 1, 4),
            _block("B4", "近線", 1, 5),
            _def("S1", "影子", DefenderKind.SHADOW, 0, 2),
        ],
        ball_holder_id="A1",
        max_turns=8,
        allow_lob=False,
    ),
    Puzzle(
        id="D4",
        title="倒三角 — Cut-back",
        description=(
            "戰術單元：倒三角傳中（Cut-back）。"
            "左翼下底——大閘被拉到邊路，回敲禁區前沿前鋒再射。"
        ),
        tip="傳拖後 → 前鋒插 (5,4) → 傳前鋒 → 射 (4,7)。",
        attackers=[
            _atk("A1", "左翼", 0, 2),
            _atk("A2", "前鋒", 4, 3),
            _atk("A3", "右翼", 6, 1),
            _atk("A4", "拖後", 2, 0),
        ],
        defenders=[
            _def("G1", "門將", DefenderKind.GOALKEEPER, 2, 7),
            _block("B1", "邊閘", 1, 4),
            _block("B2", "近線", 1, 5),
            _block("B3", "中閘", 3, 5),
            _block("B4", "右閘", 5, 4),
            _def("S1", "影子", DefenderKind.SHADOW, 6, 2),
        ],
        ball_holder_id="A1",
        max_turns=8,
        allow_lob=False,
    ),
    Puzzle(
        id="D5",
        title="撞牆 — Wall Pass",
        description=(
            "戰術單元：撞牆配合（Wall pass / give-and-go）。"
            "傳給牆 → 無球前插 → 接回傳推進射門。"
            "影子盯死牆，正面硬射沒用；大閘只沿走廊橫移。"
        ),
        tip="盤 (3,3) 結束 → (3,4) 結束 → 射 (2,7)。",
        attackers=[
            _atk("A1", "持球", 2, 2),
            _atk("A2", "牆", 4, 2),
            _atk("A3", "前鋒", 0, 3),
            _atk("A4", "邊", 6, 0),
        ],
        defenders=[
            _def("G1", "門將", DefenderKind.GOALKEEPER, 3, 7),
            _block("B1", "中閘", 2, 3, cover_ball=True),
            _block("B2", "近線", 0, 5, cover_ball=False),
            _block("B3", "中後", 1, 4, cover_ball=False),
            _block("B4", "左肋", 1, 3, cover_ball=True),
            _def("S1", "影子", DefenderKind.SHADOW, 4, 3),
        ],
        ball_holder_id="A1",
        max_turns=8,
        allow_lob=False,
    ),
    Puzzle(
        id="D6",
        title="繞後腰 — Beat the DM",
        description=(
            "戰術單元：面對防守中場（攔截員）。"
            "後腰卡在中路——硬塞會被斷，腳下射門也會被他擋。"
            "撞牆繞過他，再高空吊給前鋒禁區內射門。"
        ),
        tip="別直塞前鋒 → 傳牆 → 插上 (4,3) 結束 → 接回傳 → 高空吊 A3 → 射門。",
        attackers=[
            _atk("A1", "中場", 3, 2),
            _atk("A2", "牆", 5, 2),
            _atk("A3", "前鋒", 3, 5),
            _atk("A4", "邊", 0, 2),
        ],
        defenders=[
            _def("G1", "門將", DefenderKind.GOALKEEPER, 3, 7),
            _def("I1", "後腰", DefenderKind.INTERCEPTOR, 3, 3),
            _block("B1", "中閘", 3, 4, cover_ball=True),
            _block("B2", "左閘", 1, 4, cover_ball=True),
            _block("B3", "右閘", 5, 4, cover_ball=False),
            _def("S1", "影子", DefenderKind.SHADOW, 0, 3),
        ],
        ball_holder_id="A1",
        max_turns=8,
        allow_lob=True,
    ),
    # --- 防守體系（S1–S5）---
    Puzzle(
        id="S1",
        title="高位逼搶 — High Press",
        category="defense",
        description=(
            "防守體系：高位逼搶。"
            "兩名逼搶員同時前壓——已貼身時硬盤會被斷。"
            "先傳出壓力區、換邊推進，再回傳禁區射門。"
        ),
        tip="傳右衛 → 傳前鋒 → 左翼插 (0,5) → 傳左翼 → 射 (2,7)。",
        attackers=[
            _atk("A1", "中場", 1, 2),
            _atk("A2", "右衛", 6, 0),
            _atk("A3", "左翼", 0, 4),
            _atk("A4", "前鋒", 4, 3),
        ],
        defenders=[
            _def("G1", "門將", DefenderKind.GOALKEEPER, 3, 7),
            _def("P1", "逼搶", DefenderKind.PRESSER, 2, 3),
            _def("P2", "逼搶", DefenderKind.PRESSER, 3, 3),
            _block("B1", "左閘", 0, 5),
            _block("B2", "中閘", 2, 5),
            _block("B3", "右閘", 4, 5),
            _block("B4", "拖後", 3, 6),
        ],
        ball_holder_id="A1",
        max_turns=8,
        allow_lob=False,
    ),
    Puzzle(
        id="S2",
        title="擺大巴 — Low Block",
        category="defense",
        description=(
            "防守體系：擺大巴（低位密集）。"
            "後腰卡橫傳、四後衛蹲走廊，拖後閘＋角區定點蓋死右路塞入。"
            "必須下底把防線扯開，倒三角回敲，再橫傳到對側空當射門。"
        ),
        tip="下底 (0,5)＋前鋒/右翼插上 → 倒三角 A2 → 橫傳 A3 → 射 (4,7)。",
        attackers=[
            _atk("A1", "左翼", 0, 2),
            _atk("A2", "前鋒", 4, 3),
            _atk("A3", "右翼", 6, 1),
            _atk("A4", "拖後", 2, 0),
        ],
        defenders=[
            _def("G1", "門將", DefenderKind.GOALKEEPER, 3, 7),
            _block("B0", "後腰", 2, 3),
            _block("B1", "邊閘", 1, 5),
            _block("B2", "中閘", 3, 5),
            _block("B3", "右閘", 5, 5),
            _block("B4", "拖後", 4, 6),
            _anchor_block("B5", "角區", 5, 6),
        ],
        ball_holder_id="A1",
        max_turns=8,
        allow_lob=False,
    ),
    Puzzle(
        id="S3",
        title="人盯人 — Man Marking",
        category="defense",
        description=(
            "防守體系：四人盯人＋區域大閘。"
            "四名影子一對一黏住進攻球員，中路再加一道大閘卡球→門走廊。"
            "影子一對一黏人；跑位／盤帶當下防守都不動，結束回合或傳球後才跟上。"
            "用跑位拉開盯人，再傳入空當射門。盤帶後同回合不能射門。"
        ),
        tip="盤 (2,4) → 傳前腰 → 前鋒插 (1,4) → 傳回 → 射 (2,7)。",
        attackers=[
            _atk("A1", "前鋒", 3, 3),
            _atk("A2", "右邊", 6, 2),
            _atk("A3", "左邊", 0, 2),
            _atk("A4", "前腰", 4, 2),
        ],
        defenders=[
            _def("G1", "門將", DefenderKind.GOALKEEPER, 3, 7),
            _block("B1", "中閘", 3, 5, cover_ball=True),
            _shadow("S1", "盯A1", 3, 4, "A1"),
            _shadow("S2", "盯A2", 6, 3, "A2"),
            _shadow("S3", "盯A3", 0, 3, "A3"),
            _shadow("S4", "盯A4", 4, 3, "A4"),
        ],
        ball_holder_id="A1",
        max_turns=8,
        allow_lob=False,
        allow_dribble=True,
    ),
    Puzzle(
        id="S4",
        title="中位防守 — Mid Block",
        category="defense",
        description=(
            "防守體系：中位防守（Mid block）。"
            "後腰卡中路——直塞與腳下射門都會被他擋；四後衛守 y=4 中線。"
            "撞牆繞過后腰，再高空吊給禁區內前鋒射門。"
        ),
        tip="傳牆 → 插上 (4,3) 結束 → 接回傳 → 高空吊 A3 → 射門。",
        attackers=[
            _atk("A1", "中場", 3, 2),
            _atk("A2", "牆", 5, 2),
            _atk("A3", "前鋒", 3, 5),
            _atk("A4", "邊", 0, 2),
        ],
        defenders=[
            _def("G1", "門將", DefenderKind.GOALKEEPER, 3, 7),
            _def("I1", "後腰", DefenderKind.INTERCEPTOR, 3, 3),
            _block("B1", "左閘", 1, 4, cover_ball=True),
            _block("B2", "中閘", 3, 4, cover_ball=True),
            _block("B3", "右閘", 5, 4, cover_ball=False),
            Player(
                id="B4",
                label="封左柱",
                side=Side.DEFENSE,
                pos=Pos(2, 5),
                kind=DefenderKind.BLOCK,
                block_max_y=5,
                anchored=True,
            ),
        ],
        ball_holder_id="A1",
        max_turns=8,
        allow_lob=True,
    ),
    Puzzle(
        id="S5",
        title="雙防中 — Double Pivot",
        category="defense",
        description=(
            "防守體系：雙防中（Double pivot）。"
            "兩名後腰並列卡中路——直塞與腳下射門都會被擋。"
            "撞牆繞過雙后腰，再高空吊給禁區內前鋒射門。"
        ),
        tip="傳牆 → 插上 (4,3) 結束 → 接回傳 → 高空吊 A3 → 射門。",
        attackers=[
            _atk("A1", "中場", 3, 2),
            _atk("A2", "牆", 5, 2),
            _atk("A3", "前鋒", 3, 5),
            _atk("A4", "邊", 0, 2),
        ],
        defenders=[
            _def("G1", "門將", DefenderKind.GOALKEEPER, 3, 7),
            _def("I1", "後腰", DefenderKind.INTERCEPTOR, 2, 3),
            _def("I2", "後腰", DefenderKind.INTERCEPTOR, 5, 3),
            _block("B1", "中閘", 3, 4, cover_ball=True),
            _block("B2", "左閘", 1, 4, cover_ball=True),
        ],
        ball_holder_id="A1",
        max_turns=8,
        allow_lob=True,
    ),
]


def get_puzzle(puzzle_id: str) -> Puzzle:
    for p in PUZZLES:
        if p.id.upper() == puzzle_id.upper():
            return p
    raise KeyError(f"Unknown puzzle {puzzle_id!r}. Choose: {[p.id for p in PUZZLES]}")
