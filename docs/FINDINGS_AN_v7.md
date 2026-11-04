# FINDINGS_AN_v7: Brookston perched water table and tile drainage in APSIM (SWIM)

These comparisons are consistency checks, not validation. All runs use APSIM 2026.11.8142.0 on PENV, Essex Brookston point (42.1631, -82.7793), 1991-2020, maize (172 kg N/ha urea, odd years) and soybean rotation, with 0 N controls.

## 1. Why SWIM failed on the CanSIS Brookston profile (option a)
- APSIM HydraulicProperties.SetupKCurve fits b = -ln(psi_dul/psi_ll15)/ln(DUL/LL15), MicroP = 2b+3 and MicroKs = Kdul/(DUL/SAT)^MicroP. When MicroKs > KS, K follows the micropore curve, which has no cap.
- The CanSIS Brookston DUL and LL15 are close together (Btg 0.36/0.31, Ckg 0.32/0.30). This gives K(sat) of about 9.4e4 mm/d at 350-550 mm and 2.6e10 mm/d at 750-1000 mm, against KS inputs of 80.6, 49.2 and 34.6 mm/d.
- The gradient lower boundary (q = (gf+gr)*hk, Swim.cs) therefore has no effect. In fallow tests for 1991-92, base drainage was 400, 424 and 476 mm for gr -0.99457, -0.9 and 0. No water table formed.
- Changing SpaceWeightingFactor (1, 0.5, 0, -2), DTMax, DTHC/DTHP or eo1440 cannot fix this. Hoytville, with the same code, behaves normally (WT minimum 73 mm).
- Conclusion: option (a) is not workable without changing the CanSIS water retention values, which we did not do.

## 2. Option (b): SSURGO densic Brookston proxy
- Source: USDA-NRCS SSURGO via Soil Data Access (scripts/fetch_ssurgo_brookston_AN_v1.py; data/apsim_site_lake_erie_AN_v3/ssurgo_brookston_densic_AN_v1.json). The map unit is MI155 Shiawassee County, "Brookston loam, dense substratum, 0 to 1 percent slopes", mukey 2393950, cokey 27985665, 81 %. It is poorly drained, fine-loamy, mixed, superactive, mesic Typic Argiaquolls, hydrologic group C/D.
- Horizons (ksat_r in um/s): Ap 0-25 cm (1), Btg 25-76 cm (0.55), Cg 76-127 cm (0.55), Cd 127-203 cm (0.005, densic restriction).
- The model profile is 0-127 cm. The lower boundary is gradient gr = Ksat(Cd)/Ksat(Cg) - 1 = -0.990909, so it represents the dense till as an impeding layer.
- Tiles reuse the v3 cases: tile_1956 (760 mm deep, 12.2 m spacing, OSU) and tile_2rod (760 mm, 10.06 m, Essex County Soil Report 11, "every two rods").
- FLAGS:
  - This is a cross-border series proxy, not an Essex profile.
  - SSURGO clay is 23-28 %, while CanSIS Essex Brookston clay is 37-51 %.
  - The MI115 Brookston component has no Cd layer.
  - No new OMAFRA drain spacing citation was found, so the depth and spacing are the flagged v3 values.
  - SSURGO cosoilmoist lists the component as "Wet" in every month.

## 3. Results (scripts/summarise_brookston_ssurgo_AN_v1.py; results/apsim_brookston_ssurgo_ef_AN_v1.json)
Values are 30-year means per year.

| case | EF % | maize-yr-only EF % | soybean-yr share | N2O-N 172N / 0N | N2 172N | tile flow mm | tile NO3-N 172N / 0N | base drain mm | base NO3-N leach 172N / 0N | Jan-Apr WT mean cm |
|---|---|---|---|---|---|---|---|---|---|---|
| tile_1956 | 3.30 | 1.93 | 0.42 | 4.62 / 1.78 | 24.1 | 46 | 6.6 / 3.4 | 53 | 6.9 / 3.4 | 85 |
| tile_2rod | 3.20 | 1.84 | 0.42 | 4.50 / 1.75 | 23.4 | 54 | 7.6 / 4.0 | 52 | 6.8 / 3.4 | 88 |

The water table reaches about 0.3 cm below the surface in some winters, so a perched water table now forms.

- **Undrained.** The run failed with "Swim failed to find solution" on 1992-12-09 (172N and 0N), after the water table reached the surface (minimum 0.06 cm). Ponding (--pond), eo1440 and both together failed in the same way. This matches the Hoytville undrained failure.
- **Matched period, 1991-01-01 to 1992-12-08 (708 d), N2O-N kg/ha, 172N / 0N:**
  - undrained 6.52 / 1.99
  - tile_1956 6.07 / 1.93
  - tile_2rod 5.99 / 1.90
  - Tile flow was 59 / 72 mm in the drained runs versus 0 mm undrained. Over the same period, drainage lowered N2O by about 7-8 %.
- **Flag:** tile flow of about 50 mm/yr is low for tiled Ontario clay loam. It is not tuned and must not be read as measured.

## 4. Consistency context
- Holos CLI Brookston EF is 1.925 % (FINDINGS_AN_v6).
- APSIM SoilWater on CanSIS Brookston gave 0.97 % (FINDINGS_AN_v5).
- The SSURGO-proxy SWIM run gives 3.2-3.3 %. That is higher because of the wet, perched profile, and about 42 % of the fertiliser-induced N2O comes in soybean years. The maize-year-only EF (1.8-1.9 %) is close to Holos.
- These are model-to-model consistency checks only.

## Novelty labels
- [method] Diagnosis of the SWIM K-curve blow-up for profiles with close DUL and LL15.
- [method] A densic-till gradient boundary taken from SSURGO Ksat.
- [result, proxy] Drained Brookston EF with soybean-year carry-over.