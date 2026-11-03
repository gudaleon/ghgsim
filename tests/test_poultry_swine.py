"""Hand-calculated IPCC 2006/2019 poultry and swine cases; turkey CE-10 fork."""

from pathlib import Path

import pytest

from ghgsim.core.registry import load_parameter_csv
from ghgsim.modules.holos.forks import get_holos_fork_registry
from ghgsim.modules.holos.manure import HolosManure
from ghgsim.modules.holos.process_defs import (
    manure_n2o_indirect_leach_process,
    poultry_enteric_process,
    swine_enteric_tier1_process,
    turkey_manure_ch4_holos_process,
)
from ghgsim.modules.ipcc2006 import IPCC2006Enteric, IPCC2006Manure
from ghgsim.modules.ipcc2019 import IPCC2019Enteric, IPCC2019Manure
from ghgsim.modules.livestock_types import EPA_ANNEX_3_11_MAP, USDA_CENSUS_MAP

ROOT = Path(__file__).resolve().parents[1]
N2ON_TO_N2O = 44.0 / 28.0
DENSITY = 0.67
EF4 = 0.01


@pytest.fixture
def ipcc_params():
    return load_parameter_csv(ROOT / "data" / "ipcc_params_AN_v5.csv", allow_unverified=False)


def _reg_flat(registry, keys: dict[str, str]) -> dict[str, float]:
    return {name: float(registry.get_value(key)) for name, key in keys.items()}


def test_us_category_maps_match_census_and_epa():
    assert USDA_CENSUS_MAP["broilers"].startswith("Broilers")
    assert USDA_CENSUS_MAP["layers"].startswith("Layers")
    assert USDA_CENSUS_MAP["turkeys"] == "Turkeys"
    assert "market" in USDA_CENSUS_MAP["market_swine"].lower()
    assert "breeding" in USDA_CENSUS_MAP["breeding_swine"].lower()
    assert EPA_ANNEX_3_11_MAP == {
        "broilers": "Broilers",
        "layers": "Layers",
        "turkeys": "Turkeys",
        "market_swine": "Market swine",
        "breeding_swine": "Breeding swine",
    }


def test_process_defs_swine_poultry_and_leach():
    swine = swine_enteric_tier1_process()
    assert swine.compute_rate({"EF_enteric_kg_head_yr": 1.5}) == pytest.approx(1.5 / 365.0)
    assert poultry_enteric_process().compute_rate({}) == 0.0
    leach = manure_n2o_indirect_leach_process()
    assert leach.compute_rate({"Nex_kg": 10.0, "FracLeachMS": 0.0, "EF5": 0.011}) == 0.0
    turkey = turkey_manure_ch4_holos_process()
    source = turkey.compute_rate(
        {"VS": 0.07, "B0": 0.36, "MCF": 0.015, "CH4_M3_TO_KG": DENSITY}
    )
    assert source == pytest.approx(0.07 * 0.36 * 0.015 * DENSITY)
    assert turkey.compute_rate({}, fork="holos_as_coded") == 0.0


def test_turkey_zero_fork_registered():
    fork = get_holos_fork_registry().get("HOLOS.CH4.turkey_zero")
    assert fork.default == "source_correct"
    assert fork.label == "holos_as_coded"
    assert fork.issue_ref == "CE-10"
    assert "0" in fork.options["holos_as_coded"]


def test_ipcc2006_swine_enteric_hand_calc(ipcc_params):
    module = IPCC2006Enteric()
    params = {
        "EF_enteric_swine": ipcc_params.get_value("IPCC2006.EF_enteric.swine|developed"),
        "EF_enteric_poultry": ipcc_params.get_value("IPCC2006.EF_enteric.poultry"),
        "Ym_dairy": 6.5,
        "Ym_feedlot": 3.0,
        "Ym_other_cattle": 6.5,
        "CH4_ENERGY": 55.65,
    }
    swine = module.compute({"head": 1000, "ym_category": "market_swine", "GE_MJ_day": 0.0}, params)
    assert swine["CH4_kg_head"] == pytest.approx(1.5)
    assert swine["CH4_total"] == pytest.approx(1500.0)
    poultry = module.compute({"head": 20000, "animal_type": "broilers", "GE_MJ_day": 0.0}, params)
    assert poultry["CH4_total"] == 0.0


