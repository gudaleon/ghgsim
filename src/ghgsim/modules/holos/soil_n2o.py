"""
Holos (Canada) soil N2O emissions.

Re-implemented from published sources. Implementation is independent, based
solely on published equations.

Sources:
- Little et al. (2008). Holos v1.1.x Methodology. AAFC.
- IPCC 2006 Guidelines Volume 4 Chapter 11 (Equations 11.1, 11.9, 11.10)
- Rochette et al. (2008). Can. J. Soil Sci. 88:641-654. DOI: 10.4141/cjss07025
  (opened). Holos docs also cite SSSAJ DOI 10.2136/sssaj2007.0351; that URL 404s.

HOLOS.N2O.ef1: source_correct uses Rochette EFeco when P_PE is supplied;
holos_as_coded (and any run without P_PE) uses IPCC 2006 EF1 = 0.01.
Holos C# / V4 algorithm soil N2O section was not opened (UNVERIFIED).
RFtext / RFtopo are applied only when the caller supplies them.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.modules.holos.common import forks_from_inputs
from ghgsim.modules.holos.forks import resolve_option
from ghgsim.modules.holos.process_defs import (
    rochette_efeco_process,
    soil_n2o_direct_process,
    soil_n2o_indirect_leach_process,
    soil_n2o_indirect_vol_process,
)

# Molecular weight conversion
N2ON_TO_N2O = 44.0 / 28.0
_DIRECT = soil_n2o_direct_process()
_VOL = soil_n2o_indirect_vol_process()
_LEACH = soil_n2o_indirect_leach_process()
_EFECO = rochette_efeco_process()


def allocate_soil_n2o_by_source(
    *,
    f_sn: float,
    f_on: float,
    f_cr: float,
    f_som: float,
    f_prp: float,
    ef1: float,
    ef3: float,
    ef4: float,
    ef5: float,
    fracgasf: float,
    fracgasm: float,
    fracleach: float,
) -> dict[str, float]:
    """Split total soil N2O (kg N2O) across Eq 11.1 / 11.9 / 11.10 N sources."""

    def _n2o(direct_n: float, vol_n: float, leach_n: float) -> float:
        return (direct_n + vol_n + leach_n) * N2ON_TO_N2O

    return {
        "F_SN": _n2o(f_sn * ef1, f_sn * fracgasf * ef4, f_sn * fracleach * ef5),
        "F_ON": _n2o(f_on * ef1, f_on * fracgasm * ef4, f_on * fracleach * ef5),
        "F_CR": _n2o(f_cr * ef1, 0.0, f_cr * fracleach * ef5),
        "F_SOM": _n2o(f_som * ef1, 0.0, f_som * fracleach * ef5),
        "F_PRP_CPP": _n2o(f_prp * ef3, f_prp * fracgasm * ef4, f_prp * fracleach * ef5),
    }


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
        "F_ON": VarSpec("F_ON", "kg N / year", "Organic N applied (Eq 11.3; typically FAM = N_MMS_Avb)", "scalar", True),
        "F_CR": VarSpec("F_CR", "kg N / year", "Crop residue N", "scalar", True),
        "F_SOM": VarSpec("F_SOM", "kg N / year", "Soil organic matter mineralization N", "scalar", False),
        "F_PRP_CPP": VarSpec("F_PRP_CPP", "kg N / year", "Pasture/range/paddock manure N", "scalar", False),
        "climate": VarSpec("climate", "dimensionless", "Climate (wet/dry)", "scalar", True),
        "P_PE": VarSpec(
            "P_PE",
            "dimensionless",
            "Precipitation / potential evapotranspiration (Rochette EFeco). Omit to keep IPCC EF1.",
            "scalar",
            False,
        ),
        "RFtext": VarSpec(
            "RFtext",
            "dimensionless",
            "Rochette texture modifier (east fine 1.2 / medium 0.8 / coarse 0.8). Default 1 if omitted.",
            "scalar",
            False,
        ),
        "RFtopo": VarSpec(
            "RFtopo",
            "dimensionless",
            "Rochette topography modifier. Lower landscape uses EFeco at P/PE=1. Default 1 if omitted.",
            "scalar",
            False,
        ),
        "forks": VarSpec("forks", "dimensionless", "Dict of fork_id -> option", "scalar", False),
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
        "EFeco_slope": ParamRef("HOLOS.N2O.EFeco.slope", "Rochette 2008 Eq 3 slope (0.022)"),
        "EFeco_intercept": ParamRef("HOLOS.N2O.EFeco.intercept", "Rochette 2008 Eq 3 intercept (−0.0048)"),
        "EFeco_min": ParamRef("HOLOS.N2O.EFeco.min", "Rochette 2008 Eq 3 clamp minimum (0.0016)"),
        "EFeco_max": ParamRef("HOLOS.N2O.EFeco.max", "Rochette 2008 Eq 3 clamp maximum (0.017)"),
    }

    outputs = {
        "N2O_total": VarSpec("N2O_total", "kg N2O / year", "Total N2O emissions", "scalar", True),
        "N2O_direct": VarSpec("N2O_direct", "kg N2O / year", "Direct N2O emissions", "scalar", True),
        "N2O_indirect_vol": VarSpec("N2O_indirect_vol", "kg N2O / year", "Indirect N2O from volatilization", "scalar", True),
        "N2O_indirect_leach": VarSpec("N2O_indirect_leach", "kg N2O / year", "Indirect N2O from leaching", "scalar", True),
        "EF1_used": VarSpec("EF1_used", "kg N2O-N / kg N", "Direct EF1 after HOLOS.N2O.ef1 and optional modifiers", "scalar", True),
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
            source="Rochette et al. (2008). Can. J. Soil Sci. 88:641-654. DOI: 10.4141/cjss07025",
            table="",
            equation="Equation 3 (EFeco); RFtext / lower-landscape P/PE=1 on p. 651",
            page="641-654",
            notes=(
                "Opened this run. Holos docs cite SSSAJ DOI 10.2136/sssaj2007.0351; that URL 404s. "
                "Holos C# soil N2O / V4 algorithm soil section was not opened (UNVERIFIED)."
            ),
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
        fork_settings = forks_from_inputs(inputs)

        ef1_ipcc = float(params["EF1"])
        p_pe = inputs.get("P_PE")
        ef1_option = resolve_option("HOLOS.N2O.ef1", fork_settings)
        if p_pe not in (None, "") and ef1_option == "source_correct":
            efeco = _EFECO.compute_rate(
                {
                    "P_PE": float(p_pe),
                    "EFeco_slope": float(params.get("EFeco_slope", 0.022)),
                    "EFeco_intercept": float(params.get("EFeco_intercept", -0.0048)),
                    "EFeco_min": float(params.get("EFeco_min", 0.0016)),
                    "EFeco_max": float(params.get("EFeco_max", 0.017)),
                }
            )
            rf_text = float(inputs["RFtext"]) if inputs.get("RFtext") not in (None, "") else 1.0
            rf_topo = float(inputs["RFtopo"]) if inputs.get("RFtopo") not in (None, "") else 1.0
            ef1 = efeco * rf_text * rf_topo
        else:
            ef1 = _EFECO.compute_rate(
                {
                    "P_PE": 0.0,
                    "EFeco_slope": 0.0,
                    "EFeco_intercept": 0.0,
                    "EFeco_min": 0.0,
                    "EFeco_max": 1.0,
                    "EF1_ipcc": ef1_ipcc,
                },
                fork="holos_as_coded",
            )
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
        
        # Direct N2O (Equation 11.1) and indirect (11.9, 11.10) via ProcessDefs
        n2o_direct_n = _DIRECT.compute_rate(
            {
                "F_SN": f_sn,
                "F_ON": f_on,
                "F_CR": f_cr,
                "F_SOM": f_som,
                "EF1": ef1,
                "F_PRP_CPP": f_prp_cpp,
                "EF3PRP": ef3prp,
            }
        )
        n2o_vol_n = _VOL.compute_rate(
            {
                "F_SN": f_sn,
                "FracGASF": fracgasf,
                "F_ON": f_on,
                "F_PRP_CPP": f_prp_cpp,
                "FracGASM": fracgasm,
                "EF4": ef4,
            }
        )
        n2o_leach_n = _LEACH.compute_rate(
            {
                "F_SN": f_sn,
                "F_ON": f_on,
                "F_CR": f_cr,
                "F_SOM": f_som,
                "F_PRP_CPP": f_prp_cpp,
                "FracLEACH": fracleach,
                "EF5": ef5,
            }
        )
        
        # Convert N2O-N to N2O
        n2o_direct = n2o_direct_n * N2ON_TO_N2O
        n2o_vol = n2o_vol_n * N2ON_TO_N2O
        n2o_leach = n2o_leach_n * N2ON_TO_N2O
        
        by_source = allocate_soil_n2o_by_source(
            f_sn=f_sn,
            f_on=f_on,
            f_cr=f_cr,
            f_som=f_som,
            f_prp=f_prp_cpp,
            ef1=ef1,
            ef3=ef3prp,
            ef4=ef4,
            ef5=ef5,
            fracgasf=fracgasf,
            fracgasm=fracgasm,
            fracleach=fracleach,
        )
        return {
            "N2O_total": n2o_direct + n2o_vol + n2o_leach,
            "N2O_direct": n2o_direct,
            "N2O_indirect_vol": n2o_vol,
            "N2O_indirect_leach": n2o_leach,
            "EF1_used": ef1,
            "soil_n2o_by_source": by_source,
        }


errors = validate_module(HolosSoilN2O())
if errors:
    raise ValueError(f"HolosSoilN2O module validation failed: {errors}")
