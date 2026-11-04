"""US county IPCC 2006 vs 2019 Tier 1 run, extended scope (AN_v2).

Changes vs AN_v1 (see docs/US_COUNTY_RUN_AN_v2.md, docs/DECISIONS_AN_v5.md):
  * Three activity variants: disclosed (as v1), reconstructed (exact Census identities fill withheld
    cattle cells), D_allocated (reconstructed + state remainder of each withheld (D) series allocated to
    withheld counties in proportion to the disclosed 'OPERATIONS WITH INVENTORY' count; equal shares if
    none). D_allocated is the headline variant.
  * Sheep, goats, horses & ponies, mules/burros/donkeys (enteric, manure CH4, PRP N2O).
  * Pullets split from layers.
  * Crop residue N (FCR) for 16 annual crops from 2022 Census harvested area and production, with
    2006 Table 11.2 (Eq 11.7A) and 2019 Table 11.1a (Eq 11.6) factors; rice uses EF1FR.
  * Indirect soil N2O reported as separate volatilisation and leaching rows.
  * 2019 runs use 2019 VS rates (Table 10.13A) and live weights (Table 10A.5); 2006 unchanged.
  * 2006 FracGasMS cells absent from Table 10.22 stay unfilled (no volatilisation computed), but their N
    now flows to soils instead of being dropped.
Inputs as v1 plus --shp cb_2021_us_county_20m.zip (pre-2022 Connecticut counties, matching NASS 2022).
Refuses to overwrite outputs.
"""
from __future__ import annotations
import argparse, csv, gzip, importlib.util, json, math, pathlib, sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("v1", ROOT / "scripts" / "run_us_county_2006_vs_2019_AN_v1.py")
v1 = importlib.util.module_from_spec(_s); _s.loader.exec_module(v1)
OUT = ROOT / "data" / "us_county_2006_vs_2019_AN_v2.csv.gz"
OUT_NAT = ROOT / "data" / "us_national_2006_vs_2019_vs_epa_AN_v2.csv"
MAN = ROOT / "data" / "us_county_run_manifest_AN_v2.json"
MAP = ROOT / "docs" / "figures" / "us_county_pct_change_2006_2019_AN_v2.png"
PARAMS = ROOT / "data" / "ipcc_params_AN_v10.csv"
GWP, N2O_N, EPA_2022 = v1.GWP, v1.N2O_N, v1.EPA_2022
AC_HA, LB_KG = 0.40468564224, 0.45359237

LIVE = {  # census short_desc stem -> key
    "CATTLE, INCL CALVES": "cattle_total", "CATTLE, COWS": "cows", "CATTLE, COWS, BEEF": "beef_cows",
    "CATTLE, (EXCL COWS)": "excl_cows", "CATTLE, COWS, MILK": "dairy", "HOGS": "swine",
    "CHICKENS, LAYERS": "layers_hens", "CHICKENS, PULLETS, REPLACEMENT": "pullets", "CHICKENS, ROOSTERS": "roosters",
    "CHICKENS, BROILERS": "broilers", "TURKEYS": "turkeys", "SHEEP, INCL LAMBS": "sheep", "GOATS": "goats",
    "EQUINE, HORSES & PONIES": "horses", "EQUINE, MULES & BURROS & DONKEYS": "mules_asses"}
