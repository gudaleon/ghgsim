# Phase 9 Handoff - VT/DE Reproduction Status

**Date:** November 1, 2026  
**Branch:** `cursor/phase-9-exact-reproduction-353b`  
**PR:** #9 (https://github.com/gudaleon/ghgsim/pull/9)

---

## Current Status

### ✅ CH4 Reproduction: COMPLETE
**Max relative difference: 0.00e+00** (EXACT MATCH)

All 14 VT counties match v3 CH4 results exactly after using EPA per-state assumptions.

### ⚠️ N2O Reproduction: 12% Difference Remaining

**Max relative difference: 2.36e-01 (24%)** across VT counties  
**Essex County analysis: 12% difference (3,445 kg vs 3,915 kg)**

---

## What Matches Exactly

### 1. CH4 - All Components Match
- **Enteric CH4:** Exact match using EPA GE and Ym values
- **Manure CH4:** Exact match using EPA VS values and correct MCF
- **VT dairy:** GE=401.2 MJ/day, Ym=5.7%
- **VT beef:** GE=220.5 MJ/day, Ym=6.5%

### 2. Soil N2O - Exact Match When Tested Directly
When calling v3's `soil_n2o()` and v4's `IPCC2006SoilN2O.compute()` with the same inputs:
```
v3: 3120.11 kg N2O
v4: 3120.11 kg N2O
Difference: 0.00 kg (EXACT)
```

**Components that match:**
- Direct soil N2O: 2378.88 kg (exact)
- Indirect volatilization: 249.11 kg (exact)
- Indirect leaching: 492.11 kg (exact)

---

## What Doesn't Match

### N2O Discrepancy: 469 kg Missing (12%)

**Essex County VT (FIPS 50009):**

| Component | v4 Calculated | v3 Expected | Difference |
|-----------|--------------|-------------|------------|
| Manure N2O | 325.00 kg | ??? | ??? |
| Soil N2O | 3120.11 kg | ??? | ??? |
| **TOTAL N2O** | **3445.10 kg** | **3914.54 kg** | **-469.44 kg (-12%)** |

**Key Finding:** When running v3's `run_farm()` with the EPA assumptions file I'm using, it ALSO produces 3,445 kg N2O (not 3,915 kg). This means:

1. The v3 results file was NOT generated with the EPA assumptions alone
2. There may be additional forks or input adjustments
3. OR the county data in the results file includes additional N inputs not in my calculation

---

## Term-by-Term Analysis (Essex County)

### Inputs Used:
```
F_SN: 119,838 kg N (synthetic)
F_ON: 7,144 kg N (organic non-cattle)
F_CR: 0 kg N (crop residue)
F_PRP_CPP: 12,201 kg N (pasture/range/paddock from manure)
```

### v4 Calculation:
```
MANURE N2O:
  Dairy direct:   79.12 kg
  Dairy indirect: 245.87 kg
  Beef direct:    0.00 kg
  Beef indirect:  0.00 kg
  Total manure:   325.00 kg

SOIL N2O:
  Direct:         2378.88 kg
  Indirect vol:   249.11 kg
  Indirect leach: 492.11 kg
  Total soil:     3120.11 kg

TOTAL: 3445.10 kg
```

### Missing: 469.44 kg (12%)

---

## Hypotheses for N2O Difference

### 1. Additional N Inputs Not Captured ✓ LIKELY
The v3 results file may include additional N sources:
- Additional F_ON from other sources
- F_CR from crop residue (withheld/missing data filled)
- Different manure N routing (more N to soil vs volatilized)

### 2. Different Fork Settings
The trial run may have used non-default forks that affect:
- EF1 values (but direct comparison shows exact match)
- FracLEACH (but parameters match)
- Additional N pathways

### 3. EPA Assumptions Mismatch
The county_assumptions_AN_v3.json file may not be the exact version used for the trial run.

### 4. Data Preprocessing Differences
The run_counties_AN_v3.py script may apply transformations to:
- Cow counts (gap-filling adjustments)
- Manure system fractions
- N excretion rates

---

## Next Steps to Achieve 1e-9 Match

### Priority 1: Trace v3's Actual Inputs
1. Run v3's `run_counties_AN_v3.py` script directly for VT
2. Capture intermediate values (F_PRP, N excretion)
3. Compare with my calculated values
4. Identify discrepancies

### Priority 2: Check Data Processing
```bash
cd legacy/livingghg_AN_v3
python scripts/run_counties_AN_v3.py --states VT --n 0 --workers 1 --out /tmp/v3_check --trial
```

Compare outputs line by line with results_TRIAL_AN_v3/counties_VT_AN_v3.csv

### Priority 3: Debug Specific Differences
For each county where N2O differs:
1. Extract v3's intermediate calculations
2. Compare F_PRP, N excretion, system fractions
3. Identify formula or parameter differences
4. Fix v4 modules or test setup