def test_ipcc2019_swine_enteric_matches_2006_high_productivity(ipcc_params):
    module = IPCC2019Enteric()
    params = {
        "EF_enteric_swine": ipcc_params.get_value("IPCC2019.EF_enteric.swine|high_productivity"),
        "EF_enteric_poultry": ipcc_params.get_value("IPCC2019.EF_enteric.poultry"),
        "CH4_ENERGY": 55.65,
    }
    swine = module.compute({"head": 10, "animal_type": "breeding_swine", "GE_MJ_day": 0.0}, params)
    assert swine["CH4_kg_head"] == pytest.approx(1.5)
    poultry = module.compute({"head": 10, "animal_type": "layers", "GE_MJ_day": 0.0}, params)
    assert poultry["CH4_total"] == 0.0


def _manure_params(ipcc_params):
    keys = {
        "VS_market_swine": "IPCC2006.VS.market_swine|north_america",
        "VS_breeding_swine": "IPCC2006.VS.breeding_swine|north_america",
        "VS_broilers": "IPCC2006.VS.broilers|north_america",
        "VS_layers": "IPCC2006.VS.layers|north_america",
        "VS_turkeys": "IPCC2006.VS.turkeys|north_america",
        "B0_market_swine": "IPCC2006.B0.market_swine|north_america",
        "B0_breeding_swine": "IPCC2006.B0.breeding_swine|north_america",
        "B0_broilers": "IPCC2006.B0.broilers|north_america",
        "B0_layers": "IPCC2006.B0.layers|north_america",
        "B0_turkeys": "IPCC2006.B0.turkeys|north_america",
        "Nrate_market_swine": "IPCC2006.Nrate.market_swine|north_america",
        "Nrate_breeding_swine": "IPCC2006.Nrate.breeding_swine|north_america",
        "Nrate_broilers": "IPCC2006.Nrate.broilers|north_america",
        "Nrate_layers": "IPCC2006.Nrate.layers|north_america",
        "Nrate_turkeys": "IPCC2006.Nrate.turkeys|north_america",
        "TAM_market_swine": "IPCC2006.TAM.market_swine|north_america",
        "TAM_breeding_swine": "IPCC2006.TAM.breeding_swine|north_america",
        "TAM_broilers": "IPCC2006.TAM.broilers|north_america",
        "TAM_layers": "IPCC2006.TAM.layers|north_america",
        "TAM_turkeys": "IPCC2006.TAM.turkeys|north_america",
        "CH4_M3_TO_KG": "BOTH.CH4_M3_TO_KG.all",
        "MCF_liquid_nocrust_15C": "IPCC2006.MCF.liquid_nocrust|15C",
        "MCF_poultry_with_litter_15C": "IPCC2006.MCF.poultry_with_litter|15C",
        "MCF_poultry_without_litter_15C": "IPCC2006.MCF.poultry_without_litter|15C",
        "MCF_pit_gt1mo_15C": "IPCC2006.MCF.pit_gt1mo|15C",
        "EF3_liquid_nocrust": "IPCC2006.EF3.liquid_nocrust",
        "EF3_poultry_with_litter": "IPCC2006.EF3.poultry_with_litter",
        "EF3_poultry_without_litter": "IPCC2006.EF3.poultry_without_litter",
        "EF3_pit": "IPCC2006.EF3.pit",
        "EF4": "IPCC2006.EF4.all",
        "EF5": "IPCC2019.EF5.all",
        "FracGasMS_swine_liquid_slurry": "IPCC2006.FracGasMS.swine|liquid_slurry",
        "FracGasMS_swine_pit": "IPCC2006.FracGasMS.swine|pit",
        "FracGasMS_poultry_poultry_with_litter": "IPCC2006.FracGasMS.poultry|poultry_with_litter",
        "FracGasMS_poultry_poultry_without_litter": "IPCC2006.FracGasMS.poultry|poultry_without_litter",
        "FracLeachMS_swine_liquid_nocrust": "IPCC2019.FracLeachMS.swine|liquid_nocrust",
        "FracLeachMS_poultry_poultry_with_litter": "IPCC2019.FracLeachMS.poultry|poultry_with_litter",
    }
    return _reg_flat(ipcc_params, keys)


