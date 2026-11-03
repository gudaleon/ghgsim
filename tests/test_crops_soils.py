"""Phase B: IPCC 2006 Ch 11 soil N2O, lime/urea CO2, once-only manure N link."""

import math
from pathlib import Path

import pytest
import yaml

from ghgsim.core.registry import load_parameter_csv
from ghgsim.modules.holos.fields import HolosFieldN
from ghgsim.modules.holos.lime_urea import HolosLimeUreaCO2
from ghgsim.modules.holos.manure import HolosManure
from ghgsim.modules.holos.process_defs import (
    crop_residue_n_process,
    field_fam_process,
    holos_ecodistrict_ef_ct_process,
    lime_co2_process,
    rochette_efeco_process,
    soil_n2o_direct_process,
    urea_co2_process,
)
from ghgsim.modules.holos.soil_n2o import HolosSoilN2O, holos_ecodistrict_ef1
from ghgsim.modules.ipcc2006 import IPCC2006LimeUreaCO2, IPCC2006SoilN2O
from ghgsim.modules.ipcc2019.crop_residue import IPCC2019CropResidue
from ghgsim.report.emissions_sankey import compute_stylized_farm_flows, stylized_params
from ghgsim.report.fork_diagram import latest_versioned

ROOT = Path(__file__).resolve().parents[1]
N2ON_TO_N2O = 44.0 / 28.0
C_TO_CO2 = 44.0 / 12.0


@pytest.fixture
def ipcc_params():
    return load_parameter_csv(latest_versioned(ROOT / "data", "ipcc_params", ".csv"), allow_unverified=False)


@pytest.fixture
def soil_params(ipcc_params):
    return {
        "EF1": ipcc_params.get_value("IPCC2006.EF1.all"),
        "EF3PRP_CPP": ipcc_params.get_value("IPCC2006.EF3PRP_CPP.all"),
        "EF4": ipcc_params.get_value("IPCC2006.EF4.all"),
        "EF5": ipcc_params.get_value("IPCC2006.EF5.all"),
        "FracGASF": ipcc_params.get_value("IPCC2006.FracGASF.all"),
        "FracGASM": ipcc_params.get_value("IPCC2006.FracGASM.all"),
        "FracLEACH_wet": ipcc_params.get_value("IPCC2006.FracLEACH.wet"),
        "EF_limestone": ipcc_params.get_value("IPCC2006.EF_lime.limestone"),
        "EF_dolomite": ipcc_params.get_value("IPCC2006.EF_lime.dolomite"),
        "EF_urea": ipcc_params.get_value("IPCC2006.EF_urea.all"),
        "C_TO_CO2": ipcc_params.get_value("BOTH.C_TO_CO2.all"),
        "FracFEED_default": ipcc_params.get_value("IPCC2006.FracFEED.default_zero"),
        "N_AG_maize": ipcc_params.get_value("IPCC2019.N_AG.maize"),
        "N_BG_maize": ipcc_params.get_value("IPCC2019.N_BG.maize"),
        "R_AG_maize": ipcc_params.get_value("IPCC2019.R_AG.maize"),
        "RS_maize": ipcc_params.get_value("IPCC2019.RS.maize"),
        "DRY_maize": ipcc_params.get_value("IPCC2019.DRY.maize"),
        "N_AG_soybeans": ipcc_params.get_value("IPCC2019.N_AG.soybeans"),
        "N_BG_soybeans": ipcc_params.get_value("IPCC2019.N_BG.soybeans"),
        "R_AG_soybeans": ipcc_params.get_value("IPCC2019.R_AG.soybeans"),
        "RS_soybeans": ipcc_params.get_value("IPCC2019.RS.soybeans"),
        "DRY_soybeans": ipcc_params.get_value("IPCC2019.DRY.soybeans"),
        "FracRenew_annual": ipcc_params.get_value("IPCC2019.FracRenew.annual"),
        "FracRemove_default": ipcc_params.get_value("IPCC2019.FracRemove.default_zero"),
        "FracBurnt_default": ipcc_params.get_value("IPCC2019.FracBurnt.default_zero"),
        "CF_default": ipcc_params.get_value("IPCC2019.CF.unused_when_unburnt"),
        "EFeco_slope": 0.022,
        "EFeco_intercept": -0.0048,
        "EFeco_min": 0.0016,
        "EFeco_max": 0.017,
        "EF_CT_slope": 0.00558,
        "EF_CT_intercept": -7.7,
        "winter_correction": 1.0 / 0.645,
    }


