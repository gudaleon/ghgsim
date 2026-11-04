# Paper B findings log (AN_v1), 4 Nov 2026

Science-first record of every finding, argument and open question so far. All model comparisons are
consistency checks, not validation. Novelty labels: **NEW** (no prior report found in the literature search),
**REPORTED** (prior report found and cited), **UNKNOWN** (search not conclusive). Citations were checked on
Crossref / doi.org. Repo: gudaleon/ghgsim (private).

## Competing interests (verbatim)

A.N. owns EnviroManagement, an environmental consulting firm working on aquatic ecosystems, environmental modelling and agricultural GHG services, which may use the methods described.

## 1. IPCC 2006 vs 2019 Refinement shifts (county scale, US)
- National direct+indirect soil N2O: 278.9 (2006) vs 287.6 (2019) Mt CO2e (withheld-cells variant). Source: docs/US_COUNTY_RUN_AN_v2.md, data/us_county_2006_vs_2019_AN_v2.csv.gz.
- 3,041 of 3,142 counties fall in IPCC "dry" zones under the zone_primary rule (data/county_climate_zones_AN_v1.csv), so the 2019 disaggregated EF1 (0.5 % dry / 1.6 % wet, synthetic N) lowers the EF for most of the Corn Belt while the national total rises through other terms.
- Novelty: the 2019 disaggregation itself is REPORTED (IPCC 2019 Refinement); the county-resolved US 2006-vs-2019 contrast is UNKNOWN (no county-level comparison found).

## 2. Inventory recalculations
- Recalculations across 7 national inventories: -4.4 % to +1.9 % (Russia +1.9 %); EU total 359.1 Mt. Source: docs/INVENTORIES_AN_v1.md. Novelty: UNKNOWN.

