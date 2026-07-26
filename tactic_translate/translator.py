"""Board validation and touch-timeline translation."""

from __future__ import annotations

from .models import (
    BoardInput,
    IntervalTranslation,
    TouchFrame,
    TranslationResult,
)
from .patterns import (
    _find_player_moves,
    _passer_id,
    detect_all_tactics,
    detect_ball_path_tactics,
    detect_basic_action,
)
from .scoring import load_rubric_for_play_id, score_touches, scoring_to_dict
from .touches import (
    build_description,
    build_evaluation_points,
    build_touches,
    tactic_hit_from_touch,
)
from .zones import VALID_ZONE_IDS, zone_depth, zone_name


def _is_pass_points(board: BoardInput) -> bool:
    return board.mode != "full"


def validate_board(board: BoardInput) -> str | None:
    if len(board.frames) < 2:
        return "至少需要 2 個傳球點（接球時刻）。"

    pass_points = _is_pass_points(board)

    for frame in board.frames:
        if frame.ball_zone not in VALID_ZONE_IDS:
            return f"第 {frame.index + 1} 點：{zone_name(frame.ball_zone)} 不合法。"

        if pass_points:
            continue

        for p in frame.players:
            if p.zone not in VALID_ZONE_IDS:
                return (
                    f"frame {frame.index}: 球員 {p.player_id} "
                    f"不在合法 zone 中心 ({p.zone})。"
                )

        rz = frame.receiver_zone()
        if frame.ball_zone != rz:
            return (
                f"frame {frame.index}: 球 zone {frame.ball_zone} "
                f"與接球者 {frame.receiver_id} zone {rz} 不一致。"
            )

    return None


def _passer_for_interval(
    before: TouchFrame, after: TouchFrame, pass_points: bool
) -> str | None:
    if pass_points:
        if after.passer_id:
            return after.passer_id
        if before.receiver_id == after.receiver_id:
            return before.receiver_id
        return before.receiver_id or None
    return _passer_id(before, after)


def translate_interval(
    before: TouchFrame, after: TouchFrame, *, pass_points: bool = False
) -> IntervalTranslation:
    ball_from = before.ball_zone
    ball_to = after.ball_zone
    runs = [] if pass_points else _find_player_moves(before, after)
    passer = _passer_for_interval(before, after, pass_points)
    basic = detect_basic_action(before, after, ball_from, ball_to)

    if after.outcome == "得分":
        basic = "得分"
    elif after.outcome == "射正":
        basic = "射正"

    if pass_points:
        if after.pass_action:
            from .models import CriterionMatch, TacticHit

            tactics = [
                TacticHit(
                    name=after.pass_action,
                    score=1.0,
                    criteria=[CriterionMatch("傳球點標註", True)],
                    narrative=f"{passer or ''}{after.pass_action}至{zone_name(ball_to)}。",
                )
            ]
        else:
            tactics = detect_ball_path_tactics(before, after, ball_from, ball_to)
            if (
                basic == "盤帶"
                and before.receiver_id == after.receiver_id
                and ball_from != ball_to
                and zone_depth(ball_to) > zone_depth(ball_from)
            ):
                from .models import CriterionMatch, TacticHit

                tactics = [
                    TacticHit(
                        name="盤帶推進",
                        score=1.0,
                        criteria=[
                            CriterionMatch("同一接球者連續觸球", True),
                            CriterionMatch("向前帶球", True),
                        ],
                        narrative=f"帶球由{zone_name(ball_from)}推進至{zone_name(ball_to)}。",
                    ),
                    *tactics,
                ]
    else:
        tactics = detect_all_tactics(before, after, ball_from, ball_to, runs)
        if basic == "盤帶" and not any(t.name == "盤帶推進" for t in tactics):
            if ball_from != ball_to and is_forward_carry(before, after):
                from .models import CriterionMatch, TacticHit

                tactics = [
                    TacticHit(
                        name="盤帶推進",
                        score=1.0,
                        criteria=[
                            CriterionMatch("人球同區推進", True),
                            CriterionMatch(
                                "向前帶球",
                                zone_depth(ball_to) > zone_depth(ball_from),
                            ),
                        ],
                        narrative=f"帶球由{zone_name(ball_from)}推進至{zone_name(ball_to)}。",
                    )
                ]

    return IntervalTranslation(
        from_index=before.index,
        to_index=after.index,
        ball_from=ball_from,
        ball_to=ball_to,
        passer_id=passer,
        receiver_id=after.receiver_id,
        basic_action=basic,
        tactics=tactics,
        player_runs=runs,
    )


def is_forward_carry(before: TouchFrame, after: TouchFrame) -> bool:
    return zone_depth(after.ball_zone) > zone_depth(before.ball_zone)


def translate_board(board: BoardInput, *, rubric=None) -> TranslationResult:
    err = validate_board(board)
    if err:
        return TranslationResult(
            play_id=board.play_id,
            title=board.title,
            valid=False,
            invalid_reason=err,
            touches=[],
            intervals=[],
            description="",
            evaluation_points={},
            scoring=None,
        )

    pass_points = _is_pass_points(board)
    touches = build_touches(board)

    intervals: list[IntervalTranslation] = []
    for i in range(len(board.frames) - 1):
        it = translate_interval(
            board.frames[i],
            board.frames[i + 1],
            pass_points=pass_points,
        )
        if pass_points and board.frames[i + 1].pass_action:
            hit = tactic_hit_from_touch(touches[i + 1], touches[i])
            if hit:
                it.tactics = [hit]
        intervals.append(it)

    if rubric is None:
        rubric = load_rubric_for_play_id(board.play_id)

    scoring = score_touches(touches, rubric) if rubric else None

    return TranslationResult(
        play_id=board.play_id,
        title=board.title,
        valid=True,
        invalid_reason=None,
        touches=touches,
        intervals=intervals,
        description=build_description(touches),
        evaluation_points=build_evaluation_points(touches),
        scoring=scoring,
    )