@pytest.fixture
def stylized():
    spec = yaml.safe_load(latest_versioned(ROOT / "data", "stylized_farms", ".yaml").read_text(encoding="utf-8"))
    params = stylized_params(ROOT, spec)
    return spec, params


def _farm(spec, farm_id: str):
    return next(farm for farm in spec["farms"] if farm["id"] == farm_id)


def test_ch11_default_cells_are_verified(ipcc_params):
    assert ipcc_params.get_value("IPCC2006.EF1.all") == pytest.approx(0.01)
    assert ipcc_params.get_value("IPCC2006.EF3PRP_CPP.all") == pytest.approx(0.02)
    assert ipcc_params.get_value("IPCC2006.EF4.all") == pytest.approx(0.01)
    assert ipcc_params.get_value("IPCC2006.EF5.all") == pytest.approx(0.0075)
    assert ipcc_params.get_value("IPCC2006.FracGASF.all") == pytest.approx(0.10)
    assert ipcc_params.get_value("IPCC2006.FracGASM.all") == pytest.approx(0.20)
    assert ipcc_params.get_value("IPCC2006.FracLEACH.wet") == pytest.approx(0.30)
    assert ipcc_params.get_value("IPCC2006.EF_lime.limestone") == pytest.approx(0.12)
    assert ipcc_params.get_value("IPCC2006.EF_lime.dolomite") == pytest.approx(0.13)
    assert ipcc_params.get_value("IPCC2006.EF_urea.all") == pytest.approx(0.20)
    assert ipcc_params.get_value("BOTH.C_TO_CO2.all") == pytest.approx(C_TO_CO2)
    assert ipcc_params.get("IPCC2006.EF_lime.limestone").status.value == "VERIFIED"
    assert ipcc_params.get("IPCC2006.EF_urea.all").status.value == "VERIFIED"


def test_process_defs_eq_11_1_and_11_12_11_13():
    direct = soil_n2o_direct_process()
    # Eq 11.1: (1000+500+200+100)*0.01 + 300*0.02 = 18 + 6 = 24 kg N2O-N
    assert direct.compute_rate(
        {
            "F_SN": 1000.0,
            "F_ON": 500.0,
            "F_CR": 200.0,
            "F_SOM": 100.0,
            "EF1": 0.01,
            "F_PRP_CPP": 300.0,
            "EF3PRP": 0.02,
        }
    ) == pytest.approx(24.0)
    lime_c = lime_co2_process().compute_rate(
        {"M_limestone_t": 2.0, "EF_limestone": 0.12, "M_dolomite_t": 1.0, "EF_dolomite": 0.13}
    )
    assert lime_c == pytest.approx(2.0 * 0.12 + 1.0 * 0.13)
    assert urea_co2_process().compute_rate({"M_urea_t": 1.0, "EF_urea": 0.20}) == pytest.approx(0.20)
    assert field_fam_process().compute_rate(
        {"N_MMS_Avb_kg": 100.0, "FracFEED": 0.0, "FracFUEL": 0.0, "FracCNST": 0.0}
    ) == pytest.approx(100.0)


def test_soil_n2o_hand_calc_matches_ipcc2006_and_holos(soil_params):
    inputs = {
        "F_SN": 1000.0,
        "F_ON": 500.0,
        "F_CR": 200.0,
        "F_SOM": 100.0,
        "F_PRP_CPP": 300.0,
        "climate": "wet",
    }
    # Direct: (1800)*0.01 + 300*0.02 = 24 kg N2O-N
    # Vol: (1000*0.10 + (500+300)*0.20)*0.01 = 2.6 kg N2O-N
    # Leach: (1800+300)*0.30*0.0075 = 4.725 kg N2O-N
    expected_direct = 24.0 * N2ON_TO_N2O
    expected_vol = 2.6 * N2ON_TO_N2O
    expected_leach = 4.725 * N2ON_TO_N2O
    ipcc = IPCC2006SoilN2O().compute(inputs, soil_params)
    holos = HolosSoilN2O().compute(inputs, soil_params)
    for result in (ipcc, holos):
        assert result["N2O_direct"] == pytest.approx(expected_direct)
        assert result["N2O_indirect_vol"] == pytest.approx(expected_vol)
        assert result["N2O_indirect_leach"] == pytest.approx(expected_leach)
        assert result["N2O_total"] == pytest.approx(expected_direct + expected_vol + expected_leach)