## 3. Consistency checks
- **GLEAM**: adapter v1 pasture N2O 2019: 152.2 vs 164.1 kg, explained by aggregated EF4 0.010 vs wet 0.014 (docs/DECISIONS_AN_v13-v25). EF4 discrepancy is a definitional issue (2019 EF4 is climate-disaggregated). Novelty: REPORTED (IPCC 2019).
- **HESTIA**: Iowa maize 3.09 kg N2O/ha/yr vs ghgsim 2.72 (2006) / 3.20 (2019). HESTIA ammonia-method gap (different NH3 volatilisation method feeds indirect N2O) documented in the HESTIA docs of the repo. Novelty: UNKNOWN.
- **APSIM Iowa (Webster, PR #51/#52, main 733a095)**: 2.92 kg N2O/ha/yr (single years 0.96-4.85), EF 1.32 % vs IPCC 1.0 % (2006) / 1.6 % wet. results/apsim_crop_sensitivity_AN_v3.csv.

## 4. Soil, drainage and parameter sensitivity (APSIM, Iowa; PR #52)
| Case | N2O kg/ha/yr | EF |
|---|---|---|
| Main Webster, SoilWater | 2.92 | 1.32 % |
| Clarion (well drained) | 2.23 | 1.04 % |
| Webster SWIM free base | 1.28 | 0.61 % |
| Webster SWIM seepage base (+/- tile, 0 mm tile flow) | 2.07 | 0.85 % |
| Webster fixed water table 0.66 m (SSURGO wet depth) | 10.2 | 3.47 % |
| FInert x0.75 / x1.25 | 3.49 / 2.45 | 1.48 / 1.20 % |
| FBiom x0.5 / x1.5 | 2.86 / 2.98 | |
| initial N x0.5 / x2 | <1 % change | |
- Finding: the hydrology representation (water model, lower boundary, water table) moves N2O by a factor of ~8 (1.28-10.2), far more than borrowed carbon-pool parameters (FInert +/-20 %, FBiom +/-2 %). Novelty: water-table sensitivity of process-model N2O is REPORTED in general (Butterbach-Bahl et al. 2013, doi:10.1098/rstb.2013.0122); its size relative to Tier 1 EF choice at one site is UNKNOWN.

## 5. Rain-pulse skewness
- Iowa: top 5 % of days carry 54 % of N2O; peak/mean day 47; 43 % of N2O falls 0-3 d after >=20 mm rain on 8.1 % of days.
- Novelty: REPORTED. Molodovskaya et al. 2012 (SSSAJ 76:1728, doi:10.2136/sssaj2012.0039): peaks up to 51 % of annual N2O in <7 % of time; hot moments, Groffman et al. 2009 (doi:10.1007/s10533-008-9277-5). Wagner-Riddle et al. 2017 (doi:10.1038/ngeo2907) covers freeze-thaw, not rain.

## 6. Research question (a): How Holos treats N2O variability (public code only)
Source: github.com/holos-aafc/Holos at commit c7683f7 (2026-10-29 11:53 EDT; GPL-3.0, read only, no code copied) and the Holos V4.0 algorithm document (Pogue et al. 2026) in the repo.
- H.Core/Calculators/Nitrogen/N2OEmissionFactorCalculator.cs: base ecodistrict EF = exp(0.00558 x - 7.7), x = growing-season (May-Oct) precipitation if P > PE, otherwise PE (eq. 2.5.1-1/2, Rochette et al. 2008, doi:10.4141/CJSS07025). In dry ecodistricts EF = f_lower EF(PE) + (1 - f_lower) EF(P), f_lower = fraction of lower landscape positions (topography term); irrigated sites use EF(PE). Modifiers for texture, tillage, N source follow.
- Climate: daily data are read (ClimateData), but only aggregated to **one growing-season P and PE per year** for N2O. No daily N2O, no rain-pulse dynamics.
- Drainage: SoilDrainageClasses is read from the Canadian soil database (NationalSoilDataBaseProvider) but **no N2O calculation uses it**; no water table, no tile drainage term was found (grep of all .cs files).
- Implication: Holos cannot represent the within-year skewness in section 5 or drained/undrained differences, except through the annual P/PE and the topography fraction. Novelty: UNKNOWN (no published code audit found).

## 7. Research question (b): county pilot, annual EF vs daily APSIM (started; branch county-pilot-AN-v1)
Design: universe = top 1,000 conterminous-US counties by synthetic N with May-Oct P/PE >= 0.3; strata = P/PE quintile x SSURGO drainage (well/poor); 2 counties per cell (20). SSURGO dominant component at the county internal point, NASA POWER 1991-2020, APSIM maize 100 kg N urea + 0 N control, Iowa management everywhere (limitation). Scripts: scripts/build_county_pilot_sample_AN_v1.py, run_apsim_county_pilot_AN_v1.py, compare_county_pilot_AN_v1.py; results/apsim_county_pilot_summary_AN_v1.csv, apsim_county_pilot_metrics_AN_v1.json.
- 17 of 20 counties ran; 3 Iowa counties (Woodbury, Hancock, Kossuth) dropped: APSIM rejects their SSURGO bulk density/saturation as inconsistent; not tuned.
- APSIM fertiliser EF 0.42-1.49 % (mean 0.79 % well vs 0.94 % poorly drained).
- Spearman rank, APSIM EF vs: IPCC 2019 EF 0.20; Holos-style base EF 0.59; P/PE 0.51 (0.37 with >=15 sown years, n = 15).
- Spearman of county totals (N x EF), APSIM vs: IPCC 2006 0.39; IPCC 2019 0.39; Holos-style 0.60.
- Top-decile (2 of 17) share of total: APSIM 21.7 %, IPCC 2006 15.9 %, IPCC 2019 22.6 %, Holos-style 19.9 %.
- Sum of totals (t N2O-N): APSIM 3,433; IPCC 2006 3,969; IPCC 2019 2,208; Holos-style 3,483.
- Pulse skew: mean top-5 %-day share 59 %.
- Question (d): APSIM/IPCC-2019 ratio vs P/PE Spearman 0.23; poorly drained counties higher EF. Pilot too small for inference.
- Reading: annual Tier 1 factors keep national totals within a factor ~1.6 but rank counties poorly (rho ~0.2-0.4); the P/PE-driven Holos-style EF ranks closer to daily APSIM. Hotspot concentration is similar. Novelty: UNKNOWN; Tier 1 vs process-model differences REPORTED in general (Philibert et al. 2012, doi:10.1371/journal.pone.0050950; nonlinear EF, Shcherbak et al. 2014, doi:10.1073/pnas.1322434111).
- Next: ~100 counties, crop-specific sowing windows, Ontario counties (c), drainage-class regression (d).

## 8. Research question (c): Ontario
Planned: CanSIS NSDB soil layer tables (Brookston clay, Essex / Chatham-Kent as primary), ECCC or NASA POWER weather; corn-soy(-wheat) with OMAFRA N rates. Not started.

## 9. Lake Erie tile-drainage experiment (pilot, results negative so far)
Site 1 (done): SSURGO Hoytville clay loam 0-1 % (OH173 Wood Co. OH, mukey per data/apsim_site_lake_erie_AN_v1/ssurgo_hoytville_AN_v1.json; very poorly drained, Mollic Epiaqualf). Horizons Ap 0-20 (ksat 7.76 um/s), Btg 20-89 (2.82), BC 89-145 (0.92), Cd 145-203 (0.005, densic restriction at 145 cm); SSURGO wet layer 15-152 cm Jan-Apr. Weather NASA POWER 41.22 N 83.76 W (OSU NW Agricultural Research Station, Hoytville).
Drain settings (cited): (i) 0.76 m depth, 12.2 m spacing (OSU Hoytville 1956 study, OSU Knowledge Bank "Hoytville soils"); (ii) 1.2 m depth, 17 m spacing (OSU long-term tillage experiment page, citing Dick et al. 1986: 1.2-1.4 m, 17 m). Klat = SSURGO ksat at drain depth; ImpermDepth 1450 mm; DrainRadius 150 mm.
- Full profile with the Cd layer: SWIM fails to converge; the SSURGO Cd Ksat (0.43 mm/d) is below the tutorial KDul (1 mm/d). Not tuned.
- Cd replaced by a seepage base at 1450 mm: runs complete for 100 kg N, but **no water table forms** (water-table depth = profile depth every day), seepage drainage 179 mm/yr, tile flow ~0. Drained and undrained give the same N2O: 2.30 kg N2O/ha/yr (1.47 kg N2O-N), N2 7.1 kg N/ha/yr, base NO3-N loss 11.4 kg/ha/yr; top-5 % days 31 %.
- 0 N controls fail on 29 Dec 1992 (APSIM soil-temperature solver), so no fertiliser EF.
- Conclusion so far: with SSURGO values and APSIM tutorial SWIM settings, APSIM does not reproduce the perched water table that makes tile drains flow. A water table needs either a cited drainable-porosity/K profile (e.g. the OSU drainage-test K/f values) or a cited regional head. So Holos crop N2O at Lake Erie sites cannot be reproduced meaningfully yet. Holos itself has no drainage term (section 6), so a drained/undrained contrast is outside Holos.
- Files: results/apsim_lake_erie_AN_v1/, results/apsim_lake_erie_annual_AN_v1.csv (per year), _summary_AN_v1.csv; copies plus .apsimx in D:\APSIM\lake_erie_drainage_AN_v1.
- Field context for drained vs undrained N2O (search; DOIs to verify before citing): doi:10.2134/jeq2016.06.0237, doi:10.2489/jswc.69.6.553, doi:10.1016/j.agee.2016.06.015.

## 10. Open questions
1. Can a cited K/drainable-porosity profile (OSU drainage tests) produce a perched water table in SWIM without tuning?
2. Brookston (CanSIS) primary site; corn-soy-wheat with OMAFRA N rates.
3. Fix the APSIM soil-temperature failure in 0 N controls (try the tutorial's soil-temperature model or a different start date).
4. Expand the county pilot; check whether the zone_primary dry classification of the Corn Belt drives the poor IPCC 2019 rank agreement.