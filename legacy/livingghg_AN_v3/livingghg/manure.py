"""Manure management CH4 (Eq 10.23) and N2O: direct (Eq 10.25) and indirect via volatilisation/leaching
(Eq 10.26-10.29), IPCC 2006 vs 2019 Refinement. Returns kg/yr for one herd.

herd["manure"] = {"region": "north_america", "animal": "dairy"|"other_cattle",
                  "systems": {system: fraction}, "mcf_zone": {"IPCC2006": "15C", "IPCC2019": "temperate"},
                  optional "VS_kg_day", "TAM_kg", "Nex_kg_yr"}
System names map to table keys per guideline via SYSTEM_MAP. Liquid systems are guideline-specific.
"""
N2ON_TO_N2O = 44.0 / 28.0

# canonical system -> (MCF key, EF3 key, FracGas key) per guideline
SYSTEM_MAP = {
    "IPCC2006": {"liquid_nocrust": ("liquid_nocrust", "liquid_nocrust", "liquid_slurry"),
                 "liquid_crust": ("liquid_crust", "liquid_crust", "liquid_slurry"),
                 "lagoon": ("lagoon", "lagoon", "lagoon"),
                 "solid_storage": ("solid_storage", "solid_storage", "solid_storage"),
                 "dry_lot": ("dry_lot", "dry_lot", "dry_lot"),
                 "daily_spread": ("daily_spread", "daily_spread", "daily_spread"),
                 "pasture": ("pasture", None, None)},
    "IPCC2019": {"liquid_nocrust": ("liquid_6mo", "liquid_nocrust", "liquid_nocrust"),
                 "liquid_crust": ("liquid_6mo", "liquid_crust", "liquid_crust"),
                 "lagoon": ("lagoon", "lagoon", "lagoon"),
                 "solid_storage": ("solid_storage", "solid_storage", "solid_storage"),
                 "dry_lot": ("dry_lot", "dry_lot", "dry_lot"),
                 "daily_spread": ("daily_spread", "daily_spread", "daily_spread"),
                 "pasture": ("pasture", None, None)},
}
# 2019 MCF zone for liquid/lagoon (moisture-specific) vs solid/dry lot/daily spread (cool/temperate/warm)
ZONE_2019_COARSE = {"cool_temperate_moist": "cool", "cool_temperate_dry": "cool",
                    "warm_temperate_moist": "temperate", "warm_temperate_dry": "temperate"}

def _mcf(P, g, mkey, zone, forks):
    if g == "IPCC2019":
        if mkey == "pasture":
            return P.get(g, "MCF", "pasture|all")
        if mkey in ("lagoon", "liquid_6mo", "liquid_12mo"):
            if mkey == "liquid_6mo" and forks.get("liquid_retention") == "12mo":
                mkey = "liquid_12mo"
            return P.get(g, "MCF", f"{mkey}|{zone}")
        return P.get(g, "MCF", f"{mkey}|{ZONE_2019_COARSE.get(zone, zone)}")
    if mkey == "pasture":
        zone = "le10C" if zone == "le10C" else "15C"
    return P.get(g, "MCF", f"{mkey}|{zone}")

def manure_emissions(herd, guideline, P, forks=None, soil_climate="wet"):
    f = dict(forks or {})
    m = herd["manure"]; g = guideline
    key = f"{m['animal']}|{m['region']}"
    head = herd["head"]
    tam = m.get("TAM_kg") or P.get(g, "TAM", key)
    nex = m.get("Nex_kg_yr") or P.get(g, "Nrate", key) * tam / 1000.0 * 365.0
    vs = m.get("VS_kg_day") or P.get(g, "VS", key)
    b0 = P.get(g, "B0", key)
    zone = m["mcf_zone"][g]
    ch4_sum = 0.0; n_direct = n_vol = n_leach = n_prp = 0.0
    for sysn, frac in m["systems"].items():
        mkey, ekey, gkey = SYSTEM_MAP[g][sysn]
        ch4_sum += _mcf(P, g, mkey, zone, f) * frac
        n = head * nex * frac
        if sysn == "pasture":   # PRP N goes to managed soils (Ch11 EF3PRP), not manure management
            n_prp += n; continue
        n_direct += n * P.get(g, "EF3", ekey)
        n_vol += n * P.get(g, "FracGasMS", f"{m['animal']}|{gkey}")
        if g == "IPCC2019":
            n_leach += n * P.get(g, "FracLeachMS", f"{m['animal']}|{gkey}")
        # 2006: no default FracLeachMS (UNVERIFIED, country-specific) -> leaching omitted
    ch4 = head * vs * 365.0 * b0 * P.get(g, "CH4_M3_TO_KG") * ch4_sum
    if g == "IPCC2019" and f.get("ef1_mode", "disaggregated") == "disaggregated":
        ef4 = P.get(g, "EF4", soil_climate)
    else:
        ef4 = P.get(g, "EF4")
    ef5 = P.get(g, "EF5")
    return {"CH4": ch4, "N2O_direct": n_direct * N2ON_TO_N2O, "N2O_vol": n_vol * ef4 * N2ON_TO_N2O,
            "N2O_leach": n_leach * ef5 * N2ON_TO_N2O, "Nex_kg_head": nex, "N_PRP_kg": n_prp,
            "N2O_total": (n_direct + n_vol * ef4 + n_leach * ef5) * N2ON_TO_N2O}
