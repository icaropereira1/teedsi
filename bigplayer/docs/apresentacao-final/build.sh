#!/usr/bin/env bash
# Gera os dois PDFs (slides e instruções) a partir dos CSVs versionados do projeto.
# Requer apenas o Google Chrome. Rodar a partir de qualquer pasta: bash build.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BP="$(cd "$HERE/../.." && pwd)"
D12="$BP/docs/apresentacao-12-11/dados"
OUT="$HERE/build/data.js"
emit() { printf '%s: `' "$1" >> "$OUT"; cat "$2" | tr -d '\r' >> "$OUT"; printf '`,\n' >> "$OUT"; }
printf 'const CSV = {\n' > "$OUT"
emit ev_wdo   "$BP/reports/estudo_evento_wdo.csv"
emit ev_win   "$BP/reports/estudo_evento_win.csv"
emit ev_r2    "$BP/reports/estudo_evento_r2_wdo.csv"
emit ev_conf  "$BP/reports/confirmacao_a1_win.csv"
emit bur_wdo  "$BP/reports/buracos_wdo.csv"
emit bur_win  "$BP/reports/buracos_win.csv"
emit picos_wdo "$BP/pt2/reports/picos_wdo.csv"
emit picos_win "$BP/pt2/reports/picos_win.csv"
emit dep_wdo  "$BP/pt2/reports/depois_wdo.csv"
emit dep_win  "$BP/pt2/reports/depois_win.csv"
for s in wdo win dolarizado; do for t in alta baixa todos; do
  emit "p30_${s}_${t}" "$D12/medianas_pico30/pico30_${s}_${t}.csv"; done; done
emit fluxo "$D12/fluxo_investidores/fluxo_investidores.csv"
printf '};\nconst MANIFEST = {wdo: %s, win: %s};\n' "$(cat "$BP/reports/split_manifest.json")" "$(cat "$BP/reports/split_manifest_win.json")" >> "$OUT"

CHROME="${CHROME:-/c/Program Files/Google/Chrome/Application/chrome.exe}"
to_pdf() {
  local src out
  src="$(cygpath -w "$HERE/build/$1" 2>/dev/null || echo "$HERE/build/$1")"
  out="$(cygpath -w "$HERE/$2" 2>/dev/null || echo "$HERE/$2")"
  "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=5000 \
    --allow-file-access-from-files --print-to-pdf="$out" "file:///${src//\//}" 2>/dev/null
}
to_pdf deck.html    "Big_Player_apresentacao_final.pdf"
to_pdf roteiro.html "Instrucoes_apresentacao.pdf"
ls -la "$HERE"/*.pdf
