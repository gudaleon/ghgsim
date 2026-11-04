"""GLEAM adapter tests (AN_v2). The R run is skipped when Rscript or gleam is absent."""

from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CMP = ROOT / "results" / "gleam_vs_ghgsim_stylized_AN_v2.csv"
MAN = ROOT / "results" / "gleam_stylized_manifest_AN_v2.json"


def _load():
    spec = importlib.util.spec_from_file_location("rg", ROOT / "scripts" / "run_gleam_stylized_AN_v2.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_adapter_inputs_reproduce_committed_inputs():
    mod = _load()
    spec = mod.load_stylized_spec(mod.SPEC)
    const = mod._const(spec)
    reg = mod.load_parameter_csv(mod.PARAMS, allow_unverified=False)
    inputs, _fr, facts, _n = mod.build_inputs(spec, reg, const)
    with mod.F_INPUT.open(encoding="utf-8") as fh:
        committed = list(csv.DictReader(fh))
    assert len(committed) == len(inputs)
    for a, b in zip(inputs, committed, strict=True):
        assert a["herd_id"] == b["herd_id"]
        assert float(a["ration_intake"]) == pytest.approx(float(b["ration_intake"]), rel=1e-9)
        assert float(a["nitrogen_excretion"]) == pytest.approx(float(b["nitrogen_excretion"]), rel=1e-9)
    assert all(f["methane_conversion_factor_mcf"] > 1 or "pasture" in f["manure_management_system"] for f in facts)


def test_manifest_pins_gleam_commit():
    m = json.loads(MAN.read_text(encoding="utf-8"))
    assert m["gleam"]["commit"].startswith("b0937d2")
    assert m["gleam"]["modified"] is False
    assert "R version" in m["r"]["r_version"]


def _rscript_with_gleam():
    r = os.environ.get("GHGSIM_RSCRIPT") or shutil.which("Rscript")
    if not r:
        return None
    env = dict(os.environ)
    if os.environ.get("GHGSIM_R_LIBS"):
        env["R_LIBS"] = os.environ["GHGSIM_R_LIBS"]
    ok = subprocess.run([r, "--vanilla", "-e", "library(gleam)"], env=env, capture_output=True).returncode == 0
    return (r, env) if ok else None


@pytest.mark.skipif(_rscript_with_gleam() is None, reason="Rscript with the gleam package not available")
def test_gleam_rerun_matches_committed(tmp_path):
    r, env = _rscript_with_gleam()
    out = tmp_path / "res.csv"
    sess = tmp_path / "s.json"
    res = ROOT / "results"
    subprocess.run(
        [
            r,
            "--vanilla",
            str(ROOT / "scripts" / "run_gleam_stylized_AN_v1.R"),
            str(res / "gleam_stylized_inputs_AN_v2.csv"),
            str(res / "gleam_stylized_mms_fraction_AN_v2.csv"),
            str(res / "gleam_stylized_mms_factors_AN_v2.csv"),
            str(out),
            str(sess),
        ],
        env=env,
        check=True,
        capture_output=True,
    )
    with out.open(encoding="utf-8") as a, (res / "gleam_stylized_cohort_results_AN_v2.csv").open(encoding="utf-8") as b:
        ra, rb = list(csv.DictReader(a)), list(csv.DictReader(b))
    assert len(ra) == len(rb)
    for x, y in zip(ra, rb, strict=True):
        assert (x["herd_id"], x["cohort_short"]) == (y["herd_id"], y["cohort_short"])
        assert float(x["ch4_enteric"]) == pytest.approx(float(y["ch4_enteric"]), rel=1e-9)
        assert float(x["ch4_manure_other"]) == pytest.approx(float(y["ch4_manure_other"]), rel=1e-9)


def test_v2_factors_match_ghgsim_modules():
    mod = _load()
    spec = mod.load_stylized_spec(mod.SPEC)
    reg = mod.load_parameter_csv(mod.PARAMS, allow_unverified=False)
    checks: list[dict] = []
    mod.build_inputs(spec, reg, mod._const(spec), checks)
    with mod.F_CHECK.open(encoding="utf-8") as fh:
        committed = list(csv.DictReader(fh))
    assert len(committed) == len(checks)
    pasture19 = [
        c for c in checks if c["herd_id"].startswith("beef_pasture_field") and c["herd_id"].endswith("IPCC2019")
    ]
    ef4 = {c["gleam_value_v2"] for c in pasture19 if c["gleam_column"] == "n2o_ef4"}
    assert ef4 == {0.014}  # 2019 Refinement Table 11.3 wet climate, as ghgsim's soil module


def test_v2_pasture_n2o_matches_ghgsim_soil():
    with CMP.open(encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["source"] == "pasture_N2O_vs_soil_N2O"]
    assert {r["factor_set"] for r in rows} == {"IPCC2006", "IPCC2019"}
    for r in rows:
        assert float(r["gleam_kg"]) == pytest.approx(float(r["ghgsim_kg"]), rel=1e-6)
