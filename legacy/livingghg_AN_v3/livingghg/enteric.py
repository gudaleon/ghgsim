"""Tier 2 enteric CH4, Eq 10.21: EF = GE * Ym/100 * 365 / 55.65 (kg CH4/head/yr)."""

def enteric_ch4(herd, guideline, P, forks=None):
    f = dict(forks or {})
    if f.get("ge_source") == "from_dmi":
        ge = herd["DMI_kg_day"] * P.get(guideline, "GE_PER_KG_DM")
    else:
        ge = herd["GE_MJ_day"]
    cat = herd["ym_category"][guideline]
    if "ym_category" in f and guideline == "IPCC2019" and cat.startswith("dairy"):
        cat = f["ym_category"]   # fork F007 applies to 2019 dairy categories only
    if herd.get("Ym_pct") is not None and f.get("ym_source", "epa_state") == "epa_state":
        ym = float(herd["Ym_pct"])   # fork F013: EPA state/regional Ym (input data, not an IPCC table value)
    else:
        ym = P.get(guideline, "Ym", cat)
    ef = ge * ym / 100.0 * 365.0 / P.get(guideline, "CH4_ENERGY")
    return {"EF_kg_head": ef, "total": ef * herd["head"]}
