# Tier 1 extras and the county-year runner (AN_v1)

New code: `src/ghgsim/modules/tier1_extras/`, `scripts/run_county_year_tier1_AN_v1.py`,
`scripts/build_params_AN_v11.py` -> `data/ipcc_params_AN_v11.csv` (all v10 rows unchanged + 143 new rows, each with
source, table, page and status VERIFIED). Tests: `tests/test_tier1_extras_AN_v1.py`. Decisions: `docs/DECISIONS_AN_v28.md`.

| Component | Method | Sources (printed page) |
|---|---|---|
| F_SOM (N mineralised from soil organic matter loss) | Eq 2.25 stock change between two Census tillage snapshots (same area at both dates, divided by D = 20 yr unless T >= 20), then Eq 11.8 with R = 10 (management change on Cropland Remaining Cropland). Only losses mineralise N. Headline = Tier 1 Approach 1 (one net dC for the state; N only if the net is a loss, split over counties by their losses). The per-county "losses only" sum is reported as an upper sensitivity. Land-use change F_SOM is 0 because no gross land-use transitions are available. | 2006 Ch2 Eq 2.25 p. 2.30, Table 2.3 p. 2.31; 2019 Ch2 Table 2.3 (Updated) p. 2.34; 2006 Ch5 Table 5.5 pp. 5.17-5.18; 2019 Ch5 Table 5.5 (Updated) pp. 5.27-5.28; Eq 11.8 2006 p. 11.16, 2019 p. 11.20 |
| Hay / haylage residue N | 2006 Eq 11.7A with Table 11.2 rows Alfalfa and Non-legume hay; 2019 Eq 11.6 (Updated) with Table 11.1a (New) N_AG, N_BG, RS, DRY and AGDM from Table 11.2 (Updated) (no R_AG for these rows). FracRenew multiplies the below-ground term only; runner flag `--forage-frac-renew` (1 = annual root turnover, 0 = renewal not counted). | 2006 Ch11 pp. 11.15, 11.17-11.18, footnote 3 p. 11.7; 2019 Ch11 pp. 11.16-11.19 |
| Corn silage residue N | No IPCC silage row. AG residue removed with the harvest; roots from maize R_BG-BIO / RS 0.22 and N_BG 0.007 times whole-plant DM. DM = green tons x 0.35 (NRCS Table 6-6 row label). | as above + NRCS p. 6-21 |
| Crop N removal | NRCS AWMFH worked example: yield x lb/bu x N% (Table 6-6 'average concentration' in the harvested part). Silage % is per DM. A DM-corrected variant (x IPCC DRY) is reported for sensitivity. | USDA NRCS AWMFH Part 651 Ch6 Table 6-6 (210-vi-AWMFH rev. 1, July 1996) pp. 6-18 to 6-22 |
| Soybean BNF (for the N budget only) | BNF_AG = Ndfa x (seed N + above-ground residue N), Ndfa 0.55 (0.50-0.60). | Salvagiotti et al. 2008, Field Crops Res. 108:1-13, abstract |
| Lime / urea CO2 | Existing `IPCC2006LimeUreaCO2` (Eq 11.12/11.13). 2019 Ch11 sections 11.3/11.4 say "No refinement" (p. 11.27), so both versions are identical. | 2006 Ch11 pp. 11.27, 11.32 |
| N budget | inputs (synthetic N, manure N applied, PRP N, soybean BNF, F_SOM) - outputs (crop N removed, soil volatilisation, leaching, direct N2O-N) = residual (unaccounted). The identity is checked to machine precision; the residual is reported, not forced to zero. | - |

## Runner

```
python scripts/run_county_year_tier1_AN_v1.py --state-fips 39 --year 2022 \
  --census-tsv crops.tsv animals.tsv economics.tsv --prev-year 2017 \
  --fert-html epa_commercial_fertilizer_purchased.html --lime-csv aglime.csv \
  --climate all_wet --soil-class HAC --forage-frac-renew 1 --out-dir OUT --suffix _AN_v1
```

Writes to `--out-dir` only and refuses to overwrite: emissions (long), county inputs, N budget, F_SOM, forage residue
and removal, lime/urea (state), mass-balance checks, and a JSON manifest with input SHA-256 hashes and the ghgsim
commit. Livestock and the original soil N2O sources are computed by the unchanged `county_calc` of
`run_us_county_2006_vs_2019_AN_v2.py`. When the previous Census has tillage only at state level, the county start
shares are the county end shares minus the state share change (clipped at 0 and renormalised); the basis is recorded
per county.

## Known gaps
* Urea CO2 needs a state urea amount; none is built in.
* Lime input is whatever the CSV supplies (e.g. producer sales, not application); limestone/dolomite split may be unknown,
  so the runner reports both bounds.
* N budget leaves out atmospheric deposition, BNF by alfalfa / clover, and below-ground soybean BNF; these sit in the residual.
