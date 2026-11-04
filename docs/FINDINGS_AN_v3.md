# FINDINGS_AN_v3: expanded county sample (d) and Ontario counties (c), Paper B

These are consistency checks, not validation. Every result comes from files in this PR, generated on 2026-11-04. Lake Erie results are in FINDINGS_AN_v2 (PR #54).

## Set-up

- **Scripts:**
  - `scripts/build_county_sample_AN_v2.py` builds the sample, resumably.
  - `scripts/run_apsim_county_AN_v2.py` runs APSIM in 4 shards.
  - `scripts/compare_county_AN_v2.py` compares the runs with the annual EFs.
- **US sample:** 97 counties, stratified by May–Oct P/PE quintile and by well vs poor drainage, 10 per cell where available. The driest-quintile poor-drainage cell had only 7.
  - Soil: SSURGO dominant component at the county point.
  - Weather: NASA POWER, 1991–2020.
- **Ontario:**
  - Units: 32 upper-tier and rural single-tier units.
  - Soil: CanSIS soil of the dominant SLC component at each unit's point.
  - Boundaries: LIO, under the Ontario OGL.
  - Weather: NASA POWER.
- **Crop and N:** maize B_110, 100 kg N/ha urea, with a 0 N control.
- **Sowing:** USDA NASS Handbook 628 (2010) "most active" state corn windows. Ontario uses Michigan's (proxy, flagged).
- **Data fixes:**
  - NASA POWER −999 values filled in 53 units.
  - SAT capped at 1 − BD/2.65 in 32 units, each change recorded. v1 had dropped these units instead.
- **Units used in the comparisons:** those with at least 5 sown years.

## (d) Is the error of one annual EF systematic? US, n = 95

**Correlations with APSIM's fertiliser-induced EF (Spearman):**

| Compared with | Spearman |
|---|---|
| IPCC 2019 EF | 0.06 |
| Holos-style base EF | 0.40 |
| May–Oct P/PE | 0.35 |

**APSIM EF by group:**
- By drainage: well drained 0.92 %, poorly drained 1.35 %.
- By P/PE quintile (dry to wet): 0.92, 0.89, 1.14, 1.29 and 1.33 %.

**Regression** of ln(APSIM EF / IPCC 2019 EF) on P/PE and a poor-drainage indicator (R² 0.12):

| Term | β | SE |
|---|---|---|
| P/PE | 0.68 | 0.38 |
| Poor drainage | 0.29 | 0.11 |

**Aggregation error** of the summed county totals (Σ N × EF), relative to APSIM, with 2,000-draw county bootstrap 95 % intervals:

| Annual EF | Error | 95 % interval |
|---|---|---|
| IPCC 2019 | −44 % | −51 to −37 % |
| IPCC 2006 | −7 % | −16 to +2 % |
| Holos-style | −7 % | −17 to +4 % |

**Other results:**
- Pulses: the top 5 % of days carry 57 % of N2O on average.
- Concentration: the top decile of counties carries 22 % of the total N2O under APSIM, 24 % under IPCC 2019 and 19 % under Holos-style.

**Reading.** Within the model, the error of an annual EF is systematic and not random. The IPCC 2019 dry/wet split misses wetness and drainage; APSIM's EF rises with both. Poor drainage alone raises the APSIM/IPCC ratio by about e^0.29 ≈ 1.34×. **new-to-us**, in the model only. This direction agrees with the drainage and wetness literature cited in FINDINGS_AN_v1. **confirm**

## (c) Ontario, n = 25 with at least 5 sown years

| Measure | APSIM | Holos-style base EF |
|---|---|---|
| Mean EF | 0.29 % | 0.52 % |

- Spearman between APSIM and Holos-style EF: 0.39.
- **This is a weak result (limitation).** Many units sow in few years, because the example sowing rule under the Michigan window often finds no sowing day. For example, Essex (Brookston) sowed in only 2 of 30 years and Lambton in 6.
- Five units failed: Frontenac, Lennox & Addington, Prince Edward, regional municipality ON26000 and district municipality ON44000. They produced no Report output because there was no harvest.
- Ontario EF levels and ranks should not be used until Ontario-specific sowing windows are cited (OMAFRA planting dates).

## Paths

- Per-county `.apsimx` files and Daily/Report CSVs: `results/apsim_county_AN_v2/`.
- Summary: `results/apsim_county_summary_AN_v2.csv`.
- Metrics: `results/apsim_county_metrics_AN_v2.json`.
- Sample inputs: `data/apsim_county_v2_AN_v1/`.
- Ontario soils and weather: `data/ontario_soils_AN_v1/` and `data/ontario_counties_power_AN_v1/`.