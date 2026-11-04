"""Unit tests for ipcc2019.manure 2.0, 2006 FracLossMS and the dry-fallback EF1 sensitivity."""
import math
from pathlib import Path

import pytest

import ghgsim.modules.holos  # noqa: F401
from ghgsim.core.registry import load_parameter_csv
from ghgsim.modules.ipcc2006.manure import IPCC2006Manure
from ghgsim.modules.ipcc2019.manure import IPCC2019Manure, climate_zone_2019

ROOT = Path(__file__).resolve().parents[1]
REG = load_parameter_csv(ROOT / "data" / "ipcc_params_AN_v9.csv", allow_unverified=False)
DENS = None


def _resolve(mod):
    out = {}
    for name, ref in mod.parameters.items():
        try:
            out[name] = float(REG.get_value(ref.key))
        except Exception:
            if ref.fallback is not None:
                out[name] = float(ref.fallback)
    return out


P19 = _resolve(IPCC2019Manure())
P06 = _resolve(IPCC2006Manure())
BASE = {"head": 100, "region": "north_america", "mcf_zone": "15C", "VS_kg_day": 5.0, "TAM_kg": 600.0, "Nex_kg_yr": 70.0}


def test_climate_zone_helper():
    assert climate_zone_2019(7.0, 1.3) == "cool_temperate_moist"
    assert climate_zone_2019(15.0, 0.6) == "warm_temperate_dry"
    assert climate_zone_2019(-2.0, 1.2) == "boreal_moist"
    assert climate_zone_2019(22.0, 1.2) is None


def test_2019_cattle_liquid_mcf_b0_fracgas():
    out = IPCC2019Manure().compute({**BASE, "animal_type": "other_cattle", "systems": {"liquid_nocrust": 1.0},
                                    "climate_zone_2019": "cool_temperate_moist", "storage_months": 12}, P19)
    ch4 = 100 * 5.0 * 365 * 0.19 * P19["CH4_M3_TO_KG"] * 0.31  # Table 10.17 12 mo cool temp moist = 31 %
    assert out["CH4"] == pytest.approx(ch4)
    n = 100 * 70.0
    assert out["N2O_indirect_vol"] == pytest.approx(n * 0.48 * 0.01 * 44 / 28)  # Table 10.22 other cattle 0.48
    assert out["N_MMS_Avb_kg"] == pytest.approx(n * (1 - 0.48))
    assert "cool_temperate_moist" in out["MCF_basis"]


def test_2019_crust_and_prp_b0_pairing():
    crust = IPCC2019Manure().compute({**BASE, "animal_type": "dairy", "systems": {"liquid_crust": 1.0},
                                      "climate_zone_2019": "warm_temperate_moist", "storage_months": 6}, P19)
    assert crust["CH4"] == pytest.approx(100 * 5.0 * 365 * 0.24 * P19["CH4_M3_TO_KG"] * 0.37 * 0.6)
    prp = IPCC2019Manure().compute({**BASE, "animal_type": "dairy", "systems": {"pasture": 1.0},
                                    "climate_zone_2019": "warm_temperate_moist"}, P19)
    # fn 2: PRP MCF 0.47 % with B0 0.19 regardless of animal B0
    assert prp["CH4"] == pytest.approx(100 * 5.0 * 365 * 0.19 * P19["CH4_M3_TO_KG"] * 0.0047)


def test_2019_without_zone_falls_back_to_2006_mcf():
    out = IPCC2019Manure().compute({**BASE, "animal_type": "dairy", "systems": {"liquid_nocrust": 1.0}}, P19)
    assert out["CH4"] == pytest.approx(100 * 5.0 * 365 * 0.24 * P19["CH4_M3_TO_KG"] * 0.27)
    assert "IPCC2006" in out["MCF_basis"]


def test_2006_fraclossms_eq_10_34():
    out = IPCC2006Manure().compute({**BASE, "animal_type": "dairy", "systems": {"liquid_nocrust": 1.0}}, P06)
    assert out["N_MMS_Avb_kg"] == pytest.approx(100 * 70.0 * (1 - 0.40))  # Table 10.23 dairy liquid/slurry 40 %
    beef = IPCC2006Manure().compute({**BASE, "animal_type": "other_cattle", "systems": {"solid_storage": 1.0}}, P06)
    assert beef["N_MMS_Avb_kg"] == pytest.approx(100 * 70.0 * 0.50)
    # No Table 10.23 other-cattle liquid cell -> NaN, never invented.
    p = dict(P06, FracGasMS_other_cattle_liquid_slurry=math.nan)
    miss = IPCC2006Manure().compute({**BASE, "animal_type": "other_cattle", "systems": {"liquid_nocrust": 1.0}}, p)
    assert math.isnan(miss["N_MMS_Avb_kg"])
