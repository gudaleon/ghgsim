# HESTIA matched runs on the stylized farms (AN_v1)

Consistency check, not validation. HESTIA Community Edition is run locally on the same activity data and site
inputs ghgsim uses, and its outputs are compared by source with ghgsim IPCC 2006 and 2019.

## Environment
- HESTIA CE v7.1.0 (docker compose, `docker-compose.example.yml` from gitlab.com/hestia-earth/hestia-community-edition).
  Versions from `/api/system/data` are recorded in the manifest: schema 39.2.0, models 0.90.0, validation 0.41.13,
  aggregation 0.23.1, glossary 0.103.0.
- No Earth Engine: the `ee` folder is empty and no key file is mounted. All site measurements are supplied directly,
  with `methodClassification` = "regional statistical data".
- No HESTIA code is copied into this repo. The script calls the local HTTP API only.

## How to run
```
python scripts/hestia_matched_stylized_AN_v1.py build   # writes data/hestia_matched_inputs_AN_v1.json and _activity_AN_v1.csv
python scripts/hestia_matched_stylized_AN_v1.py run     # upload -> PATCH validate -> calculate via /api/drafts, then write outputs
```
`HESTIA_API` (default `http://localhost/api`) can be overridden with an environment variable. `run` needs a CE instance
whose `/api/system/data` reports `ready: true`.

## Outputs (all new files, nothing overwritten)
- `data/hestia_matched_inputs_AN_v1.json`: the uploaded nodes
- `data/hestia_matched_activity_AN_v1.csv`: per-farm activity data supplied
- `data/hestia_matched_emissions_raw_AN_v1.csv`: every recalculated emission, with model and tier
- `data/hestia_matched_vs_ipcc_stylized_AN_v1.csv`: by farm and source, HESTIA against ghgsim 2006/2019 (`data/ipcc_2006_vs_2019_stylized_AN_v2.csv`)
- `data/hestia_matched_manifest_AN_v1.json`: HESTIA versions, draft id, route, GWPs, and sha256 of the inputs and outputs

## Mapping
- Site: country GADM-USA, ecoClimateZone 1 (Warm Temperate Moist), temperatureAnnual 15 C for 2022 (the ghgsim stylized climate).
- Livestock farms are modelled as manure-management Cycles: excreta are Cycle **inputs** (kg N = head x Nex; kg VS = head x VS x 365,
  where cattle VS comes from GE by IPCC Eq 10.24 as in ghgsim), with one excretaManagement practice at 100%.
  HESTIA's ipcc2019 ch4ToAirExcreta and n2OToAirExcreta models read excreta only from inputs.
- MMS: liquid (all cover variants) -> liquidSlurryWithoutNaturalCrustCover (the cover factor is a Holos-only fork, so ghgsim's IPCC paths
  keep the uncovered MCF as well); poultry with/without litter -> poultryManureWithLitter/WithoutLitter; pit -> pitStorageBelowAnimalConfinements;
  pasture -> pastureRangePaddockExcretaManagement.
- Primary product: milkCowRaw (head x milk yield) for dairy; otherwise a 1 kg liveweight placeholder, used only so the Cycle links to an
  ImpactAssessment. No per-product intensities are reported.
- crop_urea_lime: per ha, 100 kg N inorganic N (unspecified), 200 kg agricultural limestone, 100 kg dolomitic lime, 8000 kg maize grain.
  Results are multiplied by 10 ha. Urea mass (the urea CO2 input) and the 100 kg SOM-mineralisation N are not supplied. Lime and urea CO2 are not compared
  because they are not in the ghgsim comparison CSV.
- Source classes: enteric_CH4 = ch4ToAirEntericFermentation; manure_CH4 = ch4ToAirExcreta; manure_N2O = n2OToAirExcretaDirect + Indirect;
  soil_N2O = fertiliser, residue and soil N2O terms, plus excreta N2O on pasture sites. Background `*InputsProduction` terms are excluded.
- Skipped in v1: broiler_litter_field and market_swine_field (their manure N is linked from another farm).

## Known gaps
- Enteric CH4 is not computed: HESTIA's ipcc2019 tier 2 model needs a feed inventory (energy and digestibility of feed inputs),
  which the stylized farms do not specify as feeds. Shown blank, not zero.
- Manure N2O: HESTIA returns IPCC 2019 EF3 direct emissions of 0 for uncovered liquid slurry. The reported totals are mostly indirect,
  and are 40-80% below ghgsim 2019 for most farms. This gap has not been broken down into its parts in v1.
