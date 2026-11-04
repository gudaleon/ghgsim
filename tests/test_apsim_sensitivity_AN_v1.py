"""Checks on the APSIM soil, drainage and borrowed-parameter sensitivity outputs (AN_v3, DECISIONS_AN_v25)."""
import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "apsim_crop_sensitivity_AN_v3.csv"
MAN = ROOT / "results" / "apsim_AN_v3" / "apsim_crop_manifest_AN_v3.json"
pytestmark = pytest.mark.skipif(not CSV.exists(), reason="sensitivity outputs not present")


def rows():
    with CSV.open(encoding="utf-8") as fh:
        return {r["case"]: r for r in csv.DictReader(fh)}


def test_all_cases_present():
    r = rows()
    for c in ("main_webster", "webster_swim", "webster_seep", "webster_tile", "webster_wt", "clarion",
              "initN_x0.5", "initN_x2", "FBiom_x0.5", "FBiom_x1.5", "FInert_x0.75", "FInert_x1.25"):
        assert c in r
        assert int(r[c]["sown_years"]) == 29


def test_main_row_matches_v2():
    r = rows()["main_webster"]
    assert abs(float(r["direct_N2O_kg_ha"]) - 2.92) < 0.01
    assert abs(float(r["fertiliser_induced_EF_pct"]) - 1.32) < 0.01


def test_tile_settings_and_flow_reported():
    r = rows()
    assert float(r["webster_tile"]["tile_drainage_mm"]) >= 0.0
    assert r["main_webster"]["tile_drainage_mm"] == ""
    m = json.loads(MAN.read_text(encoding="utf-8"))
    assert m["tile"]["DrainDepth"] == 1200.0 and m["tile"]["DrainSpacing"] == 28500.0


def test_values_finite_and_positive():
    for r in rows().values():
        assert 0 < float(r["direct_N2O_kg_ha"]) < 50
        assert float(r["direct_N2O_kg_ha_min_year"]) <= float(r["direct_N2O_kg_ha"]) <= float(r["direct_N2O_kg_ha_max_year"])
        assert 0 < float(r["share_top5pct_days"]) <= 1