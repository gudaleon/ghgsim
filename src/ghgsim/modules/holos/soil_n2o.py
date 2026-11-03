"""
Holos (Canada) soil N2O emissions.

Re-implemented from published sources. Implementation is independent, based
solely on published equations.

Sources:
- Little et al. (2008). Holos v1.1.x Methodology. AAFC.
- IPCC 2006 Guidelines Volume 4 Chapter 11 (Equations 11.1, 11.9, 11.10)
- Liang et al. (2020). Nutr. Cycl. Agroecosyst. 117:145-167.
  DOI: 10.1007/s10705-020-10058-w
- Pogue et al. (2025). Holos V4.0 Algorithm Document Sec 2.5 (opened docx
  @036f862). Holos C# N2OEmissionFactorCalculator.cs:478-656,777-788 matches.
- Rochette et al. (2008). Can. J. Soil Sci. 88:641-654. DOI: 10.4141/cjss07025
  (opened). Supplies FR_Topo only, not the coded EF.

HOLOS.N2O.ef1 is a model-version option (not a bug fork):
ipcc2006_ef1 (default) = IPCC 2006 Table 11.1 EF1 = 0.01.
holos_liang2020 = Holos V4 Sec 2.5 / Liang et al. 2020
EF_CT = exp(0.00558 * P_or_PE_mm - 7.7), times topography / RF_TX /
winter 1/0.645. Requires growing-season P and PE in mm. Rochette 2008
supplies FR_Topo only. Holos C# @036f862 matches the opened manual
(no holos_as_coded EF1 bug). Missing climate is UNVERIFIED-input.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.modules.holos.common import forks_from_inputs
from ghgsim.modules.holos.county_climate import county_p_pe
from ghgsim.modules.holos.forks import resolve_option
from ghgsim.modules.holos.process_defs import (
    holos_ecodistrict_ef_ct_process,
    soil_n2o_direct_process,
    soil_n2o_indirect_leach_process,
    soil_n2o_indirect_vol_process,
)

# Molecular weight conversion
N2ON_TO_N2O = 44.0 / 28.0
_DIRECT = soil_n2o_direct_process()
_VOL = soil_n2o_indirect_vol_process()
_LEACH = soil_n2o_indirect_leach_process()
_EF_CT = holos_ecodistrict_ef_ct_process()
WINTER_CORRECTION = 1.0 / 0.645


def holos_ecodistrict_ef1(
    *,
    precip_mm: float,
    pe_mm: float,
    fr_topo: float | None = None,
    irrigation_mm: float = 0.0,
    rf_tx: float = 1.0,
    rf_ns: float = 1.0,
    rf_till: float = 1.0,
    rf_cs: float = 1.0,
    rf_am: float = 1.0,
    slope: float = 0.00558,
    intercept: float = -7.7,
    winter: float = WINTER_CORRECTION,
) -> tuple[float, str]:
    """Holos V4 Eq 2.5.1-2.5.4. Returns (EF1, status).

    status is holos_liang2020 when all required climate inputs are present,
    else UNVERIFIED-input (caller should fall back to IPCC EF1).
    Dry (P/PE < 1) without irrigation needs FR_Topo (Rochette 2008 / CanSIS).
    P == PE does not need FR_Topo because Eq 2.5.2-2 then equals EF_CT(PE).
    """
    if pe_mm == 0.0:
        return 0.0, "UNVERIFIED-input"
    ratio = precip_mm / pe_mm
    ef_p = _EF_CT.compute_rate({"moisture_mm": precip_mm, "EF_CT_slope": slope, "EF_CT_intercept": intercept})
    ef_pe = _EF_CT.compute_rate({"moisture_mm": pe_mm, "EF_CT_slope": slope, "EF_CT_intercept": intercept})
    if irrigation_mm > 0.0:
        ef_topo = ef_pe
    elif ratio > 1.0:
        ef_topo = ef_p
    elif abs(ratio - 1.0) < 1e-12:
        ef_topo = ef_pe
    elif fr_topo is None:
        return 0.0, "UNVERIFIED-input"
    else:
        ef_topo = ef_pe * fr_topo + ef_p * (1.0 - fr_topo)
    ef = ef_topo * rf_tx * winter * rf_ns * rf_till * rf_cs * rf_am
    return ef, "holos_liang2020"


FALLBACK_IPCC_DEFAULT = "fallback-IPCC-default"


def _is_dry_without_topo(precip, pe, fr_topo, irrigation_mm) -> bool:
    """True when Holos Eq 2.5.2 needs FR_Topo (P/PE < 1, not irrigated) and none is given."""
    try:
        p, e = float(precip), float(pe)
    except (TypeError, ValueError):
        return False
    irr = float(irrigation_mm) if irrigation_mm not in (None, "") else 0.0
    return e > 0.0 and p / e < 1.0 and irr <= 0.0 and fr_topo in (None, "")


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

    Direct/indirect N2O follow IPCC 2006 Equations 11.1, 11.9, 11.10.
    HOLOS.N2O.ef1 chooses the direct EF: IPCC 2006 Table 11.1 (default) or
    Holos V4 Sec 2.5 / Liang et al. 2020 when growing-season P and PE exist.
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
            "Unused for Holos EF. Holos Eq 2.5.1 needs growing-season P and PE in mm, not a ratio.",
            "scalar",
            False,
        ),
        "growing_season_precip_mm": VarSpec(
            "growing_season_precip_mm",
            "mm",
            "May-October precipitation (Holos V4: CanSIS 1980-2010). Required for holos_liang2020.",
            "scalar",
            False,
        ),
        "growing_season_pe_mm": VarSpec(
            "growing_season_pe_mm",
            "mm",
            "May-October potential evapotranspiration (Holos V4: CanSIS 1980-2010).",
            "scalar",
            False,
        ),
        "county_fips": VarSpec(
            "county_fips",
            "dimensionless",
            "US county FIPS. For holos_liang2020, fills missing growing-season P/PE from "
            "data/county_p_pe_may_oct_AN_v2.csv (nClimDiv 1991-2020, Hargreaves PE). Explicit P/PE win.",
            "scalar",
            False,
        ),
        "FR_Topo": VarSpec(
            "FR_Topo",
            "fraction",
            "Fraction of low-lying land (Rochette 2008 / Holos ecodistrict table). Required when P/PE <= 1.",
            "scalar",
            False,
        ),
        "irrigation_mm": VarSpec(
            "irrigation_mm",
            "mm",
            "Growing-season irrigation. Holos treats irrigated sites as P = PE.",
            "scalar",
            False,
        ),
        "RF_TX": VarSpec(
            "RF_TX",
            "dimensionless",
            "Holos Table 13 texture modifier. Default 1 when texture is not specified (manual Sec 2.5).",
            "scalar",
            False,
        ),
        "RFtext": VarSpec(
            "RFtext",
            "dimensionless",
            "Unused alias kept for older callers. Holos Table 13 RF_TX is RF_TX.",
            "scalar",
            False,
        ),
        "RFtopo": VarSpec(
            "RFtopo",
            "dimensionless",
            "Unused alias kept for older callers. Holos FR_Topo is FR_Topo.",
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
        "EFeco_slope": ParamRef("HOLOS.N2O.EFeco.slope", "Rochette 2008 Eq 3 slope (not Holos-coded EF)"),
        "EFeco_intercept": ParamRef("HOLOS.N2O.EFeco.intercept", "Rochette 2008 Eq 3 intercept"),
        "EFeco_min": ParamRef("HOLOS.N2O.EFeco.min", "Rochette 2008 Eq 3 clamp minimum"),
        "EFeco_max": ParamRef("HOLOS.N2O.EFeco.max", "Rochette 2008 Eq 3 clamp maximum"),
        "EF_CT_slope": ParamRef("HOLOS.N2O.EF_CT.slope", "Holos V4 Eq 2.5.1 slope 0.00558"),
        "EF_CT_intercept": ParamRef("HOLOS.N2O.EF_CT.intercept", "Holos V4 Eq 2.5.1 intercept −7.7"),
        "winter_correction": ParamRef("HOLOS.N2O.winter_correction", "Holos V4 Eq 2.5.3-2; 1/0.645 (Pelster 2023)"),
    }

    outputs = {
        "N2O_total": VarSpec("N2O_total", "kg N2O / year", "Total N2O emissions", "scalar", True),
        "N2O_direct": VarSpec("N2O_direct", "kg N2O / year", "Direct N2O emissions", "scalar", True),
        "N2O_indirect_vol": VarSpec("N2O_indirect_vol", "kg N2O / year", "Indirect N2O from volatilization", "scalar", True),
        "N2O_indirect_leach": VarSpec("N2O_indirect_leach", "kg N2O / year", "Indirect N2O from leaching", "scalar", True),
        "EF1_used": VarSpec("EF1_used", "kg N2O-N / kg N", "Direct EF1 after HOLOS.N2O.ef1 model-version option", "scalar", True),
        "EF1_status": VarSpec("EF1_status", "dimensionless", "ipcc2006_ef1, holos_liang2020, fallback-IPCC-default (dry, no FR_Topo), or UNVERIFIED-input", "scalar", True),
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
            source="Liang et al. (2020). Nutr. Cycl. Agroecosyst. 117:145-167. DOI 10.1007/s10705-020-10058-w",
            table="",
            equation="N2OEF = exp(0.00558*P - 7.7)",
            page="145-167",
            notes="Opened via Holos V4 Sec 2.5 citation. Country-specific Canadian soil N2O EF.",
        ),
        Citation(
            source="Pogue et al. (2025). Holos V4.0 Algorithm Document. holos-aafc/Holos repo root @036f862",
            table="Table 13 (link; values not printed in the docx)",
            equation="Eq 2.5.1-1, 2.5.1-2, 2.5.2-1..3, 2.5.3-2, 2.5.4-1",
            page="Sec 2.5 Nitrous oxide emission factor calculation (IPCC Canada Tier 2)",
            notes=(
                "Opened this run. EF_CT=exp(0.00558*P_or_PE-7.7). P, PE = May-October CanSIS 1980-2010. "
                "Rochette 2008 is cited for FR_Topo only. Liang et al. 2020 is the EF source. "
                "C# N2OEmissionFactorCalculator.cs:478-656,777-788 matches the manual (no holos_as_coded EF1 bug)."
            ),
        ),
        Citation(
            source="Rochette et al. (2008). Can. J. Soil Sci. 88:641-654. DOI: 10.4141/cjss07025",
            table="",
            equation="FR_Topo (low-lying land fraction); not Holos Eq 2.5.1",
            page="641-654",
            notes="Opened. Holos uses this paper for FR_Topo, not Rochette Eq 3 EFeco=0.022*(P/PE)-0.0048.",
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
        ef1_option = resolve_option("HOLOS.N2O.ef1", fork_settings)
        ef1 = ef1_ipcc
        ef1_status = "ipcc2006_ef1"
        precip = inputs.get("growing_season_precip_mm")
        pe = inputs.get("growing_season_pe_mm")
        fr_topo = inputs.get("FR_Topo")
        if ef1_option == "holos_liang2020":
            fips = inputs.get("county_fips")
            if fips not in (None, "") and (precip in (None, "") or pe in (None, "")):
                looked = county_p_pe(fips)
                if looked is not None:
                    if precip in (None, ""):
                        precip = looked["growing_season_precip_mm"]
                    if pe in (None, ""):
                        pe = looked["growing_season_pe_mm"]
            if precip not in (None, "") and pe not in (None, ""):
                holos_ef, holos_status = holos_ecodistrict_ef1(
                    precip_mm=float(precip),
                    pe_mm=float(pe),
                    fr_topo=None if fr_topo in (None, "") else float(fr_topo),
                    irrigation_mm=float(inputs["irrigation_mm"]) if inputs.get("irrigation_mm") not in (None, "") else 0.0,
                    rf_tx=float(inputs["RF_TX"]) if inputs.get("RF_TX") not in (None, "") else 1.0,
                    slope=float(params.get("EF_CT_slope", 0.00558)),
                    intercept=float(params.get("EF_CT_intercept", -7.7)),
                    winter=float(params.get("winter_correction", WINTER_CORRECTION)),
                )
                if holos_status == "holos_liang2020":
                    ef1 = holos_ef
                    ef1_status = holos_status
                elif _is_dry_without_topo(precip, pe, fr_topo, inputs.get("irrigation_mm")):
                    # Alex 2026-11-03: dry (P/PE < 1) with no FR_Topo -> IPCC default EF1
                    # (2006 GL Vol4 Ch11 Table 11.1 = 0.01; 2019 Refinement Table 11.1
                    # aggregated = 0.010). ef1 stays at params["EF1"].
                    ef1_status = FALLBACK_IPCC_DEFAULT
                else:
                    ef1_status = "UNVERIFIED-input"
            else:
                ef1_status = "UNVERIFIED-input"
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
            "EF1_status": ef1_status,
            "soil_n2o_by_source": by_source,
        }


errors = validate_module(HolosSoilN2O())
if errors:
    raise ValueError(f"HolosSoilN2O module validation failed: {errors}")
