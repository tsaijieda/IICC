"""Interactive CLI for defense puzzles.

Usage:
  python -m defense_game.cli
  python -m defense_game.cli D5
  python -m defense_game.cli D5 --demo
"""

from __future__ import annotations

import argparse
import sys

from .game import Action, ActionType, DefenseGame
from .grid import Pos
from .puzzles import PUZZLES, get_puzzle


HELP = """
指令
  map                     重畫棋盤
  roster                  列出球員
  move <id> <x> <y>       移動球員 1 格（同回合可移動多人；持球＝盤帶）
  dribble <x> <y>         持球盤帶 1 格
  pass <id>               地滾傳球（結束本回合，防守者移動）
  pass <id> <x> <y>       地滾 + 撞牆插上
  lob <id>                高空傳球（結束本回合）
  lob <id> <x> <y>        高空 + 撞牆插上
  shoot [x y]             射門（結束本回合）
  end                     結束移動階段（需已移動至少一人）
  hint                    提示
  quit                    離開

圖例  ● 持球  ○ 隊友  P逼搶 B大閘 S影子 I攔截 G門將  ⌂球門
棋盤：短邊（寬 5）= 球門邊，長邊（深 6）= 進攻方向
"""


def parse_action(line: str, game: DefenseGame) -> Action | None:
    parts = line.strip().split()
    if not parts:
        return None
    cmd = parts[0].lower()

    if cmd in {"help", "h", "?"}:
        print(HELP)
        return None
    if cmd == "map":
        print(game.render())
        return None
    if cmd == "roster":
        print(game.roster())
        return None
    if cmd == "hint":
        print(game.puzzle.tip)
        return None
    if cmd in {"quit", "exit", "q"}:
        raise SystemExit(0)

    if cmd == "end":
        return Action(ActionType.END_TURN)
    if cmd == "move":
        if len(parts) != 4:
            raise ValueError("用法: move <id> <x> <y>")
        return Action(
            ActionType.MOVE,
            actor_id=parts[1].upper(),
            dest=Pos(int(parts[2]), int(parts[3])),
        )
    if cmd == "dribble":
        if len(parts) != 3:
            raise ValueError("用法: dribble <x> <y>")
        return Action(ActionType.DRIBBLE, dest=Pos(int(parts[1]), int(parts[2])))
    if cmd in {"pass", "lob"}:
        atype = ActionType.LOB if cmd == "lob" else ActionType.PASS
        if len(parts) == 2:
            return Action(atype, target_id=parts[1].upper())
        if len(parts) == 4:
            return Action(
                atype,
                target_id=parts[1].upper(),
                dest=Pos(int(parts[2]), int(parts[3])),
            )
        raise ValueError(f"用法: {cmd} <id> [x y]")
    if cmd == "shoot":
        if len(parts) == 1:
            return Action(ActionType.SHOOT)
        if len(parts) == 3:
            return Action(
                ActionType.SHOOT, dest=Pos(int(parts[1]), int(parts[2]))
            )
        raise ValueError("用法: shoot [x y]")

    raise ValueError(f"未知指令 {cmd!r}。輸入 help。")


def run_interactive(game: DefenseGame) -> int:
    p = game.puzzle
    print(f"\n=== {p.id}: {p.title} ===")
    print(p.description)
    print(HELP)
    print(game.render())
    print(game.roster())

    while not game.finished:
        try:
            line = input(f"\n[t{game.turn + 1}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 1
        if not line:
            continue
        try:
            action = parse_action(line, game)
        except ValueError as e:
            print(f"! {e}")
            continue
        if action is None:
            continue
        result = game.apply(action)
        for log in result.logs:
            print(f"  · {log}")
        print(result.message)
        print(game.render())
        if game.finished:
            break

    if game.won:
        print(f"\n★ 過關 — {game.score}/10 分（{game.turn} 回合）")
        return 0
    print("\n✗ 失敗")
    return 1


def run_demo(puzzle_id: str) -> int:
    """Scripted clear for each puzzle (teaching line)."""
    from .solutions import solution_actions

    try:
        actions = solution_actions(puzzle_id)
    except KeyError:
        print(f"No demo script for {puzzle_id}")
        return 1

    game = DefenseGame(get_puzzle(puzzle_id))
    print(f"\n=== DEMO {game.puzzle.id}: {game.puzzle.title} ===")
    print(game.render())
    for action in actions:
        if game.finished:
            break
        print(f"\n>> {action.type.value} {action}")
        result = game.apply(action)
        for log in result.logs:
            print(f"  · {log}")
        print(result.message)
        print(game.render())

    print(f"\nwon={game.won} score={game.score} turns={game.turn}")
    return 0 if game.won else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="7×8 defense puzzle simulator")
    parser.add_argument(
        "puzzle",
        nargs="?",
        default=None,
        help="Puzzle id D1..D6 or S1..S5 (default: menu)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a scripted solution instead of interactive play",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List puzzles and exit",
    )
    args = parser.parse_args(argv)

    if args.list or args.puzzle is None and not args.demo:
        print("Defense puzzles:\n")
        last_cat = None
        for p in PUZZLES:
            if p.category != last_cat:
                label = "進攻戰術" if p.category == "tactical" else "防守體系"
                print(f"── {label} ──\n")
                last_cat = p.category
            print(f"  {p.id}  {p.title}")
            print(f"      {p.description}\n")
        if args.list:
            return 0
        choice = input("Select puzzle [D1-D6 / S1-S5]: ").strip() or "D1"
        args.puzzle = choice

    assert args.puzzle is not None
    if args.demo:
        return run_demo(args.puzzle)

    game = DefenseGame(get_puzzle(args.puzzle))
    return run_interactive(game)


if __name__ == "__main__":
    sys.exit(main())
