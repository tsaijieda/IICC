"""Defender AI — one update per turn end."""

from __future__ import annotations

from .entities import DefenderKind, Player
from .grid import (
    COLS,
    GOAL_CELLS,
    GOAL_CENTRE_X,
    GOAL_LINE_Y,
    Pos,
    ROWS,
    cells_on_segment,
    corridor_x_at_depth,
    intercept_cell,
)

# Who yields when two defenders want the same cell (lower = keeps the cell)
_KIND_PRIORITY = {
    DefenderKind.GOALKEEPER: 0,
    DefenderKind.BLOCK: 1,
    DefenderKind.PRESSER: 2,
    DefenderKind.INTERCEPTOR: 3,  # keep the cut lane over Shadow
    DefenderKind.SHADOW: 4,
}


def lock_shadow_marks(defenders: list[Player], attackers: list[Player]) -> None:
    """Each Shadow locks onto one attacker and stays with them (sticky mark)."""
    for d in defenders:
        if d.kind != DefenderKind.SHADOW:
            continue
        if d.mark_id is not None and any(a.id == d.mark_id for a in attackers):
            continue
        nearest = min(attackers, key=lambda a: d.pos.chebyshev(a.pos))
        d.mark_id = nearest.id


def update_defenders(
    defenders: list[Player],
    attackers: list[Player],
    ball_pos: Pos,
    ball_holder_id: str,
    *,
    react: str = "full",
) -> list[str]:
    """Move all defenders without stacking on the same cell.

    react:
      "full" — everyone adjusts (after off-ball END_TURN / pass / lob).
      "ball" — Presser, GK, Interceptor, and ball-covering Blocks slide.
               Shadows hold (same as during an off-ball MOVE soft phase —
               they catch up on turn resolve with the mark→goal-side rule).
               Runner-Blocks hold so a carry cannot free-pull cover shape.
      "shadows" — only Shadows adjust (carry turn close after ball react;
                  same mark→goal-side step as on full / after MOVE+END).
    """
    logs: list[str] = []
    holder = next((a for a in attackers if a.id == ball_holder_id), None)
    ball_only = react == "ball"
    shadows_only = react == "shadows"

    desired: dict[str, Pos] = {}
    lanes: dict[str, list[Pos]] = {}
    for d in defenders:
        if shadows_only and d.kind != DefenderKind.SHADOW:
            desired[d.id] = d.pos
            continue
        # After a carry: Shadows wait until turn resolve (like after MOVE).
        # Runner-covering blocks hold; ball-covering blocks still slide.
        if ball_only and (
            d.kind == DefenderKind.SHADOW
            or (d.kind == DefenderKind.BLOCK and not d.block_hold_channel)
        ):
            desired[d.id] = d.pos
            continue
        want, lane = _compute_desired(d, attackers, ball_pos, holder)
        desired[d.id] = want
        if lane:
            lanes[d.id] = lane

    # Vacate-and-claim so two defenders never share a cell
    occupied: set[tuple[int, int]] = {(d.pos.x, d.pos.y) for d in defenders}
    # Nobody may land on an attacker or the ball carrier
    for a in attackers:
        occupied.add((a.pos.x, a.pos.y))
    ordered = sorted(
        defenders,
        key=lambda d: (
            _KIND_PRIORITY.get(d.kind, 9),  # type: ignore[arg-type]
            d.id,
        ),
    )

    for d in ordered:
        old = d.pos
        want = desired[d.id]
        occupied.discard((old.x, old.y))
        # Keep attacker cells reserved while this defender vacates
        land = _land_without_stack(
            d, old, want, occupied, prefer_lane=lanes.get(d.id)
        )
        d.pos = land
        occupied.add((land.x, land.y))

        if land != want and want != old:
            logs.append(
                f"{d.label} 改站 ({land.x},{land.y})"
                f"（原目標 {want.x},{want.y} 已被佔）"
            )
        elif d.kind == DefenderKind.PRESSER:
            logs.append(f"{d.label} 逼搶 → ({d.pos.x},{d.pos.y})")
        elif d.kind == DefenderKind.BLOCK:
            if land.y > old.y:
                logs.append(f"{d.label} 後退 → ({d.pos.x},{d.pos.y})")
            else:
                logs.append(f"{d.label} 橫移 → ({d.pos.x},{d.pos.y})")
        elif d.kind == DefenderKind.SHADOW:
            mark = next((a for a in attackers if a.id == d.mark_id), None)
            label = mark.label if mark else "?"
            logs.append(f"{d.label} 盯防 {label} → ({d.pos.x},{d.pos.y})")
        elif d.kind == DefenderKind.INTERCEPTOR:
            logs.append(f"{d.label} 卡位 → ({d.pos.x},{d.pos.y})")
        elif d.kind == DefenderKind.GOALKEEPER:
            logs.append(f"{d.label} 站位 → ({d.pos.x},{d.pos.y})")
        else:
            logs.append(f"{d.label} → ({d.pos.x},{d.pos.y})")

    return logs