### Priority 4: Verify with DE Counties
Once VT matches, test all 3 DE counties to confirm the fix is general.

---

## Code Locations

### Test File
`tests/test_exact_vt_de_reproduction.py`

**Key Functions:**
- `build_v3_farm_from_row()`: Assembles farm from EPA assumptions
- `run_v4_farm_ipcc2006()`: Runs v4 modules
- `test_vt_counties_exact_reproduction_2006()`: Main test

### EPA Data
`legacy/livingghg_AN_v3/scripts/county_assumptions_AN_v3.json`

VT-specific values accessed via:
```python
epa["states"]["VT"]["dairy"]["GE_MJ_day"]  # 401.2
epa["states"]["VT"]["dairy"]["Ym_pct"]     # 5.7
epa["states"]["VT"]["dairy"]["manure"]["VS_kg_day"]  # 7.4466
```

### v3 Modules
- `legacy/livingghg_AN_v3/livingghg/engine.py`: `run_farm()`
- `legacy/livingghg_AN_v3/livingghg/soil_n2o.py`: `soil_n2o()`
- `legacy/livingghg_AN_v3/livingghg/manure.py`: `manure_emissions()`

### v4 Modules
- `src/ghgsim/modules/ipcc2006/soil_n2o.py`: IPCC2006SoilN2O
- `src/ghgsim/modules/ipcc2006/manure.py`: IPCC2006Manure
- `src/ghgsim/modules/ipcc2006/enteric.py`: IPCC2006Enteric

---

## Parameter Verification

All IPCC parameters match between v2 and v4:
- EF1: 0.01 ✓
- EF3PRP_CPP: 0.02 ✓
- EF4: 0.01 ✓
- EF5: 0.0075 ✓
- FracGASF: 0.1 ✓
- FracGASM: 0.2 ✓
- FracLEACH: 0.3 ✓

MCF values corrected:
- solid_storage@15C: 0.04 ✓ (was 0.015)
- liquid_nocrust@15C: 0.27 ✓ (was 0.17)
- daily_spread@15C: 0.005 ✓ (was 0.001)
- lagoon@15C: 0.74 ✓ (was 0.07)

---

## Debugging Commands

### Compare v3 and v4 soil calculations directly:
```python
from livingghg.soil_n2o import soil_n2o
from livingghg.params import ParamTable
from ghgsim.modules.ipcc2006 import IPCC2006SoilN2O
from ghgsim.core.registry import load_parameter_csv

P = ParamTable()
params_v4 = load_parameter_csv('data/ipcc_params_AN_v4.csv')

farm_soil = {
    "F_SN": 119838, "F_ON": 7144, "F_CR": 0, 
    "F_SOM": 0, "F_PRP_CPP": 12201, "climate": "wet"
}

v3_result = soil_n2o(farm_soil, "IPCC2006", P, forks={})
# v4 calculation...
```

### Run v3's full county script:
```bash
cd legacy/livingghg_AN_v3
python scripts/run_counties_AN_v3.py --states VT --n 0 --workers 1 \
    --out /tmp/v3_debug --trial
```

### Check individual county in v3:
```python
import pandas as pd
vt_results = pd.read_csv('legacy/livingghg_AN_v3/results_TRIAL_AN_v3/counties_VT_AN_v3.csv')
essex = vt_results[vt_results['fips'] == '50009'].iloc[0]
print(essex.to_dict())
```

---

## Test Status

### Current Test Results:
```bash
pytest tests/test_exact_vt_de_reproduction.py -v -s

VT Counties (14):
  CH4:  0.00e+00 ✅ EXACT
  N2O:  2.36e-01 ⏳ 24% difference
  CO2e: 3.40e-02 ⏳ 3.4% difference (driven by N2O)
```

### Test is Currently SKIPPED
The test fails because N2O doesn't match to 1e-9. Once fixed, remove the skip logic and un-skip for CI.

---

## Success Criteria

For completion:
1. ✅ CH4: < 1e-9 relative difference (DONE)
2. ⏳ N2O: < 1e-9 relative difference (12% remaining)
3. ⏳ CO2e: < 1e-9 relative difference (follows from CH4+N2O)
4. ⏳ Test all VT counties (14)
5. ⏳ Test all DE counties (3)
6. ⏳ Un-skip test for CI

---

## Remaining Tasks (Post-Match)

After achieving 1e-9 match:
1. Implement working NASS/USGS loaders (wrap v3 data)
2. Dashboard manifest scanning
3. Spot-check 15 parameters in PARAM_RECONCILIATION
4. Final PR update with all metrics

---

**Status Summary:**
- CH4: ✅ Complete (0% error)
- N2O: ⏳ 12% error remaining
- Root cause: Input discrepancy or data preprocessing, not module math
- Next: Trace v3's actual inputs for discrepancy

---

**End of Handoff Document**
