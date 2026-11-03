---
title: Paper B living-paper dashboard
emoji: 🌾
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 5.50.0
app_file: app_AN_v1.py
pinned: false
license: apache-2.0
# Visibility: PRIVATE until submission. Spaces set visibility at creation
# (create with --private); it is not a README key. Not published yet.
---

# Paper B living-paper dashboard (AN_v1)

A Gradio app over ghgsim. Every number comes from ghgsim data files, a live
ghgsim run, or a SHA-256 hash computed at load time.

| Tab | What it shows | Source |
|---|---|---|
| County P/PE | May-Oct precipitation / potential evapotranspiration, Hargreaves vs Thornthwaite; state map + county table | `data/county_p_pe_may_oct_AN_v2.csv` |
| Version diff | Live recompute of a stylized example farm under IPCC 2006 vs the 2019 Refinement | `ghgsim.compat.farm.FarmModel`, `data/ipcc_params_AN_v*.csv` |
| Provenance | Commit SHA, package versions, external engines, manifest hashes re-checked | git, `docs/BUBBLE_SETUP_AN_v*.md`, `data/*manifest_AN_v*.json` |

Jargon: **P/PE** = growing-season precipitation divided by potential
evapotranspiration (below 1 = drier). **SHA-256** = a file fingerprint; a
match means the file is byte-identical to the one recorded in the manifest.

## Run locally

```bash
# from the ghgsim repo root
pip install -e .
pip install -r dashboard/requirements_AN_v1.txt
python dashboard/app_AN_v1.py      # then open http://127.0.0.1:7860
pytest tests/test_dashboard_AN_v1.py
```

## Known limits

- `example_farm_AN_v2` (with manure) runs under IPCC 2006 but not 2019: the
  parameter registry has no 2019 MCF climate zone (`cool_temperate_moist`).
  The app shows the ghgsim error instead of a number.
- The Holos stylized farms (`data/stylized_farms_AN_v*.yaml`) are not yet
  wired in; the clean IPCC 2006 vs 2019 stylized-farm run is a separate branch.
- For a Space, the app needs a ghgsim checkout with `data/`, `docs/` and
  `legacy/`; set `GHGSIM_ROOT` (and `GHGSIM_COMMIT`) when deploying.