"""Pitch zone grid for 戰術復刻 (zones 1–20, full pitch)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Zone:
    id: int
    # depth: higher = closer to opponent goal
    depth: int
    lane: str  # left_wide | left_hs | center | right_hs | right_wide
    half_space: bool = False
    in_box: bool = False
    on_byline: bool = False


# Full pitch (goal at top / high depth). Wing columns split horizontally;
# half-space and center columns use taller cells (row_span=2).
ZONES: dict[int, Zone] = {
    1: Zone(1, depth=0, lane="left_wide"),
    2: Zone(2, depth=0, lane="center", in_box=True),
    3: Zone(3, depth=0, lane="right_wide"),
    4: Zone(4, depth=1, lane="left_wide"),
    5: Zone(5, depth=2, lane="left_wide"),
    6: Zone(6, depth=1, lane="left_hs", half_space=True),
    7: Zone(7, depth=1, lane="center"),
    8: Zone(8, depth=1, lane="right_hs", half_space=True),
    9: Zone(9, depth=1, lane="right_wide"),
    10: Zone(10, depth=2, lane="right_wide"),
    11: Zone(11, depth=2, lane="left_wide"),
    12: Zone(12, depth=3, lane="left_wide"),
    13: Zone(13, depth=3, lane="left_hs", half_space=True),
    14: Zone(14, depth=3, lane="center"),
    15: Zone(15, depth=3, lane="right_hs", half_space=True),
    16: Zone(16, depth=2, lane="right_wide"),
    17: Zone(17, depth=3, lane="right_wide"),
    18: Zone(18, depth=4, lane="left_wide", on_byline=True),
    19: Zone(19, depth=4, lane="right_wide", on_byline=True),
    20: Zone(20, depth=4, lane="center", in_box=True),
}

VALID_ZONE_IDS = frozenset(ZONES)

ZONE_NAMES: dict[int, str] = {
    1: "後場左角",
    2: "後場禁區",
    3: "後場右角",
    4: "左邊路（後段）",
    5: "左邊路（中段）",
    6: "左肋深處",
    7: "後場中路",
    8: "右肋深處",
    9: "右邊路（後段）",
    10: "右邊路（中段）",
    11: "左邊路",
    12: "左邊路（前段）",
    13: "左肋",
    14: "弧頂前緣",
    15: "右肋",
    16: "右路中路",
    17: "右邊路",
    18: "左路底線",
    19: "右路底線",
    20: "禁區中央",
}

LEFT_WEAK = frozenset({4, 5, 6, 11, 12, 13, 18})
RIGHT_STRONG = frozenset({8, 9, 10, 15, 16, 17, 19})
HALF_SPACES = frozenset(z.id for z in ZONES.values() if z.half_space)
BYLINE = frozenset({18, 19})
BOX = frozenset({20})
DEF_BOX = frozenset({2})
CROSS_ORIGIN = BYLINE | frozenset({12, 17})
GOAL_FRAME = frozenset({20})

PITCH_W = 68.0
PITCH_L = 105.0
PA_WIDTH = 40.32  # 大禁區寬
PA_DEPTH = 16.5   # 大禁區深
WING_W = (PITCH_W - PA_WIDTH) / 2  # 13.84m 邊路欄
CENTER_LANE_W = PA_WIDTH / 3  # 13.44m 中路三欄各寬
MID_LENGTH = PITCH_L - 2 * PA_DEPTH  # 兩禁區之間 72m
HALF_MID = MID_LENGTH / 2  # 36m 半場
WING_HALF = HALF_MID / 2  # 18m 邊路半段
HALFWAY_Y = PA_DEPTH + HALF_MID  # 52.5m

PITCH_ASPECT = PITCH_L / PITCH_W


def _pct_rect(zone: int, x: float, y: float, w: float, h: float) -> dict[str, float | int]:
    return {
        "zone": zone,
        "x": round(x / PITCH_W * 100, 2),
        "y": round(y / PITCH_L * 100, 2),
        "w": round(w / PITCH_W * 100, 2),
        "h": round(h / PITCH_L * 100, 2),
    }


def _build_zone_rects() -> list[dict[str, float | int]]:
    """20 戰術區 = 依 FIFA 球場線（禁區、中線、邊路）切出來的格子。"""
    wg, cw, pd, wh, hm = WING_W, CENTER_LANE_W, PA_DEPTH, WING_HALF, HALF_MID
    cx = wg
    half = HALFWAY_Y
    bottom = PITCH_L - pd

    return [
        # 進攻端：角區 + 大禁區（zone 20 = 禁區三中路欄）
        _pct_rect(18, 0, 0, wg, pd),
        _pct_rect(20, wg, 0, PA_WIDTH, pd),
        _pct_rect(19, wg + PA_WIDTH, 0, wg, pd),
        # 進攻半場
        _pct_rect(12, 0, pd, wg, wh),
        _pct_rect(13, cx, pd, cw, hm),
        _pct_rect(14, cx + cw, pd, cw, hm),
        _pct_rect(15, cx + 2 * cw, pd, cw, hm),
        _pct_rect(17, wg + PA_WIDTH, pd, wg, wh),
        _pct_rect(11, 0, pd + wh, wg, wh),
        _pct_rect(16, wg + PA_WIDTH, pd + wh, wg, wh),
        # 防守半場
        _pct_rect(5, 0, half, wg, wh),
        _pct_rect(6, cx, half, cw, hm),
        _pct_rect(7, cx + cw, half, cw, hm),
        _pct_rect(8, cx + 2 * cw, half, cw, hm),
        _pct_rect(10, wg + PA_WIDTH, half, wg, wh),
        _pct_rect(4, 0, half + wh, wg, wh),
        _pct_rect(9, wg + PA_WIDTH, half + wh, wg, wh),
        # 防守端
        _pct_rect(1, 0, bottom, wg, pd),
        _pct_rect(2, wg, bottom, PA_WIDTH, pd),
        _pct_rect(3, wg + PA_WIDTH, bottom, wg, pd),
    ]


ZONE_RECTS: list[dict[str, float | int]] = _build_zone_rects()

# CSS grid cells (1-based row/col). row 1 = attacking goal line.
ZONE_CELLS: list[dict[str, int]] = [
    {"zone": 18, "row": 1, "col": 1},
    {"zone": 20, "row": 1, "col": 2, "col_span": 3},
    {"zone": 19, "row": 1, "col": 5},
    {"zone": 12, "row": 2, "col": 1},
    {"zone": 13, "row": 2, "col": 2, "row_span": 2},
    {"zone": 14, "row": 2, "col": 3, "row_span": 2},
    {"zone": 15, "row": 2, "col": 4, "row_span": 2},
    {"zone": 17, "row": 2, "col": 5},
    {"zone": 11, "row": 3, "col": 1},
    {"zone": 16, "row": 3, "col": 5},
    {"zone": 5, "row": 4, "col": 1},
    {"zone": 6, "row": 4, "col": 2, "row_span": 2},
    {"zone": 7, "row": 4, "col": 3, "row_span": 2},
    {"zone": 8, "row": 4, "col": 4, "row_span": 2},
    {"zone": 10, "row": 4, "col": 5},
    {"zone": 4, "row": 5, "col": 1},
    {"zone": 9, "row": 5, "col": 5},
    {"zone": 1, "row": 6, "col": 1},
    {"zone": 2, "row": 6, "col": 2, "col_span": 3},
    {"zone": 3, "row": 6, "col": 5},
]

# Flat layout kept for simple consumers (None = covered by row/col span).
ZONE_LAYOUT: list[list[int | None]] = [
    [18, 20, 20, 20, 19],
    [12, 13, 14, 15, 17],
    [11, None, None, None, 16],
    [5, 6, 7, 8, 10],
    [4, None, None, None, 9],
    [1, 2, 2, 2, 3],
]


def zone_depth(zid: int) -> int:
    return ZONES[zid].depth


def zone_name(zid: int) -> str:
    """場地名稱，用於戰術敘述與評分文案。"""
    return ZONE_NAMES.get(zid, f"區域{zid}")


def zone_path(z0: int, z1: int) -> str:
    return f"{zone_name(z0)} → {zone_name(z1)}"


def is_forward(from_zone: int, to_zone: int) -> bool:
    return zone_depth(to_zone) > zone_depth(from_zone)


def lateral_side(zid: int) -> str:
    lane = ZONES[zid].lane
    if lane in ("left_wide", "left_hs"):
        return "left"
    if lane in ("right_wide", "right_hs"):
        return "right"
    return "center"
