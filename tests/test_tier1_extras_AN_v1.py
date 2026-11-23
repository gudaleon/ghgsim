"""Unit tests for the Tier 1 extras (F_SOM, forage residue N, crop N removal, lime/urea, N budget) and the
county-year runner. Hand-calculated expectations use the values printed in the cited tables."""
import csv
import importlib.util
import json
import math
import pathlib

import pytest

from ghgsim.modules.tier1_extras import (
    crop_n_removal_kg,
    forage_residue_n,
    fsom_kg_n,
    lime_urea_co2_kg,
    n_budget,
    silage_residue_n,
    soc_stock_t,
    soybean_bnf_kg,
    tillage_soc_change_t,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
V11 = ROOT / "data" / "ipcc_params_AN_v11.csv"


@pytest.fixture(scope="module")
def p():
    return {r["key"]: float(r["value"]) for r in csv.DictReader(open(V11, encoding="utf-8"))}


def _runner():
    s = importlib.util.spec_from_file_location("cy", ROOT / "scripts" / "run_county_year_tier1_AN_v1.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- parameters
def test_params_v11_superset_unique_and_cited():
    rows = list(csv.DictReader(open(V11, encoding="utf-8")))
    keys = [r["key"] for r in rows]
    assert len(keys) == len(set(keys))
    v10 = list(csv.DictReader(open(ROOT / "data" / "ipcc_params_AN_v10.csv", encoding="utf-8")))
    assert rows[: len(v10)] == v10  # v10 rows carried over unchanged
    for r in rows[len(v10):]:
        assert r["status"] == "VERIFIED" and r["page"] and r["table"] and r["source_doi_or_url"], r["key"]


def test_params_v11_spot_values(p):
    assert p["IPCC2006.RES.alfalfa.slope"] == 0.29 and p["IPCC2006.RES.nonlegume_hay.slope"] == 0.18
    assert p["IPCC2019.RES.alfalfa.RS"] == 0.40 and p["IPCC2019.RES.nonlegume_hay.RS"] == 0.54
    assert "IPCC2019.RES.alfalfa.R_AG" not in p  # Table 11.1a gives '-'
    assert p["IPCC2006.SOCref.warm_temperate_moist|HAC"] == 88 and p["IPCC2019.SOCref.warm_temperate_moist|HAC"] == 64
    assert p["IPCC2006.FMG.no_till|cool_temperate_moist"] == 1.15 and p["IPCC2019.FMG.no_till|cool_temperate_moist"] == 1.09
    assert p["IPCC2006.FSOM.R_cropland_mgmt"] == 10 and p["IPCC2006.SOC.D_years"] == 20
    assert p["NRCS.CROPN_pct.corn_grain"] == 1.61 and p["NRCS.CROPN_pct.soybeans"] == 6.25
    assert p["NRCS.DM_frac.corn_silage"] == 0.35 and p["SALV2008.soy_Ndfa"] == 0.55


# ---------------------------------------------------------------- forage / silage residue N
def test_forage_residue_alfalfa_hand_calc(p):
    # 1 ha, 5000 kg DM/ha: AGDM = 5000*0.29 = 1450; AG = 1450*0.027; BG = (1450+5000)*0.40*0.019
    for ver in ("2006", "2019"):
        r = forage_residue_n(p, ver, "alfalfa", 1.0, 5000.0)
        assert r["AGDM_kg_ha"] == pytest.approx(1450.0)
        assert r["AG"] == pytest.approx(39.15) and r["BG"] == pytest.approx(49.02)
    r0 = forage_residue_n(p, "2006", "alfalfa", 1.0, 5000.0, frac_renew=0.0)
    assert r0["BG"] == 0.0 and r0["AG"] == pytest.approx(39.15)


def test_forage_residue_2019_uses_rag_when_given(p):
    r = forage_residue_n(p, "2019", "perennial_grasses", 2.0, 4000.0)
    assert r["AGDM_kg_ha"] == pytest.approx(1200.0)  # R_AG 0.3
    assert r["AG"] == pytest.approx(2 * 1200 * 0.015) and r["BG"] == pytest.approx(2 * 5200 * 0.80 * 0.012)


def test_forage_residue_guards(p):
    assert forage_residue_n(p, "2006", "alfalfa", 0.0, 5000.0)["total"] == 0.0
    with pytest.raises(KeyError):
        forage_residue_n(p, "2006", "corn", 1.0, 1.0)
    with pytest.raises(ValueError):
        forage_residue_n(p, "2006", "alfalfa", 1.0, 1.0, frac_renew=1.5)


def test_silage_residue_maize_roots(p):
    assert silage_residue_n(p, "2006", 1.0, 10000.0)["BG"] == pytest.approx(10000 * 0.22 * 0.007)
    assert silage_residue_n(p, "2019", 1.0, 10000.0)["AG"] == 0.0


# ---------------------------------------------------------------- F_SOM
def test_soc_stock_and_fsom_loss(p):
    full, nt = {"full": 1.0}, {"no_till": 1.0}
    assert soc_stock_t(p, "2006", "warm_temperate_moist", "HAC", full, 1.0) == pytest.approx(88 * 0.69)
    dc = tillage_soc_change_t(p, "2006", "warm_temperate_moist", "HAC", nt, full, 1.0, 5)
    assert dc == pytest.approx(88 * 0.69 * (1.0 - 1.15) / 20)  # T < D: divide by D
    assert fsom_kg_n(dc, p["IPCC2006.FSOM.R_cropland_mgmt"]) == pytest.approx(-dc * 1000 / 10)


def test_fsom_gain_gives_zero_and_t_over_d(p):
    dc = tillage_soc_change_t(p, "2019", "cool_temperate_moist", "HAC", {"full": 1.0}, {"no_till": 1.0}, 1.0, 25)
    assert dc == pytest.approx(81 * 0.70 * 0.09 / 25)  # T >= D: divide by T
    assert fsom_kg_n(dc, 10) == 0.0
    with pytest.raises(ValueError):
        soc_stock_t(p, "2006", "tropical_moist", "HAC", {"full": 1.0}, 1.0)


# ---------------------------------------------------------------- crop N removal, BNF, lime, budget
def test_crop_n_removal_matches_nrcs_example(p):
    # NRCS AWMFH p. 6-18 example: 130 bu/ac corn @ 56 lb/bu, 1.61% N -> 117 lb N
    lb = crop_n_removal_kg(p, "corn_grain", 130 * 56) / 0.45359237
    assert round(lb) == 117
    # corn silage 22 t/ac @ 35% dm, 1.10% N -> 169 lb N
    assert round(crop_n_removal_kg(p, "corn_silage", 22 * 2000, dm_frac=0.35) / 0.45359237) == 169
    with pytest.raises(KeyError):
        crop_n_removal_kg(p, "millet_proso", 1.0)


def test_soybean_bnf(p):
    assert soybean_bnf_kg(100.0, 20.0, 0.55) == pytest.approx(66.0)
    with pytest.raises(ValueError):
        soybean_bnf_kg(1.0, 1.0, 1.2)


def test_lime_urea_both_versions(p):
    r = lime_urea_co2_kg(p, limestone_t=100.0, dolomite_t=10.0, urea_t=5.0)
    assert r["CO2_lime_kg"] == pytest.approx((100 * 0.12 + 10 * 0.13) * 1000 * 44 / 12)
    assert r["CO2_urea_kg"] == pytest.approx(5 * 0.20 * 1000 * 44 / 12)


def test_n_budget_identity():
    t = dict(synthetic_N=100.0, manure_N_applied=20.0, PRP_N=5.0, BNF_soy_AG=30.0, F_SOM=1.0, crop_N_removed=120.0,
             soil_volatilised=12.0, soil_leached=30.0, soil_N2O_N_direct=1.5)
    b = n_budget(t)
    assert b["inputs_total"] == pytest.approx(156.0) and b["outputs_total"] == pytest.approx(163.5)
    assert b["residual_unaccounted"] == pytest.approx(-7.5) and b["closure_error"] == 0.0
    with pytest.raises(KeyError):
        n_budget({"synthetic_N": 1.0})


# ---------------------------------------------------------------- runner helpers + smoke run
def test_runner_forage_inputs_haylage_split():
    m = _runner()
    ext = {k: None for k in m.EXTRA_KEYS}
    ext.update(hay_alf_t=100.0, hay_oth_t=50.0, hh_dry_t=210.0, haylage_alf_green_t=90.0, haylage_oth_green_t=30.0,
               haylage_ac=40.0, hay_alf_ac=30.0, hay_oth_ac=20.0, silage_green_t=500.0, silage_ac=25.0)
    fi = m.forage_inputs(ext)
    assert fi["haylage_alf_dryeq_t"] == pytest.approx(45.0) and fi["haylage_oth_dryeq_t"] == pytest.approx(15.0)
    assert fi["haylage_alf_ac"] == pytest.approx(30.0) and not fi["haylage_dryeq_negative"]


def test_runner_alloc_extra_remainder():
    m = _runner()
    county = {"1": {"x": (10.0, ""), "w": (1.0, "")}, "2": {"x": (None, "(D)"), "w": (3.0, "")},
              "3": {"x": (None, "(D)"), "w": (1.0, "")}}
    a = m.alloc_extra(county, {"x": (50.0, "")}, "x", "w")
    assert a["2"] == pytest.approx(30.0) and a["3"] == pytest.approx(10.0)


def _tsv(path, rows):
    cols = ["SOURCE_DESC", "DOMAIN_DESC", "AGG_LEVEL_DESC", "STATE_FIPS_CODE", "COUNTY_CODE", "STATE_ALPHA", "STATE_NAME",
            "COUNTY_NAME", "YEAR", "SHORT_DESC", "VALUE"]
    with open(path, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(cols)
        for r in rows:
            w.writerow(r)


def test_runner_smoke(tmp_path):
    m = _runner()
    rows = []
    data = {  # short_desc: (county 001, county 003, state)
        "CATTLE, INCL CALVES - INVENTORY": ("1,000", "500", "1,500"), "CATTLE, COWS, MILK - INVENTORY": ("200", "(D)", "300"),
        "CATTLE, COWS, MILK - OPERATIONS WITH INVENTORY": ("4", "2", "6"),
        "FERTILIZER TOTALS, INCL LIME & SOIL CONDITIONERS - EXPENSE, MEASURED IN $": ("600", "400", "1,000"),
        "CORN, GRAIN - ACRES HARVESTED": ("1,000", "1,000", "2,000"),
        "CORN, GRAIN - PRODUCTION, MEASURED IN BU": ("180,000", "170,000", "350,000"),
        "SOYBEANS - ACRES HARVESTED": ("1,000", "500", "1,500"),
        "SOYBEANS - PRODUCTION, MEASURED IN BU": ("55,000", "27,000", "82,000"),
        "AG LAND, CROPLAND, HARVESTED - ACRES": ("2,300", "1,700", "4,000"),
        "HAY, ALFALFA - ACRES HARVESTED": ("100", "50", "150"), "HAY, ALFALFA - PRODUCTION, MEASURED IN TONS": ("300", "140", "440"),
        "HAY, (EXCL ALFALFA) - ACRES HARVESTED": ("100", "50", "150"),
        "HAY, (EXCL ALFALFA) - PRODUCTION, MEASURED IN TONS": ("200", "100", "300"),
        "HAY & HAYLAGE - PRODUCTION, MEASURED IN TONS, DRY BASIS": ("520", "250", "770"),
        "HAY & HAYLAGE - ACRES HARVESTED": ("210", "100", "310"),
        "HAYLAGE - ACRES HARVESTED": ("10", "0", "10"), "HAYLAGE, ALFALFA - PRODUCTION, MEASURED IN TONS": ("40", "0", "40"),
        "CORN, SILAGE - ACRES HARVESTED": ("100", "0", "100"), "CORN, SILAGE - PRODUCTION, MEASURED IN TONS": ("2,000", "0", "2,000"),
    }
    till = {2022: ("300", "400", "300", "700", "800", "1,000", "1,000", "1,200", "1,300"),
            2017: ("400", "400", "300", "700", "700", "1,000", "1,100", "1,100", "1,300")}
    tnames = ["PRACTICES, LAND USE, CROPLAND, CONVENTIONAL TILLAGE - ACRES",
              "PRACTICES, LAND USE, CROPLAND, CONSERVATION TILLAGE, (EXCL NO-TILL) - ACRES",
              "PRACTICES, LAND USE, CROPLAND, CONSERVATION TILLAGE, NO-TILL - ACRES"]
    for yr in (2017, 2022):
        for sd, (a1, a3, st) in data.items():
            rows += [("CENSUS", "TOTAL", "COUNTY", "39", "001", "OH", "OHIO", "ADAMS", yr, sd, a1),
                     ("CENSUS", "TOTAL", "COUNTY", "39", "003", "OH", "OHIO", "ALLEN", yr, sd, a3),
                     ("CENSUS", "TOTAL", "STATE", "39", "", "OH", "OHIO", "", yr, sd, st)]
        for i, sd in enumerate(tnames):
            a1, a3, st = till[yr][i * 3: i * 3 + 3]
            rows += [("CENSUS", "TOTAL", "COUNTY", "39", "001", "OH", "OHIO", "ADAMS", yr, sd, a1),
                     ("CENSUS", "TOTAL", "COUNTY", "39", "003", "OH", "OHIO", "ALLEN", yr, sd, a3),
                     ("CENSUS", "TOTAL", "STATE", "39", "", "OH", "OHIO", "", yr, sd, st)]
    _tsv(tmp_path / "c.tsv", rows)
    (tmp_path / "fert.csv").write_text("state,kg_N\nOHIO,100000\n")
    (tmp_path / "lime.csv").write_text("year,limestone_t,dolomite_t,aglime_unspecified_t,urea_t,source\n2022,,,1000,,test\n")
    out = tmp_path / "out"
    args = ["--state-fips", "39", "--year", "2022", "--census-tsv", str(tmp_path / "c.tsv"), "--prev-year", "2017",
            "--fert-csv", str(tmp_path / "fert.csv"), "--lime-csv", str(tmp_path / "lime.csv"), "--climate", "all_wet",
            "--out-dir", str(out), "--suffix", "_t"]
    m.main(args)
    nb = list(csv.DictReader(open(next(out.glob("county_year_n_budget_*_t.csv")))))
    assert len(nb) == 4 and all(abs(float(r["closure_error"])) < 1e-6 for r in nb)
    assert sum(float(r["synthetic_N"]) for r in nb if r["version"] == "2006") == pytest.approx(100000.0)
    fs = list(csv.DictReader(open(next(out.glob("county_year_fsom_*_t.csv")))))
    assert {r["basis"] for r in fs} == {"county_both_years"}
    em = list(csv.DictReader(open(next(out.glob("county_year_emissions_long_*_t.csv")))))
    assert any(r["source"] == "lime_co2" for r in em) and any(r["item"].startswith("forage_residue:") for r in em)
    man = json.load(open(next(out.glob("county_year_run_manifest_*_t.json"))))
    assert man["n_counties"] == 2 and not math.isnan(float(nb[0]["inputs_total"]))
    with pytest.raises(SystemExit):  # never overwrites
        m.main(args)
