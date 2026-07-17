"""Players and defender kinds."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .grid import Pos


class Side(str, Enum):
    ATTACK = "attack"
    DEFENSE = "defense"


class DefenderKind(str, Enum):
    PRESSER = "presser"  # 瘋狗逼搶員 — 只逼搶，不擋射／不截傳
    BLOCK = "block"  # 區域大閘 — 擋射門走廊，不跳傳切線
    SHADOW = "shadow"  # 影子盯人 — 只擋「自己盯的人」的射門
    INTERCEPTOR = "interceptor"  # 路線攔截 — 截地滾；站在射門線上也擋射
    GOALKEEPER = "goalkeeper"  # 守門員 — 球門線撲救


# Short copy for UI / tooltips — what each role uniquely does.
ROLE_BLURB: dict[DefenderKind, str] = {
    DefenderKind.PRESSER: "朝持球者猛衝 2 格；已貼身時硬盤／拖時間會被斷——用傳球甩掉。站在射門線上也擋射。",
    DefenderKind.BLOCK: "卡球→門走廊，只沿橫線橫移；地滾可穿過——要拉邊再倒三角。站在射門線上擋射。",
    DefenderKind.SHADOW: "黏一名進攻者；回合結束／傳球後朝「人與球門之間」走 1 格，卡在門側跟著，不站到人前面（遠離球門那一側）。站在射門線上擋射。",
    DefenderKind.INTERCEPTOR: "卡地滾傳切；站在射門線上擋射——拉開角度或高空過頂。",
    DefenderKind.GOALKEEPER: "球門線橫移撲救——打他另一邊門柱。",
}


@dataclass
class Player:
    id: str
    label: str
    side: Side
    pos: Pos
    kind: DefenderKind | None = None  # only for defenders
    # Shadow: locked target attacker id (set at turn start)
    mark_id: str | None = None
    # Block: holding-line y — never advances past this depth
    block_max_y: int | None = None
    # Unused legacy fields (kept for save compatibility)
    block_home_x: int | None = None
    block_hold_channel: bool = False
    anchored: bool = False

    def copy(self) -> Player:
        return Player(
            id=self.id,
            label=self.label,
            side=self.side,
            pos=Pos(self.pos.x, self.pos.y),
            kind=self.kind,
            mark_id=self.mark_id,
            block_max_y=self.block_max_y,
            block_home_x=self.block_home_x,
            block_hold_channel=self.block_hold_channel,
            anchored=self.anchored,
        )


@dataclass
class Puzzle:
    """One defending lesson.

    Prefer teaching with the defensive picture (roles + AI) while keeping the
    full attacking toolkit. `allow_*` remains available for rare hard locks.
    """

    id: str
    title: str
    description: str
    tip: str
    attackers: list[Player]
    defenders: list[Player]
    ball_holder_id: str
    category: str = "tactical"
    max_turns: int = 10
    allow_dribble: bool = True
    allow_pass: bool = True
    allow_lob: bool = True
    allow_move: bool = True

    def all_players(self) -> list[Player]:
        return [*self.attackers, *self.defenders]

    def tools(self) -> dict[str, bool]:
        return {
            "dribble": self.allow_dribble,
            "pass": self.allow_pass,
            "lob": self.allow_lob,
            "move": self.allow_move,
            "shoot": True,
            "end": True,
        }