# crop key: (area desc, production desc, lb per unit, 2006 row, 2019 row). Bushel weights: USDA ERS AH-697.
CROPS = {
    "corn_grain": ("CORN, GRAIN - ACRES HARVESTED", "CORN, GRAIN - PRODUCTION, MEASURED IN BU", 56, "maize", "maize"),
    "soybeans": ("SOYBEANS - ACRES HARVESTED", "SOYBEANS - PRODUCTION, MEASURED IN BU", 60, "soybeans", "soybeans"),
    "wheat_winter": ("WHEAT, WINTER - ACRES HARVESTED", "WHEAT, WINTER - PRODUCTION, MEASURED IN BU", 60, "winter_wheat", "winter_wheat"),
    "wheat_spring": ("WHEAT, SPRING, (EXCL DURUM) - ACRES HARVESTED", "WHEAT, SPRING, (EXCL DURUM) - PRODUCTION, MEASURED IN BU", 60, "spring_wheat", "spring_wheat"),
    "wheat_durum": ("WHEAT, SPRING, DURUM - ACRES HARVESTED", "WHEAT, SPRING, DURUM - PRODUCTION, MEASURED IN BU", 60, "spring_wheat", "spring_wheat"),
    "barley": ("BARLEY - ACRES HARVESTED", "BARLEY - PRODUCTION, MEASURED IN BU", 48, "barley", "barley"),
    "oats": ("OATS - ACRES HARVESTED", "OATS - PRODUCTION, MEASURED IN BU", 32, "oats", "oats"),
    "sorghum_grain": ("SORGHUM, GRAIN - ACRES HARVESTED", "SORGHUM, GRAIN - PRODUCTION, MEASURED IN BU", 56, "sorghum", "sorghum"),
    "rye": ("RYE - ACRES HARVESTED", "RYE - PRODUCTION, MEASURED IN BU", 56, "rye", "rye"),
    "rice": ("RICE - ACRES HARVESTED", "RICE - PRODUCTION, MEASURED IN CWT", 100, "rice", "rice"),
    "millet_proso": ("MILLET, PROSO - ACRES HARVESTED", "MILLET, PROSO - PRODUCTION, MEASURED IN BU", 50, "millet", "millet"),
    "beans_dry": ("BEANS, DRY EDIBLE, (EXCL CHICKPEAS & LIMA) - ACRES HARVESTED", "BEANS, DRY EDIBLE, (EXCL CHICKPEAS & LIMA) - PRODUCTION, MEASURED IN CWT", 100, "dry_bean", "beans_pulses"),
    "beans_lima": ("BEANS, DRY EDIBLE, LIMA - ACRES HARVESTED", "BEANS, DRY EDIBLE, LIMA - PRODUCTION, MEASURED IN CWT", 100, "dry_bean", "beans_pulses"),
    "chickpeas": ("CHICKPEAS - ACRES HARVESTED", "CHICKPEAS - PRODUCTION, MEASURED IN CWT", 100, "beans_pulses", "beans_pulses"),
    "lentils": ("LENTILS - ACRES HARVESTED", "LENTILS - PRODUCTION, MEASURED IN CWT", 100, "beans_pulses", "beans_pulses"),
    "peas_dry": ("PEAS, DRY EDIBLE - ACRES HARVESTED", "PEAS, DRY EDIBLE - PRODUCTION, MEASURED IN CWT", 100, "beans_pulses", "beans_pulses"),
    "cowpeas": ("PEAS, DRY, SOUTHERN (COWPEAS) - ACRES HARVESTED", "PEAS, DRY, SOUTHERN (COWPEAS) - PRODUCTION, MEASURED IN BU", 60, "beans_pulses", "beans_pulses"),
    "potatoes": ("POTATOES - ACRES HARVESTED", "POTATOES - PRODUCTION, MEASURED IN CWT", 100, "potato", "potatoes_tubers"),
    "peanuts": ("PEANUTS - ACRES HARVESTED", "PEANUTS - PRODUCTION, MEASURED IN LB", 1, "peanut", "peanuts"),
}
SERIES = {}
for stem, k in LIVE.items():
    SERIES[f"{stem} - INVENTORY"] = k
    SERIES[f"{stem} - OPERATIONS WITH INVENTORY"] = k + "_ops"
SERIES["FERTILIZER TOTALS, INCL LIME & SOIL CONDITIONERS - EXPENSE, MEASURED IN $"] = "fert_expense"
for c, (a_, p_, *_r) in CROPS.items():
    SERIES[a_] = c + "_ac"; SERIES[p_] = c + "_prod"
ALLOC = [k for k in LIVE.values()] + ["fert_expense"] + [c + "_ac" for c in CROPS] + [c + "_prod" for c in CROPS]
CLASSES = ["dairy", "other_cattle", "swine", "layers", "pullets", "broilers", "turkeys", "sheep", "goats", "horses", "mules_asses"]
SMALL_RUM = ("sheep", "goats", "horses", "mules_asses")


def read_nass(path):
    county, state = defaultdict(dict), defaultdict(dict)
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            k = SERIES.get(r["SHORT_DESC"])
            if not k or r["DOMAIN_DESC"] != "TOTAL" or r["YEAR"] != "2022":
                continue
            if r["AGG_LEVEL_DESC"] == "COUNTY" and r["COUNTY_CODE"] != "998":
                f_ = r["STATE_FIPS_CODE"] + r["COUNTY_CODE"]
                county[f_][k] = v1.num(r["VALUE"]); county[f_]["_name"] = (r["STATE_ALPHA"], r["COUNTY_NAME"])
            elif r["AGG_LEVEL_DESC"] == "STATE":
                state[r["STATE_FIPS_CODE"]][k] = v1.num(r["VALUE"]); state[r["STATE_FIPS_CODE"]]["_name"] = r["STATE_NAME"]
    return county, state


