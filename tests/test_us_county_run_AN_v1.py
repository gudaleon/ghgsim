"""US county 2006 vs 2019 run (AN_v1): parameter rows and calculation spot checks."""
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_us_county_2006_vs_2019_AN_v1 as run  # noqa: E402

P = run.P()
MS = run.mms()


def test_v9_new_mcf_rows():
    assert P["IPCC2019.MCF.lagoon|boreal_dry"] == pytest.approx(0.49)
    assert P["IPCC2019.MCF.liquid_12mo|tropical_moist"] == pytest.approx(0.80)
    assert P["IPCC2019.MCF.liquid_6mo|tropical_montane"] == pytest.approx(0.59)
    assert P["IPCC2006.MCF.liquid_nocrust|T20C"] == pytest.approx(0.42)
    assert P["IPCC2006.MCF.lagoon|T28C"] == pytest.approx(0.80)
    assert P["IPCC2006.MCF.solid_storage|T14C"] == pytest.approx(0.02)
    assert P["IPCC2006.MCF.solid_storage|T15C"] == pytest.approx(0.04)
    assert P["IPCC2019.EF_enteric.dairy|north_america"] == 138


def test_v9_rows_cite_page_and_verified():
    rows = list(csv.DictReader(open(ROOT / "data" / "ipcc_params_AN_v9.csv", encoding="utf-8")))
    assert all(r["page"] and r["status"] == "VERIFIED" for r in rows if "tropical" in r["key"] or "|T" in r["key"])


def test_dairy_enteric_and_lagoon_hand_calc():
    out, gaps = run.county_calc(P, {**MS, "dairy": {"lagoon": 1.0}}, "2019", {"dairy": 100.0}, None, 20.0,
                                "warm_temperate_moist", True)
    assert out[("enteric", "dairy", "CH4")] == pytest.approx(100 * 138)
    assert out[("manure_ch4", "dairy", "CH4")] == pytest.approx(100 * 5.4 * 365 * 0.24 * 0.67 * 0.73)
    o6, _ = run.county_calc(P, {**MS, "dairy": {"lagoon": 1.0}}, "2006", {"dairy": 100.0}, None, 20.0, None, True)
    assert o6[("manure_ch4", "dairy", "CH4")] == pytest.approx(100 * 5.4 * 365 * 0.24 * 0.67 * 0.78)  # 2006 Table 10.17 lagoon 20 C


def test_synthetic_n_wet_dry():
    w, _ = run.county_calc(P, MS, "2019", {}, 1000.0, 12.0, "cool_temperate_moist", True)
    d, _ = run.county_calc(P, MS, "2019", {}, 1000.0, 12.0, "cool_temperate_dry", False)
    assert w[("soil_n2o_direct", "synthetic_N", "N2O")] == pytest.approx(1000 * 0.016 * 44 / 28)
    assert d[("soil_n2o_direct", "synthetic_N", "N2O")] == pytest.approx(1000 * 0.005 * 44 / 28)


def test_output_shape():
    out = ROOT / "data" / "us_county_2006_vs_2019_AN_v1.csv"
    rows = list(csv.DictReader(open(out, encoding="utf-8")))
    assert len({r["fips"] for r in rows}) > 3000
    assert {r["gas"] for r in rows} == {"CH4", "N2O"}
