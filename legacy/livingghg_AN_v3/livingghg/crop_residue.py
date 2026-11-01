"""IPCC 2019 Refinement Eq 11.6 (Updated) and Eq 11.7: N in crop residues returned to soils (F_CR), kg N/yr.
Annual crops: FracRenew = 1. FracRemove and FracBurnt default to 0 (IPCC: assume no removal if no data)."""
import pandas as pd

def f_cr(area_ha, yield_fresh_kg_ha, p, frac_remove=0.0, frac_burnt=0.0, cf=0.0):
    crop = yield_fresh_kg_ha * p["DRY"]                     # Eq 11.7
    agdm = crop * p["R_AG"]                                 # AGDM = Crop * RAG
    agr = agdm * area_ha
    bgr = (crop + agdm) * p["RS"] * area_ha * 1.0           # FracRenew = 1 for annual crops
    return agr * p["N_AG"] * (1 - frac_remove - frac_burnt * cf) + bgr * p["N_BG"]

def county_f_cr(crops_df, params_df):
    """crops_df: NASS county rows for '<crop> - ACRES HARVESTED' and '<crop> - PRODUCTION, MEASURED IN BU'.
    Returns DataFrame fips -> F_CR_kgN (counties with (D) area or production contribute 0 for that crop; flagged)."""
    d = crops_df.copy()
    d["v"] = pd.to_numeric(d.VALUE.astype(str).str.replace(",", "").str.strip(), errors="coerce")
    d["fips"] = d.STATE_FIPS_CODE.astype(str).str.zfill(2) + d.COUNTY_CODE.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(3)
    out = {}
    flags = {}
    for p in params_df.to_dict("records"):
        a = d[d.SHORT_DESC == f"{p['nass_short_desc']} - ACRES HARVESTED"].set_index("fips").v
        q = d[d.SHORT_DESC == f"{p['nass_short_desc']} - PRODUCTION, MEASURED IN BU"].set_index("fips").v
        for f in a.index.union(q.index):
            A, Q = a.get(f), q.get(f)
            if pd.notna(A) and pd.notna(Q) and A > 0:
                ha = A * 0.40468564224                        # acre -> ha (exact definition)
                out[f] = out.get(f, 0.0) + f_cr(ha, Q * p["kg_per_bu"] / ha, p)
            else:
                flags[f] = flags.get(f, "") + f"{p['crop']}:withheld_or_missing;"
                out.setdefault(f, 0.0)
    return pd.DataFrame({"fips": list(out), "F_CR_kgN": list(out.values()),
                         "F_CR_flag": [flags.get(f, "") for f in out]})
