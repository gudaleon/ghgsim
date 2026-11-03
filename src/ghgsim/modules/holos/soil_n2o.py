"""
Holos (Canada) soil N2O emissions.

Re-implemented from published sources. Implementation is independent, based 
solely on published equations.

Sources:
- Little et al. (2008). Holos v1.1.x Methodology. AAFC.
- IPCC 2006 Guidelines Volume 4 Chapter 11 (Equations 11.1, 11.9, 11.10)
- Rochette et al. (2008). N2O emissions from agricultural soils in eastern Canada.
  Soil Sci Soc Am J. 72(5): 1396-1403. DOI: 10.2136/sssaj2007.0351

Holos uses IPCC 2006 soil N2O methodology with consideration for Canadian
climate and soil conditions.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, Module, ParamRef, VarSpec

# Molecular weight conversion
N2ON_TO_N2O = 44.0 / 28.0


class HolosSoilN2O:
    """
    Holos soil N2O emissions.
    
    Uses IPCC 2006 methodology (Equations 11.1, 11.9, 11.10) with Canadian
    climate considerations. Holos technical documentation indicates following
    IPCC 2006 approach for soil N2O.
    """

    id = "holos.soil_n2o"
    version = "1.0.0"

    inputs = {
        "F_SN": VarSpec("F_SN", "kg N / year", "Synthetic fertilizer N", "scalar", True),
        "F_ON": VarSpec("F_ON", "kg N / year", "Organic fertilizer N (non-manure)", "scalar", True),
        "F_CR": VarSpec("F_CR", "kg N / year", "Crop residue N", "scalar", True),
        "F_SOM": VarSpec("F_SOM", "kg N / year", "Soil organic matter mineralization N", "scalar", False),
        "F_PRP_CPP": VarSpec("F_PRP_CPP", "kg N / year", "Pasture/range/paddock manure N", "scalar", False),
        "climate": VarSpec("climate", "dimensionless", "Climate (wet/dry)", "scalar", True),
    }

    parameters = {
        # Direct emissions - uses IPCC 2006 defaults
        # (Holos documentation indicates following IPCC guidelines)
        "EF1": ParamRef("IPCC2006.EF1.all", "Direct N2O EF for managed soils"),
        "EF3PRP_CPP": ParamRef("IPCC2006.EF3PRP_CPP.all", "Direct N2O EF for pasture/range/paddock"),
        
        # Indirect emissions
        "EF4": ParamRef("IPCC2006.EF4.all", "Indirect N2O EF for volatilization"),
        "EF5": ParamRef("IPCC2006.EF5.all", "Indirect N2O EF for leaching"),
        
        # Fractions
        "FracGASF": ParamRef("IPCC2006.FracGASF.all", "Fraction of synthetic N volatilized"),
        "FracGASM": ParamRef("IPCC2006.FracGASM.all", "Fraction of organic N volatilized"),
        "FracLEACH_wet": ParamRef("IPCC2006.FracLEACH.wet", "Fraction leached in wet climate"),
        "FracLEACH_dry": ParamRef("IPCC2006.FracLEACH.dry", "Fraction leached in dry climate"),
    }

    outputs = {
        "N2O_total": VarSpec("N2O_total", "kg N2O / year", "Total N2O emissions", "scalar", True),
        "N2O_direct": VarSpec("N2O_direct", "kg N2O / year", "Direct N2O emissions", "scalar", True),
        "N2O_indirect_vol": VarSpec("N2O_indirect_vol", "kg N2O / year", "Indirect N2O from volatilization", "scalar", True),
        "N2O_indirect_leach": VarSpec("N2O_indirect_leach", "kg N2O / year", "Indirect N2O from leaching", "scalar", True),
    }

    sources = [
        Citation(
            source="Little et al. (2008). Holos v1.1.x Methodology. AAFC",
            table="Soil N2O section",
            equation="IPCC 2006 Eq 11.1, 11.9, 11.10",
            page="",
        ),
        Citation(
            source="IPCC 2006 Guidelines Volume 4 Chapter 11",
            table="Table 11.1, 11.3",
            equation="Equations 11.1, 11.9, 11.10",
            page="11.11, 11.24",
        ),
        Citation(
            source="Rochette et al. (2008). Soil Sci Soc Am J. DOI: 10.2136/sssaj2007.0351",
            table="",
            equation="",
            page="",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        """
        Compute soil N2O emissions using IPCC 2006 methodology.
        
        Direct: (F_SN + F_ON + F_CR + F_SOM) × EF1 + F_PRP_CPP × EF3PRP_CPP
        Indirect vol: (F_SN × FracGASF + (F_ON + F_PRP_CPP) × FracGASM) × EF4
        Indirect leach: (F_SN + F_ON + F_CR + F_SOM + F_PRP_CPP) × FracLEACH × EF5
        
        Args:
            inputs: F_SN, F_ON, F_CR, F_SOM, F_PRP_CPP, climate
            params: EF1, EF3PRP_CPP, EF4, EF5, FracGASF, FracGASM, FracLEACH
            
        Returns:
            N2O_total, N2O_direct, N2O_indirect_vol, N2O_indirect_leach
        """
        f_sn = inputs["F_SN"]
        f_on = inputs["F_ON"]
        f_cr = inputs["F_CR"]
        f_som = inputs.get("F_SOM", 0.0)
        f_prp_cpp = inputs.get("F_PRP_CPP", 0.0)
        climate = inputs["climate"]
        
        ef1 = params["EF1"]
        ef3prp = params["EF3PRP_CPP"]
        ef4 = params["EF4"]
        ef5 = params["EF5"]
        fracgasf = params["FracGASF"]
        fracgasm = params["FracGASM"]
        
        # Climate-specific leaching
        if climate == "wet":
            fracleach = params["FracLEACH_wet"]
        else:
            fracleach = params.get("FracLEACH_dry", 0.1)  # Fallback for dry
        
        # Direct N2O (Equation 11.1)
        n_inputs = f_sn + f_on + f_cr + f_som
        n2o_direct_n = n_inputs * ef1 + f_prp_cpp * ef3prp
        
        # Indirect via volatilization (Equation 11.9)
        n_volatilized = f_sn * fracgasf + (f_on + f_prp_cpp) * fracgasm
        n2o_vol_n = n_volatilized * ef4
        
        # Indirect via leaching (Equation 11.10)
        n_total = n_inputs + f_prp_cpp
        n_leached = n_total * fracleach
        n2o_leach_n = n_leached * ef5
        
        # Convert N2O-N to N2O
        n2o_direct = n2o_direct_n * N2ON_TO_N2O
        n2o_vol = n2o_vol_n * N2ON_TO_N2O
        n2o_leach = n2o_leach_n * N2ON_TO_N2O
        
        return {
            "N2O_total": n2o_direct + n2o_vol + n2o_leach,
            "N2O_direct": n2o_direct,
            "N2O_indirect_vol": n2o_vol,
            "N2O_indirect_leach": n2o_leach,
        }


# Validate module
from ghgsim.core.module import validate_module

errors = validate_module(HolosSoilN2O())
if errors:
    raise ValueError(f"HolosSoilN2O module validation failed: {errors}")
