"""Tactic pattern detectors with partial scoring (點＋邊)."""

from __future__ import annotations

from .models import CriterionMatch, PlayerSnapshot, TacticHit, TouchFrame
from .zones import (
    BOX,
    BYLINE,
    CROSS_ORIGIN,
    LEFT_WEAK,
    RIGHT_STRONG,
    ZONES,
    is_forward,
    lateral_side,
    zone_depth,
    zone_name,
    zone_path,
)


def _pct(matches: list[CriterionMatch]) -> float:
    if not matches:
        return 0.0
    return sum(1 for m in matches if m.matched) / len(matches)


def _find_player_moves(
    before: TouchFrame, after: TouchFrame
) -> list[tuple[str, int, int]]:
    bz = before.player_zones()
    az = after.player_zones()
    out: list[tuple[str, int, int]] = []
    for pid, z0 in bz.items():
        z1 = az.get(pid)
        if z1 is not None and z1 != z0:
            out.append((pid, z0, z1))
    return out


def _passer_id(before: TouchFrame, after: TouchFrame) -> str | None:
    rid = after.receiver_id
    for p in before.players:
        if p.player_id == rid:
            continue
        if p.zone == before.ball_zone:
            return p.player_id
    # ball was with receiver already (dribble / carry)
    if before.receiver_id != rid and before.receiver_zone() == before.ball_zone:
        return before.receiver_id
    return before.receiver_id if before.receiver_id != rid else None


def detect_basic_action(
    before: TouchFrame,
    after: TouchFrame,
    ball_from: int,
    ball_to: int,
) -> str:
    if ball_to in BOX and ball_from in BOX:
        return "得分"
    if ball_to in BOX:
        return "射正"
    if ball_from == ball_to:
        return "盤帶"
    return "傳球"


def detect_switch(
    ball_from: int,
    ball_to: int,
    before: TouchFrame,
    after: TouchFrame,
) -> TacticHit | None:
    criteria: list[CriterionMatch] = []

    right_to_left = ball_from in RIGHT_STRONG and ball_to in LEFT_WEAK
    left_to_right = ball_from in LEFT_WEAK and ball_to in RIGHT_STRONG
    flank_switch = right_to_left or left_to_right

    deep_long = (
        zone_depth(ball_from) <= 2
        and lateral_side(ball_from) != lateral_side(ball_to)
        and zone_depth(ball_to) - zone_depth(ball_from) >= 2
    )

    arc_to_wide = (
        ball_from in {11, 13, 14, 15, 16}
        and ball_to in {12, 17, 18, 19}
        and lateral_side(ball_from) != lateral_side(ball_to)
    )

    switched = flank_switch or deep_long or arc_to_wide
    criteria.append(
        CriterionMatch(
            "強弱邊轉移 (橫跨半場或弱側)",
            switched,
            detail=f"{ball_from}→{ball_to}",
        )
    )

    lateral = lateral_side(ball_from) != lateral_side(ball_to)
    criteria.append(CriterionMatch("橫向轉移", lateral))

    depth_similar = abs(zone_depth(ball_from) - zone_depth(ball_to)) <= 1
    depth_ok = (depth_similar and flank_switch) or deep_long or arc_to_wide
    criteria.append(
        CriterionMatch(
            "轉移路徑合理",
            depth_ok,
            detail=f"Δdepth={zone_depth(ball_to) - zone_depth(ball_from)}",
        )
    )

    score = _pct(criteria)
    if score == 0:
        return None
    return TacticHit(
        name="強弱邊轉移",
        score=score,
        criteria=criteria,
        narrative="由強側長傳轉移弱側利用空間。",
    )


def detect_layoff(ball_from: int, ball_to: int) -> TacticHit | None:
    """回做球：向前區域往回傳。"""
    if zone_depth(ball_to) >= zone_depth(ball_from):
        return None
    to_lane = ZONES[ball_to].lane
    if to_lane in ("left_wide", "right_wide") and ZONES[ball_from].lane in (
        "left_hs",
        "right_hs",
        "center",
    ):
        return None
    criteria = [
        CriterionMatch("起點在前場區 (depth≥2)", zone_depth(ball_from) >= 2),
        CriterionMatch("往回傳（深度減少）", zone_depth(ball_to) < zone_depth(ball_from)),
    ]
    score = _pct(criteria)
    if score == 0:
        return None
    return TacticHit(
        name="回做球",
        score=score,
        criteria=criteria,
        narrative=f"回做球 {zone_path(ball_from, ball_to)}。",
    )


def detect_cutback(ball_from: int, ball_to: int) -> TacticHit | None:
    criteria: list[CriterionMatch] = []

    from_deep = ball_from in BYLINE or ball_from == 20
    criteria.append(
        CriterionMatch(
            "起點在底線／禁區深處 (18/19/20)",
            from_deep,
            detail=f"from={ball_from}",
        )
    )

    to_arc = ball_to == 14
    criteria.append(CriterionMatch(f"終點{zone_name(14)}", to_arc))

    # 回傳：深度不增加，或自邊路內切至弧頂
    inward = ball_from in BYLINE and ball_to == 14
    backward = zone_depth(ball_to) < zone_depth(ball_from)
    criteria.append(
        CriterionMatch("回傳至禁區前沿", inward or backward)
    )

    score = _pct(criteria)
    if score == 0:
        return None
    return TacticHit(
        name="倒三角傳球",
        score=score,
        criteria=criteria,
        narrative="底線附近回傳禁區前沿隊友。",
    )


