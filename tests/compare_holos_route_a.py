"""
Compare IPCC 2006/2019 vs Holos Route A on VT/DE counties.

Runs all three approaches side-by-side to evaluate differences.
"""

import sys
from pathlib import Path

import pandas as pd

# Add paths
sys.path.insert(0, str(Path(__file__).parents[1]))
legacy_root = Path(__file__).parents[1] / "legacy" / "livingghg_AN_v3"
sys.path.insert(0, str(legacy_root))

from ghgsim.core.registry import load_parameter_csv  # noqa: E402
from ghgsim.modules.holos import HolosEnteric, HolosManure, HolosSoilN2O  # noqa: E402


def load_epa_assumptions():
    """Load EPA per-state assumptions."""
    import json
    path = legacy_root / "scripts" / "county_assumptions_AN_v3.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_holos_us_county(row, state_code, epa_assumptions, params_holos_us, params_ipcc):
    """Run Holos US config on one county using EPA per-state values."""
    state_data = epa_assumptions["states"][state_code]
    
    # Enteric CH4
    ch4_total = 0.0
    n2o_manure = 0.0
    n_prp_total = 0.0
    
    enteric_module = HolosEnteric()
    manure_module = HolosManure()
    
    # Dairy
    if pd.notna(row["milk_cows"]) and row["milk_cows"] > 0:
        # Get state-specific params
        ge_key = f"HOLOS.GE.dairy|{state_code}"
        ym_key = f"HOLOS.Ym.dairy|{state_code}"
        
        try:
            ge_val = params_holos_us.get_value(ge_key)
        except (ValueError, KeyError):
            ge_val = None
        
        try:
            ym_val = params_holos_us.get_value(ym_key)
        except (ValueError, KeyError):
            ym_val = 6.5
        
        enteric_inputs = {
            "head": float(row["milk_cows"]),
            "animal_type": "dairy",
            "GE_MJ_day": ge_val,
        }
        enteric_params = {
            "GE_dairy_canada": 380.0,  # Fallback (not used if GE_MJ_day provided)
            "Ym_dairy_canada": ym_val,
            "CH4_ENERGY": params_ipcc.get_value("BOTH.CH4_ENERGY.all"),
        }
        ch4_result = enteric_module.compute(enteric_inputs, enteric_params)
        ch4_total += ch4_result["CH4_total"]
        
        # Manure
        manure_inputs = {
            "head": float(row["milk_cows"]),
            "animal_type": "dairy",
            "region": "canada",  # Using config
            "climate_zone": "temperate",  # US northeast
            "systems": state_data["dairy"]["manure"]["systems"],
        }
        manure_params = {
            "VS_dairy_canada": params_holos_us.get_value(f"HOLOS.VS.dairy|{state_code}") if f"HOLOS.VS.dairy|{state_code}" in params_holos_us._data else 5.65,
            "Nrate_dairy_canada": params_holos_us.get_value(f"HOLOS.Nrate.dairy|{state_code}") if f"HOLOS.Nrate.dairy|{state_code}" in params_holos_us._data else 0.47,
            "TAM_dairy_canada": params_holos_us.get_value(f"HOLOS.TAM.dairy|{state_code}") if f"HOLOS.TAM.dairy|{state_code}" in params_holos_us._data else 565.0,
            "B0_dairy_canada": params_holos_us.get_value(f"HOLOS.B0.dairy|{state_code}") if f"HOLOS.B0.dairy|{state_code}" in params_holos_us._data else 0.24,
            "VS_beef_canada": 4.0,  # Fallback
            "Nrate_beef_canada": 0.31,
            "TAM_beef_canada": 388.0,
            "B0_beef_canada": 0.17,
            "MCF_liquid_nocrust_temperate": params_holos_us.get_value("HOLOS.MCF.liquid_nocrust|US"),
            "MCF_solid_storage_temperate": params_holos_us.get_value("HOLOS.MCF.solid_storage|US"),
            "MCF_pasture_cool": params_holos_us.get_value("HOLOS.MCF.pasture|US"),
            "MCF_daily_spread_cool": params_holos_us.get_value("HOLOS.MCF.daily_spread|US"),
            "EF3_liquid_nocrust": params_ipcc.get_value("IPCC2006.EF3.liquid_nocrust"),
            "EF3_solid_storage": params_ipcc.get_value("IPCC2006.EF3.solid_storage"),
            "EF3_daily_spread": params_ipcc.get_value("IPCC2006.EF3.daily_spread"),
            "EF4": params_ipcc.get_value("IPCC2006.EF4.all"),
            "FracGasMS_dairy_liquid_slurry": params_ipcc.get_value("IPCC2006.FracGasMS.dairy|liquid_slurry"),
            "FracGasMS_dairy_solid_storage": params_ipcc.get_value("IPCC2006.FracGasMS.dairy|solid_storage"),
            "FracGasMS_dairy_daily_spread": params_ipcc.get_value("IPCC2006.FracGasMS.dairy|daily_spread"),
            "CH4_M3_TO_KG": params_ipcc.get_value("BOTH.CH4_M3_TO_KG.all"),
        }
        manure_result = manure_module.compute(manure_inputs, manure_params)
        ch4_total += manure_result["CH4"]
        n2o_manure += manure_result["N2O_total"]
        n_prp_total += manure_result["N_PRP_kg"]
    
    # Beef (similar structure)
    if pd.notna(row["beef_cows"]) and row["beef_cows"] > 0:
        ge_key = f"HOLOS.GE.beef|{state_code}"
        ym_key = f"HOLOS.Ym.beef|{state_code}"
        
        enteric_inputs = {
            "head": float(row["beef_cows"]),
            "animal_type": "beef",
            "GE_MJ_day": params_holos_us.get_value(ge_key) if ge_key in params_holos_us._data else None,
        }
        enteric_params = {
            "GE_beef_medium": 200.0,
            "Ym_beef_medium": params_holos_us.get_value(ym_key) if ym_key in params_holos_us._data else 6.5,
            "CH4_ENERGY": params_ipcc.get_value("BOTH.CH4_ENERGY.all"),
        }
        ch4_result = enteric_module.compute(enteric_inputs, enteric_params)
        ch4_total += ch4_result["CH4_total"]
    
    # Soil N2O
    soil_module = HolosSoilN2O()
    soil_inputs = {
        "F_SN": float(row["F_SN"]),
        "F_ON": float(row["F_ON"]),
        "F_CR": float(row["F_CR"]),
        "F_SOM": 0.0,
        "F_PRP_CPP": n_prp_total,
        "climate": "wet",
    }
    soil_params = {
        "EF1": params_ipcc.get_value("IPCC2006.EF1.all"),
        "EF3PRP_CPP": params_ipcc.get_value("IPCC2006.EF3PRP_CPP.all"),
        "EF4": params_ipcc.get_value("IPCC2006.EF4.all"),
        "EF5": params_ipcc.get_value("IPCC2006.EF5.all"),
        "FracGASF": params_ipcc.get_value("IPCC2006.FracGASF.all"),
        "FracGASM": params_ipcc.get_value("IPCC2006.FracGASM.all"),
        "FracLEACH_wet": params_ipcc.get_value("IPCC2006.FracLEACH.wet"),
        "FracLEACH_dry": 0.1,  # Fallback
    }
    soil_result = soil_module.compute(soil_inputs, soil_params)
    n2o_total = n2o_manure + soil_result["N2O_total"]
    
    # Convert to CO2e (AR5 GWP)
    co2e_t = (n2o_total * 265.0 + ch4_total * 28.0) / 1000.0
    
    return {
        "CO2e_t": co2e_t,
        "CH4_kg": ch4_total,
        "N2O_kg": n2o_total,
    }


