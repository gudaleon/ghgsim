"""Residue N for hay, haylage and silage (IPCC Tier 1).

2006: Eq 11.7A (Vol4 Ch11 p. 11.15) with Table 11.2 (pp. 11.17-11.18):
    F_CR = Area * [AGDM * N_AG * (1 - FracRemove) + FracRenew * (AGDM + Crop) * R_BG-BIO * N_BG],
    AGDM (kg/ha) = (Crop/1000 * slope + intercept) * 1000.
2019: Eq 11.6 (Updated) (p. 11.16): AGR = AGDM * Area; BGR = (Crop + AGDM) * RS * Area * FracRenew, with
    N_AG, N_BG, RS from Table 11.1a (New) (p. 11.18). Alfalfa and non-legume hay have no R_AG (footnote e), so AGDM
    comes from Table 11.2 (Updated) (p. 11.19), as the Eq 11.6 text (p. 11.17) allows.
FracRenew: the equations apply it to the below-ground term only. IPCC text says perennial-forage residue N is counted
at renewal (2006 Ch11 footnote 3, p. 11.7) while the alfalfa / hay R_BG-BIO and RS are described as annual root
turnover in perennial systems (Table footnotes n / g). Callers pass FracRenew explicitly; the runner reports the
bounds 1 (annual turnover) and 0 (renewal not counted).
Silage: no IPCC silage row. Whole-plant harvest means AG residue is removed (AGDM taken as 0) and roots follow the
maize factors (2006 R_BG-BIO 0.22, N_BG 0.007; 2019 RS 0.22, N_BG 0.007) applied to the harvested whole-plant DM.
"""
from __future__ import annotations

from collections.abc import Mapping

FORAGE_ROWS = ("alfalfa", "nonlegume_hay", "n_fixing_forages", "non_n_fixing_forages", "perennial_grasses", "grass_clover")


def _agdm(p: Mapping[str, float], ver: str, row: str, crop_dm_kg_ha: float) -> float:
    if ver == "2006":
        return (crop_dm_kg_ha / 1000.0 * p[f"IPCC2006.RES.{row}.slope"] + p[f"IPCC2006.RES.{row}.intercept"]) * 1000.0
    rag = p.get(f"IPCC2019.RES.{row}.R_AG")
    if rag is not None:
        return crop_dm_kg_ha * rag
    return crop_dm_kg_ha * p[f"IPCC2019.RES.{row}.slope"] + p[f"IPCC2019.RES.{row}.intercept"]


def forage_residue_n(p: Mapping[str, float], ver: str, row: str, area_ha: float, crop_dm_kg_ha: float,
                     frac_renew: float = 1.0, frac_remove: float = 0.0) -> dict[str, float]:
    """kg N/yr in above- and below-ground residues of a forage crop. ``crop_dm_kg_ha`` is harvested dry matter."""
    if row not in FORAGE_ROWS:
        raise KeyError(row)
    if not 0.0 <= frac_renew <= 1.0 or not 0.0 <= frac_remove <= 1.0:
        raise ValueError("fractions must be in [0, 1]")
    if area_ha <= 0 or crop_dm_kg_ha <= 0:
        return {"AG": 0.0, "BG": 0.0, "total": 0.0, "AGDM_kg_ha": 0.0}
    agdm = _agdm(p, ver, row, crop_dm_kg_ha)
    if ver == "2006":
        ag = area_ha * agdm * p[f"IPCC2006.RES.{row}.N_AG"] * (1.0 - frac_remove)
        bg = area_ha * frac_renew * (agdm + crop_dm_kg_ha) * p[f"IPCC2006.RES.{row}.R_BG_BIO"] * p[f"IPCC2006.RES.{row}.N_BG"]
    else:
        ag = area_ha * agdm * p[f"IPCC2019.RES.{row}.N_AG"] * (1.0 - frac_remove)
        bg = area_ha * frac_renew * (agdm + crop_dm_kg_ha) * p[f"IPCC2019.RES.{row}.RS"] * p[f"IPCC2019.RES.{row}.N_BG"]
    return {"AG": ag, "BG": bg, "total": ag + bg, "AGDM_kg_ha": agdm}


def silage_residue_n(p: Mapping[str, float], ver: str, area_ha: float, whole_plant_dm_kg_ha: float) -> dict[str, float]:
    """kg N/yr in below-ground residue of corn silage (maize root factors; AG residue removed with the harvest)."""
    if area_ha <= 0 or whole_plant_dm_kg_ha <= 0:
        return {"AG": 0.0, "BG": 0.0, "total": 0.0}
    if ver == "2006":
        bg = area_ha * whole_plant_dm_kg_ha * p["IPCC2006.RES.maize.R_BG_BIO"] * p["IPCC2006.RES.maize.N_BG"]
    else:
        bg = area_ha * whole_plant_dm_kg_ha * p["IPCC2019.RES.maize.RS"] * p["IPCC2019.RES.maize.N_BG"]
    return {"AG": 0.0, "BG": bg, "total": bg}