def test_prp_uses_ef3_not_ef1(soil_params):
    inputs = {
        "F_SN": 0.0,
        "F_ON": 0.0,
        "F_CR": 0.0,
        "F_SOM": 0.0,
        "F_PRP_CPP": 1000.0,
        "climate": "wet",
    }
    result = HolosSoilN2O().compute(inputs, soil_params)
    assert result["N2O_direct"] == pytest.approx(1000.0 * 0.02 * N2ON_TO_N2O)
    assert result["N2O_direct"] != pytest.approx(1000.0 * 0.01 * N2ON_TO_N2O)


def test_lime_urea_hand_calc(soil_params):
    result = IPCC2006LimeUreaCO2().compute(
        {"M_limestone_t": 2.0, "M_dolomite_t": 1.0, "M_urea_t": 1.0},
        soil_params,
    )
    lime = (2.0 * 0.12 + 1.0 * 0.13) * 1000.0 * C_TO_CO2
    urea = 1.0 * 0.20 * 1000.0 * C_TO_CO2
    assert result["CO2_lime_kg"] == pytest.approx(lime)
    assert result["CO2_urea_kg"] == pytest.approx(urea)
    assert result["CO2_total_kg"] == pytest.approx(lime + urea)
    holos = HolosLimeUreaCO2().compute(
        {"M_limestone_t": 2.0, "M_dolomite_t": 1.0, "M_urea_t": 1.0},
        soil_params,
    )
    assert holos["CO2_total_kg"] == pytest.approx(result["CO2_total_kg"])
    assert HolosLimeUreaCO2.id == "holos.lime_urea_co2"


def test_field_n_uses_n_mms_avb_not_raw_nex(soil_params):
    n_mms = 4336.2
    nex_total = 7227.0
    linked = HolosFieldN().compute(
        {"N_MMS_Avb_kg": n_mms, "N_PRP_kg": 0.0, "F_SN": 0.0, "F_CR": 200.0},
        soil_params,
    )
    assert linked["F_ON"] == pytest.approx(n_mms)
    assert linked["F_AM_kg"] == pytest.approx(n_mms)
    assert linked["F_ON"] != pytest.approx(nex_total)
    unlinked = HolosFieldN().compute(
        {
            "N_MMS_Avb_kg": n_mms,
            "N_PRP_kg": 0.0,
            "F_SN": 0.0,
            "F_CR": 200.0,
            "link_manure_n": False,
        },
        soil_params,
    )
    assert unlinked["F_ON"] == pytest.approx(0.0)
    assert unlinked["F_AM_kg"] == pytest.approx(0.0)


def test_broiler_litter_field_links_manure_n_once(stylized, ipcc_params):
    spec, params = stylized
    farm = _farm(spec, "broiler_litter_field")
    flows = compute_stylized_farm_flows(spec, farm, params, {}, run="source_correct")
    nex = 1.10 * 0.9 / 1000.0 * 365.0
    nex_total = 20000.0 * nex
    frac_gas = ipcc_params.get_value("IPCC2006.FracGasMS.poultry|poultry_with_litter")
    n_mms = nex_total * (1.0 - frac_gas)
    man = HolosManure().compute(
        {
            "head": 20000,
            "animal_type": "broilers",
            "climate_zone": "15C",
            "systems": {"poultry_with_litter": 1.0},
            "VS_kg_day": 0.02,
            "Nex_kg_yr": nex,
        },
        params,
    )
    assert man["N_MMS_Avb_kg"] == pytest.approx(n_mms)
    assert flows.extras["N_MMS_Avb_kg"] == pytest.approx(n_mms)
    assert flows.extras["F_ON"] == pytest.approx(n_mms)
    assert flows.extras["F_ON"] != pytest.approx(nex_total)
    # 3 ha maize x 8000 kg/ha: F_CR = 189.5904; default IPCC EF1=0.01
    f_cr = 189.5904
    assert flows.extras["F_CR"] == pytest.approx(f_cr)
    assert flows.extras["EF1_used"] == pytest.approx(0.01)
    assert flows.extras["EF1_status"] == "ipcc2006_ef1"
    direct_n = (n_mms + f_cr) * 0.01
    vol_n = n_mms * 0.20 * 0.01
    leach_n = (n_mms + f_cr) * 0.30 * 0.0075
    expected_soil = (direct_n + vol_n + leach_n) * N2ON_TO_N2O
    assert flows.soil_n2o_kg == pytest.approx(expected_soil)
    assert flows.lime_co2_kg == pytest.approx(0.0)
    assert flows.extras["F_AM_kg"] + (nex_total - n_mms) == pytest.approx(nex_total)


