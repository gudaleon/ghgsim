"""
Holos (Canada) manure management emissions.

Re-implemented from published sources. Implementation is independent, based 
solely on published equations.

Sources:
- Little et al. (2008). Holos v1.1.x Methodology. AAFC.
- IPCC 2006 Guidelines Volume 4 Chapter 10 (Equations 10.23, 10.25-10.29)
- Coates et al. (2020). Canadian dairy farms can reduce greenhouse gas emissions.
  J Dairy Sci. 103(4): 3383-3395. DOI: 10.3168/jds.2019-17361

Holos follows IPCC 2006 manure management methodology with Canadian-specific
MCF values for Canadian climate zones and manure system distributions.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, Module, ParamRef, VarSpec

# Molecular weight conversion
N2ON_TO_N2O = 44.0 / 28.0

# Manure system mappings (same as IPCC 2006)
SYSTEM_MAP = {
    "liquid_nocrust": ("liquid_nocrust", "liquid_nocrust", "liquid_slurry"),
    "liquid_crust": ("liquid_crust", "liquid_crust", "liquid_slurry"),
    "lagoon": ("lagoon", "lagoon", "lagoon"),
    "solid_storage": ("solid_storage", "solid_storage", "solid_storage"),
    "dry_lot": ("dry_lot", "dry_lot", "dry_lot"),
    "daily_spread": ("daily_spread", "daily_spread", "daily_spread"),
    "pasture": ("pasture", None, None),
}


class HolosManure:
    """
    Holos manure management CH4 and N2O emissions.
    
    Uses IPCC 2006 methodology (Equations 10.23, 10.25-10.29) with 
    Canadian-specific MCF values for Canadian climate conditions.
    """

    id = "holos.manure"
    version = "1.0.0"

    inputs = {
        "head": VarSpec("head", "dimensionless", "Number of animals", "scalar", True),
        "animal_type": VarSpec("animal_type", "dimensionless", "Animal type (dairy/beef)", "scalar", True),
        "region": VarSpec("region", "dimensionless", "Region (canada/north_america)", "scalar", True),
        "climate_zone": VarSpec("climate_zone", "dimensionless", "Canadian climate zone (cool/temperate)", "scalar", True),
        "systems": VarSpec("systems", "dimensionless", "Dict of system -> fraction", "scalar", True),
    }

    parameters = {
        # Animal characteristics (Canadian defaults from Holos)
        "VS_dairy_canada": ParamRef("HOLOS.VS.dairy|canada", "VS for Canadian dairy"),
        "VS_beef_canada": ParamRef("HOLOS.VS.beef|canada", "VS for Canadian beef"),
        "Nrate_dairy_canada": ParamRef("HOLOS.Nrate.dairy|canada", "N rate for Canadian dairy"),
        "Nrate_beef_canada": ParamRef("HOLOS.Nrate.beef|canada", "N rate for Canadian beef"),
        "TAM_dairy_canada": ParamRef("HOLOS.TAM.dairy|canada", "TAM for Canadian dairy"),
        "TAM_beef_canada": ParamRef("HOLOS.TAM.beef|canada", "TAM for Canadian beef"),
        "B0_dairy_canada": ParamRef("HOLOS.B0.dairy|canada", "B0 for Canadian dairy"),
        "B0_beef_canada": ParamRef("HOLOS.B0.beef|canada", "B0 for Canadian beef"),
        
        # MCF for Canadian climate zones (cool = 5-10°C, temperate = 10-15°C)
        "MCF_liquid_nocrust_cool": ParamRef("HOLOS.MCF.liquid_nocrust|cool", "MCF liquid no crust, cool"),
        "MCF_liquid_nocrust_temperate": ParamRef("HOLOS.MCF.liquid_nocrust|temperate", "MCF liquid no crust, temperate"),
        "MCF_solid_storage_cool": ParamRef("HOLOS.MCF.solid_storage|cool", "MCF solid storage, cool"),
        "MCF_solid_storage_temperate": ParamRef("HOLOS.MCF.solid_storage|temperate", "MCF solid storage, temperate"),
        "MCF_pasture_cool": ParamRef("HOLOS.MCF.pasture|cool", "MCF pasture, cool"),
        "MCF_daily_spread_cool": ParamRef("HOLOS.MCF.daily_spread|cool", "MCF daily spread, cool"),
        
        # EF3 and volatilization (uses IPCC 2006 defaults)
        "EF3_liquid_nocrust": ParamRef("IPCC2006.EF3.liquid_nocrust", "EF3 for liquid no crust"),
        "EF3_solid_storage": ParamRef("IPCC2006.EF3.solid_storage", "EF3 for solid storage"),
        "EF3_daily_spread": ParamRef("IPCC2006.EF3.daily_spread", "EF3 for daily spread"),
        "EF4": ParamRef("IPCC2006.EF4.all", "EF4 for volatilization"),
        "FracGasMS_dairy_liquid_slurry": ParamRef("IPCC2006.FracGasMS.dairy|liquid_slurry", "FracGasMS dairy liquid"),
        "FracGasMS_dairy_solid_storage": ParamRef("IPCC2006.FracGasMS.dairy|solid_storage", "FracGasMS dairy solid"),
        "FracGasMS_dairy_daily_spread": ParamRef("IPCC2006.FracGasMS.dairy|daily_spread", "FracGasMS dairy daily"),
        
        # Constants
        "CH4_M3_TO_KG": ParamRef("BOTH.CH4_M3_TO_KG.all", "CH4 density"),
    }

    outputs = {
        "CH4": VarSpec("CH4", "kg CH4 / year", "Total CH4 emissions", "scalar", True),
        "N2O_total": VarSpec("N2O_total", "kg N2O / year", "Total N2O emissions", "scalar", True),
        "N_PRP_kg": VarSpec("N_PRP_kg", "kg N / year", "Nitrogen to pasture", "scalar", True),
    }

    sources = [
        Citation(
            source="Little et al. (2008). Holos v1.1.x Methodology. AAFC",
            table="Manure Management section",
            equation="IPCC 2006 Eq 10.23, 10.25-10.29",
            page="",
        ),
        Citation(
            source="Coates et al. (2020). J Dairy Sci. DOI: 10.3168/jds.2019-17361",
            table="",
            equation="",
            page="",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute manure management emissions (Holos approach with IPCC 2006 equations).
        
        Args:
            inputs: head, animal_type, region, climate_zone, systems
            params: VS, Nrate, TAM, B0, MCF, EF3, EF4, FracGasMS
            
        Returns:
            CH4, N2O_total, N_PRP_kg
        """
        head = inputs["head"]
        animal = inputs["animal_type"]
        climate = inputs["climate_zone"]
        systems = inputs["systems"]
        
        # Get animal parameters (Canadian defaults)
        vs = params[f"VS_{animal}_canada"]
        tam = params[f"TAM_{animal}_canada"]
        nrate = params[f"Nrate_{animal}_canada"]
        b0 = params[f"B0_{animal}_canada"]
        
        nex = nrate * tam / 1000.0 * 365.0  # kg N/year per animal
        ch4_density = params["CH4_M3_TO_KG"]
        ef4 = params["EF4"]
        
        # Calculate CH4 and N2O by system
        ch4_sum_mcf = 0.0
        n_direct = 0.0
        n_vol = 0.0
        n_prp = 0.0
        
        for system, fraction in systems.items():
            mcf_key, ef3_key, fracgas_key = SYSTEM_MAP[system]
            
            # Get MCF for Canadian climate zone
            mcf_param_name = f"MCF_{mcf_key}_{climate}"
            if mcf_param_name in params:
                mcf = params[mcf_param_name]
            else:
                # Fallback to cool if parameter not found
                mcf = params.get(f"MCF_{mcf_key}_cool", 0.02)
            
            ch4_sum_mcf += mcf * fraction
            
            # N2O calculation
            n = head * nex * fraction
            
            if system == "pasture":
                n_prp += n
                continue
            
            # Direct and indirect N2O
            ef3 = params[f"EF3_{ef3_key}"]
            n_direct += n * ef3
            
            fracgas_param = f"FracGasMS_{animal}_{fracgas_key}"
            if fracgas_param in params:
                fracgas = params[fracgas_param]
            else:
                # Fallback
                fracgas = 0.2
            n_vol += n * fracgas
        
        # CH4 (Equation 10.23)
        ch4 = head * vs * 365.0 * b0 * ch4_density * ch4_sum_mcf
        
        # N2O from volatilization
        n2o_vol_n = n_vol * ef4
        
        # Convert to N2O
        n2o_direct = n_direct * N2ON_TO_N2O
        n2o_vol = n2o_vol_n * N2ON_TO_N2O
        
        return {
            "CH4": ch4,
            "N2O_total": n2o_direct + n2o_vol,
            "N_PRP_kg": n_prp,
        }


# Validate module
from ghgsim.core.module import validate_module

errors = validate_module(HolosManure())
if errors:
    raise ValueError(f"HolosManure module validation failed: {errors}")
