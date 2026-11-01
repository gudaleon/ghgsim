# Holos Route A - Sources Table

**Generated:** 2026-11-01  
**Goal:** 4 (Holos Route A) Phase 2  
**Supersedes:** `docs/HOLOS_SOURCES_AN_v1.md` (not overwritten)

## Complete Source Citations

| # | Source | Type | DOI/URL | Module | Coverage |
|---|--------|------|---------|--------|----------|
| 1 | IPCC 2006 Guidelines Vol 4 Ch 10 | International Standard | https://www.ipcc-nggip.iges.or.jp/public/2006gl/ | Enteric, VS, Manure | Eq 10.3, 10.21, 10.23, 10.24, 10.25-10.27, 10.30; Tables 10.12, 10.17, 10.19, 10.21, 10.22, 10A-4, 10A-5 |
| 2 | IPCC 2006 Guidelines Vol 4 Ch 11 | International Standard | https://www.ipcc-nggip.iges.or.jp/public/2006gl/ | Soil N2O | Eq 11.1, 11.9, 11.10; Tables 11.1, 11.3 |
| 3 | IPCC 2019 Refinement Vol 4 Ch 10 | International Standard | https://www.ipcc-nggip.iges.or.jp/public/2019rf/vol4.html | Enteric Ym where matched | Table 10.12 (Updated) p. 10.46 values already in `data/ipcc_params_AN_v4.csv` |
| 4 | Little et al. (2008) Holos v1.1.x Methodology | AAFC Technical Report | https://agriculture.canada.ca/en/agricultural-production/holos-software-program | All modules | General methodology |
| 5 | EPA 2025 Inventory Annex 3.11 | US Government Report | EPA GHGI website | US config | Table A-177 state GE, Ym, VS, TAM, Nex |

Benchaar et al. (2001), Coates et al. (2020), and Rochette et al. (2008) remain listed in `HOLOS_SOURCES_AN_v1.md`. Phase 2 modules implement IPCC 2006 equations; those papers were not re-used as numeric sources here.

## Equations by Module (Phase 2)

### HolosEnteric (`holos.enteric` v1.1.0)

| Equation | Source | Page | Implementation |
|----------|--------|------|----------------|
| CH4 = GE × (Ym/100) × 365 / 55.65 | IPCC 2006 Vol4 Ch10 Eq 10.21 | 10.30 | `enteric.py` via `process_defs.enteric_ch4_process` |
| GE from NE and DE% | IPCC 2006 Vol4 Ch10 Eq 10.3 | 10.16 | `process_defs.ge_intake_variable` |

### HolosVolatileSolids (`holos.vs` v1.0.0)

| Equation | Source | Page | Implementation |
|----------|--------|------|----------------|
| VS = [GE × (1 − DE%/100) + UE × GE] × [(1 − ASH)/18.45] | IPCC 2006 Vol4 Ch10 Eq 10.24 | 10.54 | `vs.py` |
| UE = 0.04 typical; 0.02 if DE% > ~80 | IPCC 2006 Vol4 Ch10 text | 10.54 | `process_defs.urinary_energy_ipcc` |

### HolosManureCH4 (`holos.manure_ch4` v1.0.0)

| Equation | Source | Page | Implementation |
|----------|--------|------|----------------|
| CH4 = VS × 365 × B0 × 0.67 × Σ(MCF × frac) | IPCC 2006 Vol4 Ch10 Eq 10.23 | 10.53 | `manure_ch4.py` |

### HolosManureN2O (`holos.manure_n2o` v1.0.0)

| Equation | Source | Page | Implementation |
|----------|--------|------|----------------|
| N2O_direct-N = Nex × Σ(EF3 × frac) | IPCC 2006 Vol4 Ch10 Eq 10.25 | 10.55 | `manure_n2o.py` |
| N_vol = Nex × Σ(FracGasMS × frac); N2O_G-N = N_vol × EF4 | IPCC 2006 Vol4 Ch10 Eq 10.26-10.27 | 10.56 | `manure_n2o.py` |
| Nex = Nrate × TAM / 1000 × 365 | IPCC 2006 Vol4 Ch10 Eq 10.30 | 10.57 | `manure_n2o.py` |

## Parameter Status Summary (Phase 2 files)

Label rule: VERIFIED requires a primary published source with page and table (or equation). A Holos file:line is never VERIFIED.

### Canada (`data/holos_params_canada_AN_v3.csv`)

Counts are asserted in `tests/test_holos_param_status.py`. Categories:

- **VERIFIED:** IPCC 2006/2019 values independently matched to `data/ipcc_params_AN_v4.csv` (selected Ym, B0 dairy, Nrate, most MCF, UE constants).
- **SOURCE-TRACED:** Holos Table 16/18 TAM and unmatched Ym; dairy Ym 5.6% citing ECCC 2022 (not independently confirmed); B0 beef 0.17; pasture MCF cool 0.015; Holos grain-percent UE switch; ASH example 8%.
- **UNVERIFIED:** calf VS coefficient 0.0093; calf N 0.078 kg N/head/day; cover factors 0.4 and 0.25.

### US (`data/holos_params_us_AN_v2.csv`)

- **VERIFIED:** EPA Annex 3.11 Table A-177 GE, Ym, VS, TAM, Nex; IPCC 2006 B0 dairy 0.24 (Table 10A-4); Nrate beef 0.31 (Table 10.19); matching Table 10.17 MCF.
- **SOURCE-TRACED:** dairy Nrate 0.47 (not Table 10.19 NA 0.44); beef B0 0.17 (not Table 10A-5 0.19); pasture MCF 0.02 (not 15C 0.015).

## Implementation Integrity

- No GPL code in Apache-2.0 modules (`scripts/check_licenses.py`).
- Holos-as-coded behaviour is a fork, not the default.
- Fork registry: `data/holos_forks_AN_v1.json`.

## Files

- Modules: `src/ghgsim/modules/holos/{enteric,vs,manure_ch4,manure_n2o,manure,soil_n2o}.py`
- Parameters: `data/holos_params_canada_AN_v3.csv`, `data/holos_params_us_AN_v2.csv`
- Forks: `data/holos_forks_AN_v1.json`
- This file: `docs/HOLOS_SOURCES_AN_v2.md`
