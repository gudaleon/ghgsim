# FINDINGS_AN_v11 - Soybean share and EFs on sowing-to-sowing crop years

Follows FINDINGS_AN_v10 (DECISIONS D27.1: carry-over is a model result contradicted by field data). Consistency checks, not validation. Existing daily APSIM outputs only, no new runs.

Method (`scripts/sowing_year_recompute_AN_v2.py` -> `results/sowing_year_AN_v2/`): crop years run from the onset of one crop to the onset of the next. Onset is the first day with crop N > 0; APSIM reports crop N from emergence, so this is a few days after sowing. Fertilised minus 0 N, day by day. Crop years longer than 400 days (spanning an unsown year) are dropped. `sowing_year_recompute_AN_v1.py` kept them and inflated some county EFs; it is kept for the record and superseded. Calendar-year values use full calendar years (sites) or the sown years in the Report (counties), as in earlier versions. Failed runs (<3 years of output: Brookston CanSIS all cases, Brookston SSURGO undrained, Hoytville undrained) are skipped.

## 1. Lake Erie rotations: the soybean share falls by more than half; EFs barely move

| Case | Soybean share, calendar | Soybean share, sowing year | EF %, calendar | EF %, sowing year |
|---|---|---|---|---|
| Hoytville tile_1956 | 0.494 | 0.187 | 3.15 | 3.19 |
| Hoytville tile_lt | 0.508 | 0.178 | 3.59 | 3.62 |
| Brookston SSURGO tile_1956 | 0.417 | 0.186 | 3.30 | 3.33 |
| Brookston SSURGO tile_2rod | 0.424 | 0.188 | 3.20 | 3.24 |
| Brookston SoilWater (no drains) | 0.303 | 0.191 | 0.97 | 0.97 |
| Berrien tile_1956 | 0.366 | 0.156 | 2.26 | 2.28 |
| Berrien tile_2rod | 0.367 | 0.156 | 2.26 | 2.27 |
| Berrien undrained | 0.364 | 0.154 | 2.28 | 2.30 |

15 maize and 14 soybean crop years per case. Counting from sowing to sowing moves the January-April emission after the maize into the maize year, so the soybean share drops from 0.30-0.51 to 0.15-0.19. EFs change by 0.00-0.04 percentage points (edge years only). A share of 0.15-0.19 remains: soybean-season N2O on fertilised plots is still higher than on 0 N plots. The field found no such effect (Fabrizzi et al. 2024), so the remaining share is still a model result not seen in the field.

## 2. Iowa (continuous maize; no soybean share)

Fertilised minus 0 N N2O-N (kg/ha/yr), mean (SD) over 28 crop years vs 29 calendar years: Webster v2 1.28 (0.56) -> 1.33 (0.51); Clarion 1.01 (0.44) -> 1.05 (0.42); Webster SWIM 0.59 (0.35) -> 0.63 (0.34); seepage/tile 0.82 (0.63) -> 0.86 (0.70); fixed water table 3.40 (0.93) -> 3.53 (0.94); till-gradient tile 0.63 (0.38) -> 0.66 (0.40). Means rise by 3-5% because the first partial year is dropped and year sets differ. Interannual SD changes by -9% to +10%.

## 3. County and Ontario EFs (continuous maize, 100 vs 0 kg N/ha)

| Region | Units with sowing-year values | Mean EF %, calendar -> sowing year | Median change (all; units with complete sowing record) | Spearman, calendar vs sowing | Top-10% overlap | Median interannual SD ratio |
|---|---|---|---|---|---|---|
| US | 95 of 97 | 1.114 -> 1.185 | +1.3%; -0.5% (n = 27) | 0.93 | 8/10 | 0.94 |
| Ontario | 31 of 32 (1 unit EF 0) | 0.524 -> 0.611 | +12.8%; +10.5% (n = 24) | 0.92 | 3/3 | 0.95 |

Two US counties (08075, 30015) have no complete crop year under the 400-day rule. Large changes (up to +123% US, +206% Ontario) occur only where crops were not sown every year: there the calendar and crop-year sets differ, so this is a sampling difference, not a carry-over effect. Where sowing was complete, US EFs change by -4% to +13% (median -0.5%). Ontario EFs still rise by about 10% (range 0% to +23%). The cause is not resolved here. A likely candidate is that crop-onset years and Report sown years count different years in Ontario (median 27 vs 25 years), so it should not yet be read as a carry-over effect.

## 4. What changes for the paper

- Lake Erie soybean share: report 0.15-0.19 (sowing year) alongside 0.30-0.51 (calendar). Most of the calendar carry-over is the post-maize winter; the remainder is still contradicted by field data.
- Lake Erie and Iowa EFs: unchanged within 0.04 percentage points (sites) or 3-5% (Iowa means).
- County and Ontario rankings are robust (Spearman 0.92-0.93; top-10% overlap 8/10 US, 3/3 Ontario). FINDINGS v8 ranking and distortion conclusions do not depend on the year definition. The Ontario level shift (~+10%) is unexplained and flagged.