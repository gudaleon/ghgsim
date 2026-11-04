# FINDINGS_AN_v2 — Lake Erie tile-drainage experiment v2 (Paper B)

These are consistency and process checks, not validation. Every number below comes from a file in this PR or from a cited source opened on 2026-11-04. Novelty labels: **known** (verified prior literature says it), **confirm** (our result agrees with a verified source), **new-to-us** (we found no verified source; this is not a claim of novelty), **limitation**.

## 1. Site choice and Alex's question

**Alex's question.** Alex asked whether the Canadian site should be a clay soil, and asked us not to assume Brookston. The Canadian site is the tile-drained farmland around Windsor, Essex County. We checked two independent sources.

- **Soil Survey of Essex County (Ontario Soil Survey Report No. 11).** Richards, Caldwell & Morwick, 1949. https://sis.agr.gc.ca/cansis/publications/surveys/on/on11/on11_report.pdf
  - Land area is 452,480 acres.
  - Brookston clay covers 250,000 acres (55 %). Adding Brookston clay loam (30,000 acres) and the clay sand-spot phase (18,000 acres) gives 298,000 acres (66 %).
  - Other series: Berrien sandy loam and sand 24,000 acres (5 %), Toledo 18,500 acres, Perth 17,000 acres, Caistor 17,500 acres.
  - The report says: "Brookston clay, the most extensive soil type in Essex County, is mapped in every township." It also says "Brookston clay loam is a large block covering most of Windsor Township".
  - On drainage it says: "The heavy textured Brookston, Clyde, and Toledo soils make up approximately two-thirds of the area" and "A large proportion of the poorly drained soils have been tile drained, particularly the Brookston and Clyde and to a lesser extent the Toledo".
  - On drain spacing it says: "tile placed at four rod intervals [20.1 m] formerly provided adequate drainage, it is now necessary to place them every two rods [10.1 m]".
- **CanSIS SLC v3.2 × soil layer tables v2r20140203.** Areas are the polygon area times the component share, within the Essex boundary from LIO (Ontario Open Government Licence). The Essex polygon total is 3,701 km², which probably includes lake area.

| Soil | Drainage | Share of area |
|---|---|---|
| Brookston | poorly drained | 41.7 % |
| Berrien | imperfectly drained | 11.6 % |
| Toledo | poorly drained | 9.5 % |
| Perth | imperfectly drained | 7.2 % |
| Marsh | – | 6.4 % |
| Caistor | – | 4.6 % |
| Harrow | well drained | 3.6 % |

  The full table is in `data/ontario_soils_AN_v1/cansis_essex_composition_AN_v1.json`.
- **Texture.** The CanSIS Brookston modal profile is 37 % clay and 16 % sand at 0–25 cm, which is silty clay loam to clay loam texture. It is 51 % clay at 25–65 cm and 43 % clay at 65–100 cm. So the topsoil is a clay loam and the subsoil is clay. Both sources agree that Brookston is the dominant tile-drained soil.
- **Answer to Alex.** Brookston is the right heavy soil, chosen from the survey and not assumed. **confirm.**
- **Contrast soil.** The lighter contrast is Berrien: 12 % clay and 68 % sand, sandy to 44 cm over clay loam. It is the second soil by area in CanSIS and is often associated with Brookston (Report 11).
- **Location.** Both Essex soils use SLC polygon 570007 (80 % Brookston, 10 % Berrien), at 42.1631 N, −82.7793 W.

**US side: Maumee basin, the former Great Black Swamp.**

SSURGO major components by component-acres:

| Survey area | Main soils (component-acres) |
|---|---|
| Wood County, OH173 | Hoytville 210,816; Mermill 23,099; Nappanee 17,639; Aurand 12,125; Latty 9,216 |
| Lucas County, OH095 (Waterville) | Urban land 18,667; Latty 17,736; Ottokee 16,467; Granby 16,239; Toledo 11,185; Hoytville 9,628 |