def test_market_swine_manure_ch4_hand_calc(ipcc_params):
    """Eq 10.23: 1000 market swine, liquid no crust, 15C."""
    vs, b0, mcf = 0.27, 0.48, 0.27
    expected = 1000.0 * vs * 365.0 * b0 * DENSITY * mcf
    result = IPCC2006Manure().compute(
        {
            "head": 1000,
            "animal_type": "market_swine",
            "region": "north_america",
            "mcf_zone": "15C",
            "systems": {"liquid_nocrust": 1.0},
        },
        _manure_params(ipcc_params),
    )
    assert result["CH4"] == pytest.approx(expected)
    nex = 0.42 * 46.0 / 1000.0 * 365.0
    assert result["Nex_kg_head"] == pytest.approx(nex)
    assert result["N2O_direct"] == pytest.approx(0.0)  # EF3 liquid no crust = 0
    n2o_vol = 1000.0 * nex * 0.48 * EF4 * N2ON_TO_N2O
    assert result["N2O_indirect_vol"] == pytest.approx(n2o_vol)
    assert result["N2O_total"] == pytest.approx(result["N2O_direct"] + result["N2O_indirect_vol"])


def test_broiler_manure_hand_calc(ipcc_params):
    vs, b0, mcf = 0.02, 0.36, 0.015
    expected_ch4 = 10000.0 * vs * 365.0 * b0 * DENSITY * mcf
    nex = 1.10 * 0.9 / 1000.0 * 365.0
    result = IPCC2006Manure().compute(
        {
            "head": 10000,
            "animal_type": "broilers",
            "region": "north_america",
            "mcf_zone": "15C",
            "systems": {"poultry_with_litter": 1.0},
        },
        _manure_params(ipcc_params),
    )
    assert result["CH4"] == pytest.approx(expected_ch4)
    assert result["Nex_kg_head"] == pytest.approx(nex)
    n2o_direct = 10000.0 * nex * 0.001 * N2ON_TO_N2O
    n2o_vol = 10000.0 * nex * 0.40 * EF4 * N2ON_TO_N2O
    assert result["N2O_direct"] == pytest.approx(n2o_direct)
    assert result["N2O_indirect_vol"] == pytest.approx(n2o_vol)


def test_turkey_source_correct_vs_holos_zero(ipcc_params):
    params = _manure_params(ipcc_params)
    params.update(
        {
            "MCF_poultry_with_litter_temperate": params["MCF_poultry_with_litter_15C"],
            "cover_crust_reduction": 0.40,
            "cover_solid_reduction": 0.25,
        }
    )
    inputs = {
        "head": 5000,
        "animal_type": "turkeys",
        "climate_zone": "15C",
        "systems": {"poultry_with_litter": 1.0},
        "VS_kg_day": 0.07,
        "Nex_kg_yr": 0.74 * 6.8 / 1000.0 * 365.0,
    }
    source = HolosManure().compute(inputs, params)
    holos = HolosManure().compute({**inputs, "forks": {"HOLOS.CH4.turkey_zero": "holos_as_coded"}}, params)
    expected = 5000.0 * 0.07 * 365.0 * 0.36 * DENSITY * 0.015
    assert source["CH4"] == pytest.approx(expected)
    assert holos["CH4"] == pytest.approx(0.0)
    assert holos["N2O_total"] == pytest.approx(source["N2O_total"])
    assert source["N_MMS_Avb_kg"] < source["N_managed_kg"]


def test_ipcc2019_poultry_leach_is_zero_on_litter(ipcc_params):
    params = _manure_params(ipcc_params)
    params["Nrate_broilers_2019"] = ipcc_params.get_value("IPCC2019.Nrate.broilers|north_america")
    params["B0_other_poultry_2019"] = ipcc_params.get_value("IPCC2019.B0.other_poultry|north_america")
    result = IPCC2019Manure().compute(
        {
            "head": 100,
            "animal_type": "broilers",
            "region": "north_america",
            "mcf_zone": "15C",
            "systems": {"poultry_with_litter": 1.0},
        },
        params,
    )
    assert result["N2O_indirect_leach"] == pytest.approx(0.0)
    nex_2019 = 1.59 * 0.9 / 1000.0 * 365.0
    assert result["Nex_kg_head"] == pytest.approx(nex_2019)


