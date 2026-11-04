# DECISIONS_AN_v19 - Dashboard hosting: private static Hugging Face Space (Gradio-Lite)

Date: 2026-11-04. Author: Alex Neumann.

1. **Why static.** Hugging Face refused to create a Gradio-SDK Space for `globaltrotter` (HTTP 402: Gradio and Docker Spaces on free cpu-basic need a PRO subscription). Static Spaces are free and can be private, so the dashboard now runs in the visitor's browser with Gradio-Lite 5.45.0 (Pyodide 0.27).
2. **Files.** `dashboard/static_AN_v1/index.html` loads `dashboard/app_AN_v2.py` unchanged from `bundle.zip`, built by `scripts/deploy_static_space_AN_v1.py` (app, src/, data/, results/, scripts/, agent/*.py, newest BUBBLE_SETUP doc, example farms, COMMIT). The Space is created with `space_sdk="static"`, `private=True`; the script aborts before upload unless the Hub reports it private. No secrets or LLM keys. `scripts/deploy_space_AN_v2.py` (Gradio-SDK route, fixes v1 shipping app_AN_v1 and missing agent/scripts/results) is kept for if PRO is ever enabled.
3. **Pyodide check (Node + Pyodide 0.27.7, bundle at 24024f9).** pint 0.26.2 installs and loads, so no precomputed fallback is needed. County P/PE, Version diff (live FarmModel), Provenance and the Ask-the-paper tools run_farm, committed_farm_result, county_results, county_climate_zone, explain_parameter and provenance all work.
4. **Limitations.** `diff_manifests` uses a subprocess, which the browser cannot run; it returns an error in the JSON panel instead of a report. The commit SHA comes from the bundle's COMMIT file (no git in the browser). First load downloads Python and about 13 MB of bundle (1-2 min).
5. **Space.** https://huggingface.co/spaces/globaltrotter/paperB-living-dashboard (private).