- We use Hoytville clay loam, the dominant Wood County soil, at 41.22 N, −83.76 W. That is in Wood County, about 30 km south of Waterville.
- Lucas County is more urban and mixed, so Wood County is the better match for heavily tiled farmland.

Verified context (DOIs checked on Crossref on 2026-11-04):

- Siman & Niewiarowski 2023, *Ecology and Society* 28(1):48, doi:10.5751/ES-13408-280148. About 24,000 km of ditches were built in 1890–1920, about 5 % of the swamp remains, and tile drainage followed. **known**
- Miller & Lyon 2021, *Hydrological Processes*, doi:10.1002/hyp.14326. The Great Black Swamp covered about 4,000 km², the area is among the most intensively tile-drained in the US, and tile drainage makes streamflow flashy. **known**
- Mitsch 2017, *Ecological Engineering*, doi:10.1016/j.ecoleng.2017.08.040. **known**
- Not used: USGS WRI 00-4091, because its DOI did not resolve on Crossref.

## 2. Set-up

Runner: `scripts/run_apsim_lake_erie_AN_v2.py`. APSIM Next Gen 2026.11.8142.0, SWIM3.

- **Rotation.** Corn in odd years and soybean in even years, 1991–2020. We ran a corn-soy rotation; we did not add wheat.
- **Sowing windows.** USDA NASS Agricultural Handbook 628 (2010), "most active" dates:

| State | Corn | Soybean |
|---|---|---|
| Ohio | 24 Apr – 24 May | 3 – 30 May |
| Michigan (proxy for Essex, flagged) | 1 – 27 May | 11 May – 9 Jun |

- **Nitrogen.** Corn gets 172 kg N/ha urea at sowing, from the OMAFRA Pub. 811 N worksheet for corn after soybean on clay. The worksheet inputs 170 bu/ac, 3,400 CHU and the price ratio are assumptions (flagged). Each run has a 0 N control. Soybean gets no N.
- **Soybean.** Cultivar Generic_MG3 (assumption, flagged). Root parameters LL, KL and XF are copied from maize (assumption, flagged).
- **Soil water.** PSIDul is −330 cm, because both sources define DUL at 33 kPa. With the tutorial value of −100 cm, Brookston failed in 66 days.
- **SAT.** APSIM rejects SAT > 1 − BD/2.65. Source SAT above that is capped to the limit and every cap is recorded in the manifest. Example: Brookston Ap 0.53 was capped to 0.520.
- **Drains** (`SwimSubsurfaceDrain`):
  - `tile_1956`: 0.76 m deep, 12.2 m spacing (OSU Hoytville study).
  - `tile_lt`: 1.2 m deep, 17 m spacing (Hoytville only).
  - DrainRadius is 150 mm and ImpermDepth is the profile base.
  - Klat is Ksat at drain depth × 86.4.
  - The lower boundary is a seepage face.
- **Tile nitrate.** Tile NO3 is reported from `[SoilWater].SubsurfaceDrainNO3`.
- **Cited drainage reference, unused in the model:** OSU Research Bulletin 1141 (Schwab, Michener & Kopcak 1982).
  - Hoytville drainable porosity: 0.067 at 0–10 cm, 0.057 at 0–20 cm, 0.047 at 0–30 cm.
  - K/f: 0.913 m/h at X/L = 1/2.
  - Recommended spacing at 20 cm/day drawdown: 18 m for Hoytville and 17 m for Toledo.
  - Implied field K ≈ 0.05 m/h.
- **0 N crash, fixed.** The cause was NASA POWER −999 radiation flags, for example Hoytville 1992-01-14 and 1992-12-30. These led to "newTemps(1) is outside range". `scripts/power_fill_AN_v1.py` now fills them by linear interpolation and logs each fill. The same flags were also present in pilot counties 19019, 19081, 19109, 19193, 38017, 38019 and 38101, and at the Essex point. The Iowa main site has none. **new-to-us** as a pitfall.

