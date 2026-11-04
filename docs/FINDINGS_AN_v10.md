# FINDINGS_AN_v10 - What drives soybean-year N2O carry-over in APSIM (diagnostic)

Status (DECISIONS D27.1): the soybean-year carry-over is a model result that field data contradict (Fabrizzi et al. 2024, doi:10.1002/jeq2.20566; Parkin & Kaspar 2006, doi:10.2134/jeq2005.0183). This note diagnoses it. Consistency checks, not validation.

Method: existing daily APSIM outputs only, no new runs (`scripts/diagnose_soy_carryover_AN_v1.py` -> `results/soy_carryover_AN_v1/`). Cases: Brookston SSURGO densic proxy (tile_1956, tile_2rod) and Hoytville (tile_1956, tile_lt), 1991-2020, 172 N minus its own 0 N control, day by day. Maize = odd calendar years, soybean = even, as in the earlier summaries. APSIM does not tag N2O by source pool, so the "pool" partition below uses the differences in each pool (NO3, NH4, net mineralisation, N2, soybean N) and their daily correlation with the N2O difference. It is an attribution by indicators, not a tracer budget. Soybean N fixation is not in the daily output; soybean aboveground N is used as a proxy.

## 1. Timing: the extra "soybean-year" N2O happens before the soybean is sown

| Case | Extra N2O, soybean yr (kg N/ha) | Jan-Apr | of which thaw days* | May-Sep | Oct-Dec | Soybean share (calendar) |
|---|---|---|---|---|---|---|
| Brookston tile_1956 | 2.36 | 1.71 (72%) | 0.46 | 0.60 | 0.06 | 0.42 |
| Brookston tile_2rod | 2.34 | 1.70 (73%) | 0.46 | 0.59 | 0.06 | 0.42 |
| Hoytville tile_1956 | 2.68 | 2.28 (85%) | 0.71 | 0.31 | 0.09 | 0.49 |
| Hoytville tile_lt | 3.14 | 2.67 (85%) | 0.83 | 0.37 | 0.10 | 0.51 |

*Thaw days: Jan-Apr days with mean T > 0 C after a day <= 0 C in the previous week.

Monthly: the extra N2O peaks in Jan-Apr (Brookston 0.32-0.51 kg/month; Hoytville up to 0.86 in January), falls through May-June and is near zero from July to November (`soy_carryover_monthly_AN_v1.csv`). Only 5-11% of fertiliser-induced N2O falls in the soybean growing season (May-Sep): Brookston 0.59-0.60 of 5.5-5.7 kg; Hoytville 0.31-0.37 of 5.4-6.2 kg.

## 2. Pools: residual nitrate, denitrified over winter and spring

| Case | dNO3 1 Jan (kg/ha) | dNO3 at soybean sowing, 11 May | dNH4 at sowing | d net mineralisation, soybean yr | dN2, soybean yr | d soybean N (max) | r(dN2O, dNO3) daily | r(dN2O, dNH4) |
|---|---|---|---|---|---|---|---|---|
| Brookston tile_1956 | +53.2 | +31.8 | -0.2 | +16.9 | +13.3 | +7.3 | 0.67 | -0.19 |
| Brookston tile_2rod | +53.7 | +31.8 | -0.2 | +17.0 | +13.1 | +7.3 | 0.66 | -0.20 |
| Hoytville tile_1956 | +71.0 | +43.6 | +0.1 | +14.1 | +15.2 | +4.2 | 0.56 | -0.41 |
| Hoytville tile_lt | +74.4 | +50.1 | +0.2 | +13.1 | +17.9 | +3.2 | 0.60 | -0.38 |

Reading, by candidate driver:
- **Residual NO3 (main driver).** Fertilised plots enter the soybean year with 53-74 kg/ha more nitrate, 32-50 kg/ha still at sowing. The daily N2O difference tracks the nitrate difference (r 0.56-0.67), not ammonium (negative r).
- **Denitrification in winter and spring thaw (the process).** 72-85% of the extra N2O falls in Jan-Apr, with extra N2 losses of 13-18 kg/ha/yr; thaw days alone give 0.46-0.83 kg/ha. This is the post-maize winter, before any soybean is present.
- **Residue mineralisation (secondary).** Net mineralisation is 13-17 kg/ha/yr higher after fertilised maize; it can sustain the smaller May-June tail, but N2O does not follow NH4.
- **Soybean N fixation (not a driver in these outputs).** Soybean N is only 3-7 kg/ha higher, and extra N2O is near zero during the soybean's main growth (Jul-Sep).

## 3. Why APSIM and the field disagree

Most of the APSIM "carry-over" is a bookkeeping effect: the calendar soybean year contains the winter and spring thaw after the fertilised maize, when residual nitrate is denitrified. Field soybean-phase measurements report season-long soybean emissions (Fabrizzi et al. 2024), and in that window APSIM's extra N2O is small (0.31-0.60 kg/ha, 5-11% of the fertiliser-induced total). APSIM's high post-maize nitrate (32-50 kg/ha extra at sowing) may still exceed field values; we have no measured soil nitrate to check. Field winter and thaw emissions are large in Ontario (30-90% of annual; Wagner-Riddle et al. 2007, doi:10.1111/j.1365-2486.2007.01388.x), so winter emission itself is plausible; its attribution to the soybean crop is not.

Implication: report carry-over as a model result, and attribute Jan-Apr emission to the preceding maize when comparing with field crop-phase data. Rerunning with a sowing-to-sowing (crop) year is a suggested next step, not done here.