# DECISIONS_AN_v28 - Tier 1 extras and county-year runner

Carries forward DECISIONS_AN_v27.

- **D28.1 New parameter version.** `data/ipcc_params_AN_v11.csv` = v10 unchanged + 143 rows built by `scripts/build_params_AN_v11.py`. v10 is not edited.
- **D28.2 F_SOM headline is Tier 1 Approach 1.** The 2006 text (p. 11.15-11.16) says that under Approach 1 dC has a single value for the area. Headline F_SOM uses the state net tillage-driven dC; if it is a gain, F_SOM = 0. The sum of county-level losses is reported as an upper sensitivity. R = 10 (cropland management change). Land-use-change F_SOM = 0: no gross transitions are available, which IPCC says biases N2O and must be acknowledged.
- **D28.3 Tillage mapping.** Census conventional -> full, conservation excluding no-till -> reduced (matches the Table 5.5 '>30% residue cover' description), no-till -> no-till. Medium input (FI = 1) throughout; HAC soils headline, Wetland (WET) as a sensitivity.
- **D28.4 Forage FracRenew.** IPCC applies FracRenew to the below-ground term and says perennial forage residue N counts at renewal (2006 footnote 3), while the alfalfa / hay root factors are described as annual root turnover (footnotes n / g). No verified stand-life is available, so runs report FracRenew = 1 and 0 as bounds; the caller chooses the headline.
- **D28.5 Silage.** Maize root factors applied to whole-plant silage DM; DM 35% from the NRCS Table 6-6 row label (typical, not regional).
- **D28.6 Crop N removal and BNF.** NRCS AWMFH Table 6-6 percentages applied as in its worked example. Census dry-basis haylage is treated as hay-equivalent (alfalfa hay 2.25% N; other haylage uses clover-grass hay 1.52%). Non-alfalfa hay uses clover-grass 1.52% (timothy 1.20% and tall fescue 1.97% are stored as brackets). Soybean BNF from Salvagiotti et al. 2008 (50-60%).
- **D28.7 N budget is closed by an explicit residual**, not by tuning. The residual collects deposition, non-soybean BNF, denitrification to N2, soil N change and the errors in every term.
