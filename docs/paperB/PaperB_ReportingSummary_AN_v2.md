# Nature Portfolio Reporting Summary: draft answers (PaperB_ReportingSummary_AN_v2, accompanies PaperB_draft_AN_v7)

To be transferred to the official Nature Reporting Summary form at submission. The form's wording is paraphrased here; check it against the current form.

**Statistics.** No statistical tests, sample sizes or P values. Results are deterministic calculations. County distributions are summarised by median and 5th–95th percentiles. Sensitivity is assessed with committed alternatives (guideline edition; withheld-cell variants; climate classification; dry EF1 option), one at a time. No uncertainty intervals are reported (Methods).

**Software and code.**
- Data collection: `scripts/fetch_inventories_AN_v1.py`, `scripts/fetch_epa_ghgi_AN_v1.py`, `scripts/build_county_p_pe_AN_v2.py`, `scripts/build_county_climate_zones_AN_v1.py`; manual browser download for UNFCCC CRT zips.
- Data analysis: ghgsim (Python 3.12; Apache-2.0), commit to be cited from the results manifest; `requirements_AN_v2.txt` pins all packages (adds geopandas for the Fig. 3 map); Gradio dashboard; MCP SDK 2.3 for the paper agent. Outside software: GLEAM R package v0.8.0-alpha (commit b0937d2); HESTIA and APSIM Next Generation installed, not used for reported results.
- Code availability: GitHub (private until submission; to be made public and archived on Zenodo, DOI to be minted at submission). Available to editors and reviewers on request.

**Data.** All inputs are public: USDA NASS 2022 Census of Agriculture; NOAA nClimDiv (doi:10.7289/V5M32STR); IPCC climate-zone raster (doi:10.5281/zenodo.7303808); EPA GHGI 2024 and 2025 editions; UNFCCC 2026 CRT and NIDs; Global N2O Database (doi:10.6073/pasta/09a95cf44cd7835db002b0089ed5ffc3; CC BY 4.0); GRACEnet (doi:10.15482/USDA.ADC/1235557; CC0). Generated data in the repository and Zenodo archive (DOI to be minted at submission). No restrictions. Source Data files to be provided for Figs 2–5.

**Human research participants / human data / dual-use / clinical:** Not applicable (no human participants; census data are published county aggregates).

**Field-specific (Ecological, evolutionary and environmental sciences).**
- Study description: computational comparison of IPCC 2006 and 2019 Tier 1/Tier 2 methods on 19 stylized farms and 3,075 US counties with estimates, plus comparison of official inventory recalculations for seven countries.
- Research sample: all US counties in the 2022 Census of Agriculture (3,142 counties with climate data; 3,075 with estimates); six Annex I comparator countries chosen by the authors for documented 2019 Refinement uptake, plus the United States.
- Sampling strategy: none (full census coverage).
- Data collection: public downloads, hashed (manifests listed in Methods).
- Timing and spatial scale: 2022 activity data; 1991–2020 climate normals; inventory years 1990, 2005, 2022–2024; US county scale.
- Data exclusions: categories outside scope (organic soils, SOM mineralisation, some residues, burning) are excluded and listed (SI S3); withheld cells handled by three variants.
- Reproducibility: one-command recompute; latest full run reproduced all 121 paper numbers.
- Randomization / blinding: not applicable.
- Field work, permits, animals, plants: none.
