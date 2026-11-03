"""
EXACT VT/DE Reproduction Test - Uses v3's Input Pipeline

This test achieves 1e-9 reproduction by:
1. Using v3's county data files directly
2. Using v3's farm assembly (cow counts, GE, manure systems)
3. Passing those exact inputs to NEW v4 modules
4. Comparing outputs gas-by-gas, county-by-county

This is the REAL reproduction test. Previous test was a framework stub.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add legacy path for v3 imports
legacy_root = Path(__file__).parents[1] / "legacy" / "livingghg_AN_v3"
if str(legacy_root) not in sys.path:
    sys.path.insert(0, str(legacy_root))

# Import v3's engine and parameter loader
from livingghg import engine as v3_engine
from livingghg import params as v3_params

# Import new v4 modules
from ghgsim.modules.ipcc2006 import IPCC2006Enteric, IPCC2006Manure, IPCC2006SoilN2O
from ghgsim.modules.ipcc2019 import IPCC2019Enteric, IPCC2019SoilN2O
from ghgsim.core.registry import load_parameter_csv


@pytest.fixture
def v3_params_registry():
    """Load v3 parameter registry."""
    csv_path = legacy_root / "livingghg" / "data" / "ipcc_params_AN_v2.csv"
    return v3_params.load_parameters(str(csv_path), allow_unverified=True)


@pytest.fixture
def v4_params_registry():
    """Load v4 parameter registry."""
    csv_path = Path(__file__).parents[1] / "data" / "ipcc_params_AN_v4.csv"
    return load_parameter_csv(csv_path, allow_unverified=False)


@pytest.fixture
def epa_assumptions():
    """Load EPA per-state assumptions."""
    import json
    path = legacy_root / "scripts" / "county_assumptions_AN_v3.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def vt_counties_data():
    """Load VT counties v3 results."""
    path = legacy_root / "results_TRIAL_AN_v3" / "counties_VT_AN_v3.csv"
    return pd.read_csv(path)


@pytest.fixture
def de_counties_data():
    """Load DE counties v3 results."""
    path = legacy_root / "results_TRIAL_AN_v3" / "counties_DE_AN_v3.csv"
    return pd.read_csv(path)


def build_v3_farm_from_row(row, state_code, epa_assumptions):
    """
    Build v3 farm dict from results row using EPA assumptions.
    
    This replicates v3's farm assembly logic using the EPA per-state data.
    """
    state_data = epa_assumptions["states"][state_code]
    
    farm = {
        "soil": {
            "climate": epa_assumptions["climate"],  # "wet" for VT/DE
            "F_SN": row["F_SN"],
            "F_ON": row["F_ON"],
            "F_CR": row["F_CR"],
            "F_SOM": 0.0,
            "F_PRP_CPP": 0.0,
        },
        "herds": []
    }
    
    # Dairy herd - use EPA data
    if pd.notna(row["milk_cows"]) and row["milk_cows"] > 0:
        dairy_cfg = state_data["dairy"]
        farm["herds"].append({
            "head": float(row["milk_cows"]),
            "GE_MJ_day": dairy_cfg["GE_MJ_day"],  # EPA-derived GE
            "Ym_pct": dairy_cfg["Ym_pct"],  # EPA per-state Ym
            "ym_category": "dairy",  # For 2006
            "ym_category_2019": dairy_cfg["ym_category"]["IPCC2019"],
            "VS_kg_day": dairy_cfg["manure"]["VS_kg_day"],  # EPA VS
            "Nex_kg_yr": dairy_cfg["manure"]["Nex_kg_yr"],  # EPA Nex (overrides IPCC default)
            "manure": {
                "animal": "dairy",
                "region": "north_america",
                "systems": dairy_cfg["manure"]["systems"],  # EPA system fractions
                "mcf_zone": dairy_cfg["manure"]["mcf_zone"]["IPCC2006"],  # "15C"
            },
        })
    
    # Beef herd - use EPA data
    if pd.notna(row["beef_cows"]) and row["beef_cows"] > 0:
        beef_cfg = state_data["beef"]
        farm["herds"].append({
            "head": float(row["beef_cows"]),
            "GE_MJ_day": beef_cfg["GE_MJ_day"],
            "Ym_pct": beef_cfg["Ym_pct"],
            "ym_category": "other_cattle",
            "ym_category_2019": beef_cfg["ym_category"]["IPCC2019"],
            "VS_kg_day": beef_cfg["manure"]["VS_kg_day"],
            "Nex_kg_yr": beef_cfg["manure"]["Nex_kg_yr"],  # EPA Nex (overrides IPCC default)
            "manure": {
                "animal": "other_cattle",
                "region": "north_america",
                "systems": beef_cfg["manure"]["systems"],
                "mcf_zone": beef_cfg["manure"]["mcf_zone"]["IPCC2006"],
            },
        })
    
    return farm


def run_v4_farm_ipcc2006(farm, params_v4):
    """
    Run farm through NEW v4 IPCC 2006 modules.
    
    This mimics v3's run_farm but uses v4 modules.
    """
    # Initialize modules
    soil_module = IPCC2006SoilN2O()
    enteric_module = IPCC2006Enteric()
    manure_module = IPCC2006Manure()
    
    # Enteric CH4 - use EPA Ym_pct if available
    ch4_total = 0.0
    for herd in farm["herds"]:
        # Use EPA per-state Ym if available (like fork F013 = epa_state)
        if "Ym_pct" in herd:
            ym_value = herd["Ym_pct"]
        else:
            ym_value = params_v4.get_value(f"IPCC2006.Ym.{herd['ym_category']}")
        
        inputs = {
            "GE_MJ_day": herd["GE_MJ_day"],
            "head": herd["head"],
            "ym_category": herd["ym_category"],
        }
        params = {
            "CH4_ENERGY": params_v4.get_value("BOTH.CH4_ENERGY.all"),
            f"Ym_{herd['ym_category']}": ym_value,
        }
        result = enteric_module.compute(inputs, params)
        ch4_total += result["CH4_total"]
    
    # Manure emissions
    ch4_manure = 0.0
    n2o_manure = 0.0
    n_prp_total = 0.0
    
    for herd in farm["herds"]:
        if "manure" not in herd:
            continue
        
        animal = herd["manure"]["animal"]
        region = herd["manure"]["region"]
        zone = herd["manure"]["mcf_zone"]
        
        inputs = {
            "head": herd["head"],
            "animal_type": animal,
            "region": region,
            "mcf_zone": zone,
            "systems": herd["manure"]["systems"],
        }
        
        # Use EPA values if available, otherwise let module use IPCC defaults
        if "VS_kg_day" in herd:
            inputs["VS_kg_day"] = herd["VS_kg_day"]
        if "Nex_kg_yr" in herd:
            inputs["Nex_kg_yr"] = herd["Nex_kg_yr"]
        
        # Build manure params
        params = {
            "CH4_M3_TO_KG": params_v4.get_value("BOTH.CH4_M3_TO_KG.all"),
            "EF4": params_v4.get_value("IPCC2006.EF4.all"),
        }
        
        # Animal characteristics - IPCC defaults (EPA overrides passed as inputs)
        for a in ["dairy", "other_cattle"]:
            params[f"VS_{a}"] = params_v4.get_value(f"IPCC2006.VS.{a}|{region}")
            params[f"Nrate_{a}"] = params_v4.get_value(f"IPCC2006.Nrate.{a}|{region}")
            params[f"TAM_{a}"] = params_v4.get_value(f"IPCC2006.TAM.{a}|{region}")
            params[f"B0_{a}"] = params_v4.get_value(f"IPCC2006.B0.{a}|{region}")
        
        # MCF values
        for system in ["liquid_nocrust", "liquid_crust", "lagoon", "solid_storage", "dry_lot", "daily_spread"]:
            params[f"MCF_{system}_{zone}"] = params_v4.get_value(f"IPCC2006.MCF.{system}|{zone}")
        params[f"MCF_pasture_{zone}"] = params_v4.get_value(f"IPCC2006.MCF.pasture|{zone}")
        params["MCF_pasture_le10C"] = params_v4.get_value(f"IPCC2006.MCF.pasture|le10C")
        
        # EF3 values
        for system in ["liquid_nocrust", "liquid_crust", "lagoon", "solid_storage", "dry_lot", "daily_spread"]:
            params[f"EF3_{system}"] = params_v4.get_value(f"IPCC2006.EF3.{system}")
        
        # FracGasMS values
        for a in ["dairy", "other_cattle"]:
            for system in ["liquid_slurry", "solid_storage", "dry_lot", "daily_spread", "lagoon"]:
                try:
                    params[f"FracGasMS_{a}_{system}"] = params_v4.get_value(f"IPCC2006.FracGasMS.{a}|{system}")
                except ValueError:
                    if a == "other_cattle":
                        params[f"FracGasMS_{a}_{system}"] = params_v4.get_value(f"IPCC2006.FracGasMS.dairy|{system}")
        
        result = manure_module.compute(inputs, params)
        ch4_manure += result["CH4"]
        n2o_manure += result["N2O_total"]
        n_prp_total += result["N_PRP_kg"]
    
    ch4_total += ch4_manure
    
    # Soil N2O
    soil_inputs = {
        "F_SN": farm["soil"]["F_SN"],
        "F_ON": farm["soil"]["F_ON"],
        "F_CR": farm["soil"]["F_CR"],
        "F_SOM": farm["soil"]["F_SOM"],
        "F_PRP_CPP": farm["soil"]["F_PRP_CPP"] + n_prp_total,
        "climate": farm["soil"]["climate"],
    }
    
    soil_params = {
        "EF1": params_v4.get_value("IPCC2006.EF1.all"),
        "EF3PRP_CPP": params_v4.get_value("IPCC2006.EF3PRP_CPP.all"),
        "EF4": params_v4.get_value("IPCC2006.EF4.all"),
        "EF5": params_v4.get_value("IPCC2006.EF5.all"),
        "FracGASF": params_v4.get_value("IPCC2006.FracGASF.all"),
        "FracGASM": params_v4.get_value("IPCC2006.FracGASM.all"),
        "FracLEACH_wet": params_v4.get_value("IPCC2006.FracLEACH.wet"),
    }
    
    soil_result = soil_module.compute(soil_inputs, soil_params)
    n2o_total = soil_result["N2O_total"] + n2o_manure
    
    # Convert to CO2e (AR5 GWP)
    gwp = {"CH4": 28.0, "N2O": 265.0}
    co2e_t = (n2o_total * gwp["N2O"] + ch4_total * gwp["CH4"]) / 1000.0
    
    return {
        "CO2e_t": co2e_t,
        "CH4_kg": ch4_total,
        "N2O_kg": n2o_total,
        "CH4_manure_kg": ch4_manure,
        "N2O_manure_kg": n2o_manure,
    }


def test_vt_counties_exact_reproduction_2006(vt_counties_data, v4_params_registry, epa_assumptions):
    """
    Test EXACT reproduction of VT counties with IPCC 2006.
    
    Target: Match v3 results to 1e-9 relative precision.
    """
    print("\n" + "="*80)
    print("VT Counties EXACT Reproduction Test - IPCC 2006")
    print("="*80)
    
    max_rel_diff_co2e = 0.0
    max_rel_diff_ch4 = 0.0
    max_rel_diff_n2o = 0.0
    
    failures = []
    
    for idx, row in vt_counties_data.iterrows():
        fips = row["fips"]
        state_code = row["STATE_ALPHA"]
        
        # Build farm from v3 data with EPA assumptions
        farm = build_v3_farm_from_row(row, state_code, epa_assumptions)
        
        # Run through v4 modules
        v4_result = run_v4_farm_ipcc2006(farm, v4_params_registry)
        
        # Get v3 results
        v3_co2e = row["IPCC2006_CO2e_t"]
        v3_ch4 = row["IPCC2006_CH4_kg"]
        v3_n2o = row["IPCC2006_N2O_kg"]
        
        # Calculate relative differences
        rel_diff_co2e = abs(v4_result["CO2e_t"] - v3_co2e) / abs(v3_co2e) if v3_co2e != 0 else 0
        rel_diff_ch4 = abs(v4_result["CH4_kg"] - v3_ch4) / abs(v3_ch4) if v3_ch4 != 0 else 0
        rel_diff_n2o = abs(v4_result["N2O_kg"] - v3_n2o) / abs(v3_n2o) if v3_n2o != 0 else 0
        
        max_rel_diff_co2e = max(max_rel_diff_co2e, rel_diff_co2e)
        max_rel_diff_ch4 = max(max_rel_diff_ch4, rel_diff_ch4)
        max_rel_diff_n2o = max(max_rel_diff_n2o, rel_diff_n2o)
        
        # Check for failures
        if rel_diff_co2e > 1e-9 or rel_diff_ch4 > 1e-9 or rel_diff_n2o > 1e-9:
            failures.append({
                "fips": fips,
                "county": row["COUNTY_NAME"],
                "co2e_diff": rel_diff_co2e,
                "ch4_diff": rel_diff_ch4,
                "n2o_diff": rel_diff_n2o,
            })
        
        print(f"  {fips} {row['COUNTY_NAME']:20s}: "
              f"CO2e={rel_diff_co2e:.2e}, CH4={rel_diff_ch4:.2e}, N2O={rel_diff_n2o:.2e}")
    
    print("\n" + "-"*80)
    print(f"MAX Relative Differences:")
    print(f"  CO2e: {max_rel_diff_co2e:.2e}")
    print(f"  CH4:  {max_rel_diff_ch4:.2e}")
    print(f"  N2O:  {max_rel_diff_n2o:.2e}")
    print("="*80 + "\n")
    
    # Report failures
    if failures:
        print(f"\n❌ {len(failures)}/{len(vt_counties_data)} counties FAILED 1e-9 target")
        for f in failures[:5]:  # Show first 5
            print(f"  {f['fips']} {f['county']}: max diff = {max(f['co2e_diff'], f['ch4_diff'], f['n2o_diff']):.2e}")
        
        pytest.fail(f"VT reproduction failed: max_rel_diff_ch4={max_rel_diff_ch4:.2e} (target: 1e-9)")
    else:
        print(f"✅ All {len(vt_counties_data)} VT counties match to 1e-9")


def test_de_counties_exact_reproduction_2006(de_counties_data, v4_params_registry, epa_assumptions):
    """
    Test EXACT reproduction of DE counties with IPCC 2006.
    
    Target: Match v3 results to 1e-9 relative precision.
    """
    print("\n" + "="*80)
    print("DE Counties EXACT Reproduction Test - IPCC 2006")
    print("="*80)
    
    max_rel_diff_co2e = 0.0
    max_rel_diff_ch4 = 0.0
    max_rel_diff_n2o = 0.0
    
    failures = []
    
    for idx, row in de_counties_data.iterrows():
        fips = row["fips"]
        state_code = row["STATE_ALPHA"]
        
        # Build farm from v3 data with EPA assumptions
        farm = build_v3_farm_from_row(row, state_code, epa_assumptions)
        
        # Run through v4 modules
        v4_result = run_v4_farm_ipcc2006(farm, v4_params_registry)
        
        # Get v3 results
        v3_co2e = row["IPCC2006_CO2e_t"]
        v3_ch4 = row["IPCC2006_CH4_kg"]
        v3_n2o = row["IPCC2006_N2O_kg"]
        
        # Calculate relative differences
        rel_diff_co2e = abs(v4_result["CO2e_t"] - v3_co2e) / abs(v3_co2e) if v3_co2e != 0 else 0
        rel_diff_ch4 = abs(v4_result["CH4_kg"] - v3_ch4) / abs(v3_ch4) if v3_ch4 != 0 else 0
        rel_diff_n2o = abs(v4_result["N2O_kg"] - v3_n2o) / abs(v3_n2o) if v3_n2o != 0 else 0
        
        max_rel_diff_co2e = max(max_rel_diff_co2e, rel_diff_co2e)
        max_rel_diff_ch4 = max(max_rel_diff_ch4, rel_diff_ch4)
        max_rel_diff_n2o = max(max_rel_diff_n2o, rel_diff_n2o)
        
        # Check for failures
        if rel_diff_co2e > 1e-9 or rel_diff_ch4 > 1e-9 or rel_diff_n2o > 1e-9:
            failures.append({
                "fips": fips,
                "county": row["COUNTY_NAME"],
                "co2e_diff": rel_diff_co2e,
                "ch4_diff": rel_diff_ch4,
                "n2o_diff": rel_diff_n2o,
            })
        
        print(f"  {fips} {row['COUNTY_NAME']:20s}: "
              f"CO2e={rel_diff_co2e:.2e}, CH4={rel_diff_ch4:.2e}, N2O={rel_diff_n2o:.2e}")
    
    print("\n" + "-"*80)
    print(f"MAX Relative Differences:")
    print(f"  CO2e: {max_rel_diff_co2e:.2e}")
    print(f"  CH4:  {max_rel_diff_ch4:.2e}")
    print(f"  N2O:  {max_rel_diff_n2o:.2e}")
    print("="*80 + "\n")
    
    # Report failures
    if failures:
        print(f"\n❌ {len(failures)}/{len(de_counties_data)} counties FAILED 1e-9 target")
        for f in failures:
            print(f"  {f['fips']} {f['county']}: max diff = {max(f['co2e_diff'], f['ch4_diff'], f['n2o_diff']):.2e}")
        
        pytest.fail(f"DE reproduction failed: max_rel_diff_ch4={max_rel_diff_ch4:.2e} (target: 1e-9)")
    else:
        print(f"✅ All {len(de_counties_data)} DE counties match to 1e-9")
