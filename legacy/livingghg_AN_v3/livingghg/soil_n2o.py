"""Direct (Eq 11.1) and indirect (Eq 11.9, 11.10) N2O from managed soils, Tier 1 (2006) / Tier 1-2 disaggregated (2019).
Inputs in kg N/yr. Returns kg N2O/yr."""
N2ON_TO_N2O = 44.0 / 28.0

def soil_n2o(farm, guideline, P, forks=None):
    f = dict(forks or {})
    clim = f.get("climate", farm.get("climate", "wet"))
    FSN, FON, FCR, FSOM = (farm.get(k, 0.0) for k in ("F_SN", "F_ON", "F_CR", "F_SOM"))
    FPRP = farm.get("F_PRP_CPP", 0.0)
    if f.get("crop_residue") == "exclude":
        FCR = 0.0
    if guideline == "IPCC2019" and f.get("ef1_mode", "disaggregated") == "disaggregated":
        if clim == "wet":
            direct = FSN * P.get(guideline, "EF1", "wet_synthetic") + (FON + FCR + FSOM) * P.get(guideline, "EF1", "wet_other")
        else:
            direct = (FSN + FON + FCR + FSOM) * P.get(guideline, "EF1", "dry")
        ef3 = P.get(guideline, "EF3PRP_CPP", clim)
        ef4 = P.get(guideline, "EF4", clim)
    else:
        direct = (FSN + FON + FCR + FSOM) * P.get(guideline, "EF1")
        ef3 = P.get(guideline, "EF3PRP_CPP")
        ef4 = P.get(guideline, "EF4")
    direct += FPRP * ef3
    fgasf_key = f.get("fracgasf", "all")
    if guideline == "IPCC2006":
        fgasf_key = "all"
    vol = (FSN * P.get(guideline, "FracGASF", fgasf_key) + (FON + FPRP) * P.get(guideline, "FracGASM")) * ef4
    leach_frac = P.get(guideline, "FracLEACH", "wet") if clim == "wet" else P.get(guideline, "FracLEACH", "dry", allow_unverified=f.get("allow_unverified", False)) if guideline == "IPCC2019" else P.get(guideline, "FracLEACH", "wet")
    leach = (FSN + FON + FPRP + FCR + FSOM) * leach_frac * P.get(guideline, "EF5")
    conv = 1.0 if f.get("unit_bug") == "omit_44_28" else N2ON_TO_N2O
    return {"direct": direct * conv, "indirect_vol": vol * conv, "indirect_leach": leach * conv,
            "total": (direct + vol + leach) * conv}
