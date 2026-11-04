"""Tests for the living-paper recompute, upstream check and diff report (AN_v1)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import diff_results_AN_v1 as dr  # noqa: E402
import recompute_all_AN_v1 as rc  # noqa: E402


def test_us_county_numbers_totals():
    n = rc.us_county_numbers({"x|enteric_CH4|2006": 10.0, "x|enteric_CH4|2019": 12.0,
                              "x|soil_N2O|2006": 10.0, "x|soil_N2O|2019": 6.0})
    assert n["us_county.x.total_in_scope.2006_MMT"] == 20.0
    assert n["us_county.x.total_in_scope.pct_change"] == -10.0
    assert n["us_county.x.enteric_CH4.pct_change"] == 20.0


def test_steps_declared_consistently():
    names = [s["name"] for s in rc.STEPS]
    assert len(names) == len(set(names))
    for s in rc.STEPS:
        assert (ROOT / s["script"]).exists()
        assert s["where"] in ("ci", "bubble_only")
        assert s["extract"] is None or s["extract"] in rc.EXTRACT


def _man(commit, nums, ins):
    return {"code": {"commit": commit}, "parameter_file": {"path": "data/p.csv", "sha256": "a"}, "packages": {},
            "upstream_sources": None, "paper_numbers": nums,
            "steps": [{"name": "s", "script": "scripts/x.py", "script_sha256": "1", "inputs_sha256": ins,
                       "paper_numbers": sorted(nums)}]}


def test_diff_report(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(_man("", {"k1": 1.0, "k2": 5.0}, {"data/in.csv": "h1"})))
    b.write_text(json.dumps(_man("", {"k1": 1.001, "k2": 6.0, "k3": 2.0}, {"data/in.csv": "h2"})))
    out = tmp_path / "d.md"
    dr.main([str(a), str(b), "--out", str(out)])
    t = out.read_text()
    assert "`k2` | 5 | 6 | 1 | +20.0" in t and "`k3` | new" in t and "`k1`" not in t
    assert "`data/in.csv` changed" in t


def test_upstream_pins_present():
    pins = sorted((ROOT / "data").glob("upstream_sources_AN_v*.json"))
    assert pins
    src = json.loads(pins[-1].read_text(encoding="utf-8"))["sources"]
    for k in ("ipcc_2019r_v4_ch10", "epa_ghgi_editions", "nass_census2022", "nclimdiv", "unfccc_crt_2026", "gleam_release"):
        assert k in src