def test_market_swine_field_synthetic_plus_linked_manure(stylized, ipcc_params):
    spec, params = stylized
    farm = _farm(spec, "market_swine_field")
    flows = compute_stylized_farm_flows(spec, farm, params, {}, run="source_correct")
    nex = 0.42 * 46.0 / 1000.0 * 365.0
    nex_total = 1000.0 * nex
    frac_gas = ipcc_params.get_value("IPCC2006.FracGasMS.swine|liquid_slurry")
    n_mms = nex_total * (1.0 - frac_gas)
    assert flows.extras["F_ON"] == pytest.approx(n_mms)
    assert flows.extras["F_SN"] == pytest.approx(500.0)
    f_cr = 117.45552
    assert flows.extras["F_CR"] == pytest.approx(f_cr)
    assert flows.extras["EF1_used"] == pytest.approx(0.01)
    assert flows.extras["EF1_status"] == "ipcc2006_ef1"
    f_sn, f_on = 500.0, n_mms
    direct_n = (f_sn + f_on + f_cr) * 0.01
    vol_n = (f_sn * 0.10 + f_on * 0.20) * 0.01
    leach_n = (f_sn + f_on + f_cr) * 0.30 * 0.0075
    assert flows.soil_n2o_kg == pytest.approx((direct_n + vol_n + leach_n) * N2ON_TO_N2O)


def test_crop_urea_lime_empty_herd_hand_calc(stylized):
    spec, params = stylized
    farm = _farm(spec, "crop_urea_lime")
    assert farm["herds"] == []
    flows = compute_stylized_farm_flows(spec, farm, params, {}, run="source_correct")
    assert flows.groups == []
    f_cr = 631.968
    assert flows.extras["F_CR"] == pytest.approx(f_cr)
    assert flows.extras["EF1_used"] == pytest.approx(0.01)
    assert flows.extras["EF1_status"] == "ipcc2006_ef1"
    # Eq 11.1: (1000+0+631.968+100)*0.01; vol 1000*0.10*0.01; leach *0.30*0.0075
    n_managed = 1000.0 + f_cr + 100.0
    expected_soil = (n_managed * 0.01 + 1.0 + n_managed * 0.30 * 0.0075) * N2ON_TO_N2O
    lime = (2.0 * 0.12 + 1.0 * 0.13) * 1000.0 * C_TO_CO2
    urea = 1.0 * 0.20 * 1000.0 * C_TO_CO2
    assert flows.soil_n2o_kg == pytest.approx(expected_soil)
    assert flows.lime_co2_kg == pytest.approx(lime)
    assert flows.urea_co2_kg == pytest.approx(urea)
    assert flows.co2e_kg == pytest.approx(flows.n2o_kg * 265.0 + lime + urea)
    assert flows.ch4_kg == pytest.approx(0.0)


def test_beef_pasture_field_uses_ef3prp(stylized):
    spec, params = stylized
    farm = _farm(spec, "beef_pasture_field")
    flows = compute_stylized_farm_flows(spec, farm, params, {}, run="source_correct")
    n_prp = flows.extras["N_PRP_kg"]
    assert n_prp > 0.0
    assert flows.extras["F_PRP_CPP"] == pytest.approx(n_prp)
    assert flows.extras["F_ON"] == pytest.approx(0.0)
    assert flows.n2o_direct_kg == pytest.approx(0.0)
    assert flows.n2o_indirect_kg == pytest.approx(0.0)
    expected_direct = n_prp * 0.02 * N2ON_TO_N2O
    expected_vol = n_prp * 0.20 * 0.01 * N2ON_TO_N2O
    expected_leach = n_prp * 0.30 * 0.0075 * N2ON_TO_N2O
    assert flows.extras["N2O_soil_direct_kg"] == pytest.approx(expected_direct)
    assert flows.extras["N2O_soil_indirect_vol_kg"] == pytest.approx(expected_vol)
    assert flows.extras["N2O_soil_indirect_leach_kg"] == pytest.approx(expected_leach)
    assert flows.soil_n2o_kg == pytest.approx(expected_direct + expected_vol + expected_leach)


