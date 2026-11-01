# Per-farm emissions Sankey — static export

**Version:** AN_v2  
**Date:** 2026-11-01  
**Does not overwrite** `docs/SANKEY_AN_v1.md`.

AN_v1 shipped HTML/JSON only. This version documents how to render paper-static SVG and PNG after installing the optional `figures` extra (plotly + kaleido) and, for the fork decision diagram, mermaid-cli.

## Install

```bash
pip install -e '.[figures]'
# or: pip install 'plotly>=6' 'kaleido>=1'
```

Fork-diagram SVG/PNG also need Node and mermaid-cli. Chromium/Chrome is required (puppeteer). In this authoring VM: `npx @mermaid-js/mermaid-cli` 12.0.0 and `/usr/local/bin/google-chrome` with `--no-sandbox`.

```bash
# mermaid-cli (uses npx; or npm install -g @mermaid-js/mermaid-cli)
npx --yes @mermaid-js/mermaid-cli --version
```

## Commands (never overwrite an existing AN_vN)

Export every view (`source_correct`, `holos_as_coded`, `fork_delta`) for every existing Sankey JSON. PNG uses kaleido **scale 2**. Names are `sankey_<farm>_<view>_AN_vN.{svg,png}` so they do not collide with `sankey_<farm>_AN_vN.html`.

```bash
ghgsim sankey --export-static-views --scale 2
ghgsim sankey --export-static-views --farm dairy_forage_uncovered --scale 2
```

Render missing SVG/PNG for every committed `fork_diagram_AN_v*.mmd` (skips files that already exist):

```bash
ghgsim fork-diagram --render-existing
```

Equivalent one-shots:

```bash
npx --yes @mermaid-js/mermaid-cli \
  -i docs/figures/fork_diagram_AN_v2.mmd \
  -o docs/figures/fork_diagram_AN_v2.png \
  -b white
```

`ghgsim sankey` (without `--export-static-views`) still writes the next free HTML/JSON and, if kaleido is present, the per-view statics for that new version.

## This snapshot

AN_v1 statics written for the eight stylized farms plus `county_ADDISON`, three views each, plus `fork_diagram_AN_v1.png` and `fork_diagram_AN_v2.png`. Existing mermaid SVGs were left in place.