def val(c, k):
    v = c.get(k)
    return 0.0 if v is None else v[0]  # absent series = none reported; None = withheld


def reconstruct(c):
    """Exact Census identities: total = cows + excl_cows; cows = dairy + beef_cows. Returns dict + notes."""
    d = {k: val(c, k) for k in ("cattle_total", "cows", "beef_cows", "excl_cows", "dairy")}
    notes = []
    for _ in range(3):
        if d["dairy"] is None and d["cows"] is not None and d["beef_cows"] is not None:
            d["dairy"] = max(0.0, d["cows"] - d["beef_cows"]); notes.append("dairy=cows-beef")
        if d["beef_cows"] is None and d["cows"] is not None and d["dairy"] is not None:
            d["beef_cows"] = max(0.0, d["cows"] - d["dairy"]); notes.append("beef=cows-dairy")
        if d["cows"] is None and d["dairy"] is not None and d["beef_cows"] is not None:
            d["cows"] = d["dairy"] + d["beef_cows"]; notes.append("cows=dairy+beef")
        if d["cattle_total"] is None and d["cows"] is not None and d["excl_cows"] is not None:
            d["cattle_total"] = d["cows"] + d["excl_cows"]; notes.append("total=cows+excl")
        if d["excl_cows"] is None and d["cattle_total"] is not None and d["cows"] is not None:
            d["excl_cows"] = max(0.0, d["cattle_total"] - d["cows"]); notes.append("excl=total-cows")
    return d, notes


def allocate(county, state, recon):
    """State remainder for each withheld cell, allocated by disclosed operations count (else equal)."""
    out = {}
    for k in ALLOC:
        for sf, sd in state.items():
            st = sd.get(k, (None, ""))[0]
            cs = [f for f in county if f[:2] == sf]
            def cv(f):
                return recon[f][0].get(k, val(county[f], k)) if k in recon[f][0] else val(county[f], k)
            dcs = [f for f in cs if cv(f) is None]
            if st is None or not dcs:
                continue
            resid = max(0.0, st - sum(cv(f) for f in cs if cv(f) is not None))
            ok = k + "_ops"
            wts = {f: (val(county[f], ok) or 0.0) for f in dcs} if ok.replace("_ops", "") in LIVE.values() else {f: 1.0 for f in dcs}
            tw = sum(wts.values())
            for f in dcs:
                out[(f, k)] = resid * (wts[f] / tw if tw else 1.0 / len(dcs))
    return out


def P():
    return {r["key"]: float(r["value"]) for r in csv.DictReader(open(PARAMS, encoding="utf-8"))}


CLS6 = {"dairy": "dairy", "other_cattle": "other_cattle", "swine": "market_swine", "layers": "layers", "pullets": "layers",
        "broilers": "broilers", "turkeys": "turkeys"}
CLS19 = {"dairy": "dairy", "other_cattle": "other_cattle", "swine": "market_swine", "layers": "layers", "pullets": "pullets",
         "broilers": "broilers", "turkeys": "turkeys"}
B0_19 = {"dairy": "dairy", "other_cattle": "other_cattle", "swine": "swine", "layers": "layers", "pullets": "layers",
         "broilers": "other_poultry", "turkeys": "other_poultry"}


def tgrp06(T):
    return "cool" if T < 15 else ("temperate" if T <= 25 else "warm")


def zgrp19(zone, T):
    if zone is None:
        return tgrp06(T)
    if zone.startswith(("cool", "boreal")):
        return "cool"
    return "temperate" if zone.startswith("warm") else "warm"


