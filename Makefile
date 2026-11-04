# Living-paper targets (AN_v1). On Windows/Bubble without make, run the python lines directly.
PY ?= python

.PHONY: test recompute-light recompute-full upstream diff-demo
test:
	$(PY) -m pytest tests/ -q --tb=short

recompute-light:   ## CI-safe: only steps whose inputs are in the repo
	$(PY) scripts/recompute_all_AN_v1.py --profile light --out build/results_manifest_light.json

recompute-full:    ## Bubble PC: every step, raw data in $$GHGSIM_DATA (default C:/ghgsim-data); writes next results/results_manifest_AN_vN.json
	$(PY) scripts/recompute_all_AN_v1.py --profile full

upstream:
	$(PY) scripts/check_upstream_AN_v1.py --report build/upstream_report_AN_v1.md --json build/upstream_check_AN_v1.json

diff-demo:
	$(PY) scripts/diff_results_AN_v1.py results/legacy_us_county_run_v1_AN_v1.json results/legacy_us_county_run_v2_AN_v1.json --out build/diff_demo.md