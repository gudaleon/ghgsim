# FINDINGS_AN_v5 — Brookston with APSIM SoilWater (addendum to FINDINGS_AN_v4)

All runs are a consistency check, not validation. Nothing was tuned.

**Change.** Brookston (Essex, CanSIS profile) was rerun with APSIM SoilWater (the cascading-bucket water model)
instead of SWIM:
- Everything else is identical to `run_apsim_lake_erie_AN_v3.py`: soil, NASA POWER weather 1991–2020, sowing
  change 5, and 172 kg N/ha urea on maize.
- SoilWater has no tile drain, so this is an **undrained** run only.
- Script: `scripts/run_apsim_brookston_soilwater_AN_v1.py`. Summary: `scripts/summarise_brookston_soilwater_AN_v1.py`
  writes `results/apsim_brookston_soilwater_summary_AN_v1.json`.

**Result.**
- Both runs (172 N and 0 N) complete 1991–2020 with no failure.
- Maize is sown in every odd year, between 10 and 17 May. These are 15 maize years; the sowing condition evaluated
  in that window is not documented here.

| Quantity, per year | 172 N | 0 N |
|---|---|---|
| N2O-N (kg/ha) | 1.30 | 0.47 |
| N2-N (kg/ha) | 5.23 | — |
| NO3-N leached (kg/ha) | 31.4 | 13.1 |
| Drainage (mm) | 231 | — |
| Runoff (mm) | 2.8 | — |

- Rain is 787 mm/yr.
- **Direct fertiliser EF is 0.97%**, against 1.93% in stock Holos. The maize-year-only EF is 0.68%.
- **30%** of the extra N2O falls in the soybean year.
- Of the soybean-year rows, 18 years show soybean grain. That is more than the 15 alternate years, possibly because
  the reporting variable carries over between seasons. This is unchecked and flagged.

**Reading.**
- This removes the numerical failure, but it is not a drainage result:
  - There is no tile.
  - SoilWater drains freely from the 1 m profile base (231 mm/yr), so the cascade model forms no perched water table.
  - This is inconsistent with the soil survey saturation (surface Dec–May, MI115 proxy), the same contradiction as
    in SWIM.
- Even so, as with Hoytville and Berrien, APSIM places a carry-over share in the soybean year that Holos does not
  represent.

**Not done: a cited seasonal water-table boundary.** The soil survey gives only months and a top depth (0 cm,
Dec–May). Turning that into a daily boundary would need an invented shape, depth and recession, so it is not
imposed. The rule against inventing soil parameters applies.

**Novelty: none** (a model-switch robustness check).