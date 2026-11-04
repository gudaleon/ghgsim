# FINDINGS_AN_v4 — making the tile drains flow (Lake Erie v3), Brookston diagnosis, Ontario planting dates

Branch `drains-AN-v4`. Earlier work: FINDINGS_AN_v2 (Lake Erie v2, PR #54) and FINDINGS_AN_v3 (counties, PR #55).
Everything here is a consistency check, not validation. No parameter was tuned to match a target. Every changed
setting is listed with its source, or flagged as an assumption or a numerical choice. Novelty labels follow the
usual scheme. A label that needs a literature check is marked "(to verify)".

## 1. Drains now flow: a cited restricting layer creates a perched water table

**Change.** The lower boundary is SWIM's gradient boundary (ibbc = 0 in Swim.cs, `q = (1 + gr) K(h)` at the base).
gr = K_restricting / K_base − 1:
- Hoytville: SSURGO Cd (densic till, 145–203 cm) ksat_r = 0.005 µm/s, under BC at 0.92 µm/s. gr = −0.99457.
- Essex sites (flagged): CanSIS gives no data below 100 cm. Exact zero flux (gr = −1) is singular, and SWIM failed
  in every Brookston soybean year with it. The Hoytville till ratio is therefore transferred to Essex. This assumes a similar clay-till
  restriction (flagged).
- Essex drain case `tile_2rod`: two-rod (10.06 m) spacing (source not re-verified this round; flagged).
  Depth is the reused OSU value (flagged).

Water-table data (OSU 1982 Bulletin 1141 drawdown tests; USGS wells) could not serve as a boundary:
- The OSU tests are sprinkler drawdown events, not seasonal series.
- The ISU SWIM water-table test archive is password protected.
- APSIM SoilWater (cascade) in 8142 has a WaterTable class but no tile drain.

SSURGO wet-month tops are used only as a consistency check (`data/lake_erie_watertable_AN_v1/`):
- Hoytville: 15 cm, Jan–Apr.
- Brookston (MI115 proxy): 0 cm, Dec–May.

**Hoytville drained results, 1991–2020, fertilised (172 N on maize) / 0 N** (curve-number surface, eo_durn 720;
`results/apsim_lake_erie_summary_AN_v3.csv`):

| case | N2O-N kg/ha/yr | N2-N | tile flow mm/yr | tile NO3-N kg/ha/yr | Jan–Apr water table, mean / min cm |
|---|---|---|---|---|---|
| tile_1956 | 4.36 / 1.64 | 23.4 / 9.1 | 97.6 / 92.4 | 14.0 / 5.8 | 108 / 7 |
| tile_lt | 4.91 / 1.82 | 26.6 / 10.2 | 70.7 / 67.4 | 7.5 / 3.2 | 100 / 0.1 |

In v2 the tile flow was 0 in every run. With cited Ksat and no tuning, Hoytville drains now carry 71–155 mm/yr,
depending on the evaporation mode (115–123 mm/yr with the ponding surface). **Novelty: methodological, (to verify).** This is
APSIM-SWIM tile flow obtained from a SSURGO restricting-layer Ksat alone.

**Undrained Hoytville** saturates to the surface in spring, and SWIM then stops ("failed to find solution"):
- Curve-number surface: stopped 1992-03-17 (fertilised).
- Ponding surface (CN2Bare = 0, which sets isbc = 1 in Swim.cs; flagged as an upper bound because it has no runoff):
  stopped 1993-09-06 (fertilised) and 1992-07-29 (0 N).
- Ponding plus eo_durn 1440: stopped 1992-07-01 (fertilised) and 1994-06-21 (0 N).

**1b. Matched-period drained vs undrained, Hoytville** (`results/apsim_lake_erie_matched_AN_v3.csv`; drained runs
cut to the undrained run's last day; totals from 1991-01-01):

| mode, N, period | case | N2O-N | N2-N | tile mm | tile NO3-N | Jan–Apr WT cm |
|---|---|---|---|---|---|---|
| pond, 172, to 1993-09-05 | undrained | 9.81 | 55.6 | 0 | 0 | 65 |
| | tile_1956 | 6.79 (−31%) | 36.3 (−35%) | 353 | 15.4 | 110 |
| | tile_lt | 7.09 (−28%) | 38.3 (−31%) | 345 | 8.4 | 95 |
| pond + eo1440, 172, to 1992-06-30 | undrained | 5.99 | 33.6 | 0 | 0 | 43 |
| | tile_1956 | 3.78 (−37%) | 21.2 | 127 | 13.0 | 106 |
| | tile_lt | 4.31 (−28%) | 24.1 | 117 | 8.2 | 96 |
| pond + eo1440, 0 N, to 1994-06-20 | undrained | 3.75 | 25.1 | 0 | 0 | 9 |
| | tile_1956 | 4.25 (+13%) | 25.9 | 552 | 13.1 | 101 |
| | tile_lt | 4.37 (+17%) | 27.0 | 518 | 9.8 | 87 |
| CN, 172, to 1992-03-16 | undrained | 2.84 | 16.3 | 0 | 0 | 122 |
| | tile_1956 | 2.70 (−5%) | 15.3 | 10 | 1.4 | 130 |

**Reading.**
- With fertiliser, drainage lowers N2O by 28–37% and N2 by 31–35% over the periods the undrained run survives.
- At 0 N the sign reverses (+13 to +17%).
- These are short records (1.2–3.5 years), so they are indicative only.
- Only the longest undrained run (0 N, pond + eo1440) has a Jan–Apr water table (9 cm) close to the SSURGO wet top
  (15 cm). The shorter runs start from a drier initial profile.

**Novelty: confirmatory in direction** (drainage reduces denitrification and N2O under N; to verify). The 0 N sign
reversal is a new observation, still to be checked against the literature.

**Berrien (Essex), full 1991–2020, fertilised** (CN, eo720):
- N2O: 2.98 undrained vs 2.96 (tile_1956) and 2.95 (tile_2rod) kg N/ha/yr, i.e. −0.7% and −0.9%.
- Tile flow: 1.4 and 1.8 mm/yr. Tile NO3-N: 0.20 and 0.27 kg/ha/yr.
- Jan–Apr water table: mean 96 cm, minimum 46 cm.

On this sandy-over-clay CanSIS profile the drains barely flow.

**Brookston (Essex):**
- No water table forms in any mode (it stays at the 100 cm profile base).
- Tiles never flow: base drainage is 735 mm over 2.4 years.
- This is inconsistent with the MI115 proxy, which is wet to the surface Dec–May. The likely cause is the 1 m CanSIS
  profile with its transferred leak, which is an open issue.

## 2. Brookston crash, diagnosed (three distinct SWIM failures)

1. **v2 soybean-year (1996) crash.** This was a numerical oscillation between soil nodes.
   SpaceWeightingFactor 0.5 (a documented Swim.cs option) cures it. Applied at all sites: **fixed**.
2. **Zero-flux base (gr = −1) crashed in soybean years.** The transferred ratio gr = −0.99457 (§1) avoids this.
3. **Maize sown on Brookston fails on 1991-06-09.**
   - First, why maize was sown at all: the example sowing rule (MinESW 100 mm, written for Dalby) can never fire on
     Brookston, whose plant-available water at DUL is 77 mm. In both v2 and the first v3 pass, Brookston maize was
     never sown. MinESW and MinRain are now 0 at all sites, with v2 windows kept.
   - Once sown, the surface node dries to air-dry (psi −6.9e5 cm, theta 0.076 against LL15 0.21) and Newton does not
     converge.
   - These settings still failed: SpaceWeightingFactor 1, 0 and −2; DTMax 10; DTHC/DTHP; solute weighting.
   - eo_durn 1440 (potential evaporation spread over 24 h instead of 12 h, same daily total; flagged as a numerical
     choice) only postpones the failure to 1991-06-22 / 1993-05-18.
   - **Not fixed. Reported as a limitation of SWIM 8142 on this CanSIS profile.**

**Side effect for v2:** v2 Lake Erie and county runs used MinESW 100. That suppressed sowing on shallow profiles,
which is the main reason for the low numbers of sown Ontario years in FINDINGS_AN_v3 (see §3).

**Sensitivity to eo_durn (Berrien and Hoytville, full runs):**
- Moving from 720 to 1440 raises Berrien base drainage from 137 to 217 mm/yr and Hoytville tile flow from 98 to
  155 mm/yr (tile_1956).
- N2O changes by +16% (Berrien) and +14% (Hoytville).
- So the sub-daily evaporation split is a first-order uncertainty on these clays (flagged).

## 3. Ontario: cited planting dates (25 → 32 units with ≥ 5 sown years)

Sources:
- **OMAFRA Agronomy Guide for Field Crops, Publication 811 (2022), Ch. 1:** "plant as soil moisture conditions
  permit after April 26 in areas receiving greater than 3,000 CHU-M1 or May 1 in areas <3,000 CHU-M1". Best yields
  come from corn planted in "late April and the first half of May", so the window ends 15-May.
- **CHU class:** CHU-M1 from NASA POWER 1991–2020, starting May 1, with the season ending at the first −2 °C or when the average temperature falls
  below 12 °C (OMAFRA wording). The daily formula follows Brown and Bootsma (1993) (citation flagged until verified).

Script `scripts/run_apsim_county_AN_v3.py`; outputs `results/apsim_ontario_summary_AN_v3.csv` and `_metrics_AN_v3.json`:

| variant | units ≥ 5 sown | mean sown years (of 30) | mean APSIM EF % | Holos-style base EF % (same units) | Spearman |
|---|---|---|---|---|---|
| v2 (MI NASS window, example rule) | 25 | 11.5 | 0.29 | 0.52 | 0.39 |
| rule (OMAFRA dates, example rule) | 25 | 10.6 | 0.27 | 0.52 | 0.53 |
| omafra (OMAFRA dates, sown on start date) | 32 | 24.9 | 0.52 | 0.52 | 0.63 |

**Reading.** The dates alone change little. The Dalby stored-water rule was what kept Ontario maize unsown. With
the cited dates and sowing on the start date:
- All 32 units are sown in most years.
- The mean APSIM EF almost doubles, to 0.52%. This equals the Holos-style mean, which is a consistency result, not
  validation.
- The rank agreement improves (ρ = 0.63).

Every v2/v3 Ontario EF that used the example rule should be read with this bias. **Novelty: methodological caveat
(to verify)**: the APSIM example sowing rule carries a Dalby stored-water threshold that is silently unreachable on
1 m Canadian profiles.

## 4. Holos (stock, public inputs) vs APSIM, Lake Erie direct fertiliser EF, 1991–2020

Holos values come from the collaborating project's stock runs (`D:\holos_lakeerie_AN_v1\results_AN_v1\`, read only).
EF = 2 × (mean annual N2O-N at 172 N − at 0 N) / 172 × 100, the same definition as Holos `EF_direct_rotation_pct`.
Holos has no drainage term and no carry-over (its rotation EF equals its corn-year EF). Script
`scripts/holos_vs_apsim_lake_erie_AN_v3.py`; output `results/holos_vs_apsim_lake_erie_AN_v3.csv`.

| site | Holos EF % | APSIM v2 EF % (soybean-year share) | APSIM v3 EF %, eo720 (share) | APSIM v3 EF %, eo1440 (share) |
|---|---|---|---|---|
| Hoytville | 3.01 | 2.70 (59%) | 3.15 tile_1956 (49%); 3.59 tile_lt (51%) | 3.27 (29%); 3.81 (29%) |
| Berrien | 0.37 | 1.41 (41%) | 2.26–2.28 (36–37%) | 2.34–2.35 (7–8%) |
| Brookston | 1.93 | failed | failed (§2) | failed |

- **Hoytville.** The totals agree within −10% to +27%. However, in APSIM 29–59% of the extra N2O falls in the
  following soybean year, a carry-over that Holos cannot represent. In v2 it was 59%, consistent with "more than half".
  In v3, with flowing drains, it is 49–51% (eo720) or 29% (eo1440). Holos therefore puts all of a comparable total
  into the corn year. The agreement in the total is partly coincidental, because the maize-year-only APSIM EF is
  1.6–2.7%.
- **Berrien.** APSIM is 6× Holos. The v3 sowing change (now sown every year) raised APSIM from 1.41% to about 2.3%.
- **Novelty: new comparison (to verify).** The soybean-year legacy is sensitive to the evaporation numerics. Report it
  as a range, not a single number.

## 5. Artifacts
- Scripts:
  - Lake Erie: `run_apsim_lake_erie_AN_v3.py` (modes `--pond`, `--eo1440`), `compare_lake_erie_AN_v3.py`,
    `matched_lake_erie_AN_v3.py`, `holos_vs_apsim_lake_erie_AN_v3.py`.
  - Water table and Ontario: `fetch_ssurgo_watertable_AN_v1.py`, `run_apsim_county_AN_v3.py`, `compare_ontario_AN_v3.py`.
- Results:
  - Run folders: `results/apsim_lake_erie_{,pond_,eo1440_,pond_eo1440_}AN_v3/`, `results/apsim_county_AN_v3/`.
  - Summary CSVs listed above.
- APSIM 2026.11.8142.0. NASA POWER 1991–2020.

## 6. Open issues
- Undrained Hoytville and all Brookston runs fail in SWIM before 2020.
- Brookston forms no water table.
- The Essex till ratio is transferred from Hoytville.
- The pond surface has no runoff.
- The eo_durn sensitivity is first order.
- US county runs (v2) also used MinESW 100 and should be rerun with the same sowing fix.