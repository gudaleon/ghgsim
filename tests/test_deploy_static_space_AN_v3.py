"""bundle.zip from scripts/deploy_static_space_AN_v3.py holds only what the dashboard tabs read, and enough to run them."""
import importlib.util
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytest.importorskip("pandas")


def _deploy():
    spec = importlib.util.spec_from_file_location("deploy_v3", ROOT / "scripts" / "deploy_static_space_AN_v3.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


PROBE = r'''
import importlib.util, json, sys
from pathlib import Path
R = Path(sys.argv[1])
def load(n):
    s = importlib.util.spec_from_file_location(n, R / f"{n}.py" if (R / f"{n}.py").exists() else R / "dashboard" / f"{n}.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
v2, v3 = load("app_AN_v2"), load("app_AN_v3")
out = {"counties": len(v2.load_county()), "methods": v2.method_compare().to_dict("records")}
farms = list(v2.example_farms())
out["diff"] = v2.run_version_diff(farms[-1], v2.latest_versioned(v2.DATA, "ipcc_params", ".csv").name)[0].to_dict("records")
out["manifests"] = v2.manifest_checks().to_dict("records")
PA = v2.PA
out["mans"] = PA.list_manifests()
out["farms"] = [f["farm_id"] for f in PA.list_farms()["farms"]]
out["county"] = PA.county_results(fips="06019") is not None
out["zone"] = PA.county_climate_zone("06019") is not None
out["committed"] = PA.committed_farm_result(out["farms"][0]) is not None
out["prov"] = "error" not in json.dumps(v2.ask_paper("provenance", "", "", "", "", "", "", "", "", out["mans"][-1], "us_county")[0])[:20]
out["tabs"] = {t: (len(v3.tab_markdown(t)), len(v3.tab_figures(t))) for t in v3.TABS}
print(json.dumps(out, default=str))
'''


def _probe(root: Path) -> dict:
    env = {**os.environ, "GHGSIM_ROOT": str(root)}
    r = subprocess.run([sys.executable, "-c", PROBE, str(root)], env=env, capture_output=True, text=True, check=True)
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_bundle_is_slim_and_runs_every_tab(tmp_path):
    d = _deploy()
    files = d.bundle_files()
    names = set(files)
    assert not [n for n in names if "Daily" in n or n.endswith(".apsimx") or n.startswith("results/") and n.count("/") > 1]
    assert not [n for n in names if n.startswith("data/") and n.count("/") > 1
                and n not in {m.relative_to(ROOT).as_posix() for f in (ROOT / "data").glob("*manifest_AN_v*.json")
                              for m in d._manifest_files(f)}]
    assert {f"docs/FINDINGS_AN_v{v}.md" for v in range(4, 10)} <= names
    stage = d.stage(tmp_path / "stage", "test")
    zsize = (stage / "bundle.zip").stat().st_size
    assert zsize < 40 * 2**20, zsize
    ext = tmp_path / "x"
    zipfile.ZipFile(stage / "bundle.zip").extractall(ext)
    slim, full = _probe(ext), _probe(ROOT)
    assert slim == full
    assert all(n > 500 for n, _ in slim["tabs"].values())
    assert slim["tabs"]["Rain pulses & averaging distortion"][1] == 6