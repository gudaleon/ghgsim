# Comparator national inventories for Paper B (AN_v1)

Checked 2026-11-03. Sources: UNFCCC "National Inventory Submissions 2026"
(<https://unfccc.int/ghg-inventories-annex-i-parties/2026>). Every number below is either read by
`scripts/fetch_inventories_AN_v1.py` from the official **CRT** (Common Reporting Tables, the
spreadsheets each country files every April) or quoted from the country's **NID/NIR** (National
Inventory Document/Report, the methods text). Files, URLs and SHA-256 hashes are in
`data/inventories_manifest_AN_v1.json`; the small CSV extracts are in `data/inventories_AN_v1/`.

**United States:** the UNFCCC 2026 page lists no US submission (row empty as of 2026-11-03), so the
US comparison has to use the 2025 submission (1990-2023) or EPA's own publication. Not handled here.

Glossary. *CO2e* = CO2-equivalent using 100-yr GWPs from IPCC AR5 (CH4 28, N2O 265), required for
all these 2026 CRTs. *Tier 1* = IPCC default factors; *Tier 2* = country-specific factors/equations;
*Tier 3* = models or detailed national measurement. In CRT Summary3, D = IPCC default, CS =
country-specific, M = model. *Recalculation* = a country revising earlier years in a new submission.

## 1. Latest submission and agriculture totals, inventory year 2024 (kt CO2e, AR5)

| Country | Latest submission (CRT filed) | 3 Total agriculture | 3.A Enteric CH4 | 3.B Manure CH4+N2O | 3.D.1 Direct soil N2O | 3.D.2 Indirect soil N2O |
|---|---|---:|---:|---:|---:|---:|
| Canada | 2026, CRT V2.0 (14 Apr 2026; V2 posted 14 May) | 56,403.5 | 26,390.3 | 8,185.6 | 14,520.4 | 3,845.2 |
| United Kingdom | 2026 (15 Apr 2026) | 40,960.6 | 22,945.2 | 6,628.3 | 7,700.2 | 1,968.1 |
| New Zealand | 2026 (15 Apr 2026) | 40,148.4 | 31,588.3 | 1,717.0 | 4,910.7 | 1,216.8 |
| Ireland | 2026 (10 Apr 2026) | 19,640.9 | 12,704.8 | 2,408.7 | 3,232.3 | 669.5 |
| Germany | 2026 (15 Apr 2026) | 53,307.9 | 25,848.0 | 9,067.3 | 12,040.7 | 2,432.4 |
| Australia | 2026 (14 Apr 2026) | 75,672.3 | 58,832.5 | 4,339.4 | 7,007.5 | 2,006.0 |

Canada's CRT zip wraps a `.7z` archive; the script opens it with `py7zr` (the Canada run is in `run_manifest_CAN_AN_v1.json`).
Australia's "2024" is its 2023-24 financial year. 3.B includes indirect N2O from manure (3.B.5).
The sector total also includes liming, urea and other small items, so the columns do not add up to it.

## 2. Methods (CRT Summary3, 2024; Tier codes as reported)

| Country | 3.A Enteric CH4 | 3.B Manure CH4 / N2O | 3.D Soils N2O | Guidelines (NID) |
|---|---|---|---|---|
| Canada | T1,T2 / D,CS | CH4 T1,T2 (D,CS); N2O T1,T2 (D) | T1,T2 / D,CS | 2006 GL required; uses 2019 Refinement values in places (e.g. MCFs) |
| United Kingdom | T1,T3 / D,CS | T1,T2 / T2 | T1,T2 / D,CS | 2006 GL; 2019 Refinement used selectively (e.g. deer). NID p.58: Refinement "yet to be adopted ... but can be used ... if specifically justified" |
| New Zealand | T1,T2 / D,CS | T1,T2 / T1 | T1,T2 / D,CS | 2006 GL; 2026 submission aligned parts of agriculture with the 2019 Refinement |
| Ireland | D,T1,T2,CS | T1,T2 / T2 | T1,T2 / D,CS | 2006 GL; cattle Ym = 6.3% per 2019 Refinement since the 2023 submission (6.5% before) |
| Germany | T1,T2,T3 / D,CS | T2 / T2 | T1,T2,T3 / D,CS | 2006 GL, with 2019 Refinement cited (38 mentions in NID) |
| Australia | T1,T2,T3 / D,CS | T2,T3 / T2,T3 | T1,T2 / D,CS | 2006 GL; 2026 submission adopts 2019 Refinement EFs for urine and dung |

The tier column shows the method codes from CRT Summary3: CH4 first, then N2O, for the method applied
and then the emission factor, e.g. "T1,T3 / D,CS".

## 3. Recalculations, 2025 submission compared with 2026 submission (sector 3 total, kt CO2e)

From CRT Table8s1 (sum of CO2 + CH4 + N2O differences), checked against each NID.

