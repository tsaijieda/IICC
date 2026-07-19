"""Tests for defender stack / priority / step-budget landing."""

from __future__ import annotations

from defense_game.defenders import update_defenders
from defense_game.entities import DefenderKind, Player, Side
from defense_game.grid import Pos


def _atk(pid: str, x: int, y: int) -> Player:
    return Player(pid, pid, Side.ATTACK, Pos(x, y))


def _def(pid: str, kind: DefenderKind, x: int, y: int, **kw) -> Player:
    return Player(pid, pid, Side.DEFENSE, Pos(x, y), kind=kind, **kw)


def test_no_stack_after_react():
    attackers = [_atk("A1", 3, 2), _atk("A2", 1, 3)]
    defenders = [
        _def("G", DefenderKind.GOALKEEPER, 3, 7),
        _def("B1", DefenderKind.BLOCK, 2, 5, block_max_y=5),
        _def("B2", DefenderKind.BLOCK, 4, 5, block_max_y=5),
        _def("P", DefenderKind.PRESSER, 3, 3),
        _def("S", DefenderKind.SHADOW, 1, 4, mark_id="A2"),
    ]
    update_defenders(defenders, attackers, Pos(3, 2), "A1", react="full")
    cells = [(d.pos.x, d.pos.y) for d in defenders]
    assert len(cells) == len(set(cells)), cells


def test_block_priority_over_shadow_same_cell():
    """Block claims first; Shadow must yield within 1 step."""
    attackers = [_atk("A1", 3, 3), _atk("A2", 3, 5)]
    block = _def("B0", DefenderKind.BLOCK, 2, 5, block_max_y=5)
    shadow = _def("S0", DefenderKind.SHADOW, 3, 4, mark_id="A2")
    defenders = [block, shadow, _def("G", DefenderKind.GOALKEEPER, 3, 7)]
    update_defenders(defenders, attackers, Pos(3, 3), "A1", react="full")
    assert block.pos != shadow.pos
    assert block.pos.y == 5
    assert block.pos.chebyshev(Pos(2, 5)) <= 1
    assert shadow.pos.chebyshev(Pos(3, 4)) <= 1


def test_interceptor_cannot_teleport_along_lane():
    """When cut is taken, Interceptor stays within its step budget."""
    attackers = [_atk("A1", 0, 2), _atk("A2", 6, 6)]
    cut_guess = Pos(3, 4)
    block = _def("B0", DefenderKind.BLOCK, cut_guess.x, 4, block_max_y=4)
    inter = _def("I0", DefenderKind.INTERCEPTOR, 0, 0)
    old = inter.pos
    defenders = [
        block,
        inter,
        _def("G", DefenderKind.GOALKEEPER, 3, 7),
    ]
    update_defenders(defenders, attackers, Pos(0, 2), "A1", react="full")
    assert inter.pos.chebyshev(old) <= 2
    assert inter.pos != block.pos


def test_anchored_cell_reserved():
    attackers = [_atk("A1", 5, 4)]
    anchored = _def(
        "B5", DefenderKind.BLOCK, 5, 6, block_max_y=6, anchored=True
    )
    presser = _def("P0", DefenderKind.PRESSER, 5, 5)
    defenders = [anchored, presser, _def("G", DefenderKind.GOALKEEPER, 3, 7)]
    update_defenders(defenders, attackers, Pos(5, 4), "A1", react="full")
    assert anchored.pos == Pos(5, 6)
    assert presser.pos != anchored.pos


def test_same_kind_id_order():
    """Two blocks wanting the same corridor cell: lower id claims first."""
    attackers = [_atk("A1", 3, 3)]
    b_low = _def("B1", DefenderKind.BLOCK, 2, 5, block_max_y=5)
    b_high = _def("B2", DefenderKind.BLOCK, 4, 5, block_max_y=5)
    defenders = [b_high, b_low, _def("G", DefenderKind.GOALKEEPER, 3, 7)]
    update_defenders(defenders, attackers, Pos(3, 3), "A1", react="full")
    assert b_low.pos != b_high.pos
    assert b_low.pos.y == 5 and b_high.pos.y == 5
    assert b_low.pos == Pos(3, 5)


if __name__ == "__main__":
    test_no_stack_after_react()
    test_block_priority_over_shadow_same_cell()
    test_interceptor_cannot_teleport_along_lane()
    test_anchored_cell_reserved()
    test_same_kind_id_order()
    print("ok")
