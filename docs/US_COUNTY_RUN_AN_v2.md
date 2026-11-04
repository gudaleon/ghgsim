# US county run AN_v2: IPCC 2006 vs 2019 Tier 1, 2022 Census activity

Follows docs/US_COUNTY_RUN_AN_v1.md. Script: `scripts/run_us_county_2006_vs_2019_AN_v2.py`; params: `data/ipcc_params_AN_v10.csv`
(built by `scripts/build_ipcc_params_AN_v10.py` = v9 + 262 rows with page citations). Decisions: docs/DECISIONS_AN_v5.md.
Comparison with EPA is a **consistency check, not validation**. Units MMT CO2e, AR5 (CH4 28, N2O 265).

## What changed from v1
1. Three activity variants: `disclosed` (v1 behaviour), `reconstructed` (exact Census identities), `D_allocated`
   (reconstructed + state remainder of each withheld series allocated to withheld counties by OPERATIONS WITH INVENTORY). Headline = D_allocated.
2. Soil N2O completed with crop residues (19 Census crop series; 2006 Eq 11.7A / Table 11.2; 2019 Eq 11.6 / Table 11.1a), rice on EF1FR,
   indirect volatilisation and leaching reported as separate rows for every N source.
3. Sheep, goats, horses, mules/asses added (enteric, manure CH4, PRP N); pullets a separate class with own Nrate.
4. 2019 run uses 2019 VS (Table 10.13A p10.56) and body weights (Table 10A.5 p10.117).
5. Map: EPSG:5070, state borders, cb_2021 boundaries (Connecticut no longer grey), clipped ±60 %, short label.

## National results (CONUS+AK+HI counties, 2022 activity)
| Variant | Category | 2006 | 2019 | Δ% | EPA 2022 | 2006/EPA | 2019/EPA |
|---|---|---|---|---|---|---|---|
| D_allocated | Enteric CH4 | 155.9 | 183.2 | +17.5 | 192.6 | 0.81 | 0.95 |
| D_allocated | Manure CH4 | 42.2 | 59.2 | +40.4 | 64.7 | 0.65 | 0.92 |
| D_allocated | Manure N2O | 11.1 | 16.6 | +49.3 | 17.0 | 0.65 | 0.98 |
| D_allocated | Soil N2O | 120.2 | 82.4 | −31.5 | 291.8 | 0.41 | 0.28 |
| D_allocated | **Total** | **329.4** | **341.4** | +3.6 | 566.1 | 0.58 | 0.60 |
| disclosed | Total | 278.9 | 287.6 | +3.1 | 566.1 | 0.49 | 0.51 |

`reconstructed` equals `disclosed` exactly: the identities (total = cows + excl. cows; cows = milk + beef) never had
exactly one unknown, because NASS applies complementary suppression. Kept as a reported variant to document this.
Full subcategory breakdown: `data/us_national_2006_vs_2019_vs_epa_AN_v2.csv`.

## Why the numbers differ from EPA
- **Livestock (≈0.92–0.98 of EPA under 2019):** EPA uses a Tier 2 cattle enteric model (diet/DE, Ym, monthly populations
  from NASS surveys) and state MMS shares with Tier 2 VS/Nex. The 2006 defaults are lower mainly via lower VS and lower
  Nex for North American cattle. The remaining gap is plausibly Census Dec-31 inventory vs annual average population and Tier 2 vs Tier 1.
- **Soils (0.28–0.41):** EPA uses DayCent (Tier 3) for major crops plus mineralisation/SOM, organic (histosol) soils, and
  Tier 1 for the rest. ghgsim Tier 1 omits F_SOM and F_OS (no public county dataset), hay/forage renewal residues, and
  has no N from other organic amendments. DayCent direct-N2O also responds to weather and soil, which Tier 1 cannot.
- **2006→2019 soil drop (D_allocated breakdown):** PRP direct N2O from cattle/swine/poultry 24.3→4.9 (lower 2019 EF3PRP, params v9/v10),
  crop residues 22.4→12.7 (Table 11.1a vs Table 11.2 factors), synthetic N 49.2→40.5 (2019 disaggregated EF1). Indirect terms rise slightly.

## Remaining gaps
1. Organic soils (F_OS) and SOM mineralisation (F_SOM): not estimated.
2. Hay/forage/silage/cotton/vegetable residues: excluded (no renewal data / no table rows).
3. 2006 Table 10.22 has no FracGas cells for other-cattle liquid and swine dry lot; N is conserved to soils with volatilisation 0 (flagged).
4. Residue factor NA cells filled from generic rows (flagged SUBSTITUTE in v10).
5. No irrigation adjustment to FracLeach in dry areas; no residue burning; FracRemove = 0.
6. Allocated (D) cells are model estimates, not disclosed data.
