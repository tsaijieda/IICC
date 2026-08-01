#!/usr/bin/env bash
# poster.md → poster.pdf（pandoc + xelatex）
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

pandoc --defaults poster.defaults.yaml -V "CJKmainfont=${CJK_FONT}" poster.md -o poster.pdf

mkdir -p output/pdf
cp -f poster.pdf output/pdf/poster.pdf
echo "已產出 poster.pdf output/pdf/poster.pdf"
