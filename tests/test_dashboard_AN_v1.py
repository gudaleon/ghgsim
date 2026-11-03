"""Smoke test for dashboard/app_AN_v1.py (no server launched)."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytest.importorskip("gradio")
pytest.importorskip("plotly")


def _app():
    spec = importlib.util.spec_from_file_location("dash_app_AN_v1", ROOT / "dashboard" / "app_AN_v1.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_county_tab():
    app = _app()
    _fig, table = app.county_view("hargreaves", "All")
    assert len(table) == len(app.load_county()) > 3000
    assert set(app.method_compare()["PE method"]) == {"hargreaves", "thornthwaite"}


def test_version_diff_matches_direct_ghgsim_run():
    app = _app()
    df, _ = app.run_version_diff("example_farm_AN_v1", "ipcc_params_AN_v7.csv")
    farm = json.loads((app.EXAMPLES / "example_farm_AN_v1.json").read_text(encoding="utf-8"))
    reg = app.load_parameter_csv(app.DATA / "ipcc_params_AN_v7.csv", allow_unverified=False)
    got = df.set_index("output")
    for g, col in (("IPCC2006", "IPCC 2006"), ("IPCC2019", "IPCC 2019")):
        direct = app.FarmModel(g).run_farm(farm, reg)
        for k in app.OUTPUTS:
            assert got.loc[k, col] == pytest.approx(direct[k])


def test_version_diff_reports_error_not_number():
    app = _app()
    df, note = app.run_version_diff("example_farm_AN_v2", "ipcc_params_AN_v7.csv")
    assert "IPCC2019 not computable" in note
    assert df["IPCC 2019"].isna().all()


def test_provenance_and_build():
    app = _app()
    m = app.manifest_checks()
    assert not (m["live check"] == "MISMATCH").any()
    assert (m["live check"] == "match").any()
    assert "ghgsim commit" in set(app.versions()["item"])
    app.build_app()