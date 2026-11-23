# DECISIONS_AN_v29 - N-budget closure inputs (Paper B Ohio, Phase 4)

Code added (no existing file edited except `tier1_extras/__init__.py` exports):
* `src/ghgsim/modules/tier1_extras/n_budget_closure.py` - `soybean_bnf_full_kg`, `soybean_bnf_per_grain_kg`, `alfalfa_bnf_kg`,
  `deposition_n_kg`, `leach_budget_kg`, `n_budget_v2`.
* `scripts/build_params_AN_v12.py` -> `data/ipcc_params_AN_v12.csv` (all 913 v11 rows unchanged + 18 new rows).
* `scripts/n_budget_closure_AN_v1.py` - reads the runner's county `n_budget` table, adds the new terms, writes county table,
  state scenario table, v3->v4 bridge, checks. Refuses to overwrite. Emissions are NOT recomputed: IPCC Tier 1 N2O does not
  use deposition, BNF or the budget leaching base, so soil N2O is unchanged from the runner.
* `tests/test_n_budget_closure_AN_v1.py` (10 tests, hand calculations).

## Why the Ohio residual was negative (mass balance)
residual = inputs - outputs. v3 inputs (F_SN + F_ON applied + F_PRP + above-ground soybean BNF + F_SOM) were incomplete
(no deposition, no alfalfa BNF, no below-ground soybean BNF) and v3 outputs were overstated (NRCS Table 6-6 N% is of DRY
material but was applied to as-sold weights; IPCC Eq 11.10 leaching applied to recycled crop-residue N that is never an input).
Each fix is additive and independent; the bridge file lists them.

## Decisions
1. Deposition: NADP/EPA-CASTNET TDep gridded total (wet+dry, measurement-model fusion), county mean, x harvested cropland ha.
   Wet-only is a sensitivity (NTN-like). File version label ambiguity (PDF 2025.01 vs tif path v2026.01) is recorded in the
   project DECISIONS.
2. Alfalfa BNF: Russelle & Birr 2004 basin mean 152 kg N/ha x (alfalfa hay + haylage area). Low 45 kg/ha (their minimum);
   high = Peterson & Russelle 1991 61 lb N/ton (secondary, via NuGIS Methods Documentation). Non-alfalfa hay legume share has no verified source: 0.
3. Soybean BNF: Salvagiotti 2008 Ndfa 0.55 (0.50-0.60) applied to total plant N = (DM-corrected seed N + above-ground residue N)/(1-0.24).
   Same Ndfa assumed for below-ground N (assumption). Range: low = Ndfa 0.50 with below-ground 4 % (Gelfand & Robertson 2015 measured);
   high = Ndfa 0.60 with below-ground 40 % (Australian values quoted in Gelfand & Robertson, secondary). Independent cross-check:
   Gelfand & Robertson 43 g N/kg grain (single Michigan site, drought year).
4. Crop N removal: DM-corrected (IPCC 2006 Table 11.2 DRY) is the v4 headline; as-is NRCS and Ohio on-farm (OSU ANR-74) are sensitivities.
5. Leaching: IPCC Eq 11.10 uses (F_SN+F_ON+F_PRP+F_CR+F_SOM) x FracLEACH (2006 Vol 4 Ch 11 pp. 11.20-11.21). v4 budget uses the same
   FracLEACH on F_SN+F_ON+F_PRP+F_SOM only (F_CR is recycled, not an input). Emissions keep the full IPCC base.
6. Fertiliser: 2017 state total kept for 2022 (no public Ohio 2022 N total found); sensitivities: USGS Falcone 2017 and NuGIS 2016 state totals.

Known limits: PRP N goes to pasture while the budget removal covers cropland and hay only (domain mismatch, quantified in the project outputs);
alfalfa below-ground fixation is not included; the closed residual is within the spread of the input sensitivities and is not a validation.
