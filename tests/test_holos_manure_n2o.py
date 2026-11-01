"""Unit tests: Holos manure N2O default vs calf Nrate holos_as_coded fork."""

import pytest

from ghgsim.modules.holos.forks import get_holos_fork_registry
from ghgsim.modules.holos.manure import HolosManure
from ghgsim.modules.holos.manure_n2o import HolosManureN2O

N2ON_TO_N2O = 44.0 / 28.0
NRATE = 0.44
TAM = 604.0
HEAD = 10.0
EF3_SOLID = 0.005
EF4 = 0.01
FRACGAS_SOLID = 0.3
CALF_N = 0.078


def _params(**overrides):
    base = {
        "Nrate_dairy_canada": NRATE,
        "Nrate_beef_canada": 0.31,
        "TAM_dairy_canada": TAM,
        "TAM_beef_canada": 389.0,
        "calf_n_kg_head_day": CALF_N,
        "EF3_liquid_nocrust": 0.0,
        "EF3_liquid_crust": 0.005,
        "EF3_lagoon": 0.0,
        "EF3_solid_storage": EF3_SOLID,
        "EF3_dry_lot": 0.02,
        "EF3_daily_spread": 0.0,
        "EF4": EF4,
        "FracGasMS_dairy_liquid_slurry": 0.4,
        "FracGasMS_dairy_solid_storage": FRACGAS_SOLID,
        "FracGasMS_dairy_daily_spread": 0.07,
        "FracGasMS_dairy_dry_lot": 0.2,
        "FracGasMS_dairy_lagoon": 0.35,
        "FracGasMS_other_cattle_solid_storage": 0.45,
        "FracGasMS_other_cattle_dry_lot": 0.3,
    }
    base.update(overrides)
    return base


def _nex_ipcc():
    return NRATE * TAM / 1000.0 * 365.0


def test_calf_nrate_fork_registered():
    fork = get_holos_fork_registry().get("HOLOS.NEX.calf_nrate")
    assert fork.default == "source_correct"
    assert fork.label == "holos_as_coded"
    assert "holos_as_coded" in fork.options


def test_default_n2o_matches_ipcc_10_25_and_10_27():
    module = HolosManureN2O()
    result = module.compute(
        {
            "head": HEAD,
            "animal_type": "dairy",
            "systems": {"solid_storage": 0.6, "pasture": 0.4},
        },
        _params(),
    )
    nex = _nex_ipcc()
    n_managed = HEAD * nex * 0.6
    n2o_direct = n_managed * EF3_SOLID * N2ON_TO_N2O
    n2o_vol = n_managed * FRACGAS_SOLID * EF4 * N2ON_TO_N2O
    assert result["Nex_kg_head"] == pytest.approx(nex)
    assert result["N2O_direct"] == pytest.approx(n2o_direct)
    assert result["N2O_indirect_vol"] == pytest.approx(n2o_vol)
    assert result["N2O_total"] == pytest.approx(n2o_direct + n2o_vol)
    assert result["N_PRP_kg"] == pytest.approx(HEAD * nex * 0.4)


def test_nex_override_skips_nrate_formula():
    module = HolosManureN2O()
    result = module.compute(
        {
            "head": 1.0,
            "animal_type": "dairy",
            "systems": {"solid_storage": 1.0},
            "Nex_kg_yr": 153.0,
        },
        _params(),
    )
    assert result["Nex_kg_head"] == 153.0
    assert result["N2O_direct"] == pytest.approx(153.0 * EF3_SOLID * N2ON_TO_N2O)


def test_calf_nrate_fork_differs_only_for_calves():
    module = HolosManureN2O()
    params = _params()
    calf = {
        "head": 1.0,
        "animal_type": "dairy",
        "animal_class": "calf",
        "systems": {"solid_storage": 1.0},
    }
    default = module.compute(calf, params)
    holos = module.compute(
        {**calf, "forks": {"HOLOS.NEX.calf_nrate": "holos_as_coded"}},
        params,
    )
    assert default["Nex_kg_head"] == pytest.approx(_nex_ipcc())
    assert holos["Nex_kg_head"] == pytest.approx(CALF_N * 365.0)
    assert default["Nex_kg_head"] != holos["Nex_kg_head"]
    assert default["N2O_total"] / holos["N2O_total"] == pytest.approx(
        default["Nex_kg_head"] / holos["Nex_kg_head"]
    )

    adult = {**calf, "animal_class": "adult"}
    adult_default = module.compute(adult, params)
    adult_fork = module.compute(
        {**adult, "forks": {"HOLOS.NEX.calf_nrate": "holos_as_coded"}},
        params,
    )
    assert adult_default["N2O_total"] == pytest.approx(adult_fork["N2O_total"])
    assert adult_default["Nex_kg_head"] == pytest.approx(adult_fork["Nex_kg_head"])


def test_holos_manure_facade_splits_direct_and_indirect():
    module = HolosManure()
    result = module.compute(
        {
            "head": HEAD,
            "animal_type": "dairy",
            "climate_zone": "temperate",
            "systems": {"solid_storage": 1.0},
            "VS_kg_day": 5.4,
        },
        {
            **_params(),
            "VS_dairy_canada": 5.4,
            "VS_beef_canada": 2.4,
            "B0_dairy_canada": 0.24,
            "B0_beef_canada": 0.19,
            "MCF_liquid_nocrust_cool": 0.17,
            "MCF_liquid_nocrust_temperate": 0.27,
            "MCF_liquid_crust_cool": 0.10,
            "MCF_liquid_crust_temperate": 0.17,
            "MCF_solid_storage_cool": 0.02,
            "MCF_solid_storage_temperate": 0.04,
            "MCF_pasture_cool": 0.015,
            "MCF_daily_spread_cool": 0.001,
            "CH4_M3_TO_KG": 0.67,
            "cover_crust_reduction": 0.40,
            "cover_solid_reduction": 0.25,
        },
    )
    assert result["CH4"] > 0
    assert result["N2O_direct"] > 0
    assert result["N2O_indirect_vol"] > 0
    assert result["N2O_total"] == pytest.approx(result["N2O_direct"] + result["N2O_indirect_vol"])