def test_turkey_litter_has_no_field(stylized):
    spec, _params = stylized
    turkey = _farm(spec, "turkey_litter")
    assert "field_id" not in turkey
    farm_ids = {farm["id"] for farm in spec["farms"]}
    assert {
        "broiler_litter_field",
        "market_swine_field",
        "beef_pasture_field",
        "crop_urea_lime",
        "turkey_litter",
    } <= farm_ids


def test_latest_stylized_yaml_is_v6():
    path = latest_versioned(ROOT / "data", "stylized_farms", ".yaml")
    assert path.name == "stylized_farms_AN_v6.yaml"
    text = path.read_text(encoding="utf-8")
    assert "P_PE" not in text
    assert "growing_season_precip_mm" not in text


def test_eq_11_6_maize_hand_calc(soil_params):
    """10 ha x 8000 kg/ha maize: Crop=6960; AGDM=6960; AGR=69600; BGR=30624; F_CR=631.968."""
    out = IPCC2019CropResidue().compute(
        {"crop": "maize", "area_ha": 10.0, "yield_fresh_kg_ha": 8000.0},
        soil_params,
    )
    assert out["Crop_kg_ha"] == pytest.approx(6960.0)
    assert out["AGDM_kg_ha"] == pytest.approx(6960.0)
    assert out["AGR_kg"] == pytest.approx(69600.0)
    assert out["BGR_kg"] == pytest.approx(30624.0)
    assert out["F_CR"] == pytest.approx(631.968)
    assert crop_residue_n_process().compute_rate(
        {
            "yield_fresh_kg_ha": 8000.0,
            "DRY": 0.87,
            "R_AG": 1.0,
            "area_ha": 10.0,
            "N_AG": 0.006,
            "FracRemove": 0.0,
            "FracBurnt": 0.0,
            "CF": 0.0,
            "RS": 0.22,
            "FracRenew": 1.0,
            "N_BG": 0.007,
        }
    ) == pytest.approx(631.968)
    assert soil_params["N_AG_maize"] == pytest.approx(0.006)
    assert soil_params["DRY_maize"] == pytest.approx(0.87)


def test_table_11_1a_cells_are_verified(ipcc_params):
    assert ipcc_params.get("IPCC2019.N_AG.maize").status.value == "VERIFIED"
    assert ipcc_params.get("IPCC2019.N_AG.soybeans").value == pytest.approx(0.008)
    assert ipcc_params.get("IPCC2019.RS.spring_wheat").value == pytest.approx(0.28)
    assert ipcc_params.get("IPCC2019.RS.winter_wheat").value == pytest.approx(0.23)
    assert ipcc_params.get("IPCC2019.DRY.grains").value == pytest.approx(0.88)
    traced = load_parameter_csv(latest_versioned(ROOT / "data", "ipcc_params", ".csv"), allow_unverified=True)
    assert traced.get("IPCC2019.kg_per_bu.maize").status.value == "SOURCE-TRACED"


def test_field_n_uses_eq_11_6_when_crops_supplied(soil_params):
    linked = HolosFieldN().compute(
        {
            "N_MMS_Avb_kg": 100.0,
            "crops": [{"crop": "maize", "area_ha": 10.0, "yield_fresh_kg_ha": 8000.0}],
        },
        soil_params,
    )
    assert linked["F_CR"] == pytest.approx(631.968)
    assert linked["F_CR"] != pytest.approx(200.0)


def test_rochette_eq3_is_not_the_holos_coded_ef():
    assert rochette_efeco_process().compute_rate(
        {
            "P_PE": 1.0,
            "EFeco_slope": 0.022,
            "EFeco_intercept": -0.0048,
            "EFeco_min": 0.0016,
            "EFeco_max": 0.017,
        }
    ) == pytest.approx(0.017)


