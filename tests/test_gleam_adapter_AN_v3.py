"""GLEAM adapter AN_v3 tests: climate-specific EF4 passed to GLEAM; committed outputs agree with ghgsim v3."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"


def _rows(p):
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _load():
    s = importlib.util.spec_from_file_location("rg3", ROOT / "scripts" / "run_gleam_stylized_AN_v3.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_v3_paths_and_reference():
    m = _load()
    assert m.v2.GHGSIM_RESULTS.name == "ipcc_2006_vs_2019_stylized_AN_v3.csv"
    assert m.v2.F_CMP.name == "gleam_vs_ghgsim_stylized_AN_v3.csv"


def test_v3_ef4_2019_managed_is_wet_climate():
    m = _load()
    spec = m.v2.load_stylized_spec(m.v2.SPEC)
    const = m.v2._const(spec)
    reg = m.v2.load_parameter_csv(m.v2.PARAMS, allow_unverified=False)
    _i, _f, facts, _n = m.v2.build_inputs(spec, reg, const, [])
    for f in facts:
        if f["herd_id"].endswith("IPCC2019"):
            assert f["n2o_ef4"] == pytest.approx(0.014)
        else:
            assert f["n2o_ef4"] == pytest.approx(0.010)


def test_v3_committed_manure_matches_ghgsim_v3():
    ref = {(r["farm_id"], r["source"]): r for r in _rows(ROOT / "data" / "ipcc_2006_vs_2019_stylized_AN_v3.csv")}
    n = 0
    for r in _rows(R / "gleam_vs_ghgsim_stylized_AN_v3.csv"):
        if r["factor_set"] == "IPCC2019" and r["source"] in ("manure_CH4", "manure_N2O") and r["gleam_kg"]:
            assert float(r["gleam_kg"]) == pytest.approx(
                float(ref[(r["farm_id"], r["source"])]["ipcc2019_kg"]), rel=1e-4
            )
            n += 1
    assert n == 18


def test_v3_manifest_unmodified_gleam():
    m = json.loads((R / "gleam_stylized_manifest_AN_v3.json").read_text(encoding="utf-8"))
    assert m["gleam"]["commit"].startswith("b0937d2") and m["gleam"]["modified"] is False
