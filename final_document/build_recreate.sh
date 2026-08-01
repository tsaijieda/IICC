#!/usr/bin/env bash
# recreate.md → recreate.pdf（pandoc + xelatex）
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "需要 pandoc：brew install pandoc" >&2
  exit 1
fi

CJK_FONT="Microsoft JhengHei"
if ! fc-list :lang=zh family 2>/dev/null | grep -qi "Microsoft JhengHei"; then
  CJK_FONT="Heiti TC"
fi

pandoc --defaults recreate.defaults.yaml -V "CJKmainfont=${CJK_FONT}" recreate.md -o recreate.pdf
echo "已產出 recreate.pdf"
