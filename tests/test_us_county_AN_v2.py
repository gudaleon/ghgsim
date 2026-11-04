import csv
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

def _load():
    s = importlib.util.spec_from_file_location("v2", ROOT / "scripts" / "run_us_county_2006_vs_2019_AN_v2.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m  # noqa: E702

def test_reconstruct_identity():
    m = _load()
    c = {"cattle_total": (100.0, ""), "cows": (40.0, ""), "beef_cows": (30.0, ""), "excl_cows": (60.0, ""), "dairy": (None, "(D)")}
    d, notes = m.reconstruct(c)
    assert d["dairy"] == 10.0 and "dairy=cows-beef" in notes

def test_allocate_by_ops():
    m = _load()
    county = {"01001": {"swine": (10.0, ""), "swine_ops": (1.0, "")},
              "01003": {"swine": (None, "(D)"), "swine_ops": (3.0, "")},
              "01005": {"swine": (None, "(D)"), "swine_ops": (1.0, "")}}
    state = {"01": {"swine": (90.0, "")}}
    recon = {f: m.reconstruct(county[f]) for f in county}
    a = m.allocate(county, state, recon)
    assert abs(a[("01003", "swine")] - 60.0) < 1e-9 and abs(a[("01005", "swine")] - 20.0) < 1e-9

def test_params_v10_unique_and_superset():
    rows = list(csv.DictReader(open(ROOT / "data" / "ipcc_params_AN_v10.csv", encoding="utf-8")))
    keys = [r["key"] for r in rows]
    assert len(keys) == len(set(keys))
    v9 = {r["key"] for r in csv.DictReader(open(ROOT / "data" / "ipcc_params_AN_v9.csv", encoding="utf-8"))}
    assert v9 <= set(keys)
    p = {r["key"]: float(r["value"]) for r in rows}
    assert p["IPCC2019.VSrate.dairy|north_america"] == 9.2 and p["IPCC2019.TAM.other_cattle|north_america"] == 407
