import csv, math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "ipcc_2006_vs_2019_stylized_AN_v2.csv"
SCRIPT = ROOT / "scripts" / "compare_ipcc_2006_2019_stylized_AN_v2.py"


def _rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_csv_v2_reproducible(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("cmp2", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = tmp_path / "out.csv"
    monkeypatch.setattr(mod, "OUT_CSV", out)
    mod.main()
    assert _rows(out) == _rows(CSV)


def test_v2_directions_and_gaps():
    r = {(x["farm_id"], x["source"]): x for x in _rows(CSV)}
    # Beef liquid manure N2O now filled for 2019 (Table 10.22 Updated other cattle 0.48); 2006 stays NaN.
    beef = r[("beef_cowcalf_uncovered", "manure_N2O")]
    assert not math.isnan(float(beef["ipcc2019_kg"])) and float(beef["ipcc2019_kg"]) > 0
    assert math.isnan(float(beef["ipcc2006_kg"]))
    # 12-month warm temperate moist liquid MCF 0.55 vs 2006 15C 0.27 -> ratio 0.55/0.27 (same B0).
    d = r[("dairy_forage_uncovered", "manure_CH4")]
    assert float(d["ipcc2019_kg"]) / float(d["ipcc2006_kg"]) == pytest.approx(0.55 / 0.27, rel=1e-4)
    assert float(r[("crop_urea_lime", "soil_N2O")]["pct_change"]) > 0
