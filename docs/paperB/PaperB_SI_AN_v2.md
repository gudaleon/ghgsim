# Supplementary Information: Living papers make agricultural greenhouse gas estimates re-runnable as methods change

**Version:** PaperB_SI_AN_v2 (2026-11-03; supersedes PaperB_SI_AN_v1, kept unchanged), to accompany PaperB_draft_AN_v8. Main-text reference numbers follow draft v8. Source: ghgsim repository (github.com/gudaleon/ghgsim, main commit d1f507f), `docs/*.md`. Every entry cites the repo file it comes from. Comparisons with EPA or field data are consistency checks, not validation.

## S1. Decision log summary

Row numbers (#) refer to items in each log; check them against the logs before submission. Full logs: `docs/DECISIONS_AN_v1.md` to `docs/DECISIONS_AN_v7.md` (earlier logs are never edited; later ones correct them).

| # | Decision | Who | Source |
|---|---|---|---|
| 1 | County PE by Hargreaves–Samani (FAO-56 Eq. 52), 1991–2020 nClimDiv normals; Thornthwaite kept as a sensitivity column | Author | DECISIONS_AN_v3 #1 |
| 2 | Dry counties on the Liang et al. regression path use IPCC default EF1 = 0.01; 0.005 (2019 dry) is a sensitivity | Author + agent | DECISIONS_AN_v3 #2; LIANG_DRY_FALLBACK_AN_v2 |
| 3 | Cattle Ym mapped by forage share (2019 Ym classes) | Agent | DECISIONS_AN_v3 #3 |
| 4 | 2019 liquid/pit MCF from the 12-month storage row; stylized farms in warm temperate moist | Agent | DECISIONS_AN_v3 #4; DECISIONS_AN_v4 #5 |
| 5 | 2006 FracLossMS path added so N after storage is comparable | Agent | DECISIONS_AN_v3 #5 |
| 6 | Global N2O Database values treated as N2O-N (×44/28), pending maintainers' reply | Agent | DECISIONS_AN_v3 #6; BENCHMARKS_AN_v6 |
| 7 | GLEAM run unmodified as outside software (AGPL-3); pin corrected to b0937d2 | Author + agent | DECISIONS_AN_v3 #7; DECISIONS_AN_v6 #9; DECISIONS_AN_v7 #4 |
| 8 | Comparator inventories: Canada, UK, New Zealand, Ireland, Germany, Australia; US from EPA 2024 vs 2025 editions | Author | DECISIONS_AN_v3 #8–9 |
| 9 | DayCent and COMET-Farm are optional outside models | Author | DECISIONS_AN_v3 #10 |
| 10 | County climate zones from the IPCC 2019 zone map (Lewis 2022); Hargreaves/Thornthwaite as sensitivities | Agent | DECISIONS_AN_v4 #2 |
| 11 | Polar (Alaska) counties use 2006 per-°C MCFs for 2019 (no polar column) | Agent | DECISIONS_AN_v4 #3 |
| 12 | Same activity data in both editions; North America 2006 Annex 10A system shares; all hogs as market swine | Agent | DECISIONS_AN_v4 #6 |
| 13 | Withheld (D) cells: three variants; headline D_allocated by operations with inventory | Agent | DECISIONS_AN_v4 #7; DECISIONS_AN_v5 #1–3 |
| 14 | Synthetic N from 2017 AAPFCO state totals allocated by 2022 fertilizer expense (gap) | Agent | DECISIONS_AN_v4 #8 |
| 15 | Soil N2O scope (synthetic, applied manure, PRP, 19 residue series); F_OS and F_SOM excluded | Agent | DECISIONS_AN_v4 #9; DECISIONS_AN_v5 #5, #10 |
| 16 | AR5 GWPs (CH4 28, N2O 265) | Agent | DECISIONS_AN_v4 #11 |
| 17 | Blank IPCC cells substituted from generic rows only where flagged SUBSTITUTE; otherwise left blank | Agent | DECISIONS_AN_v5 #4, #9 |
| 18 | Recompute pipeline: staging copy, light/full profiles, reproduction rules, weekly upstream check | Agent | DECISIONS_AN_v6 #1–12 |
| 19 | CI lint and licence-check fixes; 0 of 121 paper numbers moved | Agent | DECISIONS_AN_v7 #1–3 |
| 20 | Paper agent (MCP) and dashboard share one code path; no LLM produces numbers | Agent | DECISIONS_AN_v7 #5–8 |

Earlier build-phase logs (DECISIONS_AN_v1–v2) record that the prior engine's Vermont/Delaware county results were reproduced to <1e-15 relative difference once EPA state N-excretion overrides were passed, and that the Holos reimplementation used only published sources.

## S2. Parameter provenance

- Registry: `data/ipcc_params_AN_v10.csv` (v9 plus 262 page-cited rows). Each row: guideline, table, equation, page, units, status.
- 2019 Table 10.17 (Updated) MCFs: all 10 columns (lagoon, liquid/slurry and pit at 1, 3, 4, 6, 12 months), boreal and four tropical sub-zones, each VERIFIED against the PDF text, p. 10.68 (DECISIONS_AN_v4 #1).
- 2006 Table 10.17 per-°C MCFs for 10–28 °C (pp. 10.44–10.45; same as Annex 10A) (DECISIONS_AN_v4 #4).
- 2019 VS (Table 10.13A, p. 10.56) and TAM (Table 10A.5, p. 10.117) used in the 2019 county run.
- 2019 B0 and N rate (Tables 10.16, 10.19 Updated); FracGasMS and FracLeachMS (Table 10.22 Updated); 2006 FracLossMS (Table 10.23, p. 10.67).
- Dry-fallback EF1: 0.01 (2006 Vol 4 Ch 11 Table 11.1); 0.005 (2019 Table 11.1 Updated, registry key IPCC2019.EF1.dry).
- Residue factors: 2006 Table 11.2; 2019 Table 11.1a; NA cells filled from generic rows, flagged SUBSTITUTE.
- Known blanks: 2006 Table 10.22 other-cattle liquid and swine dry-lot FracGasMS; 2006 Table 10.23 other-cattle liquid FracLossMS.
- Source PDFs: IPCC 2006 and 2019 Vol 4 Ch 10 and 11, SHA-256 fingerprinted in `data/upstream_sources_AN_v1.json`.
- Earlier spot checks: 15 of 15 parameters verified against IPCC tables (`docs/PARAM_SPOT_CHECK_AN_v1.md`); reconciliation in `docs/PARAM_RECONCILIATION_AN_v1.md`.

## S3. US county run: coverage and gaps

National results (Mt CO2e, AR5, 2022 activity) from `docs/US_COUNTY_RUN_AN_v2.md`:

| Variant | Category | 2006 | 2019 | Δ% | EPA 2022 | 2019/EPA |
|---|---|---:|---:|---:|---:|---:|
| D_allocated | Enteric CH4 | 155.9 | 183.2 | +17.5 | 192.6 | 0.95 |
| D_allocated | Manure CH4 | 42.2 | 59.2 | +40.4 | 64.7 | 0.92 |
| D_allocated | Manure N2O | 11.1 | 16.6 | +49.3 | 17.0 | 0.98 |
| D_allocated | Soil N2O | 120.2 | 82.4 | −31.5 | 291.8 | 0.28 |
| D_allocated | Total | 329.4 | 341.4 | +3.6 | 566.1 | 0.60 |
| disclosed | Total | 278.9 | 287.6 | +3.1 | 566.1 | 0.51 |

The *reconstructed* variant equals *disclosed* exactly (complementary suppression).

Drivers of the 2006→2019 soil drop (D_allocated): PRP direct N2O 24.3→4.9; crop residues 22.4→12.7; synthetic N 49.2→40.5.

Gaps (1–6 as listed in US_COUNTY_RUN_AN_v2; 7–8 from DECISIONS_AN_v4 #6, #8):
1. Organic soils (F_OS) and SOM mineralisation (F_SOM) not estimated (no public county data; EPA uses DayCent).
2. Hay, forage, silage, cotton and vegetable residues excluded.
3. 2006 Table 10.22 FracGas blanks: N conserved to soils, volatilisation 0 (flagged).
4. Residue NA cells filled from generic rows (SUBSTITUTE).
5. No irrigation adjustment to FracLeach; no residue burning; FracRemove = 0.
6. Allocated (D) cells are model estimates.
7. Census 31 December inventories vs annual average populations; all hogs as market swine; poultry litter split assumed.
8. Synthetic N mixes 2017 state totals with a 2022 expense-based allocation.

Climate zones (IPCC map, 3,142 counties; `docs/CLIMATE_ZONES_AN_v1.md`): warm temperate moist 1,232; warm temperate dry 898; cool temperate dry 612; cool temperate moist 288; tropical moist 62; tropical dry 30; boreal dry 11; boreal moist 5; polar moist 3; polar dry 1.

## S4. Inventory tables

### S4.1 Comparator countries, 2025 vs 2026 submission, sector 3 (kt CO2e; CRT Table 8s1)

| Country | 1990 | 2005 | 2023 | Main documented cause |
|---|---:|---:|---:|---|
| Canada | +225.5 (+0.53%) | +507.8 (+0.90%) | +279.5 (+0.51%) | Temperature-based MCF method for dairy and swine liquid manure; lime and crop-yield corrections |
| United Kingdom | +459.8 (+0.91%) | +447.3 (+0.97%) | +595.2 (+1.44%) | Dairy growth curve re-fitted; grass energy content for sheep; low-emission slurry spreading uptake |
| New Zealand | −165.1 (−0.45%) | −249.7 (−0.58%) | −326.5 (−0.80%) | Dairy effluent practices; non-urea fertiliser EF; partial alignment with the 2019 Refinement; corrections |
| Ireland | 0.0 | 0.0 | +42.2 (+0.21%) | Revised populations and crop statistics, 2013–2023 |
| Germany | +787.7 (+1.08%) | +202.8 (+0.34%) | +410.8 (+0.75%) | Higher milk yields; gilts split from sows; soil N2O revisions |
| Australia | −4,406.3 (−4.68%) | −3,956.9 (−4.56%) | −3,606.1 (−4.38%) | New grazing-manure method; 2019 Refinement wet/dry urine and dung EFs; new sheep data |

Source: `docs/INVENTORIES_AN_v1.md`; NIDs [35–40].

### S4.2 Agriculture totals, inventory year 2024 (kt CO2e, AR5)

| Country | Total | 3.A Enteric | 3.B Manure | 3.D.1 Direct soil | 3.D.2 Indirect soil |
|---|---:|---:|---:|---:|---:|
| Canada | 56,403.5 | 26,390.3 | 8,185.6 | 14,520.4 | 3,845.2 |
| United Kingdom | 40,960.6 | 22,945.2 | 6,628.3 | 7,700.2 | 1,968.1 |
| New Zealand | 40,148.4 | 31,588.3 | 1,717.0 | 4,910.7 | 1,216.8 |
| Ireland | 19,640.9 | 12,704.8 | 2,408.7 | 3,232.3 | 669.5 |
| Germany | 53,307.9 | 25,848.0 | 9,067.3 | 12,040.7 | 2,432.4 |
| Australia | 75,672.3 | 58,832.5 | 4,339.4 | 7,007.5 | 2,006.0 |

### S4.3 United States, EPA 2024 vs 2025 editions (Mt CO2e, AR5; Table 5-1)

| Category | 1990 | 2005 | 2022 |
|---|---:|---:|---:|
| Enteric CH4 | 0.0 | 0.0 | 0.0 |
| Manure CH4 | 0.0 | 0.0 | 0.0 |
| Manure N2O | 0.0 | 0.0 | 0.0 |
| Agricultural soils N2O | +0.3 | +0.6 | +1.0 |
| Rice CH4 | 0.0 | 0.0 | −0.9 |
| Liming CO2 | 0.0 | 0.0 | −0.1 |
| Urea CO2 | 0.0 | 0.0 | −0.1 |
| Total (Table 5-1 difference) | +0.4 | +0.7 | −0.1 |
| Total (EPA Table 9-2) | +0.3 | +0.7 | −0.1 |

Source: `docs/INVENTORIES_US_AN_v1.md`. Open flag: EPA's rice text gives −0.3 Mt for 2022, its tables −0.9 Mt.

Inventory gaps: no US 2026 UNFCCC submission or EPA 1990–2024 edition; the AR4→AR5 GWP switch effect is not in the 2026 documents; no country isolates the 2019 Refinement effect; five of six CRT 2026 zips must be downloaded by hand (unfccc.int blocks scripts).

## S5. Reproduction

```
pip install -r requirements_AN_v1.txt && pip install -e . --no-deps
python scripts/recompute_all_AN_v1.py --profile full
python scripts/diff_results_AN_v1.py results/results_manifest_AN_v2.json build/m.json --out build/diff.md
```
Reference manifest: `results/results_manifest_AN_v2.json` (121 paper numbers; latest full recompute moved 0).
