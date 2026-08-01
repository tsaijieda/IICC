#!/usr/bin/env bash
# 編譯 final_document 內 PDF
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(cd .. && pwd)"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
else
  PY=python3
fi
export MPLCONFIGDIR="${ROOT}/.mplconfig"
mkdir -p "${MPLCONFIGDIR}"
"${PY}" -m tactic_translate.plot_zone_map --pdf -o "$(pwd)"
"${PY}" -m tactic_translate.plot_zone_map --play a000.yaml --pdf -o "$(pwd)"
if [[ -f handball_2.png ]]; then
  sips -s format pdf handball_2.png --out handball.pdf >/dev/null
fi
./build_recreate.sh >/dev/null
for f in PHYSICAL_GAME_RULES points_table "A001-A006_戰術語言"; do
  xelatex -interaction=nonstopmode "${f}.tex" >/dev/null
done
./build_poster.sh >/dev/null
echo "已產出 zone_map.svg zone_map.pdf A000_zone_map.svg A000_zone_map.pdf handball.pdf recreate.pdf poster.pdf output/pdf/poster.pdf PHYSICAL_GAME_RULES.pdf points_table.pdf A001-A006_戰術語言.pdf"
