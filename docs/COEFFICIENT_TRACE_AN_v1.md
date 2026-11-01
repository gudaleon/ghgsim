# Coefficient trace of Holos UNVERIFIED and SOURCE-TRACED values

**Version:** AN_v1  
**Date:** 2026-11-01  
**Machine-readable table:** `data/coefficient_trace_AN_v1.csv`  
**Scope:** every coefficient labelled UNVERIFIED or SOURCE-TRACED in `data/holos_params_canada_AN_v4.csv` and `data/holos_params_us_AN_v2.csv`, plus the numeric/behaviour coefficients of the Holos forks in `data/holos_forks_AN_v2.json`.

Does not overwrite prior versioned files.

## Rule used this phase

- **VERIFIED** only if a primary published source that was opened this phase contains the same numeric value (or the same switch) at an exact table, page, or equation.
- A Holos file:line is never VERIFIED.
- If the value is present only in Holos code or Holos tables, the row is **HOLOS-ONLY**, with the Holos path, the citation Holos gives, and whether that cited source actually contains the value.

Param CSVs are not rewritten this phase. Operational labels in `holos_params_*` stay as they were; this document is the independent trace.

## Sources opened

| Source | URL or DOI | Opened | Used for |
|--------|------------|--------|----------|
| IPCC 2006 Vol 4 Ch 10 | https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_10_Ch10_Livestock.pdf | Y | Eq 10.3, 10.21, 10.24; Tables 10.12, 10.17, 10.19, 10A-4, 10A-5, 10A-7 |
| IPCC 2019 Refinement Vol 4 Ch 10 | https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4/19R_V4_Ch10_Livestock.pdf | Y | Table 10.12 (Updated); Eq 10.24 (Updated); weaning text p.10.19 |
| IPCC 2006 equation summary | https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_14_An2_SumEqua.pdf | Y | Eq 10.24 UE/ASH wording |
| ECCC 2024 NIR Part 2 | https://unfccc.int/sites/default/files/resource/2024NIR%20-%20Part%202.pdf | Y | Annex 3.4 A3.4.2.1 dairy Ym range 5.5–5.7% |
| ECCC 2025 NIR Part 2 | https://unfccc.int/sites/default/files/resource/2025NIR%20-%20Part%202.pdf | Y | same Ym range; dry cows/heifers 6.5% |
| ECCC 2022 NIR Part 2 (Holos citation year) | https://publications.gc.ca/collections/collection_2022/eccc/En81-4-2020-2-eng.pdf | N | archive interstitial; 5.6% still not a 2024/2025 table cell |
| Little et al. 2008 Holos v1.1.x methodology | https://publications.gc.ca/collections/collection_2009/agr/A52-136-2008E.pdf | Y | TAM, Ym 0.065, calf enteric (not today’s hard zero) |
| Sheppard et al. 2015 | DOI 10.4141/cjas-2014-158 | Y | beef husbandry survey; cows ~545 kg, not 610 |
| Lactanet 2020 Canada herds | https://lactanet.ca/wp-content/uploads/2021/03/2020_Canada_Herds.pdf | Y | milk-value benchmarks; no 687 kg body weight |
| Benchaar et al. 2001 | DOI 10.4141/A00-119 (methane modelling paper; SOURCES_AN_v1 listed A00-079) | Y | no 5.6 / 3.5 / 0.0093 / 0.078 table cells |
| Coates/De Vries 2020 | DOI 10.3168/jds.2019-17361 | Y | productive lifespan; not a manure-cover paper |
| Sommer et al. 2000 | DOI 10.2134/jeq2000.00472425002900030009x | Y | slurry covers reduced CH4 ~38%, not a 0.4 remaining factor |
| Nennich et al. 2005 | J. Dairy Sci. 88:3721–3733 | Y | calf N 0.063 kg/d typical, not 0.078 |
| ASAE D384.2 / NRCS AWMFH Ch. 4 | https://directives.nrcs.usda.gov/sites/default/files2/1712930943/17165.pdf | Y | 9.2 lb VS / 1000 lb AU (lactating); 9.3 lb VS/d-a (dry cow) |
| 40 CFR Table JJ-2 | https://www.law.cornell.edu/cfr/text/40/appendix-Table_JJ-2_to_subpart_JJ_of_part_98 | Y | dairy-calf VS 6.41 / B0 0.17 (heifers and calves) |
| EPA 2025 Inventory Annexes | https://ghgi.cgs.umd.edu/Web%20Content/FAQ%20Files/US-GHG-Inventory-2025-Annexes.pdf | Y | TOC: cattle Nex is A-155/A-156; TAM A-128; DE/Ym A-138/A-139. Table A-177 is not those cattle tables. |

