#!/usr/bin/env python3
"""CLI: tactical board YAML → 戰術文字（evaluation_points 格式）。"""

from __future__ import annotations

import argparse
import json
import sys

from tactic_translate import load_board, result_to_dict, translate_board, write_result_yaml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="將戰術板（每次接球時刻）轉譯為戰術語言，輸出格式對齊 *.yaml 範例。"
    )
    parser.add_argument("board", help="戰術板 YAML（見 examples/boards/）")
    parser.add_argument(
        "-o",
        "--output",
        help="輸出 YAML 路徑（預設印到 stdout）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 印出完整轉譯結構",
    )
    args = parser.parse_args(argv)

    board = load_board(args.board)
    result = translate_board(board)

    if not result.valid:
        print(f"無效戰術板：{result.invalid_reason}", file=sys.stderr)
        return 1

    if args.json:
        text = json.dumps(result_to_dict(result), ensure_ascii=False, indent=2)
        if args.output:
            open(args.output, "w", encoding="utf-8").write(text)
        else:
            print(text)
        return 0

    if args.output:
        write_result_yaml(result, args.output)
        print(f"已寫入 {args.output}")
        return 0

    print(f"# {result.title or result.play_id}")
    if result.scoring:
        s = result.scoring
        print(f"score: {s.earned} / {s.max_points}")
    print(f"description: \"{result.description}\"")
    print("evaluation_points:")
    for k, v in result.evaluation_points.items():
        print(f"  {k}: \"{v}\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