def test_verified_poultry_swine_params_load_strict(ipcc_params):
    assert ipcc_params.get_value("IPCC2006.EF_enteric.swine|developed") == 1.5
    assert ipcc_params.get_value("IPCC2006.B0.market_swine|north_america") == 0.48
    assert ipcc_params.get_value("IPCC2006.VS.turkeys|north_america") == 0.07
    assert ipcc_params.get("IPCC2006.Nrate.broilers|north_america").status.value == "VERIFIED"


def test_manure_n_mass_balance_market_swine_and_broilers(ipcc_params):
    """Nex = N_managed + N_PRP; N_MMS_Avb = N_managed * (1 - FracGasMS - FracLeachMS)."""
    params = _manure_params(ipcc_params)
    swine = IPCC2006Manure().compute(
        {
            "head": 1000,
            "animal_type": "market_swine",
            "region": "north_america",
            "mcf_zone": "15C",
            "systems": {"liquid_nocrust": 1.0},
        },
        params,
    )
    nex_swine = 0.42 * 46.0 / 1000.0 * 365.0
    assert swine["Nex_kg_head"] == pytest.approx(nex_swine)
    assert swine["N_managed_kg"] == pytest.approx(1000.0 * nex_swine)
    assert swine["N_PRP_kg"] == pytest.approx(0.0)
    assert swine["N_managed_kg"] + swine["N_PRP_kg"] == pytest.approx(1000.0 * nex_swine)

    broiler = IPCC2019Manure().compute(
        {
            "head": 10000,
            "animal_type": "broilers",
            "region": "north_america",
            "mcf_zone": "15C",
            "systems": {"poultry_with_litter": 1.0},
        },
        {**params, "Nrate_broilers_2019": ipcc_params.get_value("IPCC2019.Nrate.broilers|north_america")},
    )
    nex_broiler = 1.59 * 0.9 / 1000.0 * 365.0
    assert broiler["Nex_kg_head"] == pytest.approx(nex_broiler)
    assert broiler["N_managed_kg"] == pytest.approx(10000.0 * nex_broiler)
    # 2019 Table 10.22 poultry with litter FracLeachMS = 0; FracGasMS 2006 = 0.40
    assert broiler["N_MMS_Avb_kg"] == pytest.approx(10000.0 * nex_broiler * (1.0 - 0.40))
    assert broiler["N_MMS_Avb_kg"] + (10000.0 * nex_broiler * 0.40) == pytest.approx(
        broiler["N_managed_kg"]
    )


def test_measured_turkey_ce10_delta_matches_eq_10_23():
    import pandas as pd

    path = ROOT / "data" / "holos_fork_deltas_stylized_AN_v3.csv"
    if not path.exists():
        pytest.skip("stylized v3 measurement CSV not generated yet")
    detail = pd.read_csv(path)
    turkey = detail[(detail["farm_id"] == "turkey_litter") & (detail["fork_id"] == "HOLOS.CH4.turkey_zero")]
    assert len(turkey) == 1
    expected_ch4 = 5000.0 * 0.07 * 365.0 * 0.36 * DENSITY * 0.015
    assert turkey.iloc[0]["delta_CH4_kg"] == pytest.approx(-expected_ch4)
    assert turkey.iloc[0]["delta_N2O_kg"] == pytest.approx(0.0)
    assert turkey.iloc[0]["delta_CO2e_pct"] < -40.0


def test_stylized_v3_has_us_poultry_and_swine_farms():
    import yaml

    spec = yaml.safe_load((ROOT / "data" / "stylized_farms_AN_v3.yaml").read_text(encoding="utf-8"))
    farm_ids = {farm["id"] for farm in spec["farms"]}
    assert {
        "broiler_litter",
        "layer_litter",
        "layer_highrise",
        "turkey_litter",
        "market_swine_liquid",
        "breeding_swine_liquid",
        "farrow_to_finish",
    } <= farm_ids
    for class_id in ("broilers", "layers", "turkeys", "market_swine", "breeding_swine"):
        animal = spec["animal_classes"][class_id]
        assert animal["usda_census"] == USDA_CENSUS_MAP[class_id]
        assert animal["epa_annex_3_11"] == EPA_ANNEX_3_11_MAP[class_id]
        assert animal["head"]["status"] == "ILLUSTRATIVE"
        assert animal["mass_kg"]["status"] == "VERIFIED"
        assert animal["VS_kg_day"]["status"] == "VERIFIED"
