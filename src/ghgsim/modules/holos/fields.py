"""
Link managed manure N to crop/soil fields (IPCC 2006 Eq 11.3–11.5).

FAM = N_MMS_Avb * (1 - FracFEED - FracFUEL - FracCNST). When those fractions
are not supplied, Chapter 11 p. 11.13 says use N_MMS_Avb as FAM. F_PRP is
urine/dung on pasture (Eq 11.5), not applied manure.

This is the Phase B once-only rule: excreted N is not added again as a second
F_ON that skips storage losses.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.modules.holos.process_defs import field_fam_process

_FAM = field_fam_process()


class HolosFieldN:
    """Assemble soil N inputs from animal manure leftovers plus field applications."""

    id = "holos.field_n"
    version = "1.0.0"

    inputs = {
        "N_MMS_Avb_kg": VarSpec(
            "N_MMS_Avb_kg", "kg N / year", "Managed manure N remaining after storage (Eq 10.34)", "scalar", False
        ),
        "N_PRP_kg": VarSpec("N_PRP_kg", "kg N / year", "N deposited on pasture (Eq 11.5 F_PRP)", "scalar", False),
        "F_SN": VarSpec("F_SN", "kg N / year", "Synthetic fertiliser N (not urea-C; N mass only)", "scalar", False),
        "F_ON_other_kg": VarSpec(
            "F_ON_other_kg", "kg N / year", "Sewage/compost/other organic N (Eq 11.3 FSEW+FCOMP+FOOA)", "scalar", False
        ),
        "F_CR": VarSpec("F_CR", "kg N / year", "Crop residue N (user-supplied; Eq 11.6 not expanded)", "scalar", False),
        "F_SOM": VarSpec("F_SOM", "kg N / year", "Mineralised soil organic matter N", "scalar", False),
        "FracFEED": VarSpec("FracFEED", "dimensionless", "Managed manure used as feed (Eq 11.4)", "scalar", False),
        "FracFUEL": VarSpec("FracFUEL", "dimensionless", "Managed manure burned for fuel (Eq 11.4)", "scalar", False),
        "FracCNST": VarSpec("FracCNST", "dimensionless", "Managed manure used for construction (Eq 11.4)", "scalar", False),
        "link_manure_n": VarSpec(
            "link_manure_n",
            "dimensionless",
            "If true (default), FAM = N_MMS_Avb after Eq 11.4 fractions",
            "scalar",
            False,
        ),
        "F_ON_override": VarSpec(
            "F_ON_override", "kg N / year", "If set, used as F_ON instead of the manure link", "scalar", False
        ),
    }

    parameters = {
        "FracFEED_default": ParamRef(
            "IPCC2006.FracFEED.default_zero", "Eq 11.4: use N_MMS_Avb as FAM when unused-manure data are absent"
        ),
    }

    outputs = {
        "F_ON": VarSpec("F_ON", "kg N / year", "Organic N applied (Eq 11.3)", "scalar", True),
        "F_PRP_CPP": VarSpec("F_PRP_CPP", "kg N / year", "PRP urine/dung N", "scalar", True),
        "F_AM_kg": VarSpec("F_AM_kg", "kg N / year", "Animal manure N applied (Eq 11.4 FAM)", "scalar", True),
    }

    sources = [
        Citation(
            source="2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4, Chapter 11",
            table="",
            equation="Eq 11.3, 11.4, 11.5",
            page="11.12-11.13",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        n_mms = float(inputs.get("N_MMS_Avb_kg") or 0.0)
        n_prp = float(inputs.get("N_PRP_kg") or 0.0)
        frac_feed = float(inputs.get("FracFEED") or params.get("FracFEED_default") or 0.0)
        frac_fuel = float(inputs.get("FracFUEL") or 0.0)
        frac_cnst = float(inputs.get("FracCNST") or 0.0)
        fam = _FAM.compute_rate(
            {
                "N_MMS_Avb_kg": n_mms,
                "FracFEED": frac_feed,
                "FracFUEL": frac_fuel,
                "FracCNST": frac_cnst,
            }
        )
        link = bool(inputs.get("link_manure_n", True))
        if inputs.get("F_ON_override") not in (None, ""):
            f_on = float(inputs["F_ON_override"])
            fam = 0.0 if not link else fam
        elif link:
            f_on = fam + float(inputs.get("F_ON_other_kg") or 0.0)
        else:
            f_on = float(inputs.get("F_ON_other_kg") or 0.0)
        return {
            "F_SN": float(inputs.get("F_SN") or 0.0),
            "F_ON": f_on,
            "F_CR": float(inputs.get("F_CR") or 0.0),
            "F_SOM": float(inputs.get("F_SOM") or 0.0),
            "F_PRP_CPP": n_prp,
            "F_AM_kg": fam if link else 0.0,
        }


errors = validate_module(HolosFieldN())
if errors:
    raise ValueError(f"HolosFieldN module validation failed: {errors}")