def test_holos_liang2020_ef1_matches_opened_equation(soil_params):
    expected_ct = math.exp(0.00558 * 700.0 - 7.7)
    assert holos_ecodistrict_ef_ct_process().compute_rate(
        {"moisture_mm": 700.0, "EF_CT_slope": 0.00558, "EF_CT_intercept": -7.7}
    ) == pytest.approx(expected_ct)
    humid, status = holos_ecodistrict_ef1(precip_mm=700.0, pe_mm=500.0)
    assert status == "holos_liang2020"
    assert humid == pytest.approx(expected_ct / 0.645)
    dry_no_topo, dry_status = holos_ecodistrict_ef1(precip_mm=400.0, pe_mm=500.0)
    assert dry_status == "UNVERIFIED-input"
    assert dry_no_topo == pytest.approx(0.0)
    ef_p = math.exp(0.00558 * 400.0 - 7.7)
    ef_pe = math.exp(0.00558 * 500.0 - 7.7)
    dry, dry_ok = holos_ecodistrict_ef1(precip_mm=400.0, pe_mm=500.0, fr_topo=0.3)
    assert dry_ok == "holos_liang2020"
    assert dry == pytest.approx((ef_pe * 0.3 + ef_p * 0.7) / 0.645)
    inputs = {
        "F_SN": 1000.0,
        "F_ON": 0.0,
        "F_CR": 0.0,
        "F_SOM": 0.0,
        "F_PRP_CPP": 0.0,
        "climate": "wet",
        "growing_season_precip_mm": 700.0,
        "growing_season_pe_mm": 500.0,
        "forks": {"HOLOS.N2O.ef1": "holos_liang2020"},
    }
    liang = HolosSoilN2O().compute(inputs, soil_params)
    ipcc = HolosSoilN2O().compute({**inputs, "forks": {"HOLOS.N2O.ef1": "ipcc2006_ef1"}}, soil_params)
    missing = HolosSoilN2O().compute(
        {k: v for k, v in inputs.items() if k not in {"growing_season_precip_mm", "growing_season_pe_mm"}},
        soil_params,
    )
    assumed_ratio = HolosSoilN2O().compute(
        {
            "F_SN": 1000.0,
            "F_ON": 0.0,
            "F_CR": 0.0,
            "F_SOM": 0.0,
            "F_PRP_CPP": 0.0,
            "climate": "wet",
            "P_PE": 1.0,
            "forks": {"HOLOS.N2O.ef1": "holos_liang2020"},
        },
        soil_params,
    )
    assert liang["EF1_used"] == pytest.approx(expected_ct / 0.645)
    assert liang["EF1_status"] == "holos_liang2020"
    assert ipcc["EF1_used"] == pytest.approx(0.01)
    assert ipcc["EF1_status"] == "ipcc2006_ef1"
    assert missing["EF1_used"] == pytest.approx(0.01)
    assert missing["EF1_status"] == "UNVERIFIED-input"
    assert assumed_ratio["EF1_used"] == pytest.approx(0.01)
    assert assumed_ratio["EF1_status"] == "UNVERIFIED-input"
    assert liang["N2O_direct"] == pytest.approx(1000.0 * (expected_ct / 0.645) * N2ON_TO_N2O)
    assert ipcc["N2O_direct"] == pytest.approx(1000.0 * 0.01 * N2ON_TO_N2O)


def test_crop_urea_lime_liang2020_needs_climate(stylized):
    spec, params = stylized
    farm = _farm(spec, "crop_urea_lime")
    ipcc = compute_stylized_farm_flows(spec, farm, params, {}, run="source_correct")
    missing = compute_stylized_farm_flows(
        spec, farm, params, {"HOLOS.N2O.ef1": "holos_liang2020"}, run="holos_liang2020"
    )
    assert ipcc.extras["EF1_used"] == pytest.approx(0.01)
    assert missing.extras["EF1_used"] == pytest.approx(0.01)
    assert missing.extras["EF1_status"] == "UNVERIFIED-input"
    assert ipcc.n2o_kg == pytest.approx(missing.n2o_kg)
    assert spec["fields"]["crop_urea_lime"].get("crops")


