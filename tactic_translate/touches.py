"""Build per-touch reception timeline (誰在何時何地接球)."""

from __future__ import annotations

from .models import BoardInput, CriterionMatch, TacticHit, TouchFrame, TouchRecord
from .patterns import detect_ball_path_tactics, detect_basic_action
from .zones import BOX, BYLINE, zone_name


def _detect_outcome(
    ball_from: int, ball_to: int, pass_action: str | None = None
) -> str | None:
    if ball_to not in BOX:
        return None
    if pass_action == "傳中" or ball_from in BYLINE:
        return "得分"
    if ball_from in BOX:
        return "得分"
    return "射正"


def _infer_pass_action(before: TouchFrame, after: TouchFrame) -> str:
    ball_from = before.ball_zone
    ball_to = after.ball_zone

    if before.receiver_id == after.receiver_id and ball_from != ball_to:
        return "盤帶推進"

    hits = detect_ball_path_tactics(before, after, ball_from, ball_to)
    for hit in hits:
        if hit.score >= 0.67:
            return hit.name

    basic = detect_basic_action(before, after, ball_from, ball_to)
    if basic in {"射正", "得分"}:
        return basic
    return "傳球"


def _resolve_passer(
    frame: TouchFrame, prev: TouchFrame | None, explicit: str | None
) -> str | None:
    if explicit:
        return explicit
    if prev is None:
        return None
    if frame.receiver_id == prev.receiver_id:
        return frame.receiver_id
    return prev.receiver_id


def _touch_narrative(
    *,
    receiver_id: str,
    place: str,
    passer_id: str | None,
    pass_action: str | None,
    outcome: str | None,
    is_first: bool,
) -> str:
    if is_first and not (passer_id and pass_action):
        return f"{receiver_id}在{place}接球。"

    action = pass_action or "傳球"
    if passer_id == receiver_id:
        tail = f"至{place}"
        if outcome == "得分":
            return f"{receiver_id}{action}{tail}得分。"
        if outcome == "射正":
            return f"{receiver_id}{action}{tail}射正。"
        return f"{receiver_id}{action}{tail}。"

    if outcome in {"射正", "得分"}:
        return (
            f"{passer_id}{action}給{receiver_id}，"
            f"{receiver_id}在{place}{outcome}。"
        )
    return f"{passer_id}{action}給{receiver_id}，{receiver_id}在{place}接球。"


def build_touches(board: BoardInput) -> list[TouchRecord]:
    """Each frame → one reception record with passer / 邊 / outcome."""
    records: list[TouchRecord] = []

    for i, frame in enumerate(board.frames):
        prev = board.frames[i - 1] if i > 0 else None
        place = frame.place or zone_name(frame.ball_zone)
        passer = _resolve_passer(frame, prev, frame.passer_id)
        action = frame.pass_action
        outcome = frame.outcome

        if prev is not None:
            if action is None:
                action = _infer_pass_action(prev, frame)
            if outcome is None:
                outcome = _detect_outcome(prev.ball_zone, frame.ball_zone, action)

        narrative = _touch_narrative(
            receiver_id=frame.receiver_id,
            place=place,
            passer_id=passer,
            pass_action=action,
            outcome=outcome,
            is_first=i == 0,
        )

        records.append(
            TouchRecord(
                index=i,
                receiver_id=frame.receiver_id,
                zone=frame.ball_zone,
                place=place,
                passer_id=passer,
                pass_action=action,
                outcome=outcome,
                narrative=narrative,
            )
        )

    return records


def build_description(touches: list[TouchRecord]) -> str:
    if not touches:
        return "無法轉譯為戰術語言。"
    return "".join(t.narrative for t in touches)


def _eval_line(touch: TouchRecord, prev: TouchRecord | None) -> tuple[str, str] | None:
    if not touch.pass_action:
        return None

    if prev is None:
        if not touch.passer_id:
            return None
        return (
            touch.pass_action,
            f"傳球人：{touch.passer_id} → {touch.receiver_id}；"
            f"邊：{touch.pass_action}；接球點：{touch.place}。",
        )

    if touch.passer_id == touch.receiver_id:
        parts = [
            f"接球人：{touch.receiver_id}",
            f"邊：{touch.pass_action}",
            f"{prev.place} → {touch.place}",
        ]
        if touch.outcome:
            parts.append(touch.outcome)
        return touch.pass_action, "；".join(parts) + "。"

    return (
        touch.pass_action,
        f"傳球人：{touch.passer_id} → {touch.receiver_id}；"
        f"邊：{touch.pass_action}；接球點：{touch.place}。",
    )


def build_evaluation_points(touches: list[TouchRecord]) -> dict[str, str]:
    out: dict[str, str] = {}
    counts: dict[str, int] = {}

    for i, touch in enumerate(touches):
        prev = touches[i - 1] if i > 0 else None
        pair = _eval_line(touch, prev)
        if not pair:
            continue
        key, value = pair
        if key in out:
            counts[key] = counts.get(key, 1) + 1
            key = f"{key} ({counts[key]})"
        else:
            counts[key] = 1
        out[key] = value

    return out


def tactic_hit_from_touch(touch: TouchRecord, prev: TouchRecord | None) -> TacticHit | None:
    if prev is None or not touch.pass_action:
        return None
    return TacticHit(
        name=touch.pass_action,
        score=1.0,
        criteria=[CriterionMatch("傳球點標註", True, detail=touch.place)],
        narrative=touch.narrative.rstrip("。"),
    )
