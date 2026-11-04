# FINDINGS_AN_v12 - Cause of the Ontario sowing-year EF shift (FINDINGS_AN_v11)

Consistency checks, not validation. Existing outputs only, no new runs (`scripts/diagnose_ontario_shift_AN_v1.py` -> `results/ontario_shift_AN_v1/`).

## 1. The shift is a year-set mismatch, not a carry-over effect

| Region | Units | Median change, as reported in v11 (sowing years vs Report "sown" years) | Median change, same years both ways | Median change, calendar all years vs Report years |
|---|---|---|---|---|
| Ontario | 31 | +12.8% | **+1.0%** | +4.2% |
| US | 97 | +1.3% | **-0.1%** | -2.9% |

When the sowing-year and calendar-year EFs are averaged over the same years, the Ontario difference falls from about +10-13% to +1%, the same as the US. The v11 shift came from comparing different sets of years.

## 2. Why the year sets differ: maize harvested the next spring

- `A.sown()` (analyse_pulses_distortion_AN_v2.py) takes "sown years" as the calendar years of Report rows. The Report is written at the `[Maize].Harvesting` event, so these are **harvest** years, not sowing years.
- The harvest manager harvests only when the crop is ripe (`IsReadyForHarvesting`), with no frost kill or end-date harvest. The sowing rule sows only if no crop is alive (`!Crop.IsAlive`). Cultivar: `B_110` (the APSIM example cultivar).
- In cool seasons the crop does not ripen before winter and is harvested the following spring (for example, unit ON9000: 1991 crop harvested 20 Apr 1992; 1993 crop harvested 29 May 1993... 1995 crop 29 Mar 1995). Ontario: **30.5% of 882 harvests fall in January-June**, in all 32 units (median 29% per unit). US: 13% of 2,416 harvests.
- Consequences: (a) Report years are shifted to the harvest year; (b) when a crop is still alive in the next sowing window, that year is not sown, so onset years (median 29 per Ontario unit) outnumber Report years (25); (c) every Ontario unit has onset years with no Report row, and 22 have Report years with no onset.

## 3. What this means

- The v11 Ontario "+10.5%" is explained; FINDINGS v11 sections 3-4 should be read with this correction. US and Ontario EFs are robust to the year definition (about 1% on matched years).
- **New caveat (model management, not soil or climate):** APSIM maize with cultivar B_110 and harvest-at-ripe does not mature before winter in about 30% of Ontario seasons and 13% of US seasons, and stands over winter. Real Ontario corn is harvested in autumn. This affects the Ontario and US county N2O (winter N uptake, residue timing, skipped years). It is a likely artifact for the Ontario numbers in FINDINGS v4/v8 (APSIM EF 0.52%, Holos-style +6%, Spearman 0.60/0.63).
- Fixing it needs reruns with a shorter-season cultivar matched to Ontario heat units, or a dated harvest/frost-kill rule. That is a parameter/management choice that must come from a cited source (for example, OMAFRA Pub. 811 hybrid-CHU guidance mapped to an APSIM cultivar). It is not done here: it is a scope decision for the author.

## 4. Manuscript numbers

No manuscript number changes: the v20 main text does not cite the v11 Ontario shift, and SI v12 Table S20 values are correct as computed. The SI S17 reading ("the Ontario shift is unexplained") is now explained, and the overwintering-maize caveat is new. Both go in the next SI version once the author decides on the rerun. No v21 made.