def _county_inputs(**extra):
    base = {"F_SN": 1000.0, "F_ON": 0.0, "F_CR": 0.0, "F_SOM": 0.0, "F_PRP_CPP": 0.0,
            "climate": "wet", "forks": {"HOLOS.N2O.ef1": "holos_liang2020"}}
    base.update(extra)
    return base


def test_county_fips_lookup_fills_p_pe(soil_params):
    from ghgsim.modules.holos.county_climate import county_p_pe
    cc = county_p_pe("15001")  # Hawaii County HI, P > PE (no FR_Topo needed)
    assert cc["pe_method"] == "hargreaves_samani_1985" and cc["period"] == "1991-2020"
    out = HolosSoilN2O().compute(_county_inputs(county_fips="15001"), soil_params)
    ef, st = holos_ecodistrict_ef1(precip_mm=cc["growing_season_precip_mm"], pe_mm=cc["growing_season_pe_mm"])
    assert st == "holos_liang2020" and out["EF1_status"] == "holos_liang2020"
    assert out["EF1_used"] == pytest.approx(ef)


def test_county_fips_explicit_inputs_win(soil_params):
    explicit = HolosSoilN2O().compute(
        _county_inputs(county_fips="15001", growing_season_precip_mm=700.0, growing_season_pe_mm=500.0), soil_params)
    plain = HolosSoilN2O().compute(
        _county_inputs(growing_season_precip_mm=700.0, growing_season_pe_mm=500.0), soil_params)
    assert explicit["EF1_used"] == pytest.approx(plain["EF1_used"])


def test_county_fips_unknown_or_ipcc_unchanged(soil_params):
    unknown = HolosSoilN2O().compute(_county_inputs(county_fips="99999"), soil_params)
    assert unknown["EF1_status"] == "UNVERIFIED-input" and unknown["EF1_used"] == pytest.approx(0.01)
    ipcc = HolosSoilN2O().compute(_county_inputs(county_fips="15001", forks={"HOLOS.N2O.ef1": "ipcc2006_ef1"}), soil_params)
    assert ipcc["EF1_status"] == "ipcc2006_ef1"


def test_county_fips_dry_needs_fr_topo(soil_params):
    from ghgsim.modules.holos.county_climate import county_p_pe
    cc = county_p_pe(50007)  # Chittenden VT, int FIPS accepted; P < PE
    assert cc["growing_season_precip_mm"] < cc["growing_season_pe_mm"]
    out = HolosSoilN2O().compute(_county_inputs(county_fips="50007"), soil_params)
    assert out["EF1_status"] == "fallback-IPCC-default"
    assert out["EF1_used"] == pytest.approx(soil_params["EF1"])
    ok = HolosSoilN2O().compute(_county_inputs(county_fips="50007", FR_Topo=0.1), soil_params)
    assert ok["EF1_status"] == "holos_liang2020"


def test_county_fips_dc_remapped():
    from ghgsim.modules.holos.county_climate import county_p_pe
    assert county_p_pe("11001") is not None and county_p_pe("24511") is None


def test_liang_dry_no_topo_falls_back_to_ipcc_default(soil_params):
    dry = _county_inputs(growing_season_precip_mm=400.0, growing_season_pe_mm=500.0)
    out = HolosSoilN2O().compute(dry, soil_params)
    assert out["EF1_status"] == "fallback-IPCC-default"
    assert out["EF1_used"] == pytest.approx(0.01)  # IPCC 2006 Table 11.1 EF1
    assert out["N2O_direct"] == pytest.approx(1000.0 * 0.01 * 44.0 / 28.0)


def test_liang_fallback_not_used_when_topo_irrigated_or_missing(soil_params):
    dry = _county_inputs(growing_season_precip_mm=400.0, growing_season_pe_mm=500.0)
    assert HolosSoilN2O().compute({**dry, "FR_Topo": 0.3}, soil_params)["EF1_status"] == "holos_liang2020"
    assert HolosSoilN2O().compute({**dry, "irrigation_mm": 100.0}, soil_params)["EF1_status"] == "holos_liang2020"
    missing = HolosSoilN2O().compute(_county_inputs(), soil_params)
    assert missing["EF1_status"] == "UNVERIFIED-input"
    zero_pe = HolosSoilN2O().compute(_county_inputs(growing_season_precip_mm=400.0, growing_season_pe_mm=0.0), soil_params)
    assert zero_pe["EF1_status"] == "UNVERIFIED-input"
