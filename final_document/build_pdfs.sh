#!/usr/bin/env bash
# 編譯 final_document 內 PDF
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(cd .. && pwd)"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  "${ROOT}/.venv/bin/python" -m tactic_translate.plot_zone_map --pdf -o "$(pwd)"
else
  python3 -m tactic_translate.plot_zone_map --pdf -o "$(pwd)"
fi
for f in recreate poster PHYSICAL_GAME_RULES points_table "A001-A006_戰術語言"; do
  xelatex -interaction=nonstopmode "${f}.tex" >/dev/null
done
echo "已產出 zone_map.svg zone_map.pdf recreate.pdf poster.pdf PHYSICAL_GAME_RULES.pdf points_table.pdf A001-A006_戰術語言.pdf"
