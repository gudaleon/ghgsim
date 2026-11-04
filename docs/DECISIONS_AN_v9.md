# Decisions AN_v9 (2026-11-03) - Fig. 3a county map, figure clean-up, draft v5

1. **County boundaries:** US Census cartographic boundary counties for 2023 at 1:20m scale,
   https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_20m.zip, SHA-256
   479956f6e3cb1573705c1ceb35d17ca7cd1b5179f3947ee6adbaa274b7e931e4. It is stored at
   D:\ghgsim-data\boundaries and kept out of git. The script checks the hash. Set GHGSIM_BOUNDARIES to override the folder.
2. **geopandas 1.2.0** (shapely 2.2.0, pyogrio 0.13.0, pyproj 3.8.0) added in requirements_AN_v2.txt. Only the
   figure script needs it, so CI and tests don't.
3. **Fig. 3a choropleth** of county % change (D_allocated), clipped at ±60%. Lower 48 states in Albers (EPSG:5070),
   with Alaska and Hawaii insets. 3,067 of 3,075 counties with estimates are mapped. The 8 not matched are Connecticut's
   old counties: the 2023 boundaries use CT planning regions, while Census of Agriculture 2022 uses the old counties. These
   and the counties with no estimate (77 boundary polygons in total) are hatched grey and labelled as such.
4. **No hatching for suppressed values:** 2,838 of the 3,067 mapped counties include allocated withheld Census values,
   so marking them hid the colours. I dropped that marking. The disclosed-only vs D_allocated difference is still in the
   text and in Fig. 3b's source CSV.
5. **Visual fixes (v2 files, v1 kept):**
   - Fig. 1: overlapping boxes, so it now has a 2x3 layout.
   - Fig. 2: readable farm names and chemical subscripts.
   - Fig. 4: clipped y-label and a legend over the bars.
   - Fig. 5: the 2022 legend entry had no visible bar, so the last year is now a single "Latest year (2023; USA 2022)"
     group with a source note.
   No values changed. They are checked in figures/paperB_figures_manifest_AN_v2.json.
6. **Draft v5** = v4 with the header line set to v5 and all five figure links pointed at the _AN_v2 images. Docx:
   G:\My Drive\Papers_To_Publish\PaperB\PaperB_draft_AN_v5.docx.
