"""Core turn loop: actions → resolve → defender update → score checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .defenders import lock_shadow_marks, update_defenders
from .entities import DefenderKind, Player, Puzzle, ROLE_BLURB
from .grid import (
    COLS,
    GOAL_CELLS,
    GOAL_CENTRE_X,
    MIN_SHOOT_Y,
    Pos,
    ROWS,
    cells_on_segment,
)


class ActionType(str, Enum):
    MOVE = "move"  # attacker relocates 1 cell (may batch in one turn)
    DRIBBLE = "dribble"  # ball carrier advances 1 cell with ball
    PASS = "pass"  # ground pass — blocked if defender on path
    LOB = "lob"  # high / lofted pass — flies over ground defenders
    SHOOT = "shoot"  # attempt at goal from current cell
    END_TURN = "end"  # finish movement phase → defenders react


@dataclass
class Action:
    type: ActionType
    # MOVE / DRIBBLE: destination; PASS/LOB: receiver via target_id; SHOOT: optional aim
    dest: Pos | None = None
    target_id: str | None = None
    actor_id: str | None = None


@dataclass
class TurnResult:
    ok: bool
    message: str
    goal: bool = False
    turnover: bool = False
    saved: bool = False
    pending: bool = False  # True = still same turn (more moves allowed)
    logs: list[str] = field(default_factory=list)


class DefenseGame:
    def __init__(self, puzzle: Puzzle):
        self.puzzle = puzzle
        self.attackers = [p.copy() for p in puzzle.attackers]
        self.defenders = [p.copy() for p in puzzle.defenders]
        self.ball_holder_id = puzzle.ball_holder_id
        self.turn = 0
        self.max_turns = puzzle.max_turns
        self.finished = False
        self.won = False
        self.history: list[str] = []
        self.last_result: TurnResult | None = None
        self.moved_ids: set[str] = set()
        # After a carry: same turn may only pass/lob/end — no shoot / re-dribble / run.
        self.after_carry: bool = False
        lock_shadow_marks(self.defenders, self.attackers)

    def attacker(self, pid: str) -> Player:
        return next(p for p in self.attackers if p.id == pid)

    def player_at(self, pos: Pos) -> Player | None:
        for p in (*self.attackers, *self.defenders):
            if p.pos == pos:
                return p
        return None

    @property
    def ball_pos(self) -> Pos:
        return self.attacker(self.ball_holder_id).pos

    @property
    def score(self) -> int:
        if not self.won:
            return 0
        return max(1, 11 - self.turn)

    def to_dict(self) -> dict:
        """JSON-serialisable snapshot for the web UI."""
        return {
            "puzzle": {
                "id": self.puzzle.id,
                "title": self.puzzle.title,
                "description": self.puzzle.description,
                "tip": self.puzzle.tip,
                "tools": self.puzzle.tools(),
            },
            "cols": COLS,
            "rows": ROWS,
            "goal_cells": [list(c) for c in GOAL_CELLS],
            "min_shoot_y": MIN_SHOOT_Y,
            "turn": self.turn,
            "max_turns": self.max_turns,
            "ball_holder_id": self.ball_holder_id,
            "finished": self.finished,
            "won": self.won,
            "score": self.score,
            "attackers": [
                {
                    "id": a.id,
                    "label": a.label,
                    "x": a.pos.x,
                    "y": a.pos.y,
                    "has_ball": a.id == self.ball_holder_id,
                    "moved": a.id in self.moved_ids,
                }
                for a in self.attackers
            ],
            "defenders": [
                {
                    "id": d.id,
                    "label": d.label,
                    "x": d.pos.x,
                    "y": d.pos.y,
                    "kind": d.kind.value if d.kind else None,
                    "blurb": ROLE_BLURB.get(d.kind, "") if d.kind else "",
                    "mark_id": d.mark_id,
                }
                for d in self.defenders
            ],
            "moved_ids": sorted(self.moved_ids),
            "after_carry": self.after_carry,
            "last_logs": self.last_result.logs if self.last_result else [],
            "last_message": self.last_result.message if self.last_result else "",
        }

    def render(self) -> str:
        grid = [["·" for _ in range(COLS)] for _ in range(ROWS)]
        for x, y in GOAL_CELLS:
            grid[y][x] = "⌂"

        marks: dict[tuple[int, int], str] = {}
        for a in self.attackers:
            ch = "●" if a.id == self.ball_holder_id else "○"
            marks[(a.pos.x, a.pos.y)] = ch
        kind_glyph = {
            DefenderKind.PRESSER: "P",
            DefenderKind.BLOCK: "B",
            DefenderKind.SHADOW: "S",
            DefenderKind.INTERCEPTOR: "I",
            DefenderKind.GOALKEEPER: "G",
        }
        for d in self.defenders:
            marks[(d.pos.x, d.pos.y)] = kind_glyph.get(d.kind, "D")  # type: ignore[arg-type]

        for (x, y), ch in marks.items():
            grid[y][x] = ch

        lines = [f"  {' '.join(str(c) for c in range(COLS))}  ← short side / goal"]
        for y in range(ROWS - 1, -1, -1):
            tag = " GOAL" if y == ROWS - 1 else ""
            lines.append(f"{y} {' '.join(grid[y])}{tag}")
        lines.append(
            f"turn {self.turn}/{self.max_turns}  ball@{self.ball_holder_id} "
            f"({self.ball_pos.x},{self.ball_pos.y})"
        )
        return "\n".join(lines)

    def roster(self) -> str:
        rows = ["Attackers:"]
        for a in self.attackers:
            ball = " ★" if a.id == self.ball_holder_id else ""
            rows.append(f"  {a.id} {a.label} @({a.pos.x},{a.pos.y}){ball}")
        rows.append("Defenders:")
        for d in self.defenders:
            extra = f" mark={d.mark_id}" if d.kind == DefenderKind.SHADOW else ""
            rows.append(
                f"  {d.id} {d.label} [{d.kind.value if d.kind else '?'}] "
                f"@({d.pos.x},{d.pos.y}){extra}"
            )
        return "\n".join(rows)

    def apply(self, action: Action) -> TurnResult:
        if self.finished:
            return TurnResult(False, "Game already finished.")

        if self.turn >= self.max_turns:
            self.finished = True
            return TurnResult(False, "Out of turns.", turnover=True)

        logs: list[str] = []
        # Snapshot before the action: already marked = must pass to escape.
        under_press = any(
            d.kind == DefenderKind.PRESSER
            and d.pos.chebyshev(self.ball_pos) <= 1
            for d in self.defenders
        )

        try:
            if action.type == ActionType.END_TURN:
                logs.append("結束進攻階段")
                return self._resolve_end_of_turn(
                    logs, react="full", press_linger=under_press
                )

            # After a carry: no shoot / re-dribble same turn. Off-ball runs OK.
            if self.after_carry:
                if action.type == ActionType.SHOOT:
                    raise ValueError(
                        "盤帶後不能直接射門——可繼續跑位、傳球，或結束回合後再射。"
                    )
                if action.type == ActionType.DRIBBLE:
                    raise ValueError("本回合已盤帶——先傳球、跑位或結束回合。")
                if action.type == ActionType.MOVE:
                    actor_id = action.actor_id or action.target_id
                    if actor_id == self.ball_holder_id:
                        raise ValueError(
                            "本回合已盤帶——不能再帶球；可移動其他球員或傳球。"
                        )
            if action.type == ActionType.DRIBBLE:
                if any(pid != self.ball_holder_id for pid in self.moved_ids):
                    raise ValueError(
                        "本回合已做無球跑動——先結束回合，再盤帶。"
                    )
            if action.type == ActionType.SHOOT and self.moved_ids:
                raise ValueError(
                    "本回合已做無球跑動——不能直接射門；可傳球，或結束回合讓防守跟上後再射。"
                )

            pass_from: str | None = None
            pass_to: str | None = None
            if action.type == ActionType.MOVE:
                result = self._do_move(action, logs)
            elif action.type == ActionType.DRIBBLE:
                result = self._do_dribble(action, logs)
            elif action.type in (ActionType.PASS, ActionType.LOB):
                result = self._do_pass(action, logs, lofted=action.type == ActionType.LOB)
            elif action.type == ActionType.SHOOT:
                result = self._do_shoot(action, logs)
            else:
                return TurnResult(False, f"Unknown action {action.type}")
        except ValueError as e:
            return TurnResult(False, str(e))

        if not result.ok:
            self.last_result = result
            return result

        logs = result.logs or logs

        # Soft phase: only off-ball MOVE stays in the same turn.
        if action.type == ActionType.MOVE and not result.turnover:
            actor_id = action.actor_id or action.target_id
            assert actor_id is not None
            # MOVE on the ball carrier is a carry — same rules as DRIBBLE.
            if actor_id == self.ball_holder_id:
                return self._soft_after_carry(logs, press_linger=under_press)
            self.moved_ids.add(actor_id)
            left = [a.id for a in self.attackers if a.id not in self.moved_ids]
            msg = (
                f"已移動 {actor_id}（還可動：{', '.join(left) or '無'}）。"
                + (
                    "可繼續跑位或傳球；不能射門／再盤帶。"
                    if self.after_carry
                    else "可繼續跑位或傳球；不能盤帶／射門——先結束回合讓防守跟上。"
                )
            )
            result = TurnResult(True, msg, pending=True, logs=logs)
            self.last_result = result
            self.history.extend(logs)
            return result

        # Carry soft phase: no defender move yet (same as off-ball MOVE);
        # shoot locked until pass/end.
        if action.type == ActionType.DRIBBLE and not result.turnover:
            return self._soft_after_carry(logs, press_linger=under_press)

        # Escape passes beat the press; lingering / pressed shot does not.
        press_linger = under_press and action.type in (
            ActionType.END_TURN,
            ActionType.SHOOT,
        )
        return self._resolve_end_of_turn(
            logs, prior=result, react="full", press_linger=press_linger
        )

    def _soft_after_carry(
        self, logs: list[str], *, press_linger: bool
    ) -> TurnResult:
        """After a dribble: turn stays open; defenders wait for pass/end (like MOVE)."""
        # Immediate press-adjacent turnover still applies if already marked.
        if self._check_turnover(logs, press_linger=press_linger):
            self.turn += 1
            self.finished = True
            self.won = False
            self.moved_ids.clear()
            self.after_carry = False
            self.history.extend(logs)
            result = TurnResult(True, "斷球！失去球權。", turnover=True, logs=logs)
            self.last_result = result
            return result

        self.after_carry = True
        self.moved_ids.clear()  # carry replaces prior run soft-phase
        msg = (
            "已盤帶；防守者尚未移動——結束回合或傳球後才跟上（與無球跑位相同）。"
            "可繼續移動其他球員或傳球——不能射門／再盤帶。"
        )
        result = TurnResult(True, msg, pending=True, logs=logs)
        self.last_result = result
        self.history.extend(logs)
        return result

    def _resolve_end_of_turn(
        self,
        logs: list[str],
        prior: TurnResult | None = None,
        *,
        react: str = "full",
        press_linger: bool = False,
    ) -> TurnResult:
        """Defenders react, then advance the turn counter.

        react="full" after END_TURN / pass / lob (including after a dribble soft phase).
        """
        if prior and prior.goal:
            self.turn += 1
            self.finished = True
            self.won = True
            self.moved_ids.clear()
            self.after_carry = False
            self.history.extend(logs)
            result = TurnResult(
                True,
                f"GOAL！{self.turn} 回合得分 — {self.score}/10 分",
                goal=True,
                logs=logs,
            )
            self.last_result = result
            return result

        if prior and prior.turnover:
            self.turn += 1
            self.finished = True
            self.won = False
            self.moved_ids.clear()
            self.after_carry = False
            self.history.extend(logs)
            result = TurnResult(True, "斷球！失去球權。", turnover=True, logs=logs)
            self.last_result = result
            return result

        lock_shadow_marks(self.defenders, self.attackers)
        dlogs = update_defenders(
            self.defenders,
            self.attackers,
            self.ball_pos,
            self.ball_holder_id,
            react=react,
        )
        logs.extend(dlogs)
        if self._check_turnover(logs, press_linger=press_linger):
            self.turn += 1
            self.finished = True
            self.won = False
            self.moved_ids.clear()
            self.after_carry = False
            self.history.extend(logs)
            result = TurnResult(True, "斷球！失去球權。", turnover=True, logs=logs)
            self.last_result = result
            return result

        self.turn += 1
        self.moved_ids.clear()
        self.after_carry = False
        lock_shadow_marks(self.defenders, self.attackers)
        self.history.extend(logs)

        if self.turn >= self.max_turns:
            self.finished = True
            result = TurnResult(
                True, "回合用盡 — 挑戰失敗。", turnover=True, logs=logs
            )
            self.last_result = result
            return result

        result = TurnResult(True, "回合結束 — 防守者已移動", logs=logs)
        self.last_result = result
        return result

    def _do_move(self, action: Action, logs: list[str]) -> TurnResult:
        actor_id = action.actor_id or action.target_id
        if actor_id is None or action.dest is None:
            raise ValueError("MOVE needs actor_id and dest.")
        if actor_id in self.moved_ids:
            raise ValueError(f"{actor_id} 本回合已經移動過了。")
        if actor_id == self.ball_holder_id:
            return self._do_dribble(
                Action(ActionType.DRIBBLE, dest=action.dest), logs
            )
        if not self.puzzle.allow_move:
            raise ValueError("本關無球跑動被鎖死——換別的辦法創造空間。")
        actor = self.attacker(actor_id)
        if actor.pos.chebyshev(action.dest) != 1 or not action.dest.in_bounds():
            raise ValueError("移動必須剛好 1 格（含斜向）。")
        if self._occupied_by_teammate(action.dest, ignore_id=actor_id):
            raise ValueError("目標格已被隊友佔用。")
        if self._occupied_by_defender(action.dest):
            raise ValueError("目標格有防守者，不能站上去。")
        actor.pos = action.dest
        logs.append(f"{actor.label} 移動 → ({actor.pos.x},{actor.pos.y})")
        return TurnResult(True, "moved", logs=logs)

    def _do_dribble(self, action: Action, logs: list[str]) -> TurnResult:
        if not self.puzzle.allow_dribble:
            raise ValueError("本關持球空間被鎖——無法盤帶，改用傳球或無球拉扯。")
        if action.dest is None:
            raise ValueError("DRIBBLE needs dest.")
        carrier = self.attacker(self.ball_holder_id)
        if carrier.id in self.moved_ids:
            raise ValueError(f"{carrier.id} 本回合已經移動過了。")
        if carrier.pos.chebyshev(action.dest) != 1 or not action.dest.in_bounds():
            raise ValueError("盤帶必須剛好 1 格（含斜向）。")
        if self._occupied_by_teammate(action.dest, ignore_id=carrier.id):
            raise ValueError("目標格已被隊友佔用。")
        for d in self.defenders:
            if d.pos == action.dest:
                carrier.pos = action.dest
                logs.append(f"{carrier.label} 帶球撞上 {d.label} — 被斷！")
                return TurnResult(True, "tackled", turnover=True, logs=logs)
        carrier.pos = action.dest
        logs.append(f"{carrier.label} 盤帶 → ({carrier.pos.x},{carrier.pos.y})")
        return TurnResult(True, "dribbled", logs=logs)

    def _do_pass(
        self, action: Action, logs: list[str], *, lofted: bool
    ) -> TurnResult:
        if lofted and not self.puzzle.allow_lob:
            raise ValueError("本關無法打高空球——地面傳切或盤帶另想辦法。")
        if not lofted and not self.puzzle.allow_pass:
            raise ValueError("本關地滾線路被鎖——改高空或盤帶。")
        if action.target_id is None:
            raise ValueError("傳球需要指定接球隊友。")
        if action.target_id == self.ball_holder_id:
            raise ValueError("不能傳給自己。")
        carrier = self.attacker(self.ball_holder_id)
        receiver = self.attacker(action.target_id)
        path = cells_on_segment(carrier.pos, receiver.pos)

        kind = "高空傳球" if lofted else "地滾傳球"
        if not lofted:
            for cell in path[1:-1]:
                for d in self.defenders:
                    if d.pos == cell and self._intercepts_pass(d):
                        logs.append(
                            f"{kind} {carrier.label}→{receiver.label} "
                            f"被 {d.label} 在 ({cell.x},{cell.y}) 攔截！"
                        )
                        return TurnResult(
                            True, "intercepted", turnover=True, logs=logs
                        )

        if action.dest is not None:
            if carrier.pos.chebyshev(action.dest) != 1 or not action.dest.in_bounds():
                raise ValueError("撞牆後插上必須剛好 1 格。")
            if self._occupied_by_teammate(action.dest, ignore_id=carrier.id):
                raise ValueError("插上目標格已被隊友佔用。")
            if self._occupied_by_defender(action.dest):
                raise ValueError("插上目標格有防守者。")
            carrier.pos = action.dest
            logs.append(
                f"{kind} {carrier.label}→{receiver.label}，"
                f"{carrier.label} 插上 → ({carrier.pos.x},{carrier.pos.y})"
            )
        else:
            via = "飛越防線" if lofted else "沿地面"
            logs.append(
                f"{kind}（{via}）{carrier.label}→{receiver.label} "
                f"({carrier.pos.x},{carrier.pos.y})→({receiver.pos.x},{receiver.pos.y})"
            )
        self.ball_holder_id = receiver.id
        return TurnResult(True, "passed", logs=logs)

    def _do_shoot(self, action: Action, logs: list[str]) -> TurnResult:
        carrier = self.attacker(self.ball_holder_id)
        if carrier.pos.y < MIN_SHOOT_Y:
            raise ValueError(
                f"距離太遠——至少推進到 y≥{MIN_SHOOT_Y}（前場）才能射門。"
            )
        if action.dest is not None:
            if (action.dest.x, action.dest.y) not in GOAL_CELLS:
                raise ValueError("射門目標必須是球門三格之一。")
            target = action.dest
        else:
            target = min(
                (Pos(x, y) for x, y in GOAL_CELLS),
                key=lambda g: carrier.pos.chebyshev(g),
            )

        path = cells_on_segment(carrier.pos, target)
        logs.append(f"{carrier.label} 射門 → 球門 ({target.x},{target.y})")
        for cell in path[1:]:
            # Other goal-mouth cells are not "in front of" the aimed post —
            # only field cells and the exact target can block/save.
            if cell != target and (cell.x, cell.y) in GOAL_CELLS:
                continue
            for a in self.attackers:
                if a.pos == cell and a.id != carrier.id:
                    logs.append(
                        f"射門路線上有 {a.label} — 被擋下！"
                    )
                    return TurnResult(True, "blocked", turnover=True, logs=logs)
            for d in self.defenders:
                if d.pos != cell:
                    continue
                if d.kind == DefenderKind.GOALKEEPER:
                    logs.append(f"被 {d.label} 撲出！")
                    return TurnResult(
                        True, "saved", saved=True, turnover=True, logs=logs
                    )
                logs.append(f"被 {d.label} 擋下！")
                return TurnResult(True, "blocked", turnover=True, logs=logs)

        logs.append("進球！")
        return TurnResult(True, "goal", goal=True, logs=logs)

    def _occupied_by_teammate(self, dest: Pos, ignore_id: str) -> bool:
        return any(p.id != ignore_id and p.pos == dest for p in self.attackers)

    def _occupied_by_defender(self, dest: Pos) -> bool:
        return any(d.pos == dest for d in self.defenders)

    def _intercepts_pass(self, d: Player) -> bool:
        """Any defender standing on a ground-pass mid-path cell cuts the lane."""
        return d.kind is not None

    def _blocked(self, dest: Pos, ignore_id: str) -> bool:
        return self._occupied_by_teammate(
            dest, ignore_id
        ) or self._occupied_by_defender(dest)

    def _check_turnover(
        self, logs: list[str], *, press_linger: bool = False
    ) -> bool:
        ball = self.ball_pos
        for d in self.defenders:
            if d.pos == ball:
                logs.append(f"{d.label} 在 ({ball.x},{ball.y}) 搶下球權！")
                return True
            # Already marked at action start + still touching after react
            # (END / dribble / pressed shot). Arrival after an escape pass
            # does not strip on the same beat.
            if (
                press_linger
                and d.kind == DefenderKind.PRESSER
                and d.pos.chebyshev(ball) <= 1
            ):
                logs.append(
                    f"{d.label} 貼身逼搶！在 ({d.pos.x},{d.pos.y}) 斷下球權。"
                )
                return True
        return False
