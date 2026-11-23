"""Tests for the N-budget closure terms (soybean full BNF, alfalfa BNF, deposition, leaching base) and params v12."""
import csv
import importlib.util
import pathlib

import pytest

from ghgsim.modules.tier1_extras import (
    alfalfa_bnf_kg,
    deposition_n_kg,
    leach_budget_kg,
    n_budget_v2,
    soybean_bnf_full_kg,
    soybean_bnf_per_grain_kg,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
V11, V12 = ROOT / "data" / "ipcc_params_AN_v11.csv", ROOT / "data" / "ipcc_params_AN_v12.csv"


@pytest.fixture(scope="module")
def p():
    return {r["key"]: float(r["value"]) for r in csv.DictReader(open(V12, encoding="utf-8"))}


def test_params_v12_superset_unique_and_cited():
    rows = list(csv.DictReader(open(V12, encoding="utf-8")))
    keys = [r["key"] for r in rows]
    assert len(keys) == len(set(keys))
    v11 = list(csv.DictReader(open(V11, encoding="utf-8")))
    assert rows[: len(v11)] == v11  # v11 rows carried over unchanged
    new = rows[len(v11):]
    assert len(new) >= 15
    for r in new:
        assert r["status"] in ("VERIFIED", "SOURCE-TRACED") and r["table"] and r["page"] and r["source_doi_or_url"], r["key"]


def test_params_v12_spot_values(p):
    assert p["SALV2008.soy_BG_share_total_N"] == 0.24 and p["SALV2008.soy_Ndfa"] == 0.55
    assert p["RUSSELLE2004.alfalfa_fixed_N_kg_per_ha"] == 152 and p["RUSSELLE2004.soy_fixed_N_kg_per_ha"] == 84
    assert p["GELFAND2015.soy_BNF_g_N_per_kg_grain"] == 43
    assert p["OHIO_ANR74.N_lb_per_bu.corn"] == 0.74 and p["OHIO_ANR74.N_lb_per_bu.soybeans"] == 3.55
    assert p["NUGIS.N_removal_lb_per_bu.corn"] == 0.67 and p["PETERSON1991.alfalfa_fixed_N_lb_per_ton"] == 61


def test_soybean_full_bnf_hand_calc():
    r = soybean_bnf_full_kg(100.0, 20.0, 0.5, 0.24)
    assert r["plant_N_AG"] == pytest.approx(120.0)
    assert r["plant_N_total"] == pytest.approx(120.0 / 0.76)
    assert r["plant_N_BG"] == pytest.approx(120.0 / 0.76 - 120.0)
    assert r["BNF_AG"] == pytest.approx(60.0) and r["BNF_total"] == pytest.approx(0.5 * 120.0 / 0.76)
    assert r["BNF_AG"] + r["BNF_BG"] == pytest.approx(r["BNF_total"])
    assert soybean_bnf_full_kg(100.0, 20.0, 0.5, 0.0)["BNF_total"] == pytest.approx(60.0)  # no below-ground = v3 term


@pytest.mark.parametrize("args", [(1, 1, -0.1, 0.2), (1, 1, 1.1, 0.2), (1, 1, 0.5, 1.0), (1, 1, 0.5, -0.1)])
def test_soybean_full_bnf_rejects_bad_fractions(args):
    with pytest.raises(ValueError):
        soybean_bnf_full_kg(*args)


def test_simple_terms_hand_calc():
    assert soybean_bnf_per_grain_kg(1000.0, 43.0) == pytest.approx(43.0)
    assert alfalfa_bnf_kg(10.0, 152.0) == pytest.approx(1520.0)
    assert deposition_n_kg(10.47, 100.0) == pytest.approx(1047.0)
    assert leach_budget_kg(0.3, 100.0, 50.0, 30.0, 0.0) == pytest.approx(54.0)
    for fn, a in ((alfalfa_bnf_kg, (-1, 1)), (deposition_n_kg, (1, -1)), (soybean_bnf_per_grain_kg, (-1, 1))):
        with pytest.raises(ValueError):
            fn(*a)
    with pytest.raises(ValueError):
        leach_budget_kg(1.2, 1, 1, 1, 1)


def test_n_budget_v2_identity_and_missing_terms():
    t = dict(synthetic_N=100.0, manure_N_applied=20.0, PRP_N=10.0, BNF_soy_total=80.0, BNF_alfalfa=5.0, N_deposition=10.0,
             F_SOM=0.0, crop_N_removed=150.0, soil_volatilised=12.0, soil_leached=30.0, soil_N2O_N_direct=2.0)
    b = n_budget_v2(t)
    assert b["inputs_total"] == pytest.approx(225.0) and b["outputs_total"] == pytest.approx(194.0)
    assert b["residual_unaccounted"] == pytest.approx(31.0) and b["closure_error"] == 0.0
    assert b["NUE_removed_over_inputs"] == pytest.approx(150.0 / 225.0)
    del t["N_deposition"]
    with pytest.raises(KeyError):
        n_budget_v2(t)


def _closure():
    s = importlib.util.spec_from_file_location("nbc", ROOT / "scripts" / "n_budget_closure_AN_v1.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_closure_scenarios_close_and_leach_variants_differ_by_residue_term(p):
    m = _closure()
    v3 = dict(synthetic_N=1000.0, manure_N_applied=200.0, PRP_N=100.0, F_SOM=0.0, soil_volatilised=150.0, soil_leached=0.3 * (1300 + 500),
              soil_N2O_N_direct=20.0, soy_AG_residue_N=100.0, cropland_harvested_ha=10.0)
    act = dict(rem={"soybeans": 400.0, "corn_grain": 800.0}, rem_dm={"soybeans": 360.0, "corn_grain": 700.0},
               rem_ohio={"soybeans": 350.0, "corn_grain": 650.0}, soy_bu=100.0, soy_ha=5.0, alf_ha=2.0, alf_t=10.0)
    e = dict(fl=0.3, fgasf=0.1)
    dep = dict(total=10.0, wet=5.0)
    res = {}
    for name, over in m.SCENARIOS.items():
        cfg = dict(m.BASE, **over)
        nb = m.terms_for(cfg, p, "2006", v3, act, dep, 1.0, e)
        assert nb["closure_error"] == 0.0, name
        res[name] = nb
    assert res["HEADLINE_v4"]["soil_leached"] == pytest.approx(0.3 * 1300.0)
    assert res["leach_ipcc_full_Eq11.10"]["soil_leached"] == pytest.approx(0.3 * 1800.0)
    assert res["v3_replica"]["BNF_soy_total"] == pytest.approx(0.55 * (400.0 + 100.0))  # v3 above-ground term
    assert res["v3_replica"]["N_deposition"] == 0.0 and res["v3_replica"]["BNF_alfalfa"] == 0.0
    assert res["HEADLINE_v4"]["BNF_soy_total"] == pytest.approx(0.55 * (360.0 + 100.0) / 0.76)
    assert res["HEADLINE_v4"]["BNF_alfalfa"] == pytest.approx(2.0 * 152.0)
    assert res["HEADLINE_v4"]["N_deposition"] == pytest.approx(100.0)
    assert res["alf_peterson61lb_per_ton"]["BNF_alfalfa"] == pytest.approx(10.0 * 61 * 0.45359237)
    assert res["fert_falcone2017_ohio_total"]["synthetic_N"] == 1000.0  # no alt totals given -> ratio 1
