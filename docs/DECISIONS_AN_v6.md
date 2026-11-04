# Decisions AN_v6 (2026-11-03) - living-paper automatic recompute

1. One pipeline, `scripts/recompute_all_AN_v1.py`, with two profiles: `light` (CI; runs steps whose inputs are in the
   repo) and `full` (Bubble; every step). Bubble-only steps under `light` hash the committed outputs instead of running.
2. Steps run in a staging copy (`build/recompute_stage_*`), never in the working tree, so no committed file is
   overwritten and each script's refuse-to-overwrite guard is kept unchanged.
3. "Reproduced" = byte-identical output, except: `.gz` compared on decompressed content (gzip header has a timestamp);
   JSON manifests compared ignoring only `created`, `generated` and `*.path` keys (run time and how a raw path was
   spelled). Anything else that differs is reported with a cell- or key-level diff, and the run does not fail unless
   `--strict`.
4. A step with a missing raw input is skipped, not half-run. The five CRT 2026 zips other than Canada's are not in
   C:/ghgsim-data/crt2026 and unfccc.int serves scripts a bot-challenge page, so `inventories_crt2026` is skipped in
   full runs until the zips are downloaded by hand; its committed tables are hashed and used.
5. Stylized run: it picks the latest parameter file (now v10, was v8 when committed). Regenerated numbers are identical;
   only the `params_file` label column differs (76 cells). The committed v2 CSV is kept; no new stylized version.
6. Pinned environment = the Bubble .venv (Python 3.12): `requirements_AN_v1.txt`, plus a pinned `geo` extra in
   pyproject. rasterio 1.5.2 added: the climate-zone step needs it and it was only in the system Python.
7. Upstream fingerprints are small (headers, listings, tags); only the four IPCC chapter PDFs are fully downloaded
   (6.5 MB total). Their SHA-256 equals the local copies in C:/ghgsim-data/ipcc_pdfs.
8. EPA GHGI fingerprint = the time-series end years named on EPA's inventory page (now 2022 and 2023, i.e. the 2024
   and 2025 editions). NASS = size + Last-Modified of qs.census2022.txt.gz. nClimDiv = newest version tag (it updates
   monthly, so a monthly issue is expected; rerun or keep the pin). Unreachable sources never open an issue.
9. GLEAM: the GitHub tags API reports tag v0.8.0-alpha at commit b0937d2, not 90e4161 as noted in the earlier GLEAM
   search. Pinned what the API returns; the discrepancy should be checked before GLEAM runs are cited.
10. Weekly check on Mondays 11:17 UTC; one open `upstream-change` issue at a time (later changes are comments).
11. Diff report causes come only from recorded evidence (hashes, parameter-file key diff, package versions, pins,
    git log). Runs before the pipeline are wrapped by `legacy_results_manifest_AN_v1.py`; for US run v1 the headline
    is keyed `disclosed` and its D-imputed sensitivity `D_allocated` (method differs; stated in the report).
12. `results/results_manifest_AN_v1.json` is the first full run, made before decision 3 existed (it lists the gz and
    two manifests as not reproduced for timestamp/path reasons only). `_AN_v2.json` is the reference manifest.