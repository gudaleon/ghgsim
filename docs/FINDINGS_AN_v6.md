# FINDINGS_AN_v6 — Holos CLI vs APSIM, Lake Erie direct fertiliser N2O EF

This is a consistency check, not validation. It compares two models run on the same public inputs. Neither model is
an observation, so nothing here validates either one. Nothing was tuned.

Follows FINDINGS_AN_v4 §4 and FINDINGS_AN_v5.

## Sources

**Holos.** Stock Holos CLI runs: source holos-aafc/Holos c7683f71, with a configuration-only bind fix and no code
change. Inputs are public only: NASA POWER weather, corn–soybean 1991–2020, and 172 vs 0 kg N/ha urea on corn.
Numbers are read from the run outputs at these commits of the Holos run repository:

| Commit | What it holds | Files |
|---|---|---|
| `b1ca6e6` | Berrien findings note | `results/lake_erie_holos/FINDINGS_berrien_sens_AN_v1.md` |
| `ec6d67a` | Berrien one-at-a-time sensitivity, 36 runs | `results/lake_erie_holos/sens_AN_v1/holos_berrien_sens_ef_summary_AN_v1.csv`, `README_berrien_sens_AN_v1.md` |
| `2405da8` | Hoytville one-at-a-time sensitivity, 24 runs | `results/lake_erie_holos/sens_hoyt_AN_v1/holos_hoyt_sens_ef_summary_AN_v1.csv`, `holos_hoyt_precip_analytic_AN_v2.csv`, `README_hoyt_sens_AN_v1.md` |
| `75352e0` | Essex Parkhill loam vs Brookston clay | `results/lake_erie_holos/essex_loam_AN_v2/holos_lakeerie_ef_summary_AN_v2.csv`, `README_essex_loam_AN_v2.md` |

**APSIM.** Values come from `results/holos_vs_apsim_lake_erie_AN_v3.csv` (SWIM3; all modes) and
`results/apsim_brookston_soilwater_summary_AN_v1.json` (SoilWater).

**Combined table:** `results/holos_vs_apsim_lake_erie_AN_v4.csv`, built by `scripts/holos_vs_apsim_lake_erie_AN_v4.py`.

**EF definition, same in both models:** EF = 2 × (mean annual direct N2O-N at 172 N − at 0 N) / 172 × 100.

## 1. Per-site comparison

| Site | Holos texture class | Holos EF direct % | Holos direct + indirect % | May–Oct P/PE | APSIM EF % | APSIM soybean-year share |
|---|---|---|---|---|---|---|
| Hoytville (OH) | Fine | 3.008 | 3.352 | 0.775 | 3.15–3.81 (SWIM, drained, all modes) | 25–51% |
| Berrien (Essex) | Coarse | 0.370 | 0.718 | 0.684 | 2.26–2.35 (SWIM, all cases and modes) | 7–37% |
| Parkhill loam (Essex) | Medium | 0.370 | 0.672 | 0.684 | not run | — |
| Brookston (Essex) | Fine | 1.925 | 2.227 | 0.684 | 0.97 (SoilWater, undrained) | 30% |

Holos rotation EF equals its corn-year EF at every site (`EF_direct_corn_year_only_pct`). It has no carry-over into
the soybean year.

## 2. What sets the Holos EF (from the sensitivity runs)

**1. Texture class is the main driver.**
- RF_TX for Eastern Canada is Fine 2.55 vs Medium/Coarse 0.49, a 5.2× effect.
- Berrien: Coarse → Fine moves the EF from 0.370% to 1.925% (ratio 5.203).
- Hoytville: Fine → Coarse or Medium moves it from 3.008% to 0.578% (ratio 0.192).
- Parkhill loam (Medium) gives exactly the Berrien value, 0.370%.
- Sand/clay fractions, SOC, bulk density, great group and pH all give ×1.00 for direct N2O. pH changes only the
  indirect part (0.718 → 0.672% at Berrien with pH 5.3).

**2. Climate (May–Oct precipitation) is the second driver.**
- Berrien with Hoytville climate: 0.578% (×1.56).
- Hoytville with Berrien climate: 1.925% (×0.64).
- Precipitation ×0.75, run directly: Berrien 0.251%, Hoytville 1.743%.
- Higher precipitation could not be run through the CLI, because the NASA provider rescales it back to the record.
  Values computed from Holos's own equations are ×1.25 → Berrien 0.585%, Hoytville 5.79%.

**3. Minor drivers.**
- FTopo (ecodistricts 550 and 547): ×0.84–1.30 at Berrien, ×0.92–1.15 at Hoytville.
- Tillage: ≤5%.

**4. No drainage term.** Drainage class does not enter the direct EF, and there is no water-table or tile term.
Parkhill loam is poorly drained and tile-drained like Brookston, yet it takes the Coarse/Medium value.

## 3. Reading

**Hoytville.** The models agree within −4% to −21% (Holos below APSIM's drained range). Holos reaches this through
Fine class × the wetter climate, not through any drainage process. It therefore cannot show APSIM's 28–37%
drained-vs-undrained N2O difference (FINDINGS_AN_v4 §1b). It also places all of a similar total in the corn year,
whereas APSIM puts 25–51% in the following soybean year.

**Berrien.** APSIM is about 6× Holos. Even with Fine texture, Holos gives 1.925%, still below APSIM's 2.26–2.35%.
Holos has no mechanism for drainage, the water table or sand-specific denitrification, so the gap is structural:
an empirical class factor against a process model. It is not an input error.

**Brookston.** The sign reverses. Holos (Fine, 1.925%) is twice APSIM SoilWater (0.97%, undrained). The SoilWater
run drains freely and forms no water table, which conflicts with the soil-survey saturation (FINDINGS_AN_v5). So
this APSIM value is probably a low bound for a wet clay. The comparison is weak until Brookston can be run with a
water table.

**Overall.** Where the two models agree (Hoytville), they agree for different reasons. Where they disagree, the
cause is texture class in Holos against hydrology in APSIM. **Novelty: new comparison (to verify).** It shows a
5.2× texture-class step and no drainage response in Holos, against drainage- and carry-over-sensitive N2O in APSIM,
at the same Lake Erie sites.