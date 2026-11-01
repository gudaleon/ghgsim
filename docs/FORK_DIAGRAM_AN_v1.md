# Holos fork decision diagram (living paper)

**Version:** AN_v1  
**Date:** 2026-11-01  
**Does not overwrite** a later `docs/FORK_DIAGRAM_AN_vN.md`.

The diagram is generated from the newest versioned inputs, not from a hard-coded registry path. Re-run it whenever a fork is added or measured deltas change.

```bash
ghgsim fork-diagram
```

That command selects, by highest `AN_vN`:

- `data/holos_forks_AN_vN.json`
- `data/holos_fork_deltas_stylized_AN_vN.csv`
- `data/holos_fork_deltas_vt_de_AN_vN.csv`
- `data/coefficient_trace_AN_vN.csv`

and writes the next free version under `docs/figures/` (never overwrites):

- `fork_diagram_AN_vN.mmd` — Mermaid flowchart
- `fork_diagram_AN_vN.json` — dashboard payload (`nodes`, `edges`, `deltas`, `status`)
- `fork_diagram_AN_vN.svg` — if `mmdc` or `npx @mermaid-js/mermaid-cli` can run

This snapshot is **AN_v1**, built from `holos_forks_AN_v3.json`, stylized and VT/DE delta CSVs `AN_v2`, and `coefficient_trace_AN_v1.csv`.

## What the figure shows

Forks are decision nodes in calculation order: GE → enteric / Ym → VS → manure CH4 → N excretion → N2O → CO2e.

Each fork has two outgoing edges:

- **default** — the registered default option (`source_correct` for bug forks; `eccc_2022_canada` for `HOLOS.YM.dairy`)
- **alternate** — the other option (`holos_as_coded`, or IPCC 6.5% Ym), labelled with the MEASURED min–max % CO2e across stylized farms and VT/DE counties

Node colour is the coefficient-trace evidence status: green VERIFIED, amber SOURCE-TRACED, rose HOLOS-ONLY, grey UNVERIFIED / missing.

The JSON is what the future dashboard and living-paper front end should render interactively. Do not parse the Mermaid text for application state.

## Rendering SVG

`.github/workflows/ci.yml` is Python-only (pytest, ruff, license check) and does **not** install Node or mermaid-cli, so the automated checks do not render SVG. AN_v1 SVG was produced in the authoring environment with mermaid-cli 12.0.0 (`npx @mermaid-js/mermaid-cli`) and is committed as the living-paper figure. Render a later version locally:

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i docs/figures/fork_diagram_AN_v1.mmd -o docs/figures/fork_diagram_AN_v1.svg
```

or one-shot:

```bash
npx --yes @mermaid-js/mermaid-cli -i docs/figures/fork_diagram_AN_v1.mmd -o docs/figures/fork_diagram_AN_v1.svg
```

GitHub and many Markdown previews will also render the `.mmd` source if it is pasted into a Mermaid fence.

## Tests

`tests/test_fork_diagram.py` locks: every registry fork appears exactly once; the Mermaid and JSON are deterministic; adding a dummy fork adds one node; the committed AN_v1 files match a fresh build from the latest inputs. If you change forks or delta CSVs, run `ghgsim fork-diagram` and commit the new `AN_vN` figure (do not overwrite AN_v1).
