"""
IPCC 2019 Refinement Tier 1-2 N2O emissions from managed soils with climate disaggregation.

Direct emissions use climate-disaggregated EF1 values:
- Wet climates: Separate EFs for synthetic fertilizer vs organic/residue
- Dry climates: Single EF for all N inputs

Indirect emissions also use climate-specific factors (EF4, FracLEACH).
Dry climates: FracLEACH = 0 for non-irrigated systems.

Source: 2019 Refinement to the 2006 IPCC Guidelines,
        Volume 4, Chapter 11 (Updated).
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, Module, ParamRef, VarSpec

# Molecular weight conversion: N2O-N to N2O
N2ON_TO_N2O = 44.0 / 28.0


class IPCC2019SoilN2O:
    """
    IPCC 2019 Refinement Tier 1-2 N2O emissions with climate disaggregation.
    
    Uses updated emission factors from 2019 Refinement that distinguish
    between wet and dry climates, and between synthetic vs organic N sources.
    """

    id = "ipcc2019.soil_n2o"
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
        # Climate-disaggregated EF1 values
        "EF1_wet_synthetic": ParamRef("IPCC2019.EF1.wet_synthetic", "EF1 for synthetic fertilizer in wet climate"),
        "EF1_wet_other": ParamRef("IPCC2019.EF1.wet_other", "EF1 for organic N/residues in wet climate"),
        "EF1_dry": ParamRef("IPCC2019.EF1.dry", "EF1 for all N inputs in dry climate"),
        # Other emission factors
        "EF3PRP_CPP_wet": ParamRef("IPCC2019.EF3PRP_CPP.wet", "EF3 for PRP/CPP in wet climate"),
        "EF3PRP_CPP_dry": ParamRef("IPCC2019.EF3PRP_CPP.dry", "EF3 for PRP/CPP in dry climate"),
        "EF4_wet": ParamRef("IPCC2019.EF4.wet", "Indirect EF for volatilization in wet climate"),
        "EF4_dry": ParamRef("IPCC2019.EF4.dry", "Indirect EF for volatilization in dry climate"),
        "EF5": ParamRef("IPCC2019.EF5.all", "Indirect emission factor (leaching)"),
        # Volatilization fractions
        "FracGASF": ParamRef("IPCC2019.FracGASF.all", "Fraction of synthetic fertilizer N volatilized"),
        "FracGASM": ParamRef("IPCC2019.FracGASM.all", "Fraction of organic N volatilized"),
        # Leaching fractions
        "FracLEACH_wet": ParamRef("IPCC2019.FracLEACH.wet", "Fraction of N leached (wet climate)"),
        "FracLEACH_dry": ParamRef("IPCC2019.FracLEACH.dry", "Fraction of N leached (dry climate, = 0)"),
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
            source="2019 Refinement to the 2006 IPCC Guidelines, Volume 4, Chapter 11",
            table="Table 11.1 (Updated), Table 11.3 (Updated)",
            equation="Eq 11.1, 11.9, 11.10",
            page="11.13, 11.25, 11.26",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute N2O emissions from managed soils (IPCC 2019 Tier 1-2).
        
        Args:
            inputs: Dictionary with F_SN, F_ON, F_CR, F_SOM, F_PRP_CPP, climate
            params: Dictionary with climate-disaggregated EF1, EF3, EF4, FracLEACH
            
        Returns:
            Dictionary with N2O_direct, N2O_indirect_vol, N2O_indirect_leach, N2O_total
        """
        # Extract inputs
        FSN = inputs["F_SN"]
        FON = inputs["F_ON"]
        FCR = inputs["F_CR"]
        FSOM = inputs["F_SOM"]
        FPRP = inputs["F_PRP_CPP"]
        climate = inputs["climate"]

        # Climate-specific parameters
        if climate == "wet":
            ef1_syn = params["EF1_wet_synthetic"]
            ef1_other = params["EF1_wet_other"]
            ef3 = params["EF3PRP_CPP_wet"]
            ef4 = params["EF4_wet"]
            frac_leach = params["FracLEACH_wet"]
        else:  # dry
            ef1_syn = params["EF1_dry"]
            ef1_other = params["EF1_dry"]  # Same for all inputs in dry climate
            ef3 = params["EF3PRP_CPP_dry"]
            ef4 = params["EF4_dry"]
            frac_leach = params["FracLEACH_dry"]  # Zero for dry non-irrigated

        ef5 = params["EF5"]
        frac_gasf = params["FracGASF"]
        frac_gasm = params["FracGASM"]

        # Direct emissions (climate-disaggregated)
        direct_n = FSN * ef1_syn + (FON + FCR + FSOM) * ef1_other + FPRP * ef3

        # Indirect emissions via volatilization (climate-specific EF4)
        vol_n = (FSN * frac_gasf + (FON + FPRP) * frac_gasm) * ef4

        # Indirect emissions via leaching (zero in dry non-irrigated)
        leach_n = (FSN + FON + FPRP + FCR + FSOM) * frac_leach * ef5

        # Convert N2O-N to N2O
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
from ghgsim.core.module import validate_module

errors = validate_module(IPCC2019SoilN2O())
if errors:
    raise ValueError(f"IPCC2019SoilN2O module validation failed: {errors}")
