"""Sanity checks for the Phase 3 VT/DE fork measurement runner."""

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


def test_eight_forks_registered():
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
        "HOLOS.NEX.calf_nrate",
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
