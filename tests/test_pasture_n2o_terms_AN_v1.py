"""The 2019 GLEAM vs ghgsim pasture-N2O gap is fully the EF4 choice (aggregated 0.010 vs wet 0.014)."""
import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dec", ROOT / "scripts" / "decompose_pasture_n2o_AN_v1.py")
dec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dec)


def test_rows_match_committed_csv():
    rows = {(r["factor_set"], r["term"]): r for r in dec.build_rows()}
    with (ROOT / "results" / "pasture_n2o_terms_gleam_vs_ghgsim_AN_v1.csv").open(encoding="utf-8") as fh:
        for c in csv.DictReader(fh):
            r = rows[(c["factor_set"], c["term"])]
            assert r["ghgsim_kg_N2O"] == pytest.approx(float(c["ghgsim_kg_N2O"]), abs=1e-3)
            assert r["gleam_kg_N2O"] == pytest.approx(float(c["gleam_kg_N2O"]), abs=1e-3)


def test_2019_gap_is_ef4_only():
    rows = {(r["factor_set"], r["term"]): r for r in dec.build_rows()}
    for t in ("direct", "indirect_leaching"):
        assert rows[("IPCC2019", t)]["ghgsim_minus_gleam_kg"] == pytest.approx(0.0, abs=1e-2)
    for t in dec.TERMS:
        assert rows[("IPCC2006", t)]["ghgsim_minus_gleam_kg"] == pytest.approx(0.0, abs=1e-2)
    vol_g = rows[("IPCC2019", "indirect_volatilisation")]
    # GLEAM run used EF4 = 0.010 (Table 11.3 aggregated); ghgsim uses the wet-climate 0.014.
    assert vol_g["ghgsim_EF4_used"] == pytest.approx(0.014)
    assert vol_g["gleam_kg_N2O"] * 0.014 / 0.010 == pytest.approx(vol_g["ghgsim_kg_N2O"], rel=1e-6)
    gap = rows[("IPCC2019", "total")]["ghgsim_minus_gleam_kg"]
    assert gap == pytest.approx(vol_g["ghgsim_minus_gleam_kg"], abs=1e-3)