NRC 2001 is cited by IPCC and Little 2008; no NRC 2001 table opened this phase contained 0.0093, 0.078, or 5.6.

## Summary counts (`data/coefficient_trace_AN_v1.csv`)

| status | n | meaning |
|--------|---|---------|
| VERIFIED | 7 | opened primary source contains the value at a cited table/page/equation |
| HOLOS-ONLY | 29 | Holos file:line (or ghgsim US param citation) is the only location of that exact use |

### Newly VERIFIED

1. **UE grain 85% / UE 0.04 and 0.02** — IPCC 2006 Eq 10.24 notes pp. 10.42–10.43 and IPCC 2019 Eq 10.24 (Updated) p. 10.65. The Holos grain-percent switch is the IPCC wording. The Phase 2 `source_correct` DE ≥ 80 path is not in those notes.
2. **ASH 8% of DM** — IPCC 2006 Eq 10.24 notes pp. 10.42–10.43 (“e.g., 0.08 for cattle”). Example text, not a table default. IPCC 2019’s example is 0.06 for sows.
3. **Ym 6.3%** (dry close-up; heifers low fiber) — IPCC 2019 Table 10.12 (Updated) p. 10.46 (dairy medium / mixed / dry-phase fn 4).
4. **Ym 7.0%** (dry far-off; heifers high fiber) — IPCC 2019 Table 10.12 (Updated) p. 10.46 (non-dairy >75% forage; fn 4 low-production dry).

Holos’ diet CSV footnote that points beef Ym at IPCC 2019 **Table 10.13** is the wrong table number. In the 2019 chapter, cattle/buffalo Ym is Table 10.12 (Updated); Table 10.13 (Updated) is sheep.

### Claimed sources that do not contain the Holos number

| Holos value | Holos citation | What the opened source actually has |
|-------------|----------------|-------------------------------------|
| Dairy Ym 5.6% | ECCC 2022 midpoint of 5.5–5.7% | 2024/2025 NIR text range only; no 5.6% table cell |
| Beef B0 0.17 | IPCC 2006 Table 10A-7 NA | Table 10A-7 is market swine. NA other cattle (Table 10A-5 p. 10.78) is **0.19**. 0.17 is Eastern Europe / Oceania other cattle |
| Cool pasture MCF 0.015 | IPCC 2006 Table 10.17 cool | Cool pasture is **0.01**; **0.015** is temperate ~15°C |
| US pasture MCF 0.02 | IPCC 2006 Table 10.17 15°C | 15°C pasture is **0.015**; **0.02** is warm |
| US dairy Nrate 0.47 | IPCC 2006 Table 10A-5 | 10A-5 is B0/VS/mass. Table 10.19 NA dairy is **0.44**; **0.47** is Asia dairy |
| Beef cow TAM 610 kg | Sheppard et al. 2015 | Opened paper: cows ~**545 kg** |
| Dairy TAM 687 kg | Lactanet 2020 | Opened 2020 herds PDF has no body-weight cell |
| Calf VS 0.0093 | none | No calf table cell. Nearest look-alike is ASAE ~9.2 lb VS / 1000 lb AU for lactating cows |
| Calf N 0.078 kg N/head/day | none | Nennich 2005 calf mean 0.063 kg N/d |
| Cover remaining 0.4 / 0.25 | none | IPCC Table 10.17 footnote is a **40% reduction** already in with-crust MCF, not a remaining factor of 0.4. Sommer 2000: ~38% reduction |

## Forks

