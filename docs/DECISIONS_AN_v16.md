# DECISIONS_AN_v16 (2026-11-03): draft v10, SI v3, GLEAM paragraph, Russia/EU document URLs

1. Draft v10 = v9 (PR #40, pulled from main) plus: abstract recalculation range now covers the seven inventories with
   Table 8s1 values (six comparators + Russia): -4.4% to +1.9%; a GLEAM consistency-check paragraph in Results
   (after the GLEAM openness paragraph) citing Supplementary Table S6; Russia/EU UNFCCC NID and CRT pages in text.
2. References stay at 50: the Russia and EU NIDs/CRTs and the 2026 submission page are cited in text as bracketed
   URLs (as for HESTIA/APSIM in v8), not as numbered references. PaperB_references_AN_v5.bib is unchanged.
3. The draft uses a hand-numbered reference list (no @keys), so the docx is built without --citeproc; the bib is not
   used by the build.
4. EU CRT: the 2026 submission page (read 2026-11-03) lists one EU CRT, https://unfccc.int/documents/656557
   (submitted 15 Apr 2026, published 17 Apr, 20.71 MB); EUA_CRT_2026.zip (21,714,000 bytes = 20.71 MB) matches.
   UNFCCC publishes no hash, so the identity check is by size and single listed version. Russia: one CRT,
   https://unfccc.int/documents/659495 (25 Jun 2026, 39.50 MB) matches RUS-CRT-2026-V1.0_0.zip (41,418,200 bytes).
5. Doc fields: run_manifest_AN_v2.json is not overwritten; scripts/fill_inventory_doc_urls_AN_v1.py writes
   run_manifest_AN_v3.json with the doc, NID and NID-annex URLs and the size check, tested by
   tests/test_inventory_doc_urls_AN_v1.py. fetch_inventories_AN_v2.py still records doc: null for these two.
6. SI v3 = SI v2 plus a Russian Federation row in Table S4.1 (CRT only, not checked against the NID) and new S6
   (GLEAM vs ghgsim, Supplementary Table S6).
7. Leftover worktree D:\ghgsim-crt (branch crt2026-AN-v1, already merged as PR #40, clean) removed with git worktree remove.
