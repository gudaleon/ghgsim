# Decisions AN_v10 (2026-11-03) - 2021 county boundaries, references v3, draft v6

1. **Fig. 3a boundaries switched to cb_2021_us_county_20m.** The cb_2022 20m file
   (https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_county_20m.zip, SHA-256
   337192bcf4348d278304ebfbe2fceaeb936b368cc476c2aba51b59bd9e0b2e13) already uses Connecticut's 9 planning regions
   (09110-09190), not the old counties. The 2021 vintage has the 8 old counties (09001-09015), which exactly match
   the 2022 Census of Agriculture FIPS codes in our data. Source:
   https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_county_20m.zip, SHA-256
   b91964d40b7332e410eb22bde239d6f2495271175c17338d5f0c30c4bb3bc16d, stored in D:\ghgsim-data\boundaries (not in git).
   All 3,075 counties with estimates now map. 68 boundary polygons have no estimate, mostly in Alaska.
   The Alaska and Hawaii insets are about 35% larger. Output: figures/fig3_us_county_and_epa_AN_v3.png via
   scripts/make_paperB_figures_AN_v3.py. The median is unchanged at +10.7%.
2. **References v3 (PaperB_references_AN_v3.bib), checked against Crossref and Zenodo:**
   - Ref 18 Smith et al.: Glob. Change Biol. 26(1), 219-241, issue dated January 2020 (online 6 Oct 2019), so the year is 2020.
   - Ref 20 Lasser: Commun. Phys. 3, article 143 (2020).
   - Ref 29 Lewis: Zenodo 10.5281/zenodo.7303808 verified (published 2022-11-08, version 0.1.0; concept DOI 10.5281/zenodo.7303807).
   - ghgsim code and data archives: no Zenodo DOI exists yet. They stay as TODO until a release is archived at submission.
   - All 42 unique DOIs in the draft and bib resolve through the doi.org handle API.
3. **Draft v6** = v5 with the header line set to v6, Fig. 3 pointed at the v3 image, and the reference list text for refs 18, 20 and 29 fixed
   to match. Docx: G:\My Drive\Papers_To_Publish\PaperB\PaperB_draft_AN_v6.docx.
