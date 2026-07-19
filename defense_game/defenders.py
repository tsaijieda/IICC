"""Defender AI — one update per turn end."""

from __future__ import annotations

from .entities import DefenderKind, Player
from .grid import (
    COLS,
    GOAL_CELLS,
    GOAL_CENTRE_X,
    GOAL_LINE_Y,
    Pos,
    cells_on_segment,
    corridor_x_at_depth,
    intercept_cell,
)

# Who claims first when two defenders want the same cell (lower = claims first)
_KIND_PRIORITY = {
    DefenderKind.GOALKEEPER: 0,
    DefenderKind.BLOCK: 1,
    DefenderKind.PRESSER: 2,
    DefenderKind.INTERCEPTOR: 3,  # keep the cut lane over Shadow
    DefenderKind.SHADOW: 4,
}

_ROLE_MAX_STEPS = {
    DefenderKind.GOALKEEPER: 1,
    DefenderKind.BLOCK: 1,
    DefenderKind.PRESSER: 2,
    DefenderKind.INTERCEPTOR: 2,
    DefenderKind.SHADOW: 1,
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

    Conflict resolution (hard rules):
      1. Compute each defender's preferred cell and this-react step budget.
      2. All non-anchored defenders vacate at once; anchored cells stay reserved.
      3. Claim in priority order: GK → Block → Presser → Interceptor → Shadow;
         same kind sorted by id.
      4. Land on preferred cell if free and legal; else best free cell within
         that defender's step budget and role zone; else stay if still free.
      5. Never teleport outside the step budget to resolve a stack.

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
    budgets: dict[str, int] = {}
    for d in defenders:
        if shadows_only and d.kind != DefenderKind.SHADOW:
            desired[d.id] = d.pos
            budgets[d.id] = 0
            continue
        # After a carry: Shadows wait until turn resolve (like after MOVE).
        # Runner-covering blocks hold; ball-covering blocks still slide.
        if ball_only and (
            d.kind == DefenderKind.SHADOW
            or (d.kind == DefenderKind.BLOCK and not d.block_hold_channel)
        ):
            desired[d.id] = d.pos
            budgets[d.id] = 0
            continue
        want, lane, steps = _compute_desired(d, attackers, ball_pos, holder)
        desired[d.id] = want
        budgets[d.id] = steps
        if lane:
            lanes[d.id] = lane

    # Phase 1: vacate every non-anchored defender. Attackers + anchored stay reserved.
    occupied: set[tuple[int, int]] = {(a.pos.x, a.pos.y) for a in attackers}
    for d in defenders:
        if d.anchored:
            occupied.add((d.pos.x, d.pos.y))

    ordered = sorted(
        defenders,
        key=lambda d: (
            _KIND_PRIORITY.get(d.kind, 9),  # type: ignore[arg-type]
            d.id,
        ),
    )

    # Phase 2: claim in priority order (later movers may take cells earlier ones left).
    for d in ordered:
        old = d.pos
        want = desired[d.id]
        if d.anchored:
            land = old
        else:
            land = _land_without_stack(
                d,
                old,
                want,
                occupied,
                max_steps=budgets[d.id],
                prefer_lane=lanes.get(d.id),
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
) -> tuple[Pos, list[Pos] | None, int]:
    """Return (preferred cell, optional prefer-lane, max steps this react)."""
    if d.anchored:
        return d.pos, None, 0

    if d.kind == DefenderKind.PRESSER:
        # Close hard, but never occupy the holder’s cell — pressure is adjacency,
        # not a free turnover on every idle END_TURN.
        want = d.pos.toward(ball_pos, steps=2)
        if want.y > ball_pos.y:
            want = Pos(want.x, ball_pos.y)
        if want == ball_pos:
            want = ball_pos.toward(d.pos, steps=1)
        return want, None, 2

    if d.kind == DefenderKind.BLOCK:
        # Low-block: hold depth, slide onto ball→goal corridor at row mid-height.
        line_y = d.block_max_y if d.block_max_y is not None else d.pos.y
        goal = Pos(GOAL_CENTRE_X, GOAL_LINE_Y)
        target_x = corridor_x_at_depth(ball_pos, goal, line_y)
        return d.pos.toward(Pos(target_x, line_y), steps=1), None, 1

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
        return want, lane or [between], 1

    if d.kind == DefenderKind.INTERCEPTOR:
        if holder is None:
            return d.pos, None, 0
        teammates = [a for a in attackers if a.id != holder.id]
        if not teammates:
            return d.pos, None, 0
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
        return d.pos.toward(cut, steps=steps), lane, steps

    if d.kind == DefenderKind.GOALKEEPER:
        # Always track the ball's column — slide 1 step toward it every react,
        # no matter how far out the ball is.
        allowed = [Pos(x, y) for x, y in GOAL_CELLS]
        target_x = min(max(ball_pos.x, allowed[0].x), allowed[-1].x)
        xs = [p.x for p in allowed]
        pos = d.pos
        if pos.x not in xs:
            pos = allowed[len(allowed) // 2]
        if target_x > pos.x:
            return Pos(pos.x + 1, GOAL_LINE_Y), None, 1
        if target_x < pos.x:
            return Pos(pos.x - 1, GOAL_LINE_Y), None, 1
        return Pos(pos.x, GOAL_LINE_Y), None, 1

    return d.pos, None, 0


def _role_zone(d: Player, old: Pos) -> set[tuple[int, int]] | None:
    """Cells this role may occupy. None = any in-bounds non-goal cell."""
    if d.kind == DefenderKind.GOALKEEPER:
        return set(GOAL_CELLS)
    if d.kind == DefenderKind.BLOCK:
        line_y = d.block_max_y if d.block_max_y is not None else old.y
        return {(x, line_y) for x in range(COLS)}
    return None


def _land_without_stack(
    d: Player,
    old: Pos,
    want: Pos,
    occupied: set[tuple[int, int]],
    *,
    max_steps: int,
    prefer_lane: list[Pos] | None = None,
) -> Pos:
    """Prefer `want`; if taken, pick best free cell within step budget + role zone."""
    zone = _role_zone(d, old)
    budget = max(0, max_steps)
    if d.kind is not None:
        budget = min(budget, _ROLE_MAX_STEPS.get(d.kind, budget))

    def legal(p: Pos) -> bool:
        if not p.in_bounds():
            return False
        if old.chebyshev(p) > budget:
            return False
        if zone is not None and (p.x, p.y) not in zone:
            return False
        # Only the keeper may stand in the goal mouth.
        if d.kind != DefenderKind.GOALKEEPER and (p.x, p.y) in GOAL_CELLS:
            return False
        return True

    def free(p: Pos) -> bool:
        return legal(p) and (p.x, p.y) not in occupied

    if free(want):
        return want

    lane_set = {p for p in (prefer_lane or []) if legal(p)}

    candidates: list[Pos] = []
    for dy in range(-budget, budget + 1):
        for dx in range(-budget, budget + 1):
            if max(abs(dx), abs(dy)) > budget:
                continue
            p = Pos(old.x + dx, old.y + dy)
            if free(p):
                candidates.append(p)

    if not candidates:
        # After a full vacate this should only happen if old is still free.
        if free(old):
            return old
        raise RuntimeError(
            f"defender {d.id} has no legal free cell within {budget} steps "
            f"of {old} (want {want}); refuse teleport/stack"
        )

    def rank(p: Pos) -> tuple[int, int, int, int, int, int]:
        # 1) prefer role lane / preferred corridor
        on_lane = 0 if p in lane_set else 1
        # 2) closer to preferred target
        dist_want = p.chebyshev(want)
        # 3) prefer not dropping away from target depth
        drop = 0 if p.y >= want.y else 1
        # 4) closer to origin (smaller move)
        dist_old = p.chebyshev(old)
        # 5) prefer deeper (larger y), then smaller x — full determinism
        return (on_lane, dist_want, drop, dist_old, -p.y, p.x)

    return min(candidates, key=rank)


def _between_and_goal(mark: Pos) -> Pos:
    """Cell between mark and goal centre (one step goal-side of mark)."""
    goal = Pos(GOAL_CENTRE_X, GOAL_LINE_Y)
    return mark.toward(goal, steps=1)