def county_calc(p, ms, ver, heads, fsn, crops, T, zone, zone19, wet):
    out, gaps = defaultdict(float), []
    nprp = nprp_so = nman = 0.0
    ef4m = p["IPCC2006.EF4.all"] if ver == "2006" else p["IPCC2019.EF4." + ("wet" if wet else "dry")]
    for cls in CLASSES:
        h = heads.get(cls)
        if h is None or h == 0:
            continue
        if cls in SMALL_RUM:
            ef = p[f"IPCC2006.EF_enteric.{cls}|developed"] if ver == "2006" else p[f"IPCC2019.EF_enteric.{cls}|high_productivity"]
            out[("enteric", cls, "CH4")] += h * ef
            if ver == "2006":
                out[("manure_ch4", cls, "CH4")] += h * p[f"IPCC2006.EF_manureCH4.{cls}|developed_{tgrp06(T)}"]
            else:  # DECISIONS_AN_v5 #6: dry lot, the 'dry systems' basis of 2006 Table 10A-9
                vs = p[f"IPCC2019.VSrate.{cls}|north_america"] * p[f"IPCC2019.TAM.{cls}|north_america"] / 1000 * 365
                out[("manure_ch4", cls, "CH4")] += h * vs * p[f"IPCC2019.EF_manureCH4_VS.{cls}|dry_lot|{zgrp19(zone19, T)}"] / 1000
            nk = "horses" if cls == "mules_asses" else cls
            nex = p[f"IPCC{ver}.Nrate.{nk}|north_america"] * p[f"IPCC{ver}.TAM.{cls}|north_america"] / 1000 * 365
            nprp_so += h * nex  # DECISIONS_AN_v5 #6: all N deposited on pasture/range/paddock
            continue
        if cls in ("dairy", "other_cattle"):
            ef = p[f"IPCC{ver}.EF_enteric.{cls}|north_america"]
        elif cls == "swine":
            ef = p["IPCC2006.EF_enteric.swine|developed"] if ver == "2006" else p["IPCC2019.EF_enteric.swine|high_productivity"]
        else:
            ef = 0.0
        if ef:
            out[("enteric", cls, "CH4")] += h * ef
        if ver == "2006":
            c6 = CLS6[cls]
            vs = p[f"IPCC2006.VS.{c6}|north_america"]; tam = p[f"IPCC2006.TAM.{c6}|north_america"]
            nrate = p[f"IPCC2006.Nrate.{'pullets' if cls == 'pullets' else c6}|north_america"]
            b0 = p[f"IPCC2006.B0.{c6}|north_america"]
        else:
            c9 = CLS19[cls]
            tam = p[f"IPCC2019.TAM.{c9}|north_america"]
            vs = p[f"IPCC2019.VSrate.{c9}|north_america"] * tam / 1000.0
            nrate = p[f"IPCC2019.Nrate.{c9}|north_america"]
            b0 = p[f"IPCC2019.B0.{B0_19[cls]}|north_america"]
        nex = nrate * tam / 1000.0 * 365.0
        msk = "layers" if cls == "pullets" else cls
        for sysk, sh in ms[msk].items():
            m, _ = v1.mcf(p, ver, sysk, T, zone19)
            b = p["IPCC2019.B0.prp|all"] if (ver == "2019" and sysk == "pasture") else b0
            out[("manure_ch4", cls, "CH4")] += h * vs * 365.0 * b * p["BOTH.CH4_M3_TO_KG.all"] * m * sh
            n = h * nex * sh
            if sysk == "pasture":
                nprp += n; continue
            out[("manure_n2o_direct", cls, "N2O")] += n * v1.ef3(p, ver, sysk) * N2O_N
            fg, fl = v1.fracgas(p, ver, "layers" if cls == "pullets" else cls, sysk)
            if fg is None:
                gaps.append(f"{ver}:FracGasMS {cls}|{sysk} not in table; no volatilisation, N passed to soils")
                fg, fl = 0.0, 0.0
            out[("manure_n2o_indirect_vol", cls, "N2O")] += n * fg * ef4m * N2O_N
            if fl:
                out[("manure_n2o_indirect_leach", cls, "N2O")] += n * fl * p[f"IPCC{ver}.EF5.all"] * N2O_N
            nman += n * (1.0 - fg - fl)
    if ver == "2006":
        ef1s = ef1o = p["IPCC2006.EF1.all"]; ef3prp = p["IPCC2006.EF3PRP_CPP.all"]; ef4 = p["IPCC2006.EF4.all"]
        fl = p["IPCC2006.FracLEACH.wet"] if wet else 0.0
        fgasf, fgasm = p["IPCC2006.FracGASF.all"], p["IPCC2006.FracGASM.all"]
    else:
        w = "wet" if wet else "dry"
        ef1s = p["IPCC2019.EF1.wet_synthetic"] if wet else p["IPCC2019.EF1.dry"]
        ef1o = p["IPCC2019.EF1.wet_other"] if wet else p["IPCC2019.EF1.dry"]
        ef3prp = p[f"IPCC2019.EF3PRP_CPP.{w}"]; ef4 = p[f"IPCC2019.EF4.{w}"]
        fl = p[f"IPCC2019.FracLEACH.{w}"]
        fgasf, fgasm = p["IPCC2019.FracGASF.all"], p["IPCC2019.FracGASM.all"]
    ef3so = p[f"IPCC{ver}.EF3PRP_SO.all"]; ef5 = p[f"IPCC{ver}.EF5.all"]; ef1fr = p[f"IPCC{ver}.EF1FR.all"]
    def soil(src, n, ef1, fgas):
        out[("soil_n2o_direct", src, "N2O")] += n * ef1 * N2O_N
        if fgas:
            out[("soil_n2o_indirect_vol", src, "N2O")] += n * fgas * ef4 * N2O_N
        if fl:
            out[("soil_n2o_indirect_leach", src, "N2O")] += n * fl * ef5 * N2O_N
    if fsn is not None:
        soil("synthetic_N", fsn, ef1s, fgasf)
    soil("manure_N_applied", nman, ef1o, fgasm)
    soil("PRP_N_cattle_swine_poultry", nprp, ef3prp, fgasm)
    soil("PRP_N_sheep_other", nprp_so, ef3so, fgasm)
    for crop, fcr in crops.items():
        soil(f"crop_residue:{crop}", fcr[ver], ef1fr if crop == "rice" else ef1o, 0.0)
    return out, sorted(set(gaps))


