"""F_SOM: N mineralised from loss of soil organic C in mineral soils (IPCC Tier 1).

Opened sources (page = printed page):
  * 2006 Vol4 Ch2 Eq 2.25 (p. 2.30): dC = (SOC_0 - SOC_(0-T)) / D, SOC = sum SOCref * FLU * FMG * FI * A; D = 20 yr
    (T replaces D only when T >= 20 yr).
  * SOCref: 2006 Ch2 Table 2.3 (p. 2.31); 2019 Ch2 Table 2.3 (Updated) (p. 2.34).
  * FLU / FMG / FI: 2006 Ch5 Table 5.5 (pp. 5.17-5.18); 2019 Ch5 Table 5.5 (Updated) (pp. 5.27-5.28).
  * Eq 11.8 (2006 Ch11 p. 11.16; 2019 Ch11 p. 11.20): F_SOM = sum dC_loss * (1/R) * 1000, R = 10 for management
    change on Cropland Remaining Cropland, 15 for land-use change to cropland. Only C LOSSES mineralise N
    (gains are not credited; 2006 p. 11.15 note). Tier 1 / Approach 1 uses a single dC for the area.

Tillage mapping (Table 5.5 descriptions): conventional tillage -> 'full'; conservation tillage excluding no-till
(>30% residue cover) -> 'reduced'; no-till -> 'no_till'.
"""
from __future__ import annotations

from collections.abc import Mapping

TILL_LEVELS = ("full", "reduced", "no_till")


def _zone_key(zone: str) -> str:
    z = zone.replace("-", "_").lower()
    if z not in ("cool_temperate_moist", "warm_temperate_moist", "cool_temperate_dry", "warm_temperate_dry"):
        raise ValueError(f"F_SOM factors are loaded only for temperate zones, got {zone!r}")
    return z


def soc_stock_t(p: Mapping[str, float], ver: str, zone: str, soil: str, shares: Mapping[str, float], area_ha: float) -> float:
    """Tier 1 SOC stock (t C) of cropland area split into tillage shares (sum to 1), medium input (FI)."""
    z = _zone_key(zone)
    tot = sum(shares.get(k, 0.0) for k in TILL_LEVELS)
    if area_ha <= 0 or tot <= 0:
        return 0.0
    socref = p[f"IPCC{ver}.SOCref.{z}|{soil}"]
    flu = p[f"IPCC{ver}.FLU.long_term_cultivated|{z}"]
    fi = p[f"IPCC{ver}.FI.medium"]
    fmg = sum(p[f"IPCC{ver}.FMG.{k}|{z}"] * shares.get(k, 0.0) / tot for k in TILL_LEVELS)
    return socref * flu * fmg * fi * area_ha


def tillage_soc_change_t(p: Mapping[str, float], ver: str, zone: str, soil: str, shares_start: Mapping[str, float],
                         shares_end: Mapping[str, float], area_ha: float, years: float) -> float:
    """Annual mineral-soil C stock change (t C / yr, negative = loss), Eq 2.25 with the same area at both dates."""
    d = p["IPCC2006.SOC.D_years"]
    denom = years if years >= d else d
    return (soc_stock_t(p, ver, zone, soil, shares_end, area_ha) - soc_stock_t(p, ver, zone, soil, shares_start, area_ha)) / denom


def fsom_kg_n(delta_c_t: float, r_cn: float) -> float:
    """Eq 11.8: kg N mineralised per year from an annual C change (t C / yr). Gains give 0."""
    if r_cn <= 0:
        raise ValueError("C:N ratio must be positive")
    return max(0.0, -delta_c_t) * 1000.0 / r_cn
