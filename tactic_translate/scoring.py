"""Score student pass_points against a question rubric."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .models import TouchRecord
from .zones import zone_name

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_WEIGHTS = {"players": 0.3, "action": 0.5, "place": 0.2}


@dataclass(slots=True)
class ScoringItem:
    name: str
    points: float
    touch_index: int | None = None
    passer: str | None = None
    receiver: str | None = None
    action: str | None = None
    place: str | None = None
    zone: int | None = None
    outcome: str | None = None
    from_place: str | None = None


@dataclass(slots=True)
class CriterionScore:
    label: str
    matched: bool
    weight: float
    earned: float
    max_points: float
    detail: str = ""


@dataclass(slots=True)
class ItemScore:
    name: str
    max_points: float
    earned: float
    criteria: list[CriterionScore] = field(default_factory=list)


@dataclass(slots=True)
class ScoringRubric:
    total: float
    weights: dict[str, float]
    items: list[ScoringItem]


@dataclass(slots=True)
class ScoringResult:
    max_points: float
    earned: float
    items: list[ItemScore]

    @property
    def ratio(self) -> float:
        if self.max_points <= 0:
            return 0.0
        return self.earned / self.max_points


def rubric_from_dict(data: dict[str, Any]) -> ScoringRubric | None:
    raw = data.get("scoring")
    if not raw:
        return None

    weights = {**DEFAULT_WEIGHTS, **(raw.get("weights") or {})}
    items: list[ScoringItem] = []
    for entry in raw.get("items") or []:
        check = entry.get("check") or entry
        items.append(
            ScoringItem(
                name=str(entry.get("name", entry.get("id", "項目"))),
                points=float(entry.get("points", 0)),
                touch_index=entry.get("touch", entry.get("touch_index")),
                passer=_opt_str(check, "passer"),
                receiver=_opt_str(check, "receiver"),
                action=_opt_str(check, "action", "pass_action"),
                place=_opt_str(check, "place"),
                zone=check.get("zone"),
                outcome=_opt_str(check, "outcome"),
                from_place=_opt_str(check, "from_place"),
            )
        )

    total = float(raw.get("total", sum(i.points for i in items)))
    return ScoringRubric(total=total, weights=weights, items=items)


def load_rubric(path: str | Path) -> ScoringRubric | None:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    return rubric_from_dict(data)


def load_rubric_for_play_id(play_id: str) -> ScoringRubric | None:
    pid = (play_id or "").strip()
    if not pid:
        return None
    num = pid.upper().removeprefix("T")
    candidates = [
        ROOT / f"{pid}.yaml",
        ROOT / f"{num}.yaml",
        ROOT / f"{pid.lower()}.yaml",
        ROOT / "examples" / "boards" / f"{pid}_pass_points.yaml",
    ]
    for path in candidates:
        if path.is_file():
            return load_rubric(path)
    return None


def _opt_str(raw: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        if key in raw and raw[key] is not None:
            return str(raw[key])
    return None


def _touch_at(touches: list[TouchRecord], index: int | None) -> TouchRecord | None:
    if index is None:
        return None
    if 0 <= index < len(touches):
        return touches[index]
    return None


def _active_weights(item: ScoringItem, weights: dict[str, float]) -> dict[str, float]:
    parts: dict[str, float] = {}
    if item.passer and item.receiver:
        parts["players"] = weights["players"]
    if item.action:
        parts["action"] = weights["action"]
    if item.place is not None or item.zone is not None:
        parts["place"] = weights["place"]
    if item.outcome and "action" not in parts:
        parts["outcome"] = weights.get("outcome", 0.1)
    if not parts:
        return {"action": 1.0}
    total = sum(parts.values())
    return {k: v / total for k, v in parts.items()}


def score_item(
    item: ScoringItem,
    touches: list[TouchRecord],
    weights: dict[str, float],
) -> ItemScore:
    touch = _touch_at(touches, item.touch_index)
    prev = (
        touches[item.touch_index - 1]
        if item.touch_index is not None and item.touch_index > 0
        else None
    )

    wmap = _active_weights(item, weights)
    criteria: list[CriterionScore] = []
    earned = 0.0

    if touch is None:
        for key, weight in wmap.items():
            label = {
                "players": "傳球人",
                "action": "邊",
                "place": "接球點",
                "outcome": "結果",
            }.get(key, key)
            pts = item.points * weight
            criteria.append(
                CriterionScore(label, False, weight, 0.0, pts, detail="缺少此拍")
            )
        return ItemScore(item.name, item.points, 0.0, criteria)

    if "players" in wmap:
        ok = touch.passer_id == item.passer and touch.receiver_id == item.receiver
        pts = item.points * wmap["players"]
        detail = f"{touch.passer_id}→{touch.receiver_id}"
        if item.passer and item.receiver:
            detail += f"（應 {item.passer}→{item.receiver}）"
        criteria.append(CriterionScore("傳球人", ok, wmap["players"], pts if ok else 0.0, pts, detail))
        earned += pts if ok else 0.0

    if "action" in wmap:
        ok = touch.pass_action == item.action
        if item.outcome:
            ok = ok and touch.outcome == item.outcome
        pts = item.points * wmap["action"]
        detail = f"{touch.pass_action}（應 {item.action}）"
        if item.outcome:
            detail += f"；{touch.outcome or '—'}（應 {item.outcome}）"
        criteria.append(
            CriterionScore(
                "邊",
                ok,
                wmap["action"],
                pts if ok else 0.0,
                pts,
                detail,
            )
        )
        earned += pts if ok else 0.0

    if "place" in wmap:
        place_ok = touch.place == item.place if item.place else True
        zone_ok = touch.zone == item.zone if item.zone is not None else True
        ok = place_ok and zone_ok
        pts = item.points * wmap["place"]
        expected = item.place or zone_name(item.zone or touch.zone)
        criteria.append(
            CriterionScore(
                "接球點",
                ok,
                wmap["place"],
                pts if ok else 0.0,
                pts,
                f"{touch.place}（應 {expected}）",
            )
        )
        earned += pts if ok else 0.0

    if item.from_place and prev:
        ok = prev.place == item.from_place
        pts = item.points * wmap.get("place", 0) * 0.5
        criteria.append(
            CriterionScore(
                "起點",
                ok,
                wmap.get("place", 0) * 0.5,
                pts if ok else 0.0,
                pts,
                f"{prev.place}（應 {item.from_place}）",
            )
        )
        earned += pts if ok else 0.0

    if "outcome" in wmap and item.outcome:
        ok = touch.outcome == item.outcome
        pts = item.points * wmap["outcome"]
        criteria.append(
            CriterionScore(
                "結果",
                ok,
                wmap["outcome"],
                pts if ok else 0.0,
                pts,
                f"{touch.outcome or '—'}（應 {item.outcome}）",
            )
        )
        earned += pts if ok else 0.0

    return ItemScore(item.name, item.points, round(earned, 2), criteria)


def score_touches(touches: list[TouchRecord], rubric: ScoringRubric) -> ScoringResult:
    items = [score_item(item, touches, rubric.weights) for item in rubric.items]
    earned = round(sum(i.earned for i in items), 2)
    max_points = rubric.total if rubric.total > 0 else sum(i.max_points for i in items)
    return ScoringResult(max_points=max_points, earned=earned, items=items)


def scoring_to_dict(result: ScoringResult) -> dict[str, Any]:
    return {
        "max_points": result.max_points,
        "earned": result.earned,
        "ratio": round(result.ratio, 4),
        "items": [
            {
                "name": item.name,
                "max_points": item.max_points,
                "earned": item.earned,
                "criteria": [
                    {
                        "label": c.label,
                        "matched": c.matched,
                        "earned": round(c.earned, 2),
                        "max_points": round(c.max_points, 2),
                        "detail": c.detail,
                    }
                    for c in item.criteria
                ],
            }
            for item in result.items
        ],
    }
