import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "ipcc_2006_vs_2019_stylized_AN_v1.csv"
SCRIPT = ROOT / "scripts" / "compare_ipcc_2006_2019_stylized_AN_v1.py"


def _rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


import pytest  # noqa: E402


@pytest.mark.skip(reason="AN_v1 CSV was produced by ipcc2019.manure 1.x and the 2006 EF4 back-out; superseded by AN_v2 (tests/test_ipcc_2006_vs_2019_stylized_AN_v2.py). v1 file kept unchanged.")
def test_csv_reproducible(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("cmp", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = tmp_path / "out.csv"
    monkeypatch.setattr(mod, "OUT_CSV", out)
    mod.main()
    assert _rows(out) == _rows(CSV)


def test_expected_directions():
    r = {(x["farm_id"], x["source"]): x for x in _rows(CSV)}
    # 2019 Ym (Table 10.12 Updated) lowers dairy enteric CH4.
    assert float(r[("dairy_forage_uncovered", "enteric_CH4")]["pct_change"]) < 0
    # 2019 EF1 wet synthetic 0.016 > 2006 0.01 raises synthetic-N soil N2O.
    assert float(r[("crop_urea_lime", "soil_N2O")]["pct_change"]) > 0
    # 2019 EF3PRP_CPP wet 0.006 < 2006 0.02 lowers PRP soil N2O.
    assert float(r[("beef_pasture_field", "soil_N2O")]["pct_change"]) < 0
    # No published 2006 other-cattle liquid FracGasMS -> NaN, not a made-up number.
    assert math.isnan(float(r[("beef_cowcalf_uncovered", "manure_N2O")]["ipcc2006_kg"]))
    assert r[("beef_cowcalf_uncovered", "manure_N2O")]["notes"]
