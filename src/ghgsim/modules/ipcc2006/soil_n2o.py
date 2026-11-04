"""
IPCC 2006 Guidelines Tier 1 N2O emissions from managed soils.

Direct emissions (Equation 11.1) and indirect emissions via volatilization
(Equations 11.9) and leaching (Equation 11.10).

Source: 2006 IPCC Guidelines for National Greenhouse Gas Inventories,
        Volume 4 (Agriculture, Forestry and Other Land Use), Chapter 11.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec

# Molecular weight conversion: N2O-N to N2O
N2ON_TO_N2O = 44.0 / 28.0


class IPCC2006SoilN2O:
    """
    IPCC 2006 Tier 1 N2O emissions from managed soils.
    
    Calculates direct and indirect N2O-N emissions from:
    - Synthetic fertilizer (FSN)
    - Organic fertilizer (FON)
    - Crop residues (FCR)
    - Soil organic matter mineralization (FSOM)
    - Pasture/range/paddock manure deposition (FPRP_CPP)
    
    Returns N2O (not N2O-N) in kg/yr.
    """

    id = "ipcc2006.soil_n2o"
    version = "1.0.0"

    inputs = {
        "F_SN": VarSpec("F_SN", "kg N / year", "Synthetic fertilizer N applied", "scalar", True),
        "F_ON": VarSpec("F_ON", "kg N / year", "Organic fertilizer N applied", "scalar", True),
        "F_CR": VarSpec("F_CR", "kg N / year", "Crop residue N returned to soil", "scalar", True),
        "F_SOM": VarSpec("F_SOM", "kg N / year", "Soil organic matter mineralization", "scalar", True),
        "F_PRP_CPP": VarSpec("F_PRP_CPP", "kg N / year", "Pasture/range/paddock manure", "scalar", True),
        "climate": VarSpec("climate", "dimensionless", "Climate: 'wet' or 'dry'", "scalar", True),
    }

    parameters = {
        "EF1": ParamRef("IPCC2006.EF1.all", "Direct emission factor for managed soils"),
        "EF3PRP_CPP": ParamRef("IPCC2006.EF3PRP_CPP.all", "Emission factor for PRP/CPP"),
        "EF4": ParamRef("IPCC2006.EF4.all", "Indirect emission factor (volatilization)"),
        "EF5": ParamRef("IPCC2006.EF5.all", "Indirect emission factor (leaching)"),
        "FracGASF": ParamRef("IPCC2006.FracGASF.all", "Fraction of synthetic fertilizer N volatilized"),
        "FracGASM": ParamRef("IPCC2006.FracGASM.all", "Fraction of organic N volatilized"),
        "FracLEACH_wet": ParamRef("IPCC2006.FracLEACH.wet", "Fraction of N leached (wet climate)"),
    }

    outputs = {
        "N2O_direct": VarSpec("N2O_direct", "kg N2O / year", "Direct N2O emissions", "scalar", True),
        "N2O_indirect_vol": VarSpec(
            "N2O_indirect_vol", "kg N2O / year", "Indirect N2O from volatilization", "scalar", True
        ),
        "N2O_indirect_leach": VarSpec(
            "N2O_indirect_leach", "kg N2O / year", "Indirect N2O from leaching", "scalar", True
        ),
        "N2O_total": VarSpec("N2O_total", "kg N2O / year", "Total N2O emissions", "scalar", True),
    }

    sources = [
        Citation(
            source="2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4, Chapter 11",
            table="Table 11.1",
            equation="Eq 11.1, 11.9, 11.10",
            page="11.11, 11.24",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute N2O emissions from managed soils (IPCC 2006 Tier 1).
        
        Args:
            inputs: Dictionary with F_SN, F_ON, F_CR, F_SOM, F_PRP_CPP, climate
            params: Dictionary with EF1, EF3PRP_CPP, EF4, EF5, FracGASF, FracGASM, FracLEACH_wet
            
        Returns:
            Dictionary with N2O_direct, N2O_indirect_vol, N2O_indirect_leach, N2O_total
        """
        # Extract inputs
        FSN = inputs["F_SN"]
        FON = inputs["F_ON"]
        FCR = inputs["F_CR"]
        FSOM = inputs["F_SOM"]
        FPRP = inputs["F_PRP_CPP"]
        inputs["climate"]

        # Extract parameters
        ef1 = params["EF1"]
        ef3 = params["EF3PRP_CPP"]
        ef4 = params["EF4"]
        ef5 = params["EF5"]
        frac_gasf = params["FracGASF"]
        frac_gasm = params["FracGASM"]
        frac_leach = params["FracLEACH_wet"]  # 2006 uses wet value for all

        # Equation 11.1: Direct emissions
        direct_n = (FSN + FON + FCR + FSOM) * ef1 + FPRP * ef3

        # Equation 11.9: Indirect emissions via volatilization
        vol_n = (FSN * frac_gasf + (FON + FPRP) * frac_gasm) * ef4

        # Equation 11.10: Indirect emissions via leaching
        # IPCC 2006 uses FracLEACH for wet climates; assumes same for all regions
        leach_n = (FSN + FON + FPRP + FCR + FSOM) * frac_leach * ef5

        # Convert N2O-N to N2O (molecular weight ratio 44/28)
        direct = direct_n * N2ON_TO_N2O
        indirect_vol = vol_n * N2ON_TO_N2O
        indirect_leach = leach_n * N2ON_TO_N2O

        return {
            "N2O_direct": direct,
            "N2O_indirect_vol": indirect_vol,
            "N2O_indirect_leach": indirect_leach,
            "N2O_total": direct + indirect_vol + indirect_leach,
        }


# Validate module on import
from ghgsim.core.module import validate_module  # noqa: E402

errors = validate_module(IPCC2006SoilN2O())
if errors:
    raise ValueError(f"IPCC2006SoilN2O module validation failed: {errors}")
