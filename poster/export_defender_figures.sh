#!/usr/bin/env bash
# 輸出五張 PNG（僅圖面，無標題／頁尾）
set -euo pipefail
cd "$(dirname "$0")"
OUT="../defender_figures"
mkdir -p "$OUT"

xelatex -interaction=nonstopmode defender_movement_figures.tex >/dev/null

names=(presser block shadow interceptor goalkeeper)

if command -v pdftoppm >/dev/null 2>&1; then
  for i in 1 2 3 4 5; do
    idx=$((i - 1))
    pdftoppm -png -singlefile -r 300 -f "$i" -l "$i" \
      defender_movement_figures.pdf "$OUT/${names[$idx]}"
    [[ -f "$OUT/${names[$idx]}-1.png" ]] && mv "$OUT/${names[$idx]}-1.png" "$OUT/${names[$idx]}.png"
    echo "Wrote $OUT/${names[$idx]}.png"
  done
else
  VENV=".venv_export"
  if [[ ! -x "$VENV/bin/python" ]]; then
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install -q pymupdf
  fi
  "$VENV/bin/python" - <<'PY'
import fitz
from pathlib import Path
names = ["presser", "block", "shadow", "interceptor", "goalkeeper"]
doc = fitz.open("defender_movement_figures.pdf")
out = Path("../defender_figures")
for i, name in enumerate(names):
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(300/72, 300/72), alpha=False)
    pix.save(out / f"{name}.png")
    print(f"Wrote {out / f'{name}.png'}")
PY
fi
