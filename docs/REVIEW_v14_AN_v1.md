# Review of PaperB_draft_AN_v14 against Nature Food Analysis requirements - AN v1

Reviewed 2026-11-04 by the agent. Requirements from https://www.nature.com/natfood/content (Analysis: main text up to 3,000 words excluding abstract, Methods, references and legends; abstract 100-150 words, unreferenced; up to 6 display items; unheaded introduction, Results, Discussion without subheadings, Methods; about 50 references as a guideline). Fixes are in PaperB_draft_AN_v15.docx and PaperB_SI_AN_v8.docx (v14 and SI v7 kept unchanged).

## Checks that passed
- Abstract: 143 words, no references.
- Introduction has no heading; Discussion has no subheadings; Methods, Data availability and Code availability present.
- References: 50, every one cited in the text, no citation outside 1-50, no remaining [CITE?] marker.
- DOIs: all 37 DOIs resolve. 30 are Crossref records whose title, year and volume match the reference; 7 are DataCite DOIs resolved through doi.org (Zenodo 10.5281/zenodo.7303808, NOAA 10.7289/V5M32STR, EDI 10.6073/pasta/09a95cf4..., DRUM 10.13016/g1xw-qftw, arXiv 10.48550/arXiv.1906.02569, Ag Data Commons 10.15482/USDA.ADC/1235557). Miao et al. Nature 658, 1272-1280 (2026) confirmed in Crossref.
- The 13 references without DOI (IPCC, EPA, NASS, six NIDs, FAO GLEAM 3.0) all have URLs that returned HTTP 200 on 2026-11-04.
- Numbers: an automated check compared every number in each tagged paragraph with the numbers in its tagged files. All matched, or were derived and then recomputed by hand: farm totals -18.5..+91.1% (swine 79.4-91.1, dairy 39.6/22.2) from data/ipcc_2006_vs_2019_stylized_AN_v3.csv; GLEAM enteric -13.5..+6.6%; zone soil N2O 57.5/62.1/93.8 (sum of soil rows); EU 359.1 Mt (359,085.6 kt); soil N2O -31.46% (abstract "31%"); EPA coverage 0.603.

## Problems found and fixes
1. Display items: 7 (Figs 1-6 + Table 1) > 6. Table 1 was also never cited in the text. Fix: Table 1 moved to Supplementary Table S9 and cited in the Results.
2. Figure order: Fig. 6 was cited (APSIM paragraph) before Figs 2-5. Fix: the GLEAM, HESTIA and APSIM paragraphs moved into a Results subsection "Outside models as consistency checks" after the inventories, so figures are cited 1-6 in order. Cross-references ("see next sections", "corrected below") reworded.
3. Reference order: refs 44-45 were first cited before 41-43, and the new Results-cited references must come before Methods-only ones. Fix: references renumbered by order of first citation (main text, then Methods); the mapping is listed in the v15 build log.
4. Word count: main text about 3,010 words (introduction 385, Results about 2,112, Discussion 515) > 3,000, before the Iowa text. Fix: GLEAM paragraph condensed, APSIM paragraph rewritten, Russian/EU document URLs moved from Results to Methods; v15 main text is at most 3,000 words (count in the build log).
5. Stale Methods: "main-branch commit d1f507f" and "decision logs DECISIONS_AN_v1 to _AN_v7" (logs now run to v24). Fixed to the merge commit of this PR and v1 to v24.
6. Stale provenance: Methods "Stylized farms" named compare_ipcc_2006_2019_stylized_AN_v2.py and data/..._AN_v2.csv with parameter file v8, but the Results use the AN_v3 table (parameter file v10, climate-specific EF4). Fixed.
7. Untagged numbers: "145.9 and 68.0 kg" (GLEAM with aggregated EF4) lacked results/gleam_vs_ghgsim_stylized_AN_v2.csv, and "3,041 of 3,142 counties" lacked data/county_p_pe_may_oct_AN_v2.csv (recounted: 3,041 of 3,142 have Hargreaves P/PE < 1). Tags added.
8. APSIM site: v14 used an Australian example soil and non-US weather. Fix: main run at Boone County, Iowa (SSURGO Webster clay loam, NASA POWER 1991-2020); Australian runs kept as sensitivity; Fig. 6 v2, Table S8 and the text updated (docs/DECISIONS_AN_v24.md).
9. Data availability lacked the APSIM sources. Added SSURGO/Soil Data Access, NASA POWER, the APSIM example soil and weather files, and the GLEAM/HESTIA/APSIM outputs.
10. Missing statements: author contributions, competing interests, acknowledgements/funding, AI-use statement and the Reporting Summary. Placeholders added and marked "[to be completed by the author]"; no content invented. The Nature Portfolio Reporting Summary is a separate form completed at submission.
11. Drafting-conventions paragraph referred to [CITE?] markers; none remain, and the paragraph now records the reference check. The paragraph and the {file} tags are removed at submission (tags move to Source Data).

## Needs the author (scope or permissions)
- Site/soil: Webster is poorly drained and APSIM has no tile drainage set; choose whether to keep it, add tile drainage, or use a well-drained Corn Belt soil (for example Clarion).
- Borrowed APSoil No. 900 crop and organic-matter parameters (KL, XF, FBiom, FInert, CN ratios, FOM, SWCON, CN2Bare, initial N) at a US site.
- Table 1 moved to the SI.
- Author statements, AI-use statement and the Reporting Summary.
- Make github.com/gudaleon/ghgsim public and mint Zenodo DOIs before submission.