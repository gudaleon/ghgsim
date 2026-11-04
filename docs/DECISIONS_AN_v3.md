# Paper B technical decisions log (AN v3)

`DECISIONS_AN_v1.md` and `DECISIONS_AN_v2.md` already exist (ghgsim build-phase logs), so this
Paper B log is v3; nothing was overwritten. Alex asked (2026-11-03) that routine technical calls
be made by the agent and logged here so he can review or reverse them later. "Who" = who made
the call. All dates are 2026 (America/Toronto).

| # | Date | Decision | Who | Rationale | How to reverse |
|---|---|---|---|---|---|
| 1 | Nov 3 | County PE = **Hargreaves-Samani (FAO-56 Eq 52)**, **1991-2020** nClimDiv normals; Thornthwaite kept as a sensitivity column | Alex (card) | Hargreaves uses Tmax/Tmin range (closer to Penman-Monteith than Thornthwaite in dry regions); 1991-2020 is the current NOAA normals period | `growing_season_pe_mm` = `pe_thornthwaite_mm` (new `_AN_v3` CSV via `scripts/build_county_p_pe_AN_v2.py` logic) or `--start/--end` for another period |
| 2 | Nov 3 | Dry counties (P/PE < 1) in `holos_liang2020` use the **IPCC default EF1 = 0.01**; **0.005** (2019 dry-climate value) reported as a sensitivity | Alex (card) + agent (0.01 vs 0.005) | Liang et al. 2020 regression is fitted for humid conditions; 0.01 is the 2006/2019 aggregated default, the conservative choice | Switch fallback EF1 to 0.005 (`LIANG_DRY_FALLBACK_AN_v2.md`) |
| 3 | Nov 3 | Cattle **Ym** mapped by **forage share** (2019 Refinement Ym classes; see the enteric module docstring) | Agent | Ym in the 2019 Refinement depends on diet digestibility / forage share; stylized farms specify forage share, not DE | Use a single default Ym per animal category |
| 4 | Nov 3 | 2019 liquid/pit MCF uses the **12-month storage** row; stylized farms placed in **warm temperate moist** | Agent | Most US slurry storage is emptied once or twice a year; 12 mo is the upper storage row and the warm temperate moist zone matches the US dairy/swine belt. Table 10.17 fn 1 suggests 6 mo when retention is unknown | `storage_months=6`, or give `climate_zone_2019` / `county_fips` per farm (see #12) |
| 5 | Nov 3 | Added the 2006 **FracLossMS** (total N loss) path to the 2006 manure module | Agent | Needed so 2006 vs 2019 compares like with like for N available after storage | Drop the term (set `include_leach`/FracLossMS to 0 in 2006 runs) |
| 6 | Nov 3 | Global N2O Database daily `n2o` treated as **g N2O-N/ha/day** (x 44/28 for N2O) | Agent | Upload template asks for gN2O-N; see `BENCHMARKS_AN_v6.md`. Maintainers asked by email, no reply yet | If maintainers say N2O, remove the 44/28 factor |
| 7 | Nov 3 | **GLEAM-X**: run FAO's `gleam` R package (un-fao/GLEAM tag v0.8.0-alpha, commit 90e4161, AGPL-3) **unmodified** as an outside model on Bubble; separately reimplement from the **CC BY 4.0 GLEAM 3.0 model description** | Alex (card) + agent | AGPL code must not enter Apache-2.0 ghgsim; the CC BY document can be reimplemented with attribution; comparison is a consistency check, not validation | Drop either arm; no ghgsim code depends on the R package |
| 8 | Nov 3 | Inventory comparison: **Canada, UK, New Zealand, Ireland, Germany, Australia** (UNFCCC 2025 vs 2026 CRT) **plus the US** | Alex (card) | Mix of Annex I countries with documented 2019-Refinement uptake | Edit `scripts/fetch_inventories_AN_v1.py` country list |
| 9 | Nov 3 | US side = **EPA GHGI 2024 vs 2025 editions** (AR5 GWPs) | Agent | No 2026 US UNFCCC submission exists; EPA editions are the official equivalent | Replace when a newer EPA edition / UNFCCC submission appears |
| 10 | Nov 3 | **DayCent** and **COMET-Farm** are **optional outside models** (DayCent under U of T terms only; COMET-Farm via API when access is fixed) | Alex (card) | Access is pending; the paper must not depend on them | Promote to core once access is confirmed |
| 11 | Nov 3 | Dashboard Space **private** under **@globaltrotter** until submission | Alex (card + chat) | Unpublished results; Spaces visibility can be switched later | Change visibility in Space settings at submission |
| 12 | Nov 3 | 2019 manure MCF zone derived from **county annual MAT + annual P/PE** (nClimDiv 1991-2020, Hargreaves) when `county_fips` is given; explicit `climate_zone_2019` or MAT/ratio win; **tropical (MAT > 18 C) and boreal counties fall back to 2006 Table 10.17** | Agent | IPCC 2006 Vol 4 Ch 3 Annex 3A.5 zone rule; tropical needs MAP/elevation classes and boreal 2019 MCF cells are not yet in the registry, so no values are guessed | Pass `climate_zone_2019` explicitly; add boreal/tropical Table 10.17 cells to a new `ipcc_params_AN_v9.csv` |

## Notes
- Comparisons with field data are consistency checks, not validation.
- Caveat for #12: uncalibrated Hargreaves overestimates PE in humid areas, so some humid
  Midwest counties classify as "dry" (e.g. Polk County IA, P/PE 0.90). See
  `COUNTY_CLIMATE_ANNUAL_AN_v1.md`.
