#!/usr/bin/env bash
# Render every figure in this folder to PNG (and SVG for Mermaid), offline, using gstack's browse daemon.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
python3 -I build_charts.py
B="$HOME/.claude/skills/gstack/browse/dist/browse"
BUNDLE="$HOME/.claude/skills/gstack/lib/diagram-render/dist/diagram-render.html"
SHA=$(shasum -a 256 "$BUNDLE" | cut -c1-16); STAGED="/tmp/gstack-diagram-render-$SHA.html"
[ -f "$STAGED" ] || { cp "$BUNDLE" "$STAGED.$$"; mv "$STAGED.$$" "$STAGED"; }
TAB=$("$B" newtab --json | sed -n 's/.*"tabId":[[:space:]]*\([0-9]*\).*/\1/p')
"$B" load-html "$STAGED" --tab-id "$TAB" >/dev/null
"$B" wait '#done' --tab-id "$TAB" >/dev/null
for f in *.mmd; do
  s=${f%.mmd}; n=$(echo "$s" | tr -cd 'a-z'); src=$(base64 < "$f" | tr -d '\n')
  "$B" js --tab-id "$TAB" "window.__renderMermaid('d$n', atob('$src')).then(x => { window.__svg = x; return 'OK $s ' + x.length })" | tail -1
  "$B" js --tab-id "$TAB" "window.__svg" --out "$PWD/$s.svg" >/dev/null
  "$B" js --tab-id "$TAB" "window.__rasterize(window.__svg, 1950)" --out "$PWD/$s.png" >/dev/null
  "$B" js --tab-id "$TAB" "window.__mermaidToExcalidraw(atob('$src')).then(j => { window.__scene = j; return 'scene' })" >/dev/null
  "$B" js --tab-id "$TAB" "window.__scene" --out "$PWD/$s.excalidraw" >/dev/null
done
for s in leak-results edit-priorities; do
  "$B" js --tab-id "$TAB" "window.__rasterize(atob('$(base64 < "$s.svg" | tr -d '\n')'), 1950)" --out "$PWD/$s.png" >/dev/null
  echo "OK $s"
done
"$B" closetab "$TAB" >/dev/null
