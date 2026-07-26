"""Data models for tactical-board → 戰術語言 translation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scoring import ScoringResult


@dataclass(slots=True)
class PlayerSnapshot:
    player_id: str
    role: str
    zone: int


@dataclass(slots=True)
class TouchFrame:
    """One receiving moment: ball + all attackers on the board."""

    index: int
    receiver_id: str
    ball_zone: int
    players: list[PlayerSnapshot]
    offside_line_depth: int | None = None  # optional defensive line depth rank
    place: str | None = None
    passer_id: str | None = None
    pass_action: str | None = None  # 邊：傳球、直塞、強弱邊轉移…
    outcome: str | None = None  # 射正 | 得分

    def player_zones(self) -> dict[str, int]:
        return {p.player_id: p.zone for p in self.players}

    def receiver_zone(self) -> int:
        for p in self.players:
            if p.player_id == self.receiver_id:
                return p.zone
        return self.ball_zone


@dataclass(slots=True)
class BoardInput:
    play_id: str = ""
    title: str = ""
    frames: list[TouchFrame] = field(default_factory=list)
    # pass_points：只記每次接球 zone；full：含全員跑位
    mode: str = "pass_points"


@dataclass(slots=True)
class CriterionMatch:
    label: str
    matched: bool
    detail: str = ""


@dataclass(slots=True)
class TacticHit:
    name: str
    score: float  # 0..1 partial credit
    criteria: list[CriterionMatch]
    narrative: str = ""


@dataclass(slots=True)
class TouchRecord:
    """One reception on the timeline: who receives where, and how the ball arrived."""

    index: int
    receiver_id: str
    zone: int
    place: str
    passer_id: str | None = None
    pass_action: str | None = None
    outcome: str | None = None
    narrative: str = ""


@dataclass(slots=True)
class IntervalTranslation:
    from_index: int
    to_index: int
    ball_from: int
    ball_to: int
    passer_id: str | None
    receiver_id: str
    basic_action: str  # 傳球 | 盤帶 | 射正 | 得分 | 無
    tactics: list[TacticHit]
    player_runs: list[tuple[str, int, int]]  # (id, z_from, z_to)


@dataclass(slots=True)
class TranslationResult:
    play_id: str
    title: str
    valid: bool
    invalid_reason: str | None
    touches: list[TouchRecord]
    intervals: list[IntervalTranslation]
    description: str
    evaluation_points: dict[str, str]
    scoring: ScoringResult | None = None
