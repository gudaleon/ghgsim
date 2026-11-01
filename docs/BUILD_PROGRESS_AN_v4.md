# ghgsim Build Progress - AN v4

## Overview

Building ghgsim from livingghg v3 as a modular, Apache-2.0, open-source GHG framework for agricultural emissions.

**Repository:** https://github.com/gudaleon/ghgsim (private, non-commercial academic)  
**Base:** livingghg v3 (Alex Neumann, University of Toronto)  
**License:** Apache-2.0  
**Target:** Full US county ensemble with IPCC 2006/2019, Holos US adaptation, soil data, CLI, dashboard

---

## Phase Status

### ✅ Phase 1: Scaffold & Compatibility (PR #1 - OPEN)
**Branch:** `cursor/phase-1-scaffold-compat-353b`  
**Status:** Complete, all 21 v3 tests passing

- Repository structure created
- Legacy v3 code imported to `legacy/livingghg_AN_v3/`
- Compatibility layer for v3 tests
- CI/CD with GitHub Actions
- Codespaces dev container
- All dependencies in pyproject.toml

### ✅ Phase 2: Module Contract & Execution Graph (PR #2 - OPEN)
**Branch:** `cursor/phase-2-contract-graph-353b`  
**Status:** Complete, 32 tests passing (21 v3 + 11 Phase 2)

- Module Protocol with pure, deterministic, vectorized interface
- Unit checking with pint
- DAG execution graph with cycle detection
- YAML model loader
- Tests for acceptance criteria 3 (stub) and 9

### ✅ Phase 3: Registry & Manifest (PR #3 - OPEN)
**Branch:** `cursor/phase-3-registry-manifest-353b`  
**Status:** Complete, 44 tests passing (21 v3 + 11 Phase 2 + 12 Phase 3)

- ParameterRegistry with VERIFIED/UNVERIFIED gate
- RunManifest with deterministic hashing
- Parameter CSV loader
- `data/ipcc_params_AN_v4.csv` with 138 VERIFIED parameters
- Tests for acceptance criteria 6 and 7

---

## Remaining Phases (To Be Implemented)

### 🔄 Phase 4: IPCC Modules (Current)
**Branch:** `cursor/phase-4-ipcc-modules-353b`  
**Base:** `cursor/phase-3-registry-manifest-353b`

**Objectives:**
- Wrap v3 modules (soil_n2o, enteric, manure, crop_residue) as ghgsim Module implementations
- Create IPCC 2006 and IPCC 2019 module variants
- Reproduce v3 VT/DE trial results to 1e-9 relative precision (Acceptance Test 2)
- Move data loaders to `src/ghgsim/io/`
- Create YAML model definitions

**Acceptance Tests:**
- Test 2: VT/DE trial reproduction to 1e-9 relative

### 📋 Phase 5: Services (Monte Carlo, Sobol, Estimation, Forks)
**Branch:** `cursor/phase-5-services-353b`  
**Base:** `cursor/phase-4-ipcc-modules-353b`

**Objectives:**
- Monte Carlo service with LHS sampling
- Sobol sensitivity service (SALib integration)
- Bayesian parameter estimation service (emcee)
- Fork registry and pipeline system
- Tests for acceptance criteria 4, 5, 8

**Acceptance Tests:**
- Test 3 (complete): User module with MC/Sobol/estimation
- Test 4: Sobol identifies top 3 factors (VT dairy)
- Test 5: Estimation with synthetic data converges
- Test 8: Fork registry importance ranking

### 📋 Phase 6: Holos US Adaptation
**Branch:** `cursor/phase-6-holos-us-353b`  
**Base:** `cursor/phase-5-services-353b`

**Objectives:**
- Route A: Re-implement Holos equations from ORIGINAL sources (not Holos code)
- Pin Holos commit from https://github.com/holos-aafc/Holos (GPL-3.0)
- Map Canadian parameters to US sources:
  - EPA GHG Inventory 1990-2023 Annex 3
  - USDA NASS agricultural data
  - USGS water/nitrogen data
  - NRCS soil data
- Provide 'Canada-default' and 'US-adapted' configurations
- CI license check: fail if GPL code enters core
- Route B (GPL wrapper): document only, no code in repo

**License Constraint:**
- Holos is GPL-3.0
- ghgsim is Apache-2.0
- Must cite ORIGINAL equation sources, not Holos code
- No GPL code in Apache core

