"""Sanity checks for the Phase 3 VT/DE fork measurement runner."""

import json
from pathlib import Path

import pandas as pd
import pytest

from ghgsim.modules.holos.enteric import HolosEnteric
from ghgsim.modules.holos.forks import get_holos_fork_registry

ROOT = Path(__file__).resolve().parents[1]


def test_ym_fork_dairy_enteric_ratio_is_6p5_over_5p6():
    """Eq 10.21 dairy enteric scales exactly with Ym when GE is held fixed."""
    module = HolosEnteric()
    params = {
        "GE_dairy_canada": 401.2,
        "Ym_dairy_canada": 5.6,
        "Ym_dairy_ipcc2006": 6.5,
        "GE_beef_high_grain": 200.0,
        "GE_beef_medium": 220.5,
        "GE_beef_low_grain": 180.0,
        "Ym_beef_high_grain": 3.0,
        "Ym_beef_medium": 6.5,
        "Ym_beef_low_grain": 7.0,
        "CH4_ENERGY": 55.65,
    }
    shared = {"head": 1.0, "animal_type": "dairy", "GE_MJ_day": 401.2}
    default = module.compute(shared, params)
    ipcc = module.compute({**shared, "forks": {"HOLOS.YM.dairy": "ipcc2006_table_10_12"}}, params)
    assert ipcc["CH4_kg_head"] / default["CH4_kg_head"] == pytest.approx(6.5 / 5.6)
    assert default["Ym_used"] == 5.6
    assert ipcc["Ym_used"] == 6.5


def test_registered_forks_include_turkey_zero():
    forks = get_holos_fork_registry().list_forks(sort_by="id")
    ids = {f.id for f in forks}
    assert ids == {
        "HOLOS.GE.digestibility",
        "HOLOS.ENTERIC.calf_zero",
        "HOLOS.YM.dairy",
        "HOLOS.VS.digestibility",
        "HOLOS.VS.urinary_energy",
        "HOLOS.VS.calf_coeff",
        "HOLOS.CH4.cover_reduction",
        "HOLOS.CH4.turkey_zero",
        "HOLOS.CH4.liquid_tank",
        "HOLOS.STORAGE.year_reset",
        "HOLOS.STORAGE.temp_window",
        "HOLOS.STORAGE.cli_no_drain",
        "HOLOS.STORAGE.carbon_removal",
        "HOLOS.NEX.calf_nrate",
        "HOLOS.N2O.ef1",
    }


def test_measurement_csv_matches_command_and_county_count():
    path = ROOT / "data" / "holos_fork_deltas_vt_de_AN_v2.csv"
    if not path.exists():
        pytest.skip("measurement CSV not generated yet")
    df = pd.read_csv(path)
    assert df["command"].nunique() == 1
    assert df["command"].iloc[0] == "python3 scripts/measure_holos_forks_vt_de_AN_v2.py"
    assert df["fips"].nunique() == 17
    ym = df[(df["pathway"] == "epa_vs") & (df["fork_id"] == "HOLOS.YM.dairy")]
    zeros = df[
        (df["pathway"] == "epa_vs")
        & (df["fork_id"] != "HOLOS.YM.dairy")
        & (df["fork_id"] != "BASELINE")
    ]
    assert (ym["delta_CH4_kg"].abs() > 1.0).all()
    assert (zeros["delta_CH4_kg"].abs() < 1e-6).all()
    assert (zeros["delta_N2O_kg"].abs() < 1e-6).all()
    assert (ym["evidence"] == "MEASURED").all()


def test_fourway_csv_matches_committed_ipcc_and_command():
    path = ROOT / "data" / "holos_fourway_vt_de_AN_v1.csv"
    if not path.exists():
        pytest.skip("four-way CSV not generated yet")
    df = pd.read_csv(path)
    assert df["command"].iloc[0] == "python3 scripts/compare_holos_fourway_vt_de_AN_v1.py"
    assert df["fips"].nunique() == 17
    assert (df["evidence"] == "MEASURED").all()
    rel_2006 = (df["IPCC2006_CO2e_t"] - df["csv_IPCC2006_CO2e_t"]).abs() / df["csv_IPCC2006_CO2e_t"]
    rel_2019 = (df["IPCC2019_CO2e_t"] - df["csv_IPCC2019_CO2e_t"]).abs() / df["csv_IPCC2019_CO2e_t"]
    assert rel_2006.max() < 1e-12
    assert rel_2019.max() < 1e-12
    # Holos N2O uses EPA Nex + IPCC 2006 EF3; must match IPCC 2006 N2O on this dataset.
    assert (df["HolosCanada_N2O_kg"] - df["IPCC2006_N2O_kg"]).abs().max() < 1e-6
    assert (df["HolosUS_N2O_kg"] - df["IPCC2006_N2O_kg"]).abs().max() < 1e-6


def test_poultry_crops_an_v2_drops_ppe_clamp():
    path = ROOT / "data" / "holos_vt_de_poultry_crops_AN_v2.csv"
    meta_path = ROOT / "data" / "holos_vt_de_poultry_crops_AN_v2.meta.json"
    summary_path = ROOT / "data" / "holos_vt_de_poultry_crops_summary_AN_v2.csv"
    if not path.exists():
        pytest.skip("AN_v2 county CSV not generated yet")
    df = pd.read_csv(path)
    assert "expanded_rochette_CO2e_t" not in df.columns
    assert "dCO2e_t_rochette_minus_ipcc_EF1" not in df.columns
    assert (df["EF1_status_liang_without_climate"] == "UNVERIFIED-input").all()
    assert (df["EF1_ipcc"] - 0.01).abs().max() < 1e-12
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["HOLOS.N2O.ef1"]["holos_liang2020"] == "UNVERIFIED-input"
    assert "P_PE" not in meta
    assert meta["run_identity"]["commit_hash"]
    assert "Holzworth" in meta["run_identity"]["apsim_requirement"]
    summary = pd.read_csv(summary_path)
    assert "dCO2e_t_rochette_minus_ipcc_EF1" not in summary.columns
    assert abs(float(summary["dCO2e_t_ipcc_EF1_minus_baseline"].iloc[0]) - 53677.7) < 1.0


def test_phase_b_followup_v2_withdraws_ppe_finding():
    text = (ROOT / "docs" / "PHASE_B_FOLLOWUP_AN_v2.md").read_text(encoding="utf-8")
    assert "holos_liang2020" in text
    assert "ipcc2006_ef1" in text
    assert "N2OEmissionFactorCalculator.cs:478-656,777-788" in text
    assert "Section 2.5" in text
    assert "Do not cite it" in text or "withdrawn" in text.lower()
    assert "Holzworth" in text
    assert "103" in text
    assert "217,229" in text or "217229" in text
    assert "53,678" in text or "53678" in text
