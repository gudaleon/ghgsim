"""Checks on committed APSIM crop outputs (AN_v1) and Fig. 6 manifest (AN_v6). No APSIM needed."""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rows(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return {r["run"]: r for r in csv.DictReader(f)}


def test_manifest_pins_version():
    with open(os.path.join(ROOT, "results", "apsim_AN_v1", "apsim_crop_manifest_AN_v1.json")) as f:
        m = json.load(f)
    assert m["apsim"]["version"] == "APSIM 2026.11.8142.0"
    assert m["apsim"]["commit"].startswith("d1dca5e")
    assert "11706" in m["apsim"]["pr"]


def test_fertiliser_raises_n2o_and_pulses_dominate():
    p = _rows("results/apsim_crop_pulses_AN_v1.csv")
    for site in ("dalby", "hamilton"):
        assert float(p[site]["total_N2O_N_kgha"]) > float(p[site + "_0N"]["total_N2O_N_kgha"])
        assert float(p[site]["share_top5pct_days"]) > 0.5
        assert float(p[site]["max_day_over_mean_day"]) > 10


def test_fig6_manifest():
    with open(os.path.join(ROOT, "figures", "paperB_figures_manifest_AN_v6.json")) as f:
        m = json.load(f)
    assert "figures/fig6_four_way_AN_v1.png" in m["outputs"]
    assert m["checks"]["c"][2] is None