def _compute_desired(
    d: Player,
    attackers: list[Player],
    ball_pos: Pos,
    holder: Player | None,
) -> tuple[Pos, list[Pos] | None]:
    if d.anchored:
        return d.pos, None

    if d.kind == DefenderKind.PRESSER:
        # Close hard, but never occupy the holder’s cell — pressure is adjacency,
        # not a free turnover on every idle END_TURN.
        want = d.pos.toward(ball_pos, steps=2)
        if want.y > ball_pos.y:
            want = Pos(want.x, ball_pos.y)
        if want == ball_pos:
            want = ball_pos.toward(d.pos, steps=1)
        return want, None

    if d.kind == DefenderKind.BLOCK:
        # Low-block: hold depth, slide onto ball→goal corridor at row mid-height.
        line_y = d.block_max_y if d.block_max_y is not None else d.pos.y
        goal = Pos(GOAL_CENTRE_X, GOAL_LINE_Y)
        target_x = corridor_x_at_depth(ball_pos, goal, line_y)
        return d.pos.toward(Pos(target_x, line_y), steps=1), None

    if d.kind == DefenderKind.SHADOW:
        mark = next((a for a in attackers if a.id == d.mark_id), None)
        if mark is None:
            mark = min(attackers, key=lambda a: d.pos.chebyshev(a.pos))
            d.mark_id = mark.id
        # Always cover the goal-side slot: one step from mark toward goal.
        # Never chase the mark's own cell (that puts you ball-side / level).
        between = _between_and_goal(mark.pos)
        if between.y >= GOAL_LINE_Y:
            between = Pos(between.x, GOAL_LINE_Y - 1)
        if between == mark.pos:
            # Mark already on the last line before goal — hold beside, goal-side.
            between = Pos(mark.pos.x, min(mark.pos.y + 1, GOAL_LINE_Y - 1))
            if between == mark.pos:
                between = mark.pos
        want = d.pos.toward(between, steps=1)
        # Do not step ball-side of the mark (lower y than the man).
        if want.y < mark.pos.y:
            dx = 0 if between.x == d.pos.x else (1 if between.x > d.pos.x else -1)
            want = Pos(d.pos.x + dx, min(d.pos.y + 1, GOAL_LINE_Y - 1)).clamp()
            if want == mark.pos or want.y < mark.pos.y:
                want = Pos(d.pos.x, min(d.pos.y + 1, GOAL_LINE_Y - 1)).clamp()
        if want.y >= GOAL_LINE_Y:
            want = Pos(want.x, GOAL_LINE_Y - 1)
        # Prefer re-landing along mark→goal if the slot is taken.
        goal = Pos(GOAL_CENTRE_X, GOAL_LINE_Y)
        lane = [
            p
            for p in cells_on_segment(mark.pos, goal)
            if p != mark.pos and p.y < GOAL_LINE_Y
        ]
        return want, lane or [between]

    if d.kind == DefenderKind.INTERCEPTOR:
        if holder is None:
            return d.pos, None
        teammates = [a for a in attackers if a.id != holder.id]
        if not teammates:
            return d.pos, None
        # Cut the most dangerous forward option (highest y), not the nearest support.
        danger = max(
            teammates,
            key=lambda a: (a.pos.y, -holder.pos.chebyshev(a.pos)),
        )
        path = cells_on_segment(holder.pos, danger.pos)
        lane = path[1:-1] if len(path) > 2 else path[1:] if len(path) > 1 else []
        cut = intercept_cell(holder.pos, danger.pos)
        # Eager: close two steps along the lane when far from the cut.
        steps = 2 if d.pos.chebyshev(cut) >= 2 else 1
        return d.pos.toward(cut, steps=steps), lane

    if d.kind == DefenderKind.GOALKEEPER:
        # Stay put until the ball enters the final third — otherwise long
        # build-up solutions drag the keeper onto the near post too early.
        if ball_pos.y < 4:
            return Pos(d.pos.x, GOAL_LINE_Y), None
        allowed = [Pos(x, y) for x, y in GOAL_CELLS]
        target_x = min(max(ball_pos.x, allowed[0].x), allowed[-1].x)
        xs = [p.x for p in allowed]
        pos = d.pos
        if pos.x not in xs:
            pos = allowed[len(allowed) // 2]
        if target_x > pos.x:
            return Pos(pos.x + 1, GOAL_LINE_Y), None
        if target_x < pos.x:
            return Pos(pos.x - 1, GOAL_LINE_Y), None
        return Pos(pos.x, GOAL_LINE_Y), None

    return d.pos, None


def _land_without_stack(
    d: Player,
    old: Pos,
    want: Pos,
    occupied: set[tuple[int, int]],
    *,
    prefer_lane: list[Pos] | None = None,
) -> Pos:
    """Prefer `want`; if taken, pick a free cell near it (GK stays in goal mouth)."""
    allowed: set[tuple[int, int]] | None = None
    if d.kind == DefenderKind.GOALKEEPER:
        allowed = set(GOAL_CELLS)
    if d.kind == DefenderKind.BLOCK:
        # Stay on the home depth line only (no drop band).
        line_y = d.block_max_y if d.block_max_y is not None else old.y
        allowed = {(x, line_y) for x in range(COLS)}

    def ok(p: Pos) -> bool:
        if not p.in_bounds():
            return False
        if (p.x, p.y) in occupied:
            return False
        # Only the keeper may stand in the goal mouth.
        if d.kind != DefenderKind.GOALKEEPER and (p.x, p.y) in GOAL_CELLS:
            return False
        if allowed is not None and (p.x, p.y) not in allowed:
            return False
        return True

    if ok(want):
        return want

    candidates: list[Pos] = []
    # Interceptor: stay on the pass lane if the midpoint is taken
    if prefer_lane:
        for p in prefer_lane:
            if p != want:
                candidates.append(p)
    step = old.toward(want, steps=1)
    if step != old:
        candidates.append(step)
    # Prefer same-depth / higher (toward goal) neighbors before dropping back
    ahead = [n for n in want.neighbors(1) if n.y >= want.y]
    behind = [n for n in want.neighbors(1) if n.y < want.y]
    candidates.extend(ahead)
    candidates.extend(behind)
    for n in old.neighbors(1):
        candidates.append(n)
    candidates.append(old)

    # Prefer: on-lane / closer to want / not dropping depth / closer to old
    def rank(p: Pos) -> tuple[int, int, int, int]:
        on_lane = 0 if prefer_lane and p in prefer_lane else 1
        drop = 0 if p.y >= want.y else 1
        return (on_lane, drop, p.chebyshev(want), p.chebyshev(old))

    seen: set[tuple[int, int]] = set()
    ordered_cands: list[Pos] = []
    for p in sorted(candidates, key=rank):
        key = (p.x, p.y)
        if key in seen:
            continue
        seen.add(key)
        ordered_cands.append(p)

    for p in ordered_cands:
        if ok(p):
            return p

    # Last resort: any free in-bounds cell (rare on 7×8)
    for y in range(ROWS):
        for x in range(COLS):
            p = Pos(x, y)
            if ok(p):
                return p
    return old


def _between_and_goal(mark: Pos) -> Pos:
    """Cell between mark and goal centre (one step goal-side of mark)."""
    goal = Pos(GOAL_CENTRE_X, GOAL_LINE_Y)
    return mark.toward(goal, steps=1)