def residue_n(p, crop, ac, prod_units, ver):
    """kg N in crop residues for one county crop (FracRemove=0, no burning, FracRenew=1)."""
    _, _, lb, r06, r19 = CROPS[crop]
    ha = ac * AC_HA
    if ha <= 0:
        return 0.0
    fresh = prod_units * lb * LB_KG / ha  # kg fresh/ha
    if ver == "2006":
        g = lambda f: p[f"IPCC2006.RES.{r06}.{f}"]
        cr = fresh * g("DRY")
        agdm = (cr / 1000.0 * g("slope") + g("intercept")) * 1000.0  # kg DM/ha (Table 11.2 regression)
        return ha * (agdm * g("N_AG") + (agdm + cr) * g("R_BG_BIO") * g("N_BG"))  # Eq 11.7A
    g = lambda f: p[f"IPCC2019.RES.{r19}.{f}"]
    cr = fresh * g("DRY")
    agdm = cr * g("R_AG")
    return ha * (agdm * g("N_AG") + (agdm + cr) * g("RS") * g("N_BG"))  # Eq 11.6 (Updated)


SRC = {"enteric": "enteric_CH4", "manure_ch4": "manure_CH4", "manure_n2o_direct": "manure_N2O",
       "manure_n2o_indirect_vol": "manure_N2O", "manure_n2o_indirect_leach": "manure_N2O",
       "soil_n2o_direct": "soil_N2O", "soil_n2o_indirect_vol": "soil_N2O", "soil_n2o_indirect_leach": "soil_N2O"}
