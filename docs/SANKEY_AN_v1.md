# Per-farm emissions Sankey diagrams (living paper)

**Version:** AN_v1  
**Date:** 2026-11-01  
**Does not overwrite** a later `docs/SANKEY_AN_vN.md`.

Each stylized farm (and optionally a VT/DE county) gets a Sankey of **computed** Holos-module flows. No invented numbers. Re-run whenever the newest `stylized_farms_AN_vN.yaml` or Holos modules change.

```bash
ghgsim sankey
ghgsim sankey --farm dairy_forage_uncovered
ghgsim sankey --county ADDISON
```

The command selects the highest `data/stylized_farms_AN_vN.yaml` and writes the next free version under `docs/figures/` (never overwrites):

- `sankey_<farm>_AN_vN.html` — Plotly (CDN), interactive, three views
- `sankey_<farm>_AN_vN.json` — dashboard payload (`nodes`, `links`, `values`, units, engine version, fork set, inputs file)
- `sankey_<farm>_AN_vN.svg` / `.png` — static paper figure **only if** `plotly` and `kaleido` are installed

This snapshot is **AN_v1**, built from `stylized_farms_AN_v2.yaml` and Holos modules in ghgsim 0.4.0. An optional county example is `sankey_county_ADDISON_AN_v1` (VT/DE trial table + EPA Annex 3.11 activity).

## Views

All values are **kg CO2e**. Gases are labelled with the GWPs used in the engine (IPCC AR5 100-year, no climate-carbon feedbacks: CH4 = 28, N2O = 265). Total CO2e in tonnes is kg / 1000, matching `scripts/measure_holos_forks_stylized_AN_v2.py`.

1. **source_correct** — registered fork defaults. Flow: animal groups → emission processes (enteric CH4, manure CH4 by storage system, direct manure N2O, indirect N2O) → CH4 / N2O → total CO2e.
2. **holos_as_coded** — every registered non-default option at once (the same stack as the COMBINED measurement row).
3. **fork delta** — `source_correct` CO2e plus or minus a band for each single-fork change, ending at `holos_as_coded`. Decreases leave as *removed* sinks; increases enter as *added* sources. A leftover *interaction* band appears only when the combined stack is not the sum of the single-fork deltas.

County diagrams add a **soil N inputs → soil N2O** path when `HolosSoilN2O` produces a number (fertilizer / crop / PRP). Stylized farms do not run soil N2O.

## Static images

`.github/workflows/ci.yml` is Python-only and does **not** install Node, plotly, or kaleido. AN_v1 HTML/JSON were produced in the authoring environment without kaleido, so **no SVG/PNG is committed** unless a later environment has:

```bash
pip install plotly kaleido
ghgsim sankey --farm dairy_forage_uncovered
```

The JSON is the source of truth for the dashboard. The HTML is a Plotly front-end over that JSON.

## Tests

`tests/test_emissions_sankey.py` locks: every stylized-YAML farm gets a diagram; inflows equal outflows at each node (within 1e-6 kg CO2e); totals match the Holos engine CO2e; output is deterministic; writes refuse to overwrite an existing `AN_vN`.