## 3. Results (30 years, mean kg/ha/yr)

Source: `results/apsim_lake_erie_summary_AN_v2.csv`, with per-year values in `results/apsim_lake_erie_annual_AN_v2.csv`.

| Run | N2O-N | N2O-N, maize years / soy years | N2 (denitrification) | Base NO3-N leached | Base drainage (mm) | Rain (mm) | Share of N2O on top 5 % of days |
|---|---|---|---|---|---|---|---|
| Berrien, 172 N | 2.35 | 2.56 / 2.14 | 10.1 | 14.1 | 96 | 787 | 34 % |
| Berrien, 0 N | 1.14 | 1.12 / 1.15 | 5.1 | 6.6 | 88 | 787 | 30 % |
| Hoytville, 172 N | 3.74 | 3.37 / 4.11 | 19.9 | 18.1 | 144 | 915 | 32 % |
| Hoytville, 0 N | 1.42 | 1.47 / 1.36 | 7.7 | 7.2 | 136 | 915 | 31 % |

- **Fertiliser-induced EF per corn N applied over the rotation cycle,** calculated as (fertilised − control) × 2 years / 172: Berrien 1.41 %, Hoytville 2.70 %.
  - More than half of the Hoytville excess falls in the soybean year (4.11 − 1.36 = 2.75 kg N₂O-N in soy years vs 1.90 in corn years). This carry-over to the following crop is missed by an EF counted only in the year of application. **new-to-us**, in the model only.
- **Brookston failed.** All four Brookston runs failed on 1996-06-22 with "Swim failed to find solution". We tested KDul 0.1 and 10, MaxWaterIncrement 1, DTMax 60, 50 mm nodes, and no seepage or tile. Brookston is therefore recorded as failed and has no results. **limitation**
- **No water table and no tile flow.** With a seepage lower boundary at the profile base, SWIM never builds a water table above the base. WaterTable stayed at the profile depth (1,000 mm in Essex, 1,450 mm at Hoytville). Tile flow and tile NO3 were 0, and drained runs equal undrained runs.
  - Adding the cited SSURGO Hoytville Cd restricting layer (Ksat 0.43 mm/d) makes SWIM fail (June 1993, July 1992).
  - SWIM3_SetLowerBC offers only gradient, seepage and potential lower boundaries. A potential boundary needs a cited head; we found none, so we did not set one by tuning.
  - **Result: no tile-drainage effect on N2O can be claimed from these runs.** **limitation**
  - Next options:
    - (a) A Hooghoudt-type check of the water-table response against the OSU K/f and drainable porosity.
    - (b) A model with a perched-water-table routine (e.g. DRAINMOD-N II, Youssef et al.).
    - (c) Toledo or Perth in place of Brookston.
- Holos (read-only audit at commit c7683f7) has no drainage or water-table term, as in FINDINGS_AN_v1.

## 4. Paths

**This experiment** (`D:\APSIM\lake_erie_drainage_AN_v2\`):
- 14 .apsimx files, named `lake_erie_<site>_<case>[_0N]_AN_v2.apsimx`.
- Annual and summary CSVs, the manifest, the scripts, and the Essex composition and site JSONs.

**Repo copies:**
- Runs: `results/apsim_lake_erie_AN_v2/`.
- Drain settings: `TILE_1956` and `TILE_LT` in `scripts/run_apsim_lake_erie_AN_v2.py`.

**Earlier files:**
- Lake Erie v1: `D:\APSIM\lake_erie_drainage_AN_v1\`.
- Iowa: `D:\ghgsim\results\apsim_AN_v2\crop_urea_lime_iowa[_0N]_AN_v2.apsimx` and `results\apsim_AN_v3\`.

## 5. Not done yet

- The expanded US sample (97 counties) and the Ontario county runs are in progress. They will be reported in FINDINGS_AN_v3 in a separate PR.