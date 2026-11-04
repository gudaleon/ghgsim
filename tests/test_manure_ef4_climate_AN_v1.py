"""ipcc2019.manure 2.1: climate-specific EF4 (2019 Ch11 Table 11.3 Updated), DECISIONS_AN_v21."""
from pathlib import Path

import pytest

import ghgsim.modules.holos  # noqa: F401
from ghgsim.core.registry import load_parameter_csv
from ghgsim.modules.ipcc2019.manure import IPCC2019Manure
from ghgsim.modules.ipcc2019.soil_n2o import IPCC2019SoilN2O

ROOT = Path(__file__).resolve().parents[1]
REG = load_parameter_csv(ROOT / "data" / "ipcc_params_AN_v10.csv", allow_unverified=False)


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
BASE = {"head": 100, "animal_type": "dairy", "region": "north_america", "VS_kg_day": 5.0, "TAM_kg": 600.0,
        "Nex_kg_yr": 100.0, "systems": {"liquid_nocrust": 1.0}, "storage_months": 12}


def _run(**kw):
    return IPCC2019Manure().compute({**BASE, **kw}, P19)


def test_table_11_3_values_registered():
    assert P19["EF4_2019_wet"] == pytest.approx(0.014)
    assert P19["EF4_2019_dry"] == pytest.approx(0.005)
    assert P19["EF4_2019_all"] == pytest.approx(0.010)


@pytest.mark.parametrize("zone,ef4", [("warm_temperate_moist", 0.014), ("cool_temperate_moist", 0.014),
                                      ("boreal_moist", 0.014), ("tropical_wet", 0.014), ("tropical_moist", 0.014),
                                      ("warm_temperate_dry", 0.005), ("cool_temperate_dry", 0.005),
                                      ("tropical_dry", 0.005)])
def test_ef4_by_climate(zone, ef4):
    out = _run(climate_zone_2019=zone)
    agg = _run(climate_zone_2019=zone, ef4_mode="aggregated")
    assert out["EF4_used"] == pytest.approx(ef4)
    assert agg["EF4_used"] == pytest.approx(0.010)
    assert out["N2O_indirect_vol"] == pytest.approx(agg["N2O_indirect_vol"] * ef4 / 0.010)
    # only the volatilisation term moves
    for k in ("CH4", "N2O_direct", "N2O_indirect_leach", "N_MMS_Avb_kg"):
        assert out[k] == pytest.approx(agg[k])


def test_no_zone_falls_back_to_aggregated():
    out = _run(mcf_zone="15C")
    assert out["EF4_used"] == pytest.approx(0.010)
    assert "no climate zone" in out["EF4_basis"]


def test_bad_mode():
    with pytest.raises(ValueError):
        _run(climate_zone_2019="warm_temperate_moist", ef4_mode="foo")


def test_consistent_with_soil_module_refs():
    soil = IPCC2019SoilN2O().parameters
    keys = {r.key for r in soil.values()}
    assert "IPCC2019.EF4.wet" in keys and "IPCC2019.EF4.dry" in keys
