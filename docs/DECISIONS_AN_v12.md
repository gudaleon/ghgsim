# Decisions AN_v12 (2026-11-03): Nature Food formatting, draft v8, references v5, SI v2

Rules applied, from the Nature Food Analysis content-type page and the AIP and formatting page (checked 2026-11-03): the introduction has no heading; website URLs are cited in brackets in the text, not in the reference list; about 50 references are recommended.

1. The "## Main text" heading is removed, so the introduction starts straight after the Abstract.
2. Three website references that were only a URL (no DOI, not formally published) moved into the text as bracketed URLs:
   - v7 ref. 53 (HESTIA platform, https://www.hestia.earth): now in the Discussion, the Methods and Table 1.
   - v7 ref. 54 (HESTIA Engine Models on GitLab, tag v0.93.3, commit 78fc3d8): now in the Methods and Table 1.
   - v7 ref. 55 (APSIM licence page, https://www.apsim.info/download-apsim/): now in the Methods and Table 1.
   Note: HESTIA asks users to cite it in a set form (https://www.hestia.earth/guide/guide-accessing-data-citation). If HESTIA data are used in a later version, add that formal citation back.
3. Formally published reports without a DOI stay in the reference list: the IPCC 2006 and 2019 guidelines, the EPA inventories, the NASS 2022 Census, the six national inventory documents and the FAO GLEAM 3.0 model description.
4. Four duplicate supporting references were cut to reach 50. In each case the claim keeps at least two references.
   - The reproducibility claim ("code and data must accompany results") was supported by v7 refs. 11-15. It keeps Peng 2011, Stodden et al. 2016 and Ince et al. 2012. Cut: Baker 2016 (a reproducibility survey) and Barnes 2010 (an opinion piece).
   - The FAIR / versioned-files claim was supported by v7 refs. 23-26. It keeps Wilkinson et al. 2016 and Sandve et al. 2013. Cut: Lowndes et al. 2017 and Wilson et al. 2014.
   None of the cut references was cited anywhere else. To undo a cut, restore the entry from PaperB_references_AN_v4.bib.
5. References are renumbered in order of first citation. Saunois 2020 moves from 45 to 4 because it is cited in the first paragraph. The old-to-new map is in docs/paperB/refmap_v7_to_v8_AN_v1.txt. The GLEAM model description is now ref. 48, cited as "ref. [48]".
6. PaperB_references_AN_v5.bib is v4 without the 7 entries removed in items 2 and 4.
7. PaperB_SI_AN_v2 is v1 with a new header and one change: the national-inventory reference numbers go from [36–41] to [35–40]. Nothing else needed to move to the SI, because the URLs moved into the text are short.
8. Word counts for v8 (file tags and citation numbers excluded; same method as AN_v11):
   - Abstract: 138 (limit 100-150).
   - Main text: 1,907 (limit 3,000). This is +4 on v7, from the in-text URLs.
   - Methods: 1,941.
   - References: 50 (guideline about 50).
   - Display items: 6 (limit 6).
