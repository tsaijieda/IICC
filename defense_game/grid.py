"""7×8 pitch helpers — short side (width 7) is the goal line.

Coordinates:
  x = 0 .. COLS-1  (left → right along the short side)
  y = 0 .. ROWS-1  (own half → goal along the long side)
Goal mouth sits on y = ROWS-1 (three central cells).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Iterator

COLS = 7  # short side = goal side
ROWS = 8  # depth toward goal

GOAL_CELLS: tuple[tuple[int, int], ...] = ((2, 7), (3, 7), (4, 7))
GOAL_LINE_Y = 7
GOAL_CENTRE_X = 3


@dataclass(frozen=True, slots=True)
class Pos:
    x: int
    y: int

    def __iter__(self) -> Iterator[int]:
        yield self.x
        yield self.y

    def clamp(self) -> Pos:
        return Pos(
            max(0, min(COLS - 1, self.x)),
            max(0, min(ROWS - 1, self.y)),
        )

    def in_bounds(self) -> bool:
        return 0 <= self.x < COLS and 0 <= self.y < ROWS

    def chebyshev(self, other: Pos) -> int:
        return max(abs(self.x - other.x), abs(self.y - other.y))

    def manhattan(self, other: Pos) -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def toward(self, target: Pos, steps: int = 1) -> Pos:
        """Move up to `steps` cells toward target (8-directional)."""
        x, y = self.x, self.y
        for _ in range(steps):
            dx = 0 if target.x == x else (1 if target.x > x else -1)
            dy = 0 if target.y == y else (1 if target.y > y else -1)
            if dx == 0 and dy == 0:
                break
            x, y = x + dx, y + dy
        return Pos(x, y).clamp()

    def neighbors(self, steps: int = 1) -> list[Pos]:
        out: list[Pos] = []
        for dx in range(-steps, steps + 1):
            for dy in range(-steps, steps + 1):
                if dx == 0 and dy == 0:
                    continue
                if max(abs(dx), abs(dy)) > steps:
                    continue
                p = Pos(self.x + dx, self.y + dy)
                if p.in_bounds():
                    out.append(p)
        return out

    def as_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)


def cells_on_segment(a: Pos, b: Pos) -> list[Pos]:
    """Cells whose squares are crossed by the center-to-center line a→b.

    Uses Amanatides & Woo grid traversal from (ax+½, ay+½) to (bx+½, by+½).
    Exact corner hits step diagonally only (adjacent cells are corner-touched,
    not entered), so blocking matches the visual shot/pass ray.
    """
    if a == b:
        return [a]

    x0 = a.x + 0.5
    y0 = a.y + 0.5
    x1 = b.x + 0.5
    y1 = b.y + 0.5
    dx = x1 - x0
    dy = y1 - y0

    cx, cy = a.x, a.y
    step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
    step_y = 0 if dy == 0 else (1 if dy > 0 else -1)

    # t = distance along the segment in [0, 1]. Next vertical / horizontal
    # grid plane crossings, and how far in t between consecutive planes.
    if step_x == 0:
        t_max_x = float("inf")
        t_delta_x = float("inf")
    else:
        next_vx = (cx + 1) if step_x > 0 else cx
        t_max_x = (next_vx - x0) / dx
        t_delta_x = abs(1.0 / dx)

    if step_y == 0:
        t_max_y = float("inf")
        t_delta_y = float("inf")
    else:
        next_hy = (cy + 1) if step_y > 0 else cy
        t_max_y = (next_hy - y0) / dy
        t_delta_y = abs(1.0 / dy)

    cells: list[Pos] = [Pos(cx, cy)]
    # Guard against float drift; segment ends at t=1 in the target cell.
    for _ in range(COLS + ROWS + 2):
        if cx == b.x and cy == b.y:
            break
        if t_max_x < t_max_y:
            t_max_x += t_delta_x
            cx += step_x
        elif t_max_y < t_max_x:
            t_max_y += t_delta_y
            cy += step_y
        else:
            # Exact corner: enter the diagonal cell only.
            t_max_x += t_delta_x
            t_max_y += t_delta_y
            cx += step_x
            cy += step_y
        cells.append(Pos(cx, cy))
    else:
        raise RuntimeError(f"cells_on_segment failed to reach {b} from {a}")

    return cells


def corridor_x_at_depth(ball: Pos, goal: Pos, line_y: int) -> int:
    """Column on ``line_y`` where ball-centre→goal-centre crosses row mid-height.

    Continuous geometry: centres ``(*.5, *.5)`` intersect ``y = line_y + 0.5``.
    That avoids diagonal grid-walk artefacts (a ray that only grazes a cell edge
    is not treated as occupying that cell).

    When the hit lands exactly on a vertical grid line, pick the column toward
    the goal — the side the shot continues into.
    """
    if goal.y == ball.y:
        return max(0, min(COLS - 1, ball.x))

    bx, by = ball.x + 0.5, ball.y + 0.5
    gx, gy = goal.x + 0.5, goal.y + 0.5
    t = ((line_y + 0.5) - by) / (gy - by)
    x = bx + t * (gx - bx)

    grid_line = round(x)
    if abs(x - grid_line) < 1e-9:
        if goal.x < ball.x:
            cell = int(grid_line) - 1
        elif goal.x > ball.x:
            cell = int(grid_line)
        else:
            cell = ball.x
    else:
        cell = math.floor(x)

    return max(0, min(COLS - 1, cell))


def intercept_cell(carrier: Pos, receiver: Pos) -> Pos:
    """Best cell that cuts the pass lane (midpoint of the segment)."""
    path = cells_on_segment(carrier, receiver)
    if len(path) <= 2:
        return carrier.toward(receiver, 1)
    return path[len(path) // 2]


def occupied_set(positions: Iterable[Pos]) -> set[tuple[int, int]]:
    return {(p.x, p.y) for p in positions}
