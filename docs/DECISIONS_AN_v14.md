# Decisions AN_v14 (2026-11-03): 2026 CRT zips from Drive, Russia and EU added, Fig. 5 v3, draft v9

1. Zips supplied by A. Neumann in Drive (Papers_To_Publish/PaperB) were copied to D:/ghgsim-data/crt2026 on PENV
   with SHA-256 in SHA256SUMS_AN_v1.txt there. AUS, CAN (V2.0) and GBR (GBRJ) are byte-identical to the zips used
   in PR #25; NZL, IRL and DEU were re-downloaded from unfccc.int by the script and are also identical.
2. Re-extraction with scripts/fetch_inventories_AN_v2.py gives extracts identical to data/inventories_AN_v1 for all
   six countries, so no existing result changes.
3. Added as extra comparisons (not comparator countries): Russian Federation (RUS-CRT-2026-V1.0_0.zip, sha256
   9159d2c6...) and European Union (EUA_CRT_2026.zip, sha256 d7a7299f...). The UNFCCC document URLs for these two
   were not recorded (doc: null in the manifest); add them when confirmed. Their values were not checked against NIDs.
4. The EU CRT Table8s1 sheets for 1990, 2005 and 2023 are empty, so no EU recalculation is reported. v2 skips empty
   Table8s1 rows instead of writing 0 kt / NaN %. The v2 script also accepts *_YYYY.xlsx names (EU file layout).
5. The United States filed no 2026 CRT; the EPA 2024 vs 2025 edition comparison stays as the US source.
6. Fig. 5 v3 (scripts/make_paperB_figures_AN_v4.py) adds Russia; draft v9 = v8 plus these changes in the Results,
   Methods and Fig. 5 caption. The abstract range (-4.4% to +1.4%) stays for the six comparator countries.