def detect_cross(ball_from: int, ball_to: int) -> TacticHit | None:
    criteria = [
        CriterionMatch(
            "起點在邊路或底線",
            ball_from in CROSS_ORIGIN,
            detail=f"from={ball_from}",
        ),
        CriterionMatch(f"終點{zone_name(20)}", ball_to == 20),
    ]
    score = _pct(criteria)
    if score == 0:
        return None
    return TacticHit(
        name="傳中",
        score=score,
        criteria=criteria,
        narrative="邊路傳中至禁區中央。",
    )


def detect_line_breaking(
    ball_from: int,
    ball_to: int,
    before: TouchFrame,
    after: TouchFrame,
) -> TacticHit | None:
    criteria: list[CriterionMatch] = []

    forward = is_forward(ball_from, ball_to)
    criteria.append(CriterionMatch("向前傳球", forward))

    line = before.offside_line_depth
    crossed = line is not None and zone_depth(ball_to) > line
  # fallback: entering box from outside counts as breaking last line
    if not crossed:
        crossed = ball_to in BOX and zone_depth(ball_from) < zone_depth(20)
    criteria.append(CriterionMatch("穿越防線", crossed))

    score = _pct(criteria)
    if score == 0:
        return None
    return TacticHit(
        name="直塞",
        score=score,
        criteria=criteria,
        narrative="向前直塞穿越防線。",
    )


def detect_lob(
    ball_from: int,
    ball_to: int,
    before: TouchFrame,
    after: TouchFrame,
) -> TacticHit | None:
    criteria: list[CriterionMatch] = []

    low_start = zone_depth(ball_from) <= 2
    criteria.append(CriterionMatch("起點在中低位 (depth≤2)", low_start))

    big_jump = zone_depth(ball_to) - zone_depth(ball_from) >= 2
    criteria.append(CriterionMatch("縱深跳躍≥2", big_jump))

    line = before.offside_line_depth
    over_line = line is not None and zone_depth(ball_from) < line <= zone_depth(ball_to)
    if line is None:
        over_line = big_jump and ball_to in ({14, 20} | BYLINE)
    criteria.append(CriterionMatch("越過防線頭頂", over_line))

    score = _pct(criteria)
    if score == 0:
        return None
    return TacticHit(
        name="過頂長傳",
        score=score,
        criteria=criteria,
        narrative="中低位起腳越過防線至身後。",
    )


def detect_dribble_carry(
    before: TouchFrame,
    after: TouchFrame,
    ball_from: int,
    ball_to: int,
) -> TacticHit | None:
    if ball_from == ball_to:
        return None
    if after.receiver_id != before.receiver_id:
        return None
    forward = is_forward(ball_from, ball_to)
    criteria = [
        CriterionMatch("同一持球者連續觸球", True),
        CriterionMatch("向前帶球", forward),
    ]
    if not forward:
        return None
    return TacticHit(
        name="盤帶推進",
        score=_pct(criteria),
        criteria=criteria,
        narrative=f"帶球由{zone_name(ball_from)}推進至{zone_name(ball_to)}。",
    )


_TACTIC_PRIORITY: dict[str, int] = {
    "傳中": 10,
    "倒三角傳球": 9,
    "直塞": 8,
    "過頂長傳": 7,
    "回做球": 6,
    "盤帶推進": 5,
    "強弱邊轉移": 1,
}


def detect_ball_path_tactics(
    before: TouchFrame,
    after: TouchFrame,
    ball_from: int,
    ball_to: int,
) -> list[TacticHit]:
    """只依球路判斷（1st_half_rules.md 戰術語言）。"""
    hits: list[TacticHit] = []
    for fn in (
        lambda: detect_switch(ball_from, ball_to, before, after),
        lambda: detect_cutback(ball_from, ball_to),
        lambda: detect_cross(ball_from, ball_to),
        lambda: detect_layoff(ball_from, ball_to),
        lambda: detect_line_breaking(ball_from, ball_to, before, after),
        lambda: detect_lob(ball_from, ball_to, before, after),
        lambda: detect_dribble_carry(before, after, ball_from, ball_to),
    ):
        hit = fn()
        if hit and hit.score > 0:
            hits.append(hit)
    hits.sort(
        key=lambda h: (h.score, _TACTIC_PRIORITY.get(h.name, 0)),
        reverse=True,
    )
    return hits


def detect_all_tactics(
    before: TouchFrame,
    after: TouchFrame,
    ball_from: int,
    ball_to: int,
    runs: list[tuple[str, int, int]],
) -> list[TacticHit]:
    return detect_ball_path_tactics(before, after, ball_from, ball_to)