| Country | 1990 | 2005 | 2023 | Main documented cause (NID) |
|---|---:|---:|---:|---|
| Canada | +225.5 (+0.53%) | +507.8 (+0.90%) | +279.5 (+0.51%) | New MCF (methane conversion factor) method for dairy and swine liquid manure, based on regional temperature, after a UNFCCC expert review (TERT) recommendation: about +0.2 to +0.4 Mt. Also lime impurity and crop-yield corrections |
| United Kingdom | +459.8 (+0.91%) | +447.3 (+0.97%) | +595.2 (+1.44%) | Dairy growth curve re-fitted from slaughter weights (heavier animals, so more enteric CH4); higher grass energy content for lambs and ewes; country-specific LESSE (low-emission slurry spreading) uptake |
| New Zealand | -165.1 (-0.45%) | -249.7 (-0.58%) | -326.5 (-0.80%) | Dairy manure and effluent practices; new non-urea fertiliser EF; **alignment with the 2019 Refinement**; error corrections. The NID gives the same three values |
| Ireland | 0.0 | 0.0 | +42.2 (+0.21%) | Revised populations and crop statistics, 2013-2023 only. The NID gives the same +42.2 kt for 2023 |
| Germany | +787.7 (+1.08%) | +202.8 (+0.34%) | +410.8 (+0.75%) | Higher dairy milk yields, so more gross energy intake (GE) and more enteric CH4; gilts split from sows; soil N2O revisions (NID Tables 260, 302-303) |
| Australia | -4,406.3 (-4.68%) | -3,956.9 (-4.56%) | -3,606.1 (-4.38%) | New grazing-manure method (farm dams mapped spatially, so less manure goes to anaerobic systems); **2019 Refinement wet/dry-climate EFs for urine and dung** (3.D alone: -789 in 1989-90, -661 in 2004-05); new ABS sheep data |

Only two of the six countries attribute a recalculation directly to the 2019 Refinement in this
submission: Australia's urine/dung EF (about -0.6 to -0.8 Mt/yr in 3.D, NID Table 5.30, column A)
and New Zealand's partial alignment. NZ does not report the Refinement's effect separately; its
Table 5.2.7 tests a Refinement default for ostriches and emus only.

### AR4 to AR5 GWP switch: magnitude NOT in the 2026 documents

All six 2026 submissions use AR5. The switch happened earlier: Ireland's 2023 submission was
already on AR5 (UNFCCC review idr8_trr5_IRL), while Canada's 2023 submission still used AR4
(idr8_trr5_CAN), so Canada switched in 2024. The kt CO2e effect of the switch is reported in the
2023 or 2024 NIDs, which this version did not fetch (a gap; see below). For a methane-heavy sector
the switch raises CH4 CO2e by 12% (GWP 25 to 28) and lowers N2O CO2e by 11% (298 to 265). Those are
arithmetic facts, not country results.

## 4. Gaps
1. US: no 2026 UNFCCC submission listed.
2. Canada: the CRT values match NIR Table 5-2 (+225 / +508 / +280).
3. AR4 to AR5 switch: need the 2023 submissions (UK, IE, DE, NZ, AU) and the 2024 submission (CA) and their recalculation tables.
4. A "2019 Refinement only" effect is not isolated in any CRT; Table 8 mixes all causes.
5. Ireland's NID Table 5.8 labels its columns "2024 vs 2025 submission" but contains 1990-2023 data that
   match CRT Table8s1 for 2025 vs 2026; this looks like a labelling slip in the NID.

## 5. Reproduce
```
pip install openpyxl requests py7zr
python scripts/fetch_inventories_AN_v1.py --zip-dir C:/ghgsim-data/crt2026 --out data/inventories_AN_v1
```
unfccc.int's bot protection usually blocks scripted downloads. If the script stops with that
message, download each CRT zip from its `doc_page` in a browser into `--zip-dir` and rerun.
Compare the zip SHA-256 values with the manifest. Each zip is 15-47 MB, so keep them off the repo.

## Citations (all accessed 2026-11-03)
- Environment and Climate Change Canada (2026). *National Inventory Report 1990-2024: Greenhouse Gas Sources and Sinks in Canada.* UNFCCC submission. https://unfccc.int/documents/656424 ; CRT https://unfccc.int/documents/656423
- Department for Energy Security and Net Zero (2026). *UK Greenhouse Gas Inventory 1990-2024, National Inventory Document* (Issue 1). https://unfccc.int/documents/656564 ; CRT https://unfccc.int/documents/656567
- Ministry for the Environment (2026). *New Zealand's Greenhouse Gas Inventory 1990-2024*, Vol. 1. https://unfccc.int/documents/656533 ; CRT https://unfccc.int/documents/656539
- Environmental Protection Agency (2026). *Ireland's National Inventory Document 2026.* https://unfccc.int/documents/656484 (mirror https://www.epa.ie/publications/monitoring--assessment/climate-change/air-emissions/Ireland-NID-2026.pdf); CRT https://unfccc.int/documents/656399
- Umweltbundesamt (2026). *Submission under the UNFCCC and the Paris Agreement 2026: National Inventory Report for the German Greenhouse Gas Inventory 1990-2024.* https://unfccc.int/documents/656482 ; CRT https://unfccc.int/documents/656483
- Department of Climate Change, Energy, the Environment and Water (2026). *National Inventory Report 2024*, Vol. 1 (Australia's 2026 submission). https://unfccc.int/documents/656436 ; CRT https://unfccc.int/documents/656438
- UNFCCC (2024). Technical review reports idr8_trr5_IRL and idr8_trr5_CAN (GWP basis of the 2023 submissions). https://unfccc.int/sites/default/files/resource/idr8_trr5_IRL_adv.pdf ; https://unfccc.int/sites/default/files/resource/idr8_trr5_CAN.pdf
