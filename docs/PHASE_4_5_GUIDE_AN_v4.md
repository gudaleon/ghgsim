# Phase 4-8 Implementation Guide

## Phase 4: IPCC Modules

### Goal
Wrap livingghg v3 calculation functions as ghgsim Module implementations that satisfy the Module Protocol while preserving exact numerical behavior.

### Strategy
1. Create module implementations in `src/ghgsim/modules/ipcc2006/` and `src/ghgsim/modules/ipcc2019/`
2. Each module wraps one v3 calculation function
3. Declare inputs, parameters, outputs with units
4. Cite original IPCC sources
5. Test reproduction of v3 VT/DE trial results to 1e-9 relative precision

### Modules to Implement

#### IPCC 2006
- `ipcc2006.soil_n2o` - Direct and indirect N2O emissions from managed soils
- `ipcc2006.enteric` - Enteric CH4 from cattle
- `ipcc2006.manure` - CH4 and N2O from manure management
- `ipcc2006.crop_residue` - N inputs from crop residues

#### IPCC 2019
- `ipcc2019.soil_n2o` - Updated N2O emission factors (climate disaggregation)
- `ipcc2019.enteric` - Updated enteric CH4 (diet-specific Ym values)
- `ipcc2019.manure` - Updated manure emission factors

### Data Loaders (move to src/ghgsim/io/)
- `nass.py` - USDA NASS Census data
- `usgs.py` - USGS nitrogen data
- `epa.py` - EPA cattle emission factors

### Test Requirements
- All v3 tests still pass (21 tests)
- VT/DE trial reproduction to 1e-9 relative (Acceptance Test 2)
- Unit tests for each module
- At least 50 total tests

---

## Phase 5: Services

### Goal
Implement Monte Carlo, Sobol sensitivity, Bayesian estimation, and fork registry services.

### Components

#### Monte Carlo Service (`src/ghgsim/services/montecarlo.py`)
- LHS (Latin Hypercube Sampling) with parameter distributions
- Vectorized execution over N samples
- Summary statistics (mean, median, percentiles, CV)

#### Sobol Service (`src/ghgsim/services/sobol.py`)
- SALib integration for global sensitivity analysis
- First-order, second-order, and total-order indices
- Importance ranking

#### Estimation Service (`src/ghgsim/services/estimation.py`)
- Bayesian parameter estimation with emcee
- MCMC sampling
- Prior specification
- Convergence diagnostics

#### Fork Registry (`src/ghgsim/services/forks.py`)
- Fork definitions (equation alternatives)
- Importance ranking based on sensitivity
- Pipeline execution

### Test Requirements
- Acceptance Test 3 (complete): User module with MC/Sobol/estimation
- Acceptance Test 4: Sobol identifies top 3 factors for VT dairy
- Acceptance Test 5: Estimation converges with synthetic data
- Acceptance Test 8: Fork registry ranks by importance
- At least 70 total tests

---

## Phase 6: Holos US Adaptation

### Goal
Implement Holos-style cattle equations using ORIGINAL published sources, adapted for US parameters.

### Route A: Apache-2.0 Re-implementation
1. **Pin Holos commit** from https://github.com/holos-aafc/Holos (GPL-3.0)
2. **Read equation descriptions** in Holos documentation
3. **Find ORIGINAL sources** cited by Holos (AAFC technical bulletins, peer-reviewed papers)
4. **Re-implement from originals**, cite those, not Holos code
5. **Map Canadian parameters to US equivalents:**
   - Province → State (EPA Inventory regions)
   - Canadian climate zones → US climate data
   - Soil Landscapes of Canada → NRCS soil data
   - Canadian feed tables → US NASS/EPA values

### Route B: GPL Wrapper (Document Only)
- Describe how a GPL wrapper could call Holos as subprocess
- NOT implemented in repo (license incompatibility)
- Document in `docs/HOLOS_GPL_WRAPPER_PLAN.md`

### Parameter Mapping
- **Canada:** Soil Landscapes of Canada, AAFC province tables
- **US:** NRCS gSSURGO, EPA Inventory 1990-2023 Annex 3, USDA NASS

### Configurations
- `holos_canada_default.yaml` - Original Canadian parameterization
- `holos_us_adapted.yaml` - US data sources

### License Safeguards
- CI check: fail if GPL headers found in `src/ghgsim/`
- All equation citations must point to ORIGINAL peer-reviewed sources
- Holos mentioned only in documentation and as inspiration

### Test Requirements
- At least 85 total tests
- Unit tests for each Holos module
- Comparison with published Holos results (qualitative, not quantitative)

---

## Phase 7: US Livestock & Soil Data

### Goal
Add US-specific livestock categories and county-level soil data.

### US Cattle Classes
Based on EPA GHG Inventory Annex 3.10:
- Dairy cows (milk producing)
- Dairy heifers
- Beef cows
- Beef cattle (feedlot)
- Beef cattle (other)

### Swine Categories
EPA Annex 3.10:
- Market swine
- Breeding swine

### Poultry Categories
EPA Annex 3.10:
- Broilers
- Layers
- Turkeys