| Fork | Trace |
|------|--------|
| `HOLOS.GE.digestibility` | TDN in the Eq 10.3 denominator is HOLOS-ONLY. IPCC Eq 10.3 p. 10.16 uses DE%. |
| `HOLOS.VS.digestibility` | TDN in Eq 10.24 is HOLOS-ONLY. |
| `HOLOS.VS.urinary_energy` | VERIFIED against Eq 10.24 85% grain notes. |
| `HOLOS.ENTERIC.calf_zero` | HOLOS-ONLY as applied to all dairy calves. IPCC 2019 p. 10.19 zeros **unweaned** calves only. |
| `HOLOS.VS.calf_coeff` | HOLOS-ONLY (0.0093). |
| `HOLOS.CH4.cover_reduction` | HOLOS-ONLY (0.4 / 0.25). |
| `HOLOS.NEX.calf_nrate` | HOLOS-ONLY (0.078 kg N/head/day). |
| `HOLOS.YM.dairy` | HOLOS-ONLY as a 5.6% point (ECCC range 5.5–5.7%). |

## Questions for Aaron (Holos team, AAFC)

These are the HOLOS-ONLY items. They are written as neutral source questions, not as requests to change Holos.

1. Dairy lactating Ym is stored as 5.6% of GE, described as the midpoint of an ECCC 5.5–5.7% range. ECCC 2024 and 2025 NIR Part 2 Annex 3.4 section A3.4.2.1 state that range in running text and do not print 5.6% in a table. Is 5.6% a Holos midpoint, or is there another table or year that lists 5.6%?
2. Dairy calf volatile solids are `VS = (9.3/1000) × live weight` at `DairyCattleResultsService.cs:159`. What is the published source for 9.3 g VS per kg live weight per day?
3. Dairy calf nitrogen excretion is hard-coded as `0.078` at `DairyCattleResultsService.cs:195`. Confirm the intended units (ghgsim treats this as kg N/head/day) and the published source.
4. Covered liquid manure multiplies CH4 by 0.4 for a natural crust (`AnimalResultsServiceBase.cs:966-976`). IPCC 2006 Table 10.17 p. 10.44 describes a 40% **reduction** already built into the with-crust MCF. Is 0.4 a remaining-emission factor, a percent reduction, or a different source?
5. The same block uses 0.25 for other covers. What is the published source for 0.25?
6. Holos documentation cites North America beef B0 = 0.17 from IPCC 2006 Table 10A-7. Table 10A-7 is market swine; Table 10A-5 North America other cattle is 0.19. Which table and region should beef B0 use?
7. Table 16 cites Sheppard et al. 2015 for beef cow TAM = 610 kg. The opened 2015 paper discusses cows at about 545 kg and does not list 610. Is 610 from the A. Alemu personal communication, from a different Sheppard table, or from another source?
8. Table 16 cites Lactanet 2020 for dairy cow TAM = 687 kg. The opened 2020 Lactanet Canada herds PDF has no body-weight cell. Which Lactanet 2020 table or extract lists 687 kg?
9. Same Lactanet 2020 citation: dairy bulls 1200 kg and dairy calves 45–127 kg. Which Lactanet table lists those masses?
10. Barley-finisher Ym is 3.5% of GE. IPCC 2019 Table 10.12 (Updated) p. 10.46 has feedlot grain 4.0% and steam-flaked corn 3.0%, and no 3.5% cell. What is the source of 3.5%?
11. Cool-climate pasture MCF is 0.015. IPCC 2006 Table 10.17 p. 10.44 cool pasture is 0.01; 0.015 is the ~15°C cell. Is cool pasture intended to use the 15°C column?
12. Dairy calf enteric CH4 is hard-coded to 0 for the whole calf class (`DairyCattleResultsService.cs:128-129`). IPCC 2019 p. 10.19 zeros unweaned calves; weaned calves use non-dairy Ym. Does Holos intend zero for unweaned animals only, or for all dairy calves including 45–127 kg?
13. Eq 10.3 / Eq 10.24 in Holos use percent TDN in the digestibility slot. IPCC writes DE%. Is TDN used as a measured stand-in for DE, or is the substitution intentional even when both are known?
14. US dairy Nrate 0.47 kg N/(1000 kg)/day is stored against IPCC Table 10A-5. Table 10.19 North America dairy is 0.44; 0.47 is the Asia dairy cell. Which source should Vermont and Delaware use?

---

**Document:** `docs/COEFFICIENT_TRACE_AN_v1.md`  
**CSV:** `data/coefficient_trace_AN_v1.csv`