### 📋 Phase 7: US Cattle Classes + Swine + Poultry + Soil Data
**Branch:** `cursor/phase-7-us-livestock-soil-353b`  
**Base:** `cursor/phase-6-holos-us-353b`

**Objectives:**
- US cattle classification system (EPA Inventory categories)
- Swine emission modules
- Poultry emission modules
- USDA NRCS soil data integration:
  - gSSURGO with STATSGO2/gNATSGO fallback
  - Aggregated area-weighted to county level
  - Texture, SOC, drainage class, pH, bulk density
  - Provenance: dataset, version/date, URL, DOI
- Commit only county aggregates (not raw rasters)
- CI uses VT/DE sample only

**Data Requirements:**
- County-level soil aggregates with provenance
- EPA Inventory cattle classes
- USDA livestock parameters

### 📋 Phase 8: Ensemble, CLI, Dashboard, Archive
**Branch:** `cursor/phase-8-final-353b`  
**Base:** `cursor/phase-7-us-livestock-soil-353b`

**Objectives:**
- US county ensemble command:
  - Windows-friendly .bat + Python entry point
  - Worker count = cores - 2
  - Trial mode for VT+DE only
  - CI runs VT+DE only
- CLI with `ghgsim` command
- Local dashboard (NOT public, Codespaces-compatible)
- Paper-agent API endpoints
- Archive command for run provenance
- Final documentation

**Commands:**
- `ghgsim run <model.yaml>` - Single run
- `ghgsim ensemble --states VT,DE` - County ensemble
- `ghgsim archive <run_id>` - Archive run
- `ghgsim serve` - Start dashboard (local only)

---

## Parameter Reconciliation

**v3 (ipcc_params_AN_v2.csv):** 139 parameters  
**v4 (ipcc_params_AN_v4.csv):** 138 parameters (all VERIFIED)

**Excluded (1):**
- `IPCC2006.FracLeachMS.all` - No default value in IPCC tables (country-specific)

**All 138 v4 parameters are VERIFIED** from IPCC 2006 Guidelines Volume 4 or IPCC 2019 Refinement Volume 4.

---

## Acceptance Test Status

| # | Test | Status | Phase |
|---|------|--------|-------|
| 2 | VT/DE trial match to 1e-9 | ⏳ Pending | Phase 4 |
| 3 | User module integration | 🟡 Stub only | Phase 5 (complete) |
| 4 | Sobol top 3 factors | ⏳ Pending | Phase 5 |
| 5 | Estimation convergence | ⏳ Pending | Phase 5 |
| 6 | Determinism | ✅ Complete | Phase 3 |
| 7 | VERIFIED gate | ✅ Complete | Phase 3 |
| 8 | Fork ranking | ⏳ Pending | Phase 5 |
| 9 | Unit mismatch | ✅ Complete | Phase 2 |

---

## Data Sources

### IPCC Parameters
- 2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4 (Agriculture, Forestry and Other Land Use)
- 2019 Refinement to the 2006 IPCC Guidelines, Volume 4

### US Data
- **EPA:** GHG Inventory 1990-2023, Annex 3 (Methodological Descriptions)
- **USDA NASS:** Census of Agriculture 2002, 2007, 2012, 2017, 2022
- **USGS:** Falcone 2021 county nitrogen data
- **USDA NRCS:** gSSURGO soil database, STATSGO2, gNATSGO

### Canadian Data (Holos comparison only)
- Soil Landscapes of Canada
- Holos model parameters (GPL-3.0, for comparison only)

---

## Build Constraints

1. **License:** Apache-2.0, no GPL code in core
2. **Reproducibility:** Deterministic hashing, full provenance
3. **Verification:** Default runs refuse UNVERIFIED parameters
4. **Testing:** All v3 tests must pass, add tests for each component
5. **CI:** Keep green, run VT/DE trial only
6. **Privacy:** Private repo, no public GitHub Pages
7. **Data:** No invented parameters/citations, use UNVERIFIED with TODO if needed
8. **Stacking:** One branch and one stacked PR per phase
9. **No merges:** Never merge, never modify earlier PR branches

---

## Current Focus: Phase 4 IPCC Modules

Starting implementation of IPCC modules to wrap v3 functionality with the new Module contract.