def main():
    print("=" * 80)
    print("Holos Route A Comparison: IPCC 2006/2019 vs Holos US")
    print("=" * 80)
    
    # Load parameters
    params_ipcc = load_parameter_csv(Path("data/ipcc_params_AN_v4.csv"))
    params_holos_us = load_parameter_csv(Path("data/holos_params_us_AN_v1.csv"), allow_unverified=False)
    
    # Load county data
    vt_results = pd.read_csv(legacy_root / "results_TRIAL_AN_v3" / "counties_VT_AN_v3.csv")
    de_results = pd.read_csv(legacy_root / "results_TRIAL_AN_v3" / "counties_DE_AN_v3.csv")
    
    epa = load_epa_assumptions()
    
    results = []
    
    # Process VT counties
    for _, row in vt_results.iterrows():
        holos_result = run_holos_us_county(row, "VT", epa, params_holos_us, params_ipcc)
        results.append({
            "fips": row["fips"],
            "state": "VT",
            "county": row["COUNTY_NAME"],
            "IPCC2006_CO2e_t": row["IPCC2006_CO2e_t"],
            "IPCC2006_CH4_kg": row["IPCC2006_CH4_kg"],
            "IPCC2006_N2O_kg": row["IPCC2006_N2O_kg"],
            "HolosUS_CO2e_t": holos_result["CO2e_t"],
            "HolosUS_CH4_kg": holos_result["CH4_kg"],
            "HolosUS_N2O_kg": holos_result["N2O_kg"],
        })
    
    # Process DE counties
    for _, row in de_results.iterrows():
        holos_result = run_holos_us_county(row, "DE", epa, params_holos_us, params_ipcc)
        results.append({
            "fips": row["fips"],
            "state": "DE",
            "county": row["COUNTY_NAME"],
            "IPCC2006_CO2e_t": row["IPCC2006_CO2e_t"],
            "IPCC2006_CH4_kg": row["IPCC2006_CH4_kg"],
            "IPCC2006_N2O_kg": row["IPCC2006_N2O_kg"],
            "HolosUS_CO2e_t": holos_result["CO2e_t"],
            "HolosUS_CH4_kg": holos_result["CH4_kg"],
            "HolosUS_N2O_kg": holos_result["N2O_kg"],
        })
    
    df = pd.DataFrame(results)
    
    # Calculate differences
    df["diff_CO2e_pct"] = ((df["HolosUS_CO2e_t"] - df["IPCC2006_CO2e_t"]) / df["IPCC2006_CO2e_t"] * 100)
    df["diff_CH4_pct"] = ((df["HolosUS_CH4_kg"] - df["IPCC2006_CH4_kg"]) / df["IPCC2006_CH4_kg"] * 100)
    df["diff_N2O_pct"] = ((df["HolosUS_N2O_kg"] - df["IPCC2006_N2O_kg"]) / df["IPCC2006_N2O_kg"] * 100)
    
    # Save results
    df.to_csv("tests/holos_comparison_vt_de_AN_v1.csv", index=False)
    
    # Print summary
    print("\nSummary Statistics:")
    print(f"  Counties processed: {len(df)}")
    print(f"  VT: {len(df[df['state'] == 'VT'])}, DE: {len(df[df['state'] == 'DE'])}")
    print()
    print("Holos US vs IPCC 2006:")
    print(f"  CO2e diff: mean={df['diff_CO2e_pct'].mean():.2f}%, max={df['diff_CO2e_pct'].abs().max():.2f}%")
    print(f"  CH4 diff:  mean={df['diff_CH4_pct'].mean():.2f}%, max={df['diff_CH4_pct'].abs().max():.2f}%")
    print(f"  N2O diff:  mean={df['diff_N2O_pct'].mean():.2f}%, max={df['diff_N2O_pct'].abs().max():.2f}%")
    print()
    print("Results saved to: tests/holos_comparison_vt_de_AN_v1.csv")
    
    return df


if __name__ == "__main__":
    main()
