"""Soil-surface N budget with an explicit closing term.

inputs  = synthetic N + manure N applied + PRP N + soybean BNF (above-ground) + F_SOM
outputs = N in harvested crops + soil NH3/NOx volatilisation + leaching/runoff + direct soil N2O-N
residual = inputs - outputs  (unaccounted: denitrification to N2, soil N storage change, atmospheric deposition,
           non-soybean BNF, and errors in every term). Crop-residue N is recycled within the field and is reported
           but not counted as an input. The identity inputs - outputs - residual = 0 is checked to machine precision.
"""
from __future__ import annotations

IN_TERMS = ("synthetic_N", "manure_N_applied", "PRP_N", "BNF_soy_AG", "F_SOM")
OUT_TERMS = ("crop_N_removed", "soil_volatilised", "soil_leached", "soil_N2O_N_direct")


def n_budget(terms: dict[str, float]) -> dict[str, float]:
    """Return a copy of ``terms`` plus inputs_total, outputs_total, residual, closure_error and NUE."""
    missing = [k for k in IN_TERMS + OUT_TERMS if k not in terms]
    if missing:
        raise KeyError(f"missing budget terms: {missing}")
    out = dict(terms)
    tin = sum(float(terms[k]) for k in IN_TERMS)
    tout = sum(float(terms[k]) for k in OUT_TERMS)
    out["inputs_total"], out["outputs_total"] = tin, tout
    out["residual_unaccounted"] = tin - tout
    out["closure_error"] = tin - tout - out["residual_unaccounted"]
    out["NUE_removed_over_inputs"] = terms["crop_N_removed"] / tin if tin else float("nan")
    return out
