# DECISIONS_AN_v15 — beef_pasture_field 2019 pasture N2O: GLEAM 152.2 vs ghgsim 164.1 kg

Date: 2026-11-03. Author: Alex Neumann. (v14 left free for the CRT/Russia-EU branch, whose DECISIONS_AN_v13 collides with the one merged in PR #39.)

## Finding
beef_pasture_field is 100% pasture with F_SN = F_SOM = F_CR = F_ON = 0, so ghgsim's soil N2O equals PRP N2O.
scripts/decompose_pasture_n2o_AN_v1.py writes results/pasture_n2o_terms_gleam_vs_ghgsim_AN_v1.csv:

| Set | Term | ghgsim | GLEAM |
|---|---|---|---|
| 2006 | direct (EF3PRP 0.02) | 271.91 | 271.91 |
| 2006 | indirect volatilisation (FracGASM 0.20, EF4 0.010) | 27.19 | 27.19 |
| 2006 | indirect leaching (FracLEACH 0.30, EF5 0.0075) | 30.59 | 30.59 |
| 2019 | direct (EF3PRP wet 0.006) | 85.00 | 85.00 |
| 2019 | indirect volatilisation (FracGASM 0.21) | 41.65 (EF4 wet 0.014) | 29.75 (EF4 0.010) |
| 2019 | indirect leaching (FracLEACH wet 0.24, EF5 0.011) | 37.40 | 37.40 |
| 2019 | total | 164.05 | 152.15 |

F_PRP: 8,651.8 kg N (2006), 9,015.2 kg N (2019). No other N input terms exist on this field.

The entire 11.90 kg gap is indirect volatilisation, and it is caused by the EF4 value we passed to GLEAM, not by either model:
the GLEAM adapter (run_gleam_stylized_AN_v1.py) took registry key IPCC2019.EF4.all (Table 11.3 aggregated 0.010),
while ghgsim's 2019 soil module applies the climate-disaggregated wet value 0.014 — consistent with its own use of
EF3PRP wet and FracLEACH wet for this "wet" field. 41.65 x 0.010/0.014 = 29.75.

## Decision
- Not a ghgsim bug; no ghgsim code change. ghgsim's 2019 choice (all three wet-disaggregated factors) is internally consistent.
- The v1 GLEAM outputs are kept as committed (never overwritten); the gap is documented as an adapter input choice
  (mixed aggregated EF4 with wet EF3PRP/FracLEACH). A future gleam adapter v2 should pass EF4_wet for wet fields.
- No scope difference: GLEAM and ghgsim compute the same three PRP terms (direct, volatilisation, leaching).
  2006 agrees to the gram.
- tests/test_pasture_n2o_terms_AN_v1.py asserts direct and leaching agree, the 2006 set agrees, and the 2019 gap
  equals the EF4 ratio.
