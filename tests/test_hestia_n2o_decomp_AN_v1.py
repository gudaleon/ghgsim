"""AN_v1: the HESTIA vs ghgsim N2O term split (hestia_matched_vs_ipcc_stylized_AN_v2.csv) adds up to the AN_v1 totals."""
import csv
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"


def _f(x):
    return float(x) if x not in ("", None, "nan") else None


def test_terms_sum_to_v1_totals():
    tot = {}
    for r in csv.DictReader((DATA / "hestia_matched_vs_ipcc_stylized_AN_v1.csv").open(encoding="utf-8")):
        tot[(r["farm_id"], r["source"])] = (_f(r["ipcc2019_kg"]), _f(r["hestia_kg"]))
    sums = {}
    for r in csv.DictReader((DATA / "hestia_matched_vs_ipcc_stylized_AN_v2.csv").open(encoding="utf-8")):
        src = "soil_N2O" if r["source"].startswith("soil_N2O") else r["source"]
        g, h = sums.get((r["farm_id"], src), (0.0, 0.0))
        sums[(r["farm_id"], src)] = (g + float(r["ghgsim2019_kg_N2O"]), h + float(r["hestia_kg_N2O"]))
    assert len(sums) == 16
    for k, (g, h) in sums.items():
        g1, h1 = tot[k]
        assert abs(g - g1) < 0.01, k
        assert abs(h - h1) < 0.01, k
