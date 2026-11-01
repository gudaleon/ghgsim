"""
IPCC 2006 CO2 from lime (Eq 11.12) and urea (Eq 11.13).

Opened: 2006 IPCC Vol 4 Ch 11 PDF
(https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_11_Ch11_N2O&CO2.pdf).
Equations report CO2-C; convert to CO2 with 44/12.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.modules.holos.process_defs import lime_co2_process, urea_co2_process

_LIME = lime_co2_process()
_UREA = urea_co2_process()


class IPCC2006LimeUreaCO2:
    """Tier 1 CO2 from carbonate lime and urea fertiliser."""

    id = "ipcc2006.lime_urea_co2"
    version = "1.0.0"

    inputs = {
        "M_limestone_t": VarSpec("M_limestone_t", "tonne / year", "Calcic limestone (CaCO3) applied", "scalar", False),
        "M_dolomite_t": VarSpec("M_dolomite_t", "tonne / year", "Dolomite (CaMg(CO3)2) applied", "scalar", False),
        "M_urea_t": VarSpec("M_urea_t", "tonne / year", "Urea fertiliser applied", "scalar", False),
    }

    parameters = {
        "EF_limestone": ParamRef("IPCC2006.EF_lime.limestone", "Eq 11.12 limestone EF (t C / t lime)"),
        "EF_dolomite": ParamRef("IPCC2006.EF_lime.dolomite", "Eq 11.12 dolomite EF (t C / t lime)"),
        "EF_urea": ParamRef("IPCC2006.EF_urea.all", "Eq 11.13 urea EF (t C / t urea)"),
        "C_TO_CO2": ParamRef("BOTH.C_TO_CO2.all", "44/12 kg CO2 per kg C"),
    }

    outputs = {
        "CO2_lime_kg": VarSpec("CO2_lime_kg", "kg CO2 / year", "CO2 from limestone + dolomite", "scalar", True),
        "CO2_urea_kg": VarSpec("CO2_urea_kg", "kg CO2 / year", "CO2 from urea", "scalar", True),
        "CO2_total_kg": VarSpec("CO2_total_kg", "kg CO2 / year", "Lime + urea CO2", "scalar", True),
    }

    sources = [
        Citation(
            source="2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4, Chapter 11",
            table="Section 11.2.2 and 11.2.3 default EFs",
            equation="Eq 11.12, 11.13",
            page="11.27, 11.32",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        limestone = float(inputs.get("M_limestone_t") or 0.0)
        dolomite = float(inputs.get("M_dolomite_t") or 0.0)
        urea = float(inputs.get("M_urea_t") or 0.0)
        c_to_co2 = float(params["C_TO_CO2"])
        lime_c_t = _LIME.compute_rate(
            {
                "M_limestone_t": limestone,
                "EF_limestone": float(params["EF_limestone"]),
                "M_dolomite_t": dolomite,
                "EF_dolomite": float(params["EF_dolomite"]),
            }
        )
        urea_c_t = _UREA.compute_rate({"M_urea_t": urea, "EF_urea": float(params["EF_urea"])})
        lime_kg = lime_c_t * 1000.0 * c_to_co2
        urea_kg = urea_c_t * 1000.0 * c_to_co2
        return {
            "CO2_lime_kg": lime_kg,
            "CO2_urea_kg": urea_kg,
            "CO2_total_kg": lime_kg + urea_kg,
        }


errors = validate_module(IPCC2006LimeUreaCO2())
if errors:
    raise ValueError(f"IPCC2006LimeUreaCO2 module validation failed: {errors}")
