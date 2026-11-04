# Living-paper automatic recompute (AN_v1)

This is the core mechanism of Paper B: one command regenerates every paper result, writes a results manifest that
proves what produced it, CI re-runs the light part on every push, a weekly job watches the upstream sources, and a
diff report says which paper numbers moved and why.

## Quick start
```
pip install -r requirements_AN_v1.txt && pip install -e . --no-deps     # pinned environment (Python 3.12)
python scripts/recompute_all_AN_v1.py --profile full                    # Bubble PC, raw data in C:/ghgsim-data (or $GHGSIM_DATA)
python scripts/recompute_all_AN_v1.py --profile light --out build/m.json   # anywhere, repo inputs only
python scripts/diff_results_AN_v1.py results/results_manifest_AN_v1.json build/m.json --out build/diff.md
python scripts/check_upstream_AN_v1.py                                  # are the upstream sources still the pinned ones?
```
`make test | recompute-light | recompute-full | upstream | diff-demo` wrap the same commands.

## What runs where
| Step | Script | Where | Inputs outside the repo |
|---|---|---|---|
| county_p_pe | build_county_p_pe_AN_v2.py | Bubble only | nClimDiv v1.0.0-20261006 (~123 MB) |
| county_climate_annual | build_county_climate_annual_AN_v1.py | Bubble only | nClimDiv |
| county_climate_zones | build_county_climate_zones_AN_v1.py | Bubble only | nClimDiv + IPCC zone raster (Zenodo 7303808) |
| stylized_2006_vs_2019 | compare_ipcc_2006_2019_stylized_AN_v2.py | CI + Bubble | none |
| fig_stylized | plot_ipcc_2006_vs_2019_stylized_AN_v2.py | CI + Bubble | none |
| us_county_run | run_us_county_2006_vs_2019_AN_v2.py (+ map) | Bubble only | NASS Census 2022 bulk (~300 MB gz), EPA fertilizer page, cb_2021 counties |
| inventories_crt2026 | fetch_inventories_AN_v1.py | Bubble only, manual zips | six CRT 2026 zips (unfccc.int blocks scripted downloads) |
| inventories_us_epa | fetch_epa_ghgi_AN_v1.py | Bubble only | EPA GHGI 2024 and 2025 PDFs |

Under `--profile light` Bubble-only steps are not run; the committed outputs are hashed and their paper numbers
extracted, so the manifest is still complete. Under `--profile full` a step whose raw input is missing is skipped
(never half-run) and listed with `missing_raw`.

## How a run works
1. The repo (minus .git, .venv, build, legacy, results) is copied to `build/recompute_stage_<stamp>/`.
2. Each step's outputs are deleted in the stage and the script is re-run there, so committed files are never
   overwritten and every script's own refuse-to-overwrite guard still holds.
3. Each output is hashed and compared with the committed file (`reproduced`). For CSVs that differ, a cell-level
   summary (`diff_vs_committed`) says which columns changed.
4. The manifest (`results/results_manifest_AN_vN.json`, next free N) records: code commit and dirty flag; Python and
   package versions; parameter file (latest `data/ipcc_params_AN_v*.csv`) and its hash; per-step input hashes (repo
   files and raw downloads), output hashes, run time and log tail; the upstream pins; and the extracted paper numbers.

## CI (.github/workflows)
- `recompute_AN_v1.yml` (push, PR, manual): pinned install, tests, light recompute, diff against the latest committed
  full manifest (written to the job summary), artifacts uploaded. The old `ci.yml` matrix stays as is.
- `upstream_check_AN_v1.yml` (Mondays 11:17 UTC, manual): `check_upstream_AN_v1.py` compares fingerprints with
  `data/upstream_sources_AN_v1.json`; on a change it opens an `upstream-change` issue (or comments on the open one).
  Unreachable sources are reported in the summary but never open an issue.

## Upstream fingerprints
IPCC 2006 and 2019R Vol 4 Ch 10/11 PDFs (SHA-256, identical to the copies in C:/ghgsim-data/ipcc_pdfs); EPA GHGI page
(time-series end years listed); NASS `qs.census2022.txt.gz` (size + Last-Modified); nClimDiv newest version tag
(updates monthly, so expect a monthly issue: rerun or keep the pin); UNFCCC 2026 CRT listing (bot-challenge page,
currently always `unreachable`: check by hand); GLEAM (newest tag of un-fao/GLEAM).

## Diff report
`diff_results_AN_v1.py OLD NEW` lists every paper number that moved (absolute tolerance 0.005), with the producing
step and that step's recorded causes: script change, changed/added/removed input hashes, parameter-file key diff,
package and upstream-pin changes, and `git log OLD..NEW` subjects for the step's files. Runs made before the pipeline
are wrapped by `legacy_results_manifest_AN_v1.py`. Demo: `docs/DIFF_US_COUNTY_RUN_v1_v2_AN_v1.md`.