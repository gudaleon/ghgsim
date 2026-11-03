"""Scan Holos forks for reduction-vs-remaining, sign, and unit errors.

Phase 3d found one such error (CH4.cover_reduction treated 0.40/0.25 as
remaining fractions). This module locks the scan of the other forks.
"""

from pathlib import Path

import pytest

from ghgsim.modules.holos.process_defs import (
    manure_ch4_process,
    urinary_energy_holos,
    urinary_energy_ipcc,
    volatile_solids_process,
)
from ghgsim.modules.holos.vs import HolosVolatileSolids

ROOT = Path(__file__).resolve().parents[1]


def test_cover_process_uses_one_minus_reduction_not_remaining():
    equation = manure_ch4_process().rate_equation_for("holos_as_coded")
    assert "* (1.0 - cover_reduction)" in equation
    assert not equation.endswith("* cover_reduction")


def test_ue_values_are_not_sign_reversed():
    """High-digestibility / high-grain must lower UE (0.02), not raise it."""
    ipcc_high = urinary_energy_ipcc().compute({"DE_percent": 82.5})
    ipcc_typical = urinary_energy_ipcc().compute({"DE_percent": 66.7})
    holos_high_grain = urinary_energy_holos().compute({"forage_percent": 10.0})  # grain 90
    holos_forage = urinary_energy_holos().compute({"forage_percent": 67.0})
    assert ipcc_high == 0.02
    assert ipcc_typical == 0.04
    assert holos_high_grain == 0.02
    assert holos_forage == 0.04
    assert ipcc_high < ipcc_typical
    assert holos_high_grain < holos_forage


def test_vs_tdn_and_de_use_one_minus_digestibility():
    """Both VS paths use (1 - digestibility/100), not digestibility/100 as remaining energy."""
    default = volatile_solids_process().rate_equation
    holos = volatile_solids_process().rate_equation_for("holos_as_coded")
    assert "1.0 - DE_percent / 100.0" in default
    assert "1.0 - TDN_percent / 100.0" in holos
    assert "1.0 - ASH_percent / 100.0" in default
    assert "1.0 - ASH_percent / 100.0" in holos


def test_calf_vs_coeff_is_kg_per_kg_weight_not_a_reduction():
    module = HolosVolatileSolids()
    result = module.compute(
        {
            "GE_MJ_day": 50.0,
            "DE_percent": 66.7,
            "ASH_percent": 8.0,
            "animal_class": "calf",
            "weight_kg": 100.0,
            "forks": {"HOLOS.VS.calf_coeff": "holos_as_coded"},
        },
        {"GE_PER_KG_DM": 18.45, "calf_vs_coeff": 0.0093},
    )
    assert result["VS_kg_day"] == pytest.approx(0.0093 * 100.0)


def test_canada_v5_cover_params_are_labelled_reductions():
    text = (ROOT / "data" / "holos_params_canada_AN_v5.csv").read_text(encoding="utf-8")
    assert "HOLOS.COVER.natural_crust_reduction,0.40,reduction fraction" in text
    assert "HOLOS.COVER.solid_cover_reduction,0.25,reduction fraction" in text
    assert "remaining=0.60" in text or "remaining = 0.60" in text
    assert "LiquidWithSolidCover" in text
    assert "HOLOS.COVER.other_cover_factor" not in text
