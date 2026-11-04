# FINDINGS_AN_v8: rain-driven N2O pulses and the distortion from annual averaging

This is a consistency check, not validation. Everything here comes from existing APSIM daily outputs; no new runs were made.

- **Script:** scripts/analyse_pulses_distortion_AN_v1.py
- **Outputs:** results/pulses_distortion_AN_v1.json and results/pulses_distortion_units_AN_v1.csv
- **Figures:** docs/figures/*_AN_v1.png
- **US:** 95 of 97 counties (two had fewer than 5 sown years), apsim_county_AN_v2, 100 vs 0 kg N/ha.
- **Ontario:** 32 units, apsim_county_AN_v3 OMAFRA variant.
- **Lake Erie:** the non-failed runs in v3 plus the Brookston SSURGO runs.
- **Iowa:** Webster in v2; Clarion and the Webster variants in v3.

## Decisions
- D1: a rain event is a day with Weather.Rain of at least 10 mm.
- D2: a k-day window (k = 1, 3, 7) is the event day plus the next k−1 days. Overlapping windows are merged, so no day is counted twice. I also report the share of days that fall inside windows, which is the expected share under random timing.
- D3: pulse metrics use the fertilised run and all days 1991–2020, pooled over years.
- D4: texture is the USDA texture class of the surface horizon, grouped as coarse, medium or fine.
- D5: each county gets one annual factor:
  - IPCC 2006: 1 %.
  - IPCC 2019: 1.6 % in wet zones and 0.5 % in dry zones.
  - Holos-style base EF: exp(0.00558 P − 7.7), using May–Oct NASA POWER P and Hargreaves PE. It is applied as the mean over sown years, and per year for the interannual comparison.
  - Ontario IPCC 2019 uses the wet value for all units. FLAG: this is an assumption I have not tested.
- D6: the APSIM EF for a year is (N2O-N at 100 N − N2O-N at 0 N)/100, over sown years.
- D7: bootstrap uses 2,000 resamples of counties (seed 20261104) with percentile 95 % CIs.

## 1. Pulses
Values are means with bootstrap 95 % CIs. "Days covered" is the share of days inside windows, i.e. the share expected under random timing.

| group | n | 1-d share | 3-d share (days covered) | 7-d share (days covered) | top 1 % days | top 5 % | top 10 % |
|---|---|---|---|---|---|---|---|
| US all | 95 | 0.27 (0.26-0.28) | 0.55 (0.54-0.56) (0.16) | 0.78 (0.77-0.79) (0.32) | 0.24 (0.22-0.25) | 0.57 (0.54-0.59) | 0.72 (0.70-0.75) |
| US poor drainage | 45 | 0.28 | 0.56 (0.55-0.58) | 0.79 | 0.22 | 0.54 | 0.69 |
| US well drained | 50 | 0.26 | 0.54 (0.52-0.55) | 0.77 | 0.25 | 0.59 | 0.75 |
| US fine texture | 26 | 0.30 (0.28-0.32) | 0.59 (0.57-0.61) | 0.81 | 0.24 | 0.58 | 0.73 |
| US medium | 57 | 0.27 | 0.54 | 0.77 | 0.24 | 0.57 | 0.72 |
| US coarse | 12 | 0.24 (0.21-0.27) | 0.50 (0.45-0.54) | 0.75 | 0.21 | 0.54 | 0.72 |
| Ontario all | 32 | 0.15 (0.14-0.17) | 0.32 (0.11) | 0.49 (0.24) | 0.24 | 0.47 | 0.62 |
| Ontario poor drainage | 9 | 0.17 | 0.37 (0.33-0.41) | 0.55 | 0.22 | 0.45 | 0.59 |
| Ontario well drained | 16 | 0.13 | 0.28 (0.25-0.31) | 0.45 | 0.26 | 0.49 | 0.65 |

- **Enrichment.** In the US, 3-day windows cover 16 % of days but carry 55 % of N2O, about 3.4 times the random share. In Ontario the windows cover 11 % of days and carry 32 % (about 2.8 times).
- **Drainage and texture.** Fine and poorly drained soils have more of their N2O tied to rain events, but the poor/well difference is small and the CIs overlap. Coarse soils are the least rain-linked.
- **Peak days.** Well-drained soils have slightly more of their N2O concentrated in the top days (fertiliser and thaw peaks that are not tied to rain).
- **Sites, 3-day share:**
  - Iowa Webster: 0.63
  - Clarion: 0.58
  - Webster SWIM: 0.69
  - Webster with a fixed water table: 0.28
  - Hoytville tile: 0.31
  - Berrien: 0.14
  - Brookston SSURGO tile: 0.16

  The Lake Erie sites have fewer events per year (Essex 14.6, Hoytville 28). FLAG: the webster_tile and webster_seep outputs are identical; this is inherited from v3 and has not been investigated here.

## 2. Distortion from annual averaging

### US, 95 counties
Each county total is synthetic N × EF.

| method | total error vs APSIM | skew (CI) | CV (CI) | P90/P10 | Spearman of totals (CI) | top-10 % overlap (CI) |
|---|---|---|---|---|---|---|
| APSIM | — | 2.67 (0.39-3.41) | 0.52 (0.37-0.67) | 2.76 | — | — |
| IPCC 2006 | −7 % (−17 to +3) | 0.21 (−0.38 to 0.95) | 0.27 (0.22-0.31) | 1.83 | 0.28 (0.07-0.47) | 0.2 (0-0.5) |
| IPCC 2019 | −45 % (−51 to −37) | 2.13 (1.56-2.82) | 0.51 (0.39-0.58) | 2.22 | 0.24 (0.03-0.44) | 0.3 (0-0.5) |
| Holos-style | +23 % (+8 to +38) | 0.29 (0.02-0.59) | 0.51 (0.44-0.57) | 4.70 | 0.46 (0.27-0.61) | 0.2 (0-0.5) |

- **Spearman on EF alone:** IPCC 2019 0.06; Holos 0.42. IPCC 2006 is undefined because its EF is constant.
- **Year-to-year variability:**
  - The IPCC factors give zero interannual variance.
  - Median APSIM interannual SD of EF is 0.52 percentage points (median CV 0.44). Holos-style gives 0.98 points, a median ratio of 2.08 (1.71-2.66).
  - The median per-county correlation between APSIM and Holos yearly EFs is 0.38.

### Ontario, 32 units
These are per-ha totals at 100 kg N/ha; there are no county N inputs.

| method | total error vs APSIM | skew | CV | Spearman (CI) | top-10 % overlap |
|---|---|---|---|---|---|
| APSIM | — | 0.94 (0.23-1.62) | 0.57 (0.42-0.69) | — | — |
| IPCC 2006 | +91 % (+60 to +138) | 0 | 0 | undefined | undefined |
| IPCC 2019 (wet, flagged) | +205 % (+154 to +275) | 0 | 0 | undefined | undefined |
| Holos-style | +6 % (−11 to +27) | 1.81 (0.52-2.64) | 0.36 (0.20-0.44) | 0.60 (0.36-0.77) | 0 of 3 (0-0.67) |

- Holos-style interannual SD relative to APSIM: median ratio 0.81 (0.69-1.04). The median yearly correlation is 0.55.

### Reading
- **Totals.** The annual factors either understate the US total (IPCC 2019, −45 %) or overstate it (Holos-style, +23 %). In Ontario, IPCC overstates by 2–3 times, while the Holos-style factor matches the total within its CI.
- **Hotspots.** All three methods identify APSIM hotspots poorly: top-10 % overlap is at most 30 %, and the rank correlation is at most 0.6.
- **Distribution shape.**
  - IPCC 2006 flattens the US skew: only N varies.
  - IPCC 2019 recovers the skew through its wet/dry split.
  - Holos-style widens the P90/P10 spread but removes the right tail that APSIM shows.
- **Interannual variance.** Annual factors either remove it (IPCC) or roughly double it in the US (Holos, which responds to P alone) while tracking APSIM only weakly (r ≈ 0.4).
- **Caveat.** The top-10 % sets are small (10 US counties, 3 Ontario units), so the overlap CIs are wide.

## Figures
- pulse_share_by_group_AN_v1.png
- county_distribution_by_method_AN_v1.png
- hotspot_rank_apsim_vs_methods_AN_v1.png
- interannual_sd_apsim_vs_holos_AN_v1.png

## Novelty labels
- [result] Rain-window attribution of APSIM N2O across 95 US counties and 32 Ontario units, with a random-timing baseline.
- [result] Hotspot and interannual-variance distortion from annual EFs, with bootstrap CIs.