"""Wrap a pre-pipeline US county run manifest (data/us_county_run_manifest_AN_v1/_v2.json) in the results-manifest
schema of scripts/recompute_all_AN_v1.py, so that scripts/diff_results_AN_v1.py can compare runs made before the
recompute pipeline existed (AN_v1).

    python scripts/legacy_results_manifest_AN_v1.py --run v1 --out results/legacy_us_county_run_v1_AN_v1.json

Key mapping (recorded in the output as "aliases_note"): run v1 had one activity variant that drops withheld (D)
Census cells; docs/US_COUNTY_RUN_AN_v2.md calls this the v1 behaviour of the v2 `disclosed` variant, so v1 headline
numbers are keyed `disclosed`. The v1 "D-imputed sensitivity" is keyed `D_allocated`, but its method differs
(v1: state residual spread over withheld counties; v2: allocation by OPERATIONS WITH INVENTORY with full soil N2O).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import recompute_all_AN_v1 as rc  # noqa: E402

RUNS = {
    "v1": dict(script="scripts/run_us_county_2006_vs_2019_AN_v1.py", manifest="data/us_county_run_manifest_AN_v1.json",
               outputs=["data/us_county_2006_vs_2019_AN_v1.csv", "data/us_national_2006_vs_2019_vs_epa_AN_v1.csv",
                        "data/us_county_zone_sensitivity_AN_v1.csv", "data/us_county_run_manifest_AN_v1.json",
                        "docs/figures/us_county_pct_change_2006_2019_AN_v1.png"],
               county_csv=("data/us_county_2006_vs_2019_AN_v1.csv", None)),
    "v2": dict(script="scripts/run_us_county_2006_vs_2019_AN_v2.py", manifest="data/us_county_run_manifest_AN_v2.json",
               outputs=["data/us_county_2006_vs_2019_AN_v2.csv.gz", "data/us_national_2006_vs_2019_vs_epa_AN_v2.csv",
                        "data/us_county_run_manifest_AN_v2.json", "docs/figures/us_county_pct_change_2006_2019_AN_v2.png"],
               county_csv=("data/us_county_2006_vs_2019_AN_v2.csv.gz", "D_allocated")),
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", choices=sorted(RUNS), required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        sys.exit(f"refusing to overwrite {out}")
    R = RUNS[a.run]
    m = json.loads((ROOT / R["manifest"]).read_text(encoding="utf-8"))
    commit = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H|%aI", "--", R["manifest"]], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip().splitlines()[-1].split("|")
    nat = dict(m["national_MMT_CO2e"])
    note = None
    if a.run == "v1":
        nat = {f"disclosed|{k}": v for k, v in m["national_MMT_CO2e"].items()}
        nat.update({f"D_allocated|{k}": v for k, v in m.get("national_MMT_CO2e_Dimputed_sensitivity", {}).items()})
        note = ("v1 headline keyed `disclosed` (withheld cells dropped); v1 D-imputed sensitivity keyed `D_allocated` "
                "(different allocation method and narrower soil scope than v2).")
    nums = rc.us_county_numbers(nat)
    cp, var = R["county_csv"]
    if (ROOT / cp).exists():
        nums.update(rc.county_distribution(ROOT / cp, var, "disclosed" if a.run == "v1" else var))
        if a.run == "v2":
            nums.update(rc.county_distribution(ROOT / cp, "disclosed", "disclosed"))
    ins = {}
    for k, v in m["inputs"].items():
        if not v:
            continue
        p = rc.norm_path(v["path"]) if hasattr(rc, "norm_path") else v["path"].replace("\\", "/")
        key = p if p.startswith("data/") else "RAW:" + "/".join(p.split("/")[-2:])
        ins[key] = v["sha256"]
    step = {"name": "us_county_run", "where": "bubble_only", "script": R["script"],
            "script_sha256": rc.sha256(ROOT / R["script"]), "status": "legacy (pre-pipeline run, wrapped)",
            "inputs_sha256": ins,
            "outputs": {o: {"sha256": rc.sha256(ROOT / o) if (ROOT / o).exists() else None} for o in R["outputs"]},
            "paper_numbers": sorted(nums)}
    params = next(k for k in ins if "ipcc_params" in k)
    man = {"schema": "ghgsim.results_manifest/1", "generated": commit[1], "profile": "legacy",
           "code": {"commit": commit[0], "note": "commit that added the run manifest"},
           "parameter_file": {"path": params, "sha256": ins[params]}, "packages": {}, "upstream_sources": None,
           "aliases_note": note, "steps": [step], "paper_numbers": dict(sorted(nums.items())),
           "source_manifest": R["manifest"]}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(man, indent=2), encoding="utf-8")
    print("wrote", out, len(nums), "numbers")


if __name__ == "__main__":
    main()