VARIANTS = ("disclosed", "reconstructed", "D_allocated")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--nass", required=True); ap.add_argument("--fert", required=True); ap.add_argument("--shp")
    a = ap.parse_args(argv)
    for o in (OUT, OUT_NAT, MAN, MAP):
        if o.exists():
            sys.exit(f"refusing to overwrite {o}")
    p, ms = P(), v1.mms()
    ms["pullets"] = ms["layers"]
    zones = {r["fips"]: r for r in csv.DictReader(open(v1.ZONES, encoding="utf-8"))}
    county, state = read_nass(a.nass)
    fert = v1.read_fert(a.fert)
    recon = {f: reconstruct(county[f]) for f in county}
    alloc = allocate(county, state, recon)
    nat = defaultdict(float); natsub = defaultdict(float); nflags = defaultdict(lambda: defaultdict(int))
    rows = []; mapagg = defaultdict(lambda: [0.0, 0.0])
    for var in VARIANTS:
        for fips in sorted(county):
            c = county[fips]; st, cname = c["_name"]; flags = []
            rc, rnotes = recon[fips]
            def g(k):
                if var != "disclosed" and k in rc:
                    v = rc[k]
                else:
                    raw = c.get(k)
                    if raw is None:
                        return 0.0
                    if raw[1]:
                        flags.append(f"{k}{raw[1]}")
                    v = raw[0]
                if v is None and var == "D_allocated":
                    if (fips, k) in alloc:
                        flags.append(f"{k}=alloc"); return alloc[(fips, k)]
                    flags.append(f"{k}=unallocated")
                return v
            if var != "disclosed":
                for k in ("cattle_total", "dairy"):
                    raw = c.get(k)
                    if raw and raw[0] is None:
                        flags.append(f"{k}(D)")
                flags += [f"recon:{n}" for n in sorted(set(rnotes))]
            tot, dairy = g("cattle_total"), g("dairy")
            if var == "D_allocated" and tot is not None and dairy is not None and dairy > tot:
                flags.append("dairy>total:clipped"); dairy = tot
            heads = {"dairy": dairy, "other_cattle": None if (tot is None or dairy is None) else max(0.0, tot - dairy)}
            for k in ("swine", "broilers", "turkeys", "pullets") + SMALL_RUM:
                heads[k] = g(k)
            lay = [g("layers_hens"), g("roosters")]
            heads["layers"] = None if any(x is None for x in lay) else sum(lay)
            sname = state[fips[:2]]["_name"]
            sexp = state[fips[:2]].get("fert_expense", (None, ""))[0]
            ce = g("fert_expense")
            fsn = None if (ce is None or not sexp or sname not in fert) else fert[sname] * ce / sexp
            crops = {}
            for crop in CROPS:
                ac = g(crop + "_ac")
                if not ac:
                    continue
                pr = g(crop + "_prod")
                if pr is None or crop + "_prod" not in c:  # use state yield
                    sa, sp = state[fips[:2]].get(crop + "_ac", (None, ""))[0], state[fips[:2]].get(crop + "_prod", (None, ""))[0]
                    if not sa or sp is None:
                        flags.append(f"{crop}:no_yield"); continue
                    pr = ac * sp / sa; flags.append(f"{crop}:state_yield")
                crops[crop] = {v: residue_n(p, crop, ac, pr, v) for v in ("2006", "2019")}
            z = zones.get(fips)
            if z is None:
                flags.append("no_climate_zone")
                for f_ in flags:
                    nflags[var][f_.split("(")[0]] += 1
                continue
            zone, T = z["zone_primary"], float(z["mean_annual_temp_c"])
            zone19 = zone if not zone.startswith("polar") else None
            if zone.startswith("polar"):
                flags.append("polar->2006_MCF")
            for f_ in set(flags):
                nflags[var][f_.split(":")[0] if f_.startswith("recon") else f_] += 1
            res = {v: county_calc(p, ms, v, heads, fsn, crops, T, zone, zone19, v1.is_wet(zone)) for v in ("2006", "2019")}
            gaps = sorted(set(res["2006"][1] + res["2019"][1]))
            for k in sorted(set(res["2006"][0]) | set(res["2019"][0])):
                v6, v9 = res["2006"][0].get(k, 0.0), res["2019"][0].get(k, 0.0); gas = k[2]
                rows.append({"variant": var, "fips": fips, "state": st, "county": cname, "zone_primary": zone, "mat_c": round(T, 2),
                             "source": k[0], "category": k[1], "gas": gas, "kg_2006": round(v6, 3), "kg_2019": round(v9, 3),
                             "t_co2e_2006": round(v6 * GWP[gas] / 1000, 4), "t_co2e_2019": round(v9 * GWP[gas] / 1000, 4),
                             "pct_change": "" if v6 == 0 else round(100 * (v9 - v6) / v6, 3),
                             "census_flags": ";".join(sorted(set(flags))), "param_gaps": ";".join(gaps)})
                s = SRC[k[0]]
                for ver, x in (("2006", v6), ("2019", v9)):
                    nat[(var, s, ver)] += x * GWP[gas] / 1e9
                    sub = k[1].split(":")[0] if k[1].startswith("crop_residue") else k[1]
                    natsub[(var, s, k[0], sub if s == "soil_N2O" else ("other_livestock" if sub in SMALL_RUM else sub), ver)] += x * GWP[gas] / 1e9
                if var == "D_allocated":
                    mapagg[fips][0] += v6 * GWP[gas]; mapagg[fips][1] += v9 * GWP[gas]
    with gzip.open(OUT, "wt", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    cats = ("enteric_CH4", "manure_CH4", "manure_N2O", "soil_N2O")
    with open(OUT_NAT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["variant", "category", "ghgsim_2006_MMT_CO2e", "ghgsim_2019_MMT_CO2e", "pct_change_2019_vs_2006",
                    "EPA_2025ed_Table5-1_2022_MMT_CO2e", "ghgsim_2006_over_EPA", "ghgsim_2019_over_EPA"])
        for var in VARIANTS:
            for s in cats + ("total_in_scope",):
                if s == "total_in_scope":
                    a6 = sum(nat[(var, x, "2006")] for x in cats); a9 = sum(nat[(var, x, "2019")] for x in cats); e = sum(EPA_2022.values())
                else:
                    a6, a9, e = nat[(var, s, "2006")], nat[(var, s, "2019")], EPA_2022[s]
                w.writerow([var, s, round(a6, 3), round(a9, 3), round(100 * (a9 - a6) / a6, 2), round(e, 1), round(a6 / e, 3), round(a9 / e, 3)])
        w.writerow([]); w.writerow(["# breakdown (MMT CO2e): variant, category, source, subcategory, 2006, 2019"])
        keys = sorted({k[:4] for k in natsub})
        for k in keys:
            w.writerow(["#", *k, round(natsub[(*k, "2006")], 3), round(natsub[(*k, "2019")], 3)])
    if a.shp:
        import geopandas as gpd, pandas as pd, matplotlib
        matplotlib.use("Agg"); import matplotlib.pyplot as plt
        agg = pd.DataFrame({f: {"t6": v[0], "t9": v[1]} for f, v in mapagg.items()}).T
        agg["pct"] = 100 * (agg.t9 - agg.t6) / agg.t6
        shp = gpd.read_file(f"zip://{a.shp}")
        shp = shp[~shp.STATEFP.isin(["02", "15", "60", "66", "69", "72", "78"])].to_crs("EPSG:5070")
        shp = shp.merge(agg, left_on="GEOID", right_index=True, how="left")
        states = shp.dissolve(by="STATEFP")
        fig, ax = plt.subplots(figsize=(12, 7.5))
        shp.plot(column="pct", ax=ax, cmap="RdBu_r", vmin=-60, vmax=60, legend=True, linewidth=0.05, edgecolor="grey",
                 missing_kwds={"color": "lightgrey"},
                 legend_kwds={"label": "% change, IPCC 2019 vs 2006 (clipped at \u00b160%)", "shrink": 0.55, "extend": "both"})
        states.boundary.plot(ax=ax, linewidth=0.4, color="black")
        ax.set_axis_off()
        ax.set_title("Change in county agricultural CH4 + N2O (CO2e, AR5) from switching IPCC 2006 to 2019 Tier 1\n"
                     "CONUS, 2022 Census activity, withheld cells allocated (ghgsim AN_v2). Grey = no data.", fontsize=11)
        MAP.parent.mkdir(parents=True, exist_ok=True); fig.savefig(MAP, dpi=150, bbox_inches="tight")
        nmiss = int(shp.pct.isna().sum()); print("map counties without value:", nmiss)
    man = {"inputs": {"nass": {"path": a.nass, "sha256": v1.sha256(a.nass)}, "fert": {"path": a.fert, "sha256": v1.sha256(a.fert)},
                      "shp": {"path": a.shp, "sha256": v1.sha256(a.shp)} if a.shp else None,
                      "params": {"path": str(PARAMS.relative_to(ROOT)), "sha256": v1.sha256(PARAMS)},
                      "mms": {"path": str(v1.MMS.relative_to(ROOT)), "sha256": v1.sha256(v1.MMS)},
                      "zones": {"path": str(v1.ZONES.relative_to(ROOT)), "sha256": v1.sha256(v1.ZONES)}},
           "n_rows": len(rows), "flag_counts": {v: dict(d) for v, d in nflags.items()},
           "national_MMT_CO2e": {f"{v}|{s}|{y}": round(x, 4) for (v, s, y), x in nat.items()},
           "gwp": GWP, "epa_reference": "EPA Inventory of U.S. GHG Emissions and Sinks 1990-2023 (2025), Table 5-1 p.5-3, 2022 column"}
    MAN.write_text(json.dumps(man, indent=2), encoding="utf-8")
    print(json.dumps(man["national_MMT_CO2e"], indent=1))


if __name__ == "__main__":
    main()
