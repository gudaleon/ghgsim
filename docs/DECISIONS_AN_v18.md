# DECISIONS_AN_v18: HESTIA CE matched runs on the stylized farms

Date: 2026-11-03. Author: Alex Neumann.

1. **Engine.** Local HESTIA Community Edition v7.1.0 (models 0.90.0, schema 39.2.0, glossary 0.103.0), run with the upstream example compose file
   on the PENV workstation. Docker's disk image was not moved off C:, because that could not be done safely while running. Earth Engine is not used.
   All site inputs are supplied, labelled "regional statistical data".
2. **Isolation.** Done in a separate worktree and branch (`hestia-matched-AN-v1`) so it doesn't collide with GLEAM work on main.
3. **Site inputs.** These match ghgsim: GADM-USA, ecoClimateZone 1 (Warm Temperate Moist), 15 C annual mean.
4. **Livestock as manure-management Cycles.** Excreta are Cycle inputs (kg N, kg VS from ghgsim's own Nex and VS), with one excretaManagement
   practice at 100%. Covered liquid variants map to the uncovered liquid term because the cover factor is Holos-only.
5. **Placeholder product.** For non-dairy farms the 1 kg liveweight product exists only so the Cycle links to an ImpactAssessment.
   Intensities are not reported.
6. **Not supplied.** Urea mass and SOM N for crop_urea_lime. The linked-manure field farms (broiler_litter_field, market_swine_field) are skipped in v1.
7. **Results (consistency check, not validation).** Manure CH4 matches ghgsim IPCC 2019 to within rounding for cattle and swine, and within 8% for poultry
   (layers -7.7%). Crop soil N2O: 39.69 kg against 41.65 (2019, -4.7%) and 34.91 (2006, +13.7%). Manure N2O is 40-80% below ghgsim 2019
   (farrow_to_finish -2.3%, turkey -11.4%). Pasture N2O is 81.6 against 164.1 (2019). Enteric CH4 is not computable without a feed inventory.
   The N2O differences have not been broken down yet. That is the next step for v2.
