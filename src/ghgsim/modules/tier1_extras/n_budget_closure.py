"""Extra N inputs and a budget-consistent leaching base for the soil-surface N budget (AN_v1 of the closure step).

Terms
-----
* ``soybean_bnf_full_kg``  - soybean BNF including below-ground N. Above-ground plant N (seed + above-ground residue)
  is divided by (1 - BG share) to give total plant N, then multiplied by %Ndfa (share of plant N derived from the air).
  Salvagiotti et al. 2008 (abstract): Ndfa 50-60 %, below-ground = 24 % of total plant N.
* ``soybean_bnf_per_grain_kg`` - independent cross-check: g N fixed per kg grain (Gelfand & Robertson 2015).
* ``alfalfa_bnf_kg`` - fixed N = kg N/ha x area (Russelle & Birr 2004 basin mean).
* ``deposition_n_kg`` - atmospheric N deposition = kg N/ha x area (NADP TDep gridded, county mean).
* ``leach_budget_kg`` - IPCC Eq 11.10 leaching applied only to the N that the budget counts as an input
  (F_SN + F_ON + F_PRP + F_SOM). IPCC Eq 11.10 also includes F_CR (crop residue N), which is recycled N and is not an
  input of this budget; including it books a loss of N that was never booked as an input (see DECISIONS_ohio_AN_v4).
* ``n_budget_v2`` - the budget identity with the extra inputs. residual = inputs - outputs, exact by construction.

Nothing here is calibrated: every coefficient is passed in by the caller from ``data/ipcc_params_AN_v12.csv``.
"""
from __future__ import annotations

from collections.abc import Mapping

IN_TERMS_V2 = ("synthetic_N", "manure_N_applied", "PRP_N", "BNF_soy_total", "BNF_alfalfa", "N_deposition", "F_SOM")
OUT_TERMS_V2 = ("crop_N_removed", "soil_volatilised", "soil_leached", "soil_N2O_N_direct")


def soybean_bnf_full_kg(seed_n_kg: float, ag_residue_n_kg: float, ndfa: float, bg_share_total_n: float) -> dict[str, float]:
    """Return above-ground, below-ground and total fixed N (kg).

    total plant N = (seed N + above-ground residue N) / (1 - bg_share); below-ground N = total - above-ground;
    fixed N = ndfa x plant N for each pool (the same Ndfa is assumed for below-ground N)."""
    if not 0.0 <= ndfa <= 1.0:
        raise ValueError("ndfa must be in [0, 1]")
    if not 0.0 <= bg_share_total_n < 1.0:
        raise ValueError("bg_share_total_n must be in [0, 1)")
    ag_n = seed_n_kg + ag_residue_n_kg
    total_n = ag_n / (1.0 - bg_share_total_n)
    bg_n = total_n - ag_n
    return dict(plant_N_AG=ag_n, plant_N_BG=bg_n, plant_N_total=total_n, BNF_AG=ndfa * ag_n, BNF_BG=ndfa * bg_n,
                BNF_total=ndfa * total_n)


def soybean_bnf_per_grain_kg(grain_kg: float, g_n_per_kg_grain: float) -> float:
    """Whole-plant fixed N (kg) = grain mass (kg) x g N per kg grain / 1000."""
    if grain_kg < 0 or g_n_per_kg_grain < 0:
        raise ValueError("grain_kg and g_n_per_kg_grain must be >= 0")
    return grain_kg * g_n_per_kg_grain / 1000.0


def alfalfa_bnf_kg(area_ha: float, kg_n_per_ha: float) -> float:
    if area_ha < 0 or kg_n_per_ha < 0:
        raise ValueError("area_ha and kg_n_per_ha must be >= 0")
    return area_ha * kg_n_per_ha


def deposition_n_kg(kg_n_per_ha: float, area_ha: float) -> float:
    if area_ha < 0 or kg_n_per_ha < 0:
        raise ValueError("area_ha and kg_n_per_ha must be >= 0")
    return kg_n_per_ha * area_ha


def leach_budget_kg(frac_leach: float, f_sn: float, f_on: float, f_prp: float, f_som: float) -> float:
    """Eq 11.10 leaching on budget inputs only (no F_CR)."""
    if not 0.0 <= frac_leach <= 1.0:
        raise ValueError("frac_leach must be in [0, 1]")
    return frac_leach * (f_sn + f_on + f_prp + f_som)


def n_budget_v2(terms: Mapping[str, float]) -> dict[str, float]:
    """Budget with the extra inputs. Adds inputs_total, outputs_total, residual_unaccounted, closure_error, NUE."""
    missing = [k for k in IN_TERMS_V2 + OUT_TERMS_V2 if k not in terms]
    if missing:
        raise KeyError(f"missing budget terms: {missing}")
    out = dict(terms)
    tin = sum(float(terms[k]) for k in IN_TERMS_V2)
    tout = sum(float(terms[k]) for k in OUT_TERMS_V2)
    out["inputs_total"], out["outputs_total"] = tin, tout
    out["residual_unaccounted"] = tin - tout
    out["closure_error"] = tin - tout - out["residual_unaccounted"]
    out["NUE_removed_over_inputs"] = terms["crop_N_removed"] / tin if tin else float("nan")
    return out
