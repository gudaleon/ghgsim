# FINDINGS_AN_v9: Webster tile fix, rain-threshold sensitivity and the Holos P/PE switch

This is a consistency check, not validation.

- **Scripts:** scripts/run_apsim_webster_drains_AN_v1.py and scripts/analyse_pulses_distortion_AN_v2.py
- **Outputs:** results/pulses_distortion_thr{5,10,20}_AN_v2.json and units CSVs, plus results/apsim_webster_drains_*_AN_v1/
- **Figures:** docs/figures/pulse_share_by_group_thr{5,20}_AN_v1.png

## 1. Why webster_tile and webster_seep were identical (results/apsim_AN_v3)
- The drain was configured correctly: SwimSubsurfaceDrain at 1200 mm depth and 28.5 m spacing, Klat 792 mm/d.
- The seepage lower boundary, however, lets the 2 m profile drain at its base as soon as the base node saturates. Cg ksat is 9.17 µm/s (792 mm/d).
- As a result WaterTable stayed at 2000 mm on every day of 1991–2020 in both runs. TileDrain was 0, so the two outputs match exactly. This is a boundary-condition problem, not a code bug.
- Webster (cokey 28627783) has no SSURGO restriction record, and an SDA query found no Iowa Webster major component that has one.

**Fix.** I used SWIM's gradient boundary, as in the Lake Erie v3 runs, with gr = K_till/K_Cg − 1 and SpaceWeightingFactor 0.5. Two cited till conductivities were tested:

| till K below 2 m | gr | undrained | drained | outcome |
|---|---|---|---|---|
| weathered Des Moines Lobe till, 3 µm/s (Ground Water 1992, doi:10.1111/j.1745-6584.1992.tb01529.x) | −0.673 | ran | ran | No water table forms: N2O 0.86 kg N/ha/yr, tile 0 mm, base drainage 92 mm/yr. The two runs are identical again. |
| unfractured till, 1e-9 m/s (Minnesota Stormwater Manual, typical) | −0.99989 | SWIM fails in early 1991 (saturates to the surface; same as undrained Hoytville and Brookston) | ran | Drained run at 100 N / 0 N: tile 44 / 25 mm/yr, N2O-N 2.45 / 0.98 kg/ha/yr (EF 1.47 %), base drainage 12 mm/yr, NO3 leaching 0.8 kg N/ha/yr, water table minimum 396 mm and mean 1772 mm. |

FLAGS:
- The unfractured value is a generic lower bound. Below 2 m, the till at the Boone site is oxidized and fractured (Young et al. 2019, doi:10.1007/s10040-019-02076-y).
- Tile flow of 44 mm/yr is well below the flow usually reported for tile-drained Iowa fields. It is not tuned.
- The v3 webster_tile and webster_seep files are left unchanged as a record. The fixed drained run is added to the Iowa sites in section 2.

## 2. Rain threshold (5, 10, 20 mm/day): N2O share after events
Values are means with bootstrap 95 % CIs. "Days covered" is the share of days inside 3-day windows, i.e. the share expected under random timing.

| group | thr 5: 3-d share (days covered) | thr 10 | thr 20 |
|---|---|---|---|
| US all (95) | 0.68 (0.67-0.69) (0.29) | 0.55 (0.54-0.56) (0.16) | 0.30 (0.29-0.31) (0.054) |
| US fine / coarse | 0.72 / 0.64 | 0.59 / 0.50 | 0.33 / 0.27 |
| US poor / well drained | 0.69 / 0.67 | 0.56 / 0.54 | 0.31 / 0.30 |
| Ontario all (32) | 0.53 (0.51-0.56) (0.30) | 0.32 (0.29-0.35) (0.11) | 0.10 (0.09-0.11) (0.017) |
| Ontario poor / well drained | 0.57 / 0.49 | 0.37 / 0.28 | 0.12 / 0.08 |

- **1-day and 7-day shares, US:** 0.39 and 0.88 at 5 mm; 0.13 and 0.49 at 20 mm.
- **Enrichment over random rises as the threshold rises:**
  - US: about 2.3 times at 5 mm, 3.4 times at 10 mm and 5.6 times at 20 mm.
  - Ontario: about 1.8, 2.8 and 5.9 times.
- **Texture and drainage.** The ordering holds at every threshold: fine above medium above coarse, and poorly drained above well drained. The Ontario drainage gap is the only drainage difference whose CIs separate.
- **Sites, 3-day share at 10 mm:**
  - Webster fixed drained run: 0.41, against 0.52 for the old v3 webster_tile.
  - Clarion: 0.58
  - Hoytville: 0.31
  - Brookston: 0.16
- **The threshold does not affect section 3.** The county distortion metrics use annual EFs and APSIM annual totals, which do not depend on rain events. The distortion JSONs for 5 mm and 20 mm are byte-identical, and the hotspot and variance results in v8 hold at every threshold.

## 3. Holos-style factor with the P/PE switch on (f_lower = 1)
The Holos base EF is exp(0.00558·X − 7.7). X is May–Oct P when P > PE. When P < PE, the documented dry-area branch uses PE, weighted by the fraction of land in lower landscape positions. I set that fraction to 1 (the upper bound), applied year by year. No other P/PE equation is cited, so none is used. Every unit has dry years: 2,013 of the US unit-years and 665 of the Ontario unit-years.

| | US: rainfall-only (v8) | US: P/PE switch | Ontario: rainfall-only | Ontario: P/PE switch |
|---|---|---|---|---|
| total error vs APSIM | +23 % (+8 to +38) | +232 % (+193 to +276) | +6 % (−11 to +27) | +172 % (+109 to +252) |
| Spearman of totals | 0.46 (0.27-0.61) | 0.32 (0.12-0.51) | 0.60 (0.36-0.77) | −0.04 (−0.44 to 0.35) |
| top-10 % overlap | 0.2 | 0.1 (0-0.4) | 0 of 3 | 0 of 3 |
| skew of county totals (APSIM US 2.67, Ontario 0.94) | 0.29 | 1.85 (0.30-2.72) | 1.81 | 0.16 |
| interannual SD ratio vs APSIM (median) | 2.08 (1.71-2.66) | 2.35 (1.77-2.83) | 0.81 | 0.77 (0.62-1.01) |
| median yearly correlation with APSIM | 0.38 | −0.14 | 0.55 | 0.00 |

Reading:
- With f_lower = 1, the PE branch roughly triples the totals. It restores the US right-skew but loses the year-to-year co-variation with APSIM: the correlation becomes negative in the US and zero in Ontario, because dry years now get the highest EF.
- In APSIM, by contrast, N2O tracks rain.
- The rainfall-only form (f_lower = 0) stays closer to APSIM on every metric except skew.
- FLAG: in Holos, f_lower comes from an ecodistrict lookup. The value 1 used here is a bound, not the Holos value for any of these units.

## Novelty labels
- [method] Diagnosis of the identical tile/no-tile outputs: a seepage face over a permeable C horizon cannot perch water.
- [result] Rain-window attribution is robust in its ordering across thresholds of 5–20 mm, and the enrichment over random timing increases with the threshold.
- [result] Turning on the Holos P/PE dry branch moves Holos further from APSIM, not closer.