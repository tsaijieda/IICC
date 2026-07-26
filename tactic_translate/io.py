"""Load tactical boards / emit YAML-like output."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import BoardInput, PlayerSnapshot, TouchFrame, TranslationResult
from .scoring import scoring_to_dict
from .zones import zone_name


def _optional_str(raw: dict[str, Any], key: str) -> str | None:
    if key not in raw or raw[key] is None:
        return None
    return str(raw[key])


def _touch_meta(raw: dict[str, Any], zone: int) -> dict[str, Any]:
    return {
        "place": raw.get("place") or zone_name(zone),
        "passer_id": _optional_str(raw, "passer"),
        "pass_action": _optional_str(raw, "pass_action"),
        "outcome": _optional_str(raw, "outcome"),
    }


def _frame_from_dict(raw: dict[str, Any], index: int) -> TouchFrame:
    players = [
        PlayerSnapshot(
            player_id=str(p["id"]),
            role=str(p.get("role", p["id"])),
            zone=int(p["zone"]),
        )
        for p in raw.get("players", [])
    ]
    zone = int(raw.get("ball_zone", raw.get("zone", 14)))
    meta = _touch_meta(raw, zone)
    return TouchFrame(
        index=index,
        receiver_id=str(raw.get("receiver", raw.get("label", f"T{index + 1}"))),
        ball_zone=zone,
        players=players,
        offside_line_depth=raw.get("offside_line_depth"),
        place=meta["place"],
        passer_id=meta["passer_id"],
        pass_action=meta["pass_action"],
        outcome=meta["outcome"],
    )


def load_board(path: str | Path) -> BoardInput:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return board_from_dict(data)


def board_from_dict(data: dict[str, Any]) -> BoardInput:
    frames_raw = data.get("frames") or data.get("pass_points") or []
    frames: list[TouchFrame] = []
    has_players = False

    for i, raw in enumerate(frames_raw):
        players_raw = raw.get("players") or []
        if players_raw:
            has_players = True
            frames.append(_frame_from_dict(raw, i))
            continue

        if "ball_zone" in raw or "zone" in raw:
            z = int(raw.get("ball_zone", raw.get("zone")))
            label = str(raw.get("receiver", raw.get("label", f"T{i + 1}")))
            meta = _touch_meta(raw, z)
            frames.append(
                TouchFrame(
                    index=i,
                    receiver_id=label,
                    ball_zone=z,
                    players=[],
                    offside_line_depth=raw.get("offside_line_depth"),
                    place=meta["place"],
                    passer_id=meta["passer_id"],
                    pass_action=meta["pass_action"],
                    outcome=meta["outcome"],
                )
            )
            continue

        frames.append(_frame_from_dict(raw, i))

    mode = data.get("mode")
    if mode is None:
        scoring = data.get("scoring_mode")
        if scoring == "pass_points":
            mode = "pass_points"
        else:
            mode = "full" if has_players else "pass_points"
    else:
        mode = str(mode)

    return BoardInput(
        play_id=str(data.get("play_id", "")),
        title=str(data.get("title", "")),
        frames=frames,
        mode=mode,
    )


def result_to_dict(result: TranslationResult) -> dict[str, Any]:
    return {
        "play_id": result.play_id,
        "title": result.title,
        "valid": result.valid,
        "invalid_reason": result.invalid_reason,
        "description": result.description,
        "evaluation_points": result.evaluation_points,
        "scoring": scoring_to_dict(result.scoring) if result.scoring else None,
        "touches": [
            {
                "index": t.index,
                "time": t.index + 1,
                "receiver": t.receiver_id,
                "zone": t.zone,
                "place": t.place,
                "passer": t.passer_id,
                "pass_action": t.pass_action,
                "outcome": t.outcome,
                "narrative": t.narrative,
            }
            for t in result.touches
        ],
        "pass_points": [
            {
                "zone": t.zone,
                "place": t.place,
                "receiver": t.receiver_id,
                **({"passer": t.passer_id} if t.passer_id and t.index > 0 else {}),
                **({"pass_action": t.pass_action} if t.pass_action and t.index > 0 else {}),
                **({"outcome": t.outcome} if t.outcome else {}),
            }
            for t in result.touches
        ],
        "intervals": [
            {
                "from_frame": it.from_index,
                "to_frame": it.to_index,
                "ball": f"{zone_name(it.ball_from)} → {zone_name(it.ball_to)}",
                "passer": it.passer_id,
                "receiver": it.receiver_id,
                "basic_action": it.basic_action,
                "player_runs": [
                    {"player": pid, "from": z0, "to": z1}
                    for pid, z0, z1 in it.player_runs
                ],
                "tactics": [
                    {
                        "name": t.name,
                        "score": round(t.score, 2),
                        "narrative": t.narrative,
                        "criteria": [
                            {"label": c.label, "matched": c.matched, "detail": c.detail}
                            for c in t.criteria
                        ],
                    }
                    for t in it.tactics
                ],
            }
            for it in result.intervals
        ],
    }


def write_result_yaml(result: TranslationResult, path: str | Path) -> None:
    payload = {
        "play_id": result.play_id or "TRANSLATED",
        "title": result.title or "轉譯結果",
        "description": result.description,
        "evaluation_points": result.evaluation_points,
        "pass_points": result_to_dict(result)["pass_points"],
        "translation": result_to_dict(result),
    }
    Path(path).write_text(
        yaml.dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
