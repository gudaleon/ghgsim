"""Tests for the Paper B paper agent (AN_v1): every number traces to ghgsim or committed data."""
import asyncio
import csv
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))
T = pytest.importorskip("paper_agent_tools_AN_v1")


def test_run_farm_reproduces_committed_csv():
    with (ROOT / "data" / "ipcc_2006_vs_2019_stylized_AN_v3.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for farm in sorted({r["farm_id"] for r in rows})[:4]:
        live = T.run_farm(farm, params_file=rows[0]["params_file"])["results"]
        for r in (x for x in rows if x["farm_id"] == farm):
            for g, col in (("IPCC2006", "ipcc2006_kg"), ("IPCC2019", "ipcc2019_kg")):
                v = live[g]["sources"][r["source"]]["kg"]
                if r[col] in ("", "nan"):
                    assert v is None
                else:
                    assert math.isclose(v, float(r[col]), rel_tol=1e-6, abs_tol=1e-3)


def test_override_is_reported_and_changes_soil_n2o():
    farm = next(f["farm_id"] for f in T.list_farms()["farms"] if f["field_id"])
    base = T.run_farm(farm, "IPCC2006")
    what = T.run_farm(farm, "IPCC2006", param_overrides={"IPCC2006.EF1.all": 0.005})
    assert what["param_overrides"]["IPCC2006.EF1.all"]["published"] == 0.01
    assert what["results"]["IPCC2006"]["sources"]["soil_N2O"]["kg"] < base["results"]["IPCC2006"]["sources"]["soil_N2O"]["kg"]


def test_unknown_inputs_raise():
    with pytest.raises(ValueError):
        T.run_farm("no_such_farm")
    with pytest.raises(ValueError):
        T.run_farm(T.list_farms()["farms"][0]["farm_id"], param_overrides={"NOT.A.KEY": 1})


def test_county_tools():
    z = T.county_climate_zone("6019")
    assert z["fips"] == "06019" and z["zone_primary"]
    r = T.county_results(fips="06019")
    assert r["n_counties"] == 1 and r["source"]["files"]
    s = T.county_results(state="IA")
    assert s["n_counties"] > 90


def test_explain_parameter_has_citation():
    e = T.explain_parameter("IPCC2006.EF1.all")
    m = e["matches"][0]
    assert m["table"] == "Table 11.1" and m["page"] and m["value"] == "0.01"
    assert len(e["history"]) == len(T.list_parameter_files())


def test_provenance_and_diff():
    p = T.provenance()
    assert p["code"]["commit"] and p["paper_numbers"]
    d = T.diff_manifests("results_manifest_AN_v1.json", "results_manifest_AN_v2.json")
    assert d["report_markdown"].startswith("# Results diff")


def test_mcp_server_lists_tools():
    srv = pytest.importorskip("paper_agent_AN_v1")
    names = {t.name for t in asyncio.run(srv.mcp.list_tools())}
    assert {"run_farm", "county_results", "county_climate_zone", "explain_parameter",
            "provenance", "diff_manifests"} <= names


def test_dashboard_tab_uses_same_tools():
    sys.path.insert(0, str(ROOT / "dashboard"))
    app = pytest.importorskip("app_AN_v2")
    out, _ = app.ask_paper("county_climate_zone", "", "", "", "", "06019", "", "", "", "", "")
    assert out == T.county_climate_zone("06019")