### Soil Data Integration
**Source:** USDA NRCS gSSURGO (Gridded Soil Survey Geographic Database)

**Workflow:**
1. Download gSSURGO for US (state-by-state)
2. Fallback to STATSGO2/gNATSGO for missing areas
3. Extract key properties:
   - Soil texture (sand/silt/clay fractions)
   - Soil organic carbon (SOC %)
   - Drainage class
   - pH
   - Bulk density
4. Aggregate to county level (area-weighted mean)
5. Store with provenance:
   ```csv
   fips,texture_sand_pct,texture_silt_pct,soc_pct,drainage_class,ph,bulk_density_g_cm3,source_dataset,source_version,source_date,source_url,source_doi
   ```

**Data Commits:**
- Commit only county aggregates to `data/soil/county_soil_nrcs_<version>.csv`
- Never commit raw rasters (too large)
- Include VT+DE sample for CI

**Provenance:**
- Dataset name (gSSURGO)
- Version/survey date
- Download URL
- DOI if available

### Test Requirements
- At least 100 total tests
- County soil loader tests
- Livestock classification tests
- VT/DE soil data included

---

## Phase 8: Ensemble, CLI, Dashboard, Archive

### Goal
Final integration: batch ensemble runs, CLI interface, local dashboard, provenance archiving.

### US County Ensemble

**Command:**
```bash
# Trial mode (VT + DE only, ~30 counties)
ghgsim ensemble --mode trial --workers 4

# Full US (optional, not run in CI)
ghgsim ensemble --mode full --workers 10
```

**Windows Support:**
- `run_ensemble.bat` batch file
- Python entry point: `ghgsim.api.cli:ensemble`

**Worker Pool:**
- Default: `multiprocessing.cpu_count() - 2`
- Configurable: `--workers N`

**CI Constraint:**
- CI runs trial mode only (VT+DE)
- Full mode documented but not executed

### CLI Interface

**Commands:**
```bash
# Single run
ghgsim run model.yaml --output results/

# Ensemble
ghgsim ensemble --mode trial --workers 4

# Archive run
ghgsim archive run_abc123 --format zip

# Start dashboard
ghgsim serve --port 8000 --host 127.0.0.1

# Validate model
ghgsim validate model.yaml

# List registered modules
ghgsim modules list
```

**Implementation:**
- `src/ghgsim/api/cli.py` - Click-based CLI
- Entry point in pyproject.toml: `[project.scripts]`

### Local Dashboard

**Technology:**
- FastAPI backend
- Simple HTML/JS frontend (no React/Vue)
- Runs locally only (127.0.0.1)
- NOT deployed to GitHub Pages

**Features:**
- Browse runs
- View manifests
- Compare results
- Visualize Sobol indices
- Download archives

**Security:**
- Localhost only, no authentication needed
- Not for public deployment

### Paper-Agent API

**Endpoints:**
```
POST /api/run - Submit run
GET /api/run/{run_id} - Get results
GET /api/run/{run_id}/manifest - Get manifest
GET /api/runs - List runs
POST /api/compare - Compare two runs
```

**Use Case:**
- Programmatic access for paper writing
- Jupyter notebook integration
- Automated analysis scripts

### Archive Command

**Format:**
```
archive/
  run_abc123/
    manifest.json
    model.yaml
    results/
      counties.csv
      summary.json
    plots/
      sobol.png
      distribution.png
```

**Storage:**
- ZIP archive with run_id name
- All inputs and outputs
- Manifest for reproduction

### Test Requirements
- At least 115 total tests
- CLI tests for all commands
- Dashboard endpoint tests
- Archive round-trip tests

---

## Development Principles

1. **One phase = one branch = one stacked PR**
2. **Base each PR on previous phase's branch**
3. **Never merge, never modify earlier branches**
4. **Keep all v3 tests passing (21 tests)**
5. **Add tests for each component**
6. **Keep CI green**
7. **Use UNVERIFIED + TODO for missing data**
8. **No invented citations or parameters**

---

## Fork Handling (Design Decision)

**Option A: Registry-Only (Recommended)**
- Forks defined in JSON registry
- Fork selection at runtime
- No module duplication
- Implementation: service layer

**Option B: Module-Level**
- Each fork is a separate module
- Graph resolver picks fork
- More modular but more files
- Implementation: module variants

**Decision:** Option A for consistency with v3 fork system and cleaner module namespace.

---

## Heavy County Runs

**Command:**
```bash
# Trial (CI-safe)
python -m ghgsim.api.cli ensemble --mode trial

# Or via batch file
run_ensemble.bat trial
```

**CI Configuration:**
- Run trial mode only (VT+DE)
- Full US documented but never executed in CI
- User can run full mode locally

**Resource Management:**
- Worker count = cores - 2 (leave room for OS)
- Progress bar and ETA
- Failure recovery (continue on county errors)
- Summary report

---

## Questions Resolved by User

1. **Soil data:** YES, include USDA NRCS gSSURGO with county aggregation
2. **All phases:** YES, implement phases 4-8 in this agent run
3. **Fork handling:** Agent's choice (using Option A: Registry-Only)
4. **Heavy runs:** Provide CLI command, run VT/DE in CI only
