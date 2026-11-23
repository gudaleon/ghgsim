#!/usr/bin/env python3
"""County-year IPCC Tier 1 run (2006 vs 2019) for one US state and one Census year.  AN_v1.

Unlike scripts/run_us_county_2006_vs_2019_AN_v2.py (locked to 2022, writes into the repo), this runner takes the
year, state and input files on the command line and writes only to --out-dir (refuses to overwrite).

Engine pieces reused unchanged from run_us_county_2006_vs_2019_AN_v2.py: reconstruct, allocate, county_calc
(livestock CH4/N2O and soil N2O from synthetic N, manure, PRP and annual-crop residues), residue_n.
New components (src/ghgsim/modules/tier1_extras, docs/TIER1_EXTRAS_AN_v1.md):
  * hay / haylage / corn-silage residue N  -> soil N2O (direct + leaching), rows 'forage_residue:*'
  * F_SOM from tillage change between two Census years (Eq 2.25 + Eq 11.8) -> soil N2O, row 'F_SOM'
  * crop N removal (NRCS AWMFH Table 6-6), soybean BNF, and a closed soil-surface N budget
  * lime CO2 (state total from --lime-csv; urea only if a urea amount is supplied there)
Parameters: data/ipcc_params_AN_v11.csv.  Climate: county zone from data/county_climate_zones_AN_v1.csv, or
--climate all_wet (every *_dry zone treated as *_moist).
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
_s = importlib.util.spec_from_file_location("ghgsim_county_v2", ROOT / "scripts" / "run_us_county_2006_vs_2019_AN_v2.py")
v2 = importlib.util.module_from_spec(_s)
sys.modules["ghgsim_county_v2"] = v2
_s.loader.exec_module(v2)
v1 = v2.v1

from ghgsim.modules.tier1_extras import (  # noqa: E402
    crop_n_removal_kg,
    forage_residue_n,
    fsom_kg_n,
    lime_urea_co2_kg,
    n_budget,
    silage_residue_n,
    soybean_bnf_kg,
    tillage_soc_change_t,
)
from ghgsim.modules.tier1_extras.crop_n_removal import LB_KG  # noqa: E402

PARAMS = ROOT / "data" / "ipcc_params_AN_v11.csv"
GWP = dict(v2.GWP, CO2=1.0)
N2O_N, AC_HA, TON_LB = v2.N2O_N, v2.AC_HA, 2000.0
VERS = ("2006", "2019")
EXTRA = {
    "AG LAND, CROPLAND, HARVESTED - ACRES": "cropland_harv_ac",
    "HAY, ALFALFA - ACRES HARVESTED": "hay_alf_ac", "HAY, ALFALFA - PRODUCTION, MEASURED IN TONS": "hay_alf_t",
    "HAY, (EXCL ALFALFA) - ACRES HARVESTED": "hay_oth_ac", "HAY, (EXCL ALFALFA) - PRODUCTION, MEASURED IN TONS": "hay_oth_t",
    "HAY - PRODUCTION, MEASURED IN TONS": "hay_t",
    "HAYLAGE - ACRES HARVESTED": "haylage_ac",
    "HAYLAGE, ALFALFA - PRODUCTION, MEASURED IN TONS": "haylage_alf_green_t",
    "HAYLAGE, (EXCL ALFALFA) - PRODUCTION, MEASURED IN TONS": "haylage_oth_green_t",
    "HAY & HAYLAGE - PRODUCTION, MEASURED IN TONS, DRY BASIS": "hh_dry_t", "HAY & HAYLAGE - ACRES HARVESTED": "hh_ac",
    "CORN, SILAGE - ACRES HARVESTED": "silage_ac", "CORN, SILAGE - PRODUCTION, MEASURED IN TONS": "silage_green_t",
    "PRACTICES, LAND USE, CROPLAND, CONVENTIONAL TILLAGE - ACRES": "till_full_ac",
    "PRACTICES, LAND USE, CROPLAND, CONSERVATION TILLAGE, (EXCL NO-TILL) - ACRES": "till_reduced_ac",
    "PRACTICES, LAND USE, CROPLAND, CONSERVATION TILLAGE, NO-TILL - ACRES": "till_no_till_ac",
}
EXTRA_KEYS = tuple(EXTRA.values())
TILL = ("full", "reduced", "no_till")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_params(path=PARAMS):
    return {r["key"]: float(r["value"]) for r in csv.DictReader(open(path, encoding="utf-8"))}


def read_census(paths, year, state_fips):
    """County and state dicts {key: (value|None, flag)} for one Census year (SOURCE CENSUS, DOMAIN TOTAL)."""
    ser = dict(v2.SERIES)
    ser.update(EXTRA)
    county, state = defaultdict(dict), defaultdict(dict)
    for fn in paths:
        with open(fn, encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                k = ser.get(r["SHORT_DESC"])
                if (not k or r["DOMAIN_DESC"] != "TOTAL" or r["YEAR"] != str(year) or r["SOURCE_DESC"] != "CENSUS"
                        or r["STATE_FIPS_CODE"] != state_fips):
                    continue
                if r["AGG_LEVEL_DESC"] == "COUNTY" and r["COUNTY_CODE"] != "998":
                    fp = r["STATE_FIPS_CODE"] + r["COUNTY_CODE"]
                    county[fp][k] = v1.num(r["VALUE"])
                    county[fp]["_name"] = (r["STATE_ALPHA"], r["COUNTY_NAME"])
                elif r["AGG_LEVEL_DESC"] == "STATE":
                    state[r["STATE_FIPS_CODE"]][k] = v1.num(r["VALUE"])
                    state[r["STATE_FIPS_CODE"]]["_name"] = r["STATE_NAME"]
    return dict(county), dict(state)


def alloc_extra(county, st, key, weight_key):
    """State remainder of a withheld extra series, split over withheld counties by a disclosed weight (else equal)."""
    out = {}
    stv = st.get(key, (None, ""))[0]
    wd = [f for f in county if key in county[f] and county[f][key][0] is None]
    if stv is None or not wd:
        return out
    rem = max(0.0, stv - sum(county[f][key][0] for f in county if county[f].get(key, (None, ""))[0] is not None))
    w = {f: (county[f].get(weight_key, (None, ""))[0] or 0.0) for f in wd}
    tw = sum(w.values())
    for f in wd:
        out[f] = rem * (w[f] / tw if tw else 1.0 / len(wd))
    return out


def efs(p, ver, wet):
    if ver == "2006":
        return dict(ef1s=p["IPCC2006.EF1.all"], ef1o=p["IPCC2006.EF1.all"], fl=p["IPCC2006.FracLEACH.wet"] if wet else 0.0,
                    fgasf=p["IPCC2006.FracGASF.all"], fgasm=p["IPCC2006.FracGASM.all"], ef5=p["IPCC2006.EF5.all"])
    w = "wet" if wet else "dry"
    return dict(ef1s=p["IPCC2019.EF1.wet_synthetic"] if wet else p["IPCC2019.EF1.dry"],
                ef1o=p["IPCC2019.EF1.wet_other"] if wet else p["IPCC2019.EF1.dry"], fl=p[f"IPCC2019.FracLEACH.{w}"],
                fgasf=p["IPCC2019.FracGASF.all"], fgasm=p["IPCC2019.FracGASM.all"], ef5=p["IPCC2019.EF5.all"])


def manure_flows(p, ms, ver, heads):
    """Excreted N and its split (kg N), mirroring county_calc; used for the N budget and closure check."""
    ex = prp = msv = msl = app = 0.0
    for cls in v2.CLASSES:
        h = heads.get(cls)
        if not h:
            continue
        if cls in v2.SMALL_RUM:
            nk = "horses" if cls == "mules_asses" else cls
            n = h * p[f"IPCC{ver}.Nrate.{nk}|north_america"] * p[f"IPCC{ver}.TAM.{cls}|north_america"] / 1000 * 365
            ex += n
            prp += n
            continue
        if ver == "2006":
            c6 = v2.CLS6[cls]
            tam = p[f"IPCC2006.TAM.{c6}|north_america"]
            nrate = p[f"IPCC2006.Nrate.{'pullets' if cls == 'pullets' else c6}|north_america"]
        else:
            c9 = v2.CLS19[cls]
            tam, nrate = p[f"IPCC2019.TAM.{c9}|north_america"], p[f"IPCC2019.Nrate.{c9}|north_america"]
        nex = h * nrate * tam / 1000.0 * 365.0
        ex += nex
        for sysk, sh in ms["layers" if cls == "pullets" else cls].items():
            n = nex * sh
            if sysk == "pasture":
                prp += n
                continue
            fg, fl = v1.fracgas(p, ver, "layers" if cls == "pullets" else cls, sysk)
            fg, fl = (fg or 0.0), (fl or 0.0) if fg is not None else 0.0
            msv += n * fg
            msl += n * fl
            app += n * (1.0 - fg - fl)
    return dict(excreted=ex, prp=prp, ms_vol=msv, ms_leach=msl, applied=app)


def residue_ag_n(p, crop, ac, prod_units, ver):
    """Above-ground part of v2.residue_n (needed for soybean above-ground N demand)."""
    _, _, lb, r06, r19 = v2.CROPS[crop]
    ha = ac * AC_HA
    if ha <= 0:
        return 0.0
    fresh = prod_units * lb * v2.LB_KG / ha
    if ver == "2006":
        cr = fresh * p[f"IPCC2006.RES.{r06}.DRY"]
        agdm = (cr / 1000.0 * p[f"IPCC2006.RES.{r06}.slope"] + p[f"IPCC2006.RES.{r06}.intercept"]) * 1000.0
        return ha * agdm * p[f"IPCC2006.RES.{r06}.N_AG"]
    cr = fresh * p[f"IPCC2019.RES.{r19}.DRY"]
    return ha * cr * p[f"IPCC2019.RES.{r19}.R_AG"] * p[f"IPCC2019.RES.{r19}.N_AG"]


def till_shares(rec):
    vals = {k: rec.get(f"till_{k}_ac") for k in TILL}
    if any(v is None for v in vals.values()):
        return None, 0.0
    tot = sum(vals.values())
    return ({k: v / tot for k, v in vals.items()} if tot > 0 else None), tot


def build_county(p, county, state, sfips, fert, fert_year, zones, climate):
    """Per-county activity data (D_allocated variant) incl. the new extras. Returns {fips: dict}, flags."""
    st = state[sfips]
    recon = {f: v2.reconstruct(county[f]) for f in county}
    alloc = v2.allocate(county, state, recon)
    ext_alloc = {}
    for k in EXTRA_KEYS:
        wk = "till_full_ac" if k.startswith("till_") else ("silage_ac" if k == "silage_green_t" else "hh_ac")
        if k in ("cropland_harv_ac", "hh_ac"):
            wk = "cropland_harv_ac" if k == "hh_ac" else "hh_ac"
        ext_alloc[k] = alloc_extra(county, st, k, wk)
    sexp = st.get("fert_expense", (None, ""))[0]
    out = {}
    for f in sorted(county):
        c, flags = county[f], []
        rc, rnotes = recon[f]

        def g(k, c=c, rc=rc, flags=flags, f=f):
            if k in rc:
                v = rc[k]
            else:
                raw = c.get(k)
                if raw is None:
                    return 0.0
                v = raw[0]
                if raw[1]:
                    flags.append(f"{k}{raw[1]}")
            if v is None:
                if (f, k) in alloc:
                    flags.append(f"{k}=alloc")
                    return alloc[(f, k)]
                if k in ext_alloc and f in ext_alloc[k]:
                    flags.append(f"{k}=alloc")
                    return ext_alloc[k][f]
                flags.append(f"{k}=unallocated")
            return v

        tot, dairy = g("cattle_total"), g("dairy")
        if tot is not None and dairy is not None and dairy > tot:
            flags.append("dairy>total:clipped")
            dairy = tot
        heads = {"dairy": dairy, "other_cattle": None if (tot is None or dairy is None) else max(0.0, tot - dairy)}
        for k in ("swine", "broilers", "turkeys", "pullets") + v2.SMALL_RUM:
            heads[k] = g(k)
        lay = [g("layers_hens"), g("roosters")]
        heads["layers"] = None if any(x is None for x in lay) else sum(lay)
        ce = g("fert_expense")
        sname = st["_name"]
        fsn = None if (ce is None or not sexp or sname not in fert) else fert[sname] * ce / sexp
        crops, cropin = {}, {}
        for crop in v2.CROPS:
            ac = g(crop + "_ac")
            if not ac:
                continue
            pr = g(crop + "_prod")
            if pr is None or crop + "_prod" not in c:
                sa, sp = st.get(crop + "_ac", (None, ""))[0], st.get(crop + "_prod", (None, ""))[0]
                if not sa or sp is None:
                    flags.append(f"{crop}:no_yield")
                    continue
                pr = ac * sp / sa
                flags.append(f"{crop}:state_yield")
            crops[crop] = {v: v2.residue_n(p, crop, ac, pr, v) for v in VERS}
            cropin[crop] = (ac, pr)
        ext = {k: g(k) for k in EXTRA_KEYS}
        z = zones[f]
        zone = z["zone_primary"]
        if climate == "all_wet":
            zone = zone.replace("_dry", "_moist")
        out[f] = dict(name=c["_name"][1], heads=heads, fsn=fsn, fert_expense=ce, crops=crops, cropin=cropin, ext=ext,
                      zone=zone, zone_file=z["zone_primary"], T=float(z["mean_annual_temp_c"]),
                      flags=sorted(set(flags + [f"recon:{n}" for n in rnotes])))
    return out


def forage_inputs(ext):
    """Hay and haylage (dry-basis hay-equivalent tons) by IPCC row, plus corn silage green tons."""
    e = {k: (v or 0.0) for k, v in ext.items()}
    hay_alf, hay_oth = e["hay_alf_t"], e["hay_oth_t"]
    haylage_dry = max(0.0, e["hh_dry_t"] - (hay_alf + hay_oth))
    green = e["haylage_alf_green_t"] + e["haylage_oth_green_t"]
    sh_alf = e["haylage_alf_green_t"] / green if green > 0 else 0.0
    hl_area = e["haylage_ac"]
    return dict(hay_alf_t=hay_alf, hay_alf_ac=e["hay_alf_ac"], hay_oth_t=hay_oth, hay_oth_ac=e["hay_oth_ac"],
                haylage_alf_dryeq_t=haylage_dry * sh_alf, haylage_oth_dryeq_t=haylage_dry * (1 - sh_alf),
                haylage_alf_ac=hl_area * sh_alf, haylage_oth_ac=hl_area * (1 - sh_alf),
                silage_green_t=e["silage_green_t"], silage_ac=e["silage_ac"],
                haylage_dryeq_negative=(e["hh_dry_t"] - (hay_alf + hay_oth)) < 0)


def forage_n(p, ver, fi, frac_renew):
    """Residue N (kg) per forage item; IPCC DRY 0.90 converts reported hay / dry-basis haylage tons to DM."""
    res = {}
    for item, row, t, ac in (("alfalfa_hay", "alfalfa", fi["hay_alf_t"], fi["hay_alf_ac"]),
                             ("other_hay", "nonlegume_hay", fi["hay_oth_t"], fi["hay_oth_ac"]),
                             ("alfalfa_haylage", "alfalfa", fi["haylage_alf_dryeq_t"], fi["haylage_alf_ac"]),
                             ("other_haylage", "nonlegume_hay", fi["haylage_oth_dryeq_t"], fi["haylage_oth_ac"])):
        ha = ac * AC_HA
        dm = t * TON_LB * LB_KG * p[f"IPCC{ver}.RES.{row}.DRY"]
        res[item] = forage_residue_n(p, ver, row, ha, dm / ha if ha > 0 else 0.0, frac_renew=frac_renew)
    ha = fi["silage_ac"] * AC_HA
    dm = fi["silage_green_t"] * TON_LB * LB_KG * p["NRCS.DM_frac.corn_silage"]
    res["corn_silage"] = silage_residue_n(p, ver, ha, dm / ha if ha > 0 else 0.0)
    return res


def removal(p, ci, fi, dm_correct=False):
    """kg N removed per crop (NRCS Table 6-6 method). dm_correct multiplies grain/hay by IPCC 2006 DRY (sensitivity)."""
    out, unmapped = {}, []
    for crop, (_ac, pr) in ci["cropin"].items():
        lb = v2.CROPS[crop][2]
        try:
            dmf = p[f"IPCC2006.RES.{v2.CROPS[crop][3]}.DRY"] if dm_correct else 1.0
            out[crop] = crop_n_removal_kg(p, crop, pr * lb, dm_frac=dmf)
        except KeyError:
            unmapped.append(crop)
    hay_dmf = p["IPCC2006.RES.alfalfa.DRY"] if dm_correct else 1.0
    for item, t in (("alfalfa_hay", fi["hay_alf_t"]), ("other_hay", fi["hay_oth_t"]),
                    ("alfalfa_haylage", fi["haylage_alf_dryeq_t"]), ("other_haylage", fi["haylage_oth_dryeq_t"])):
        key = "alfalfa_hay" if item == "alfalfa_haylage" else None  # dry-basis haylage treated as hay-equivalent
        out[item] = crop_n_removal_kg(p, item, t * TON_LB, dm_frac=hay_dmf, nrcs_key=key)
    out["corn_silage"] = crop_n_removal_kg(p, "corn_silage", fi["silage_green_t"] * TON_LB, dm_frac=p["NRCS.DM_frac.corn_silage"])
    return out, unmapped


def outp(d, name, suffix, ext="csv"):
    path = d / f"{name}{suffix}.{ext}"
    if path.exists():
        sys.exit(f"refusing to overwrite {path}")
    return path


def write_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--state-fips", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--census-tsv", nargs="+", required=True, help="NASS Quick Stats TSVs holding --year")
    ap.add_argument("--prev-year", type=int, help="previous Census year for the tillage change (F_SOM)")
    ap.add_argument("--prev-census-tsv", nargs="*", default=[], help="TSVs holding --prev-year tillage (county and/or state)")
    ap.add_argument("--fert-html", help="EPA 'Commercial fertilizer purchased' table (state 1000 kg N; needs lxml)")
    ap.add_argument("--fert-csv", help="alternative to --fert-html: CSV with columns state,kg_N")
    ap.add_argument("--fert-year", type=int, default=2017)
    ap.add_argument("--lime-csv", help="CSV: year,limestone_t,dolomite_t,aglime_unspecified_t,urea_t,source")
    ap.add_argument("--climate", choices=("zones", "all_wet"), default="zones")
    ap.add_argument("--soil-class", choices=("HAC", "WET"), default="HAC")
    ap.add_argument("--forage-frac-renew", type=float, default=1.0)
    ap.add_argument("--params", default=str(PARAMS))
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--suffix", default="_AN_v1")
    a = ap.parse_args(argv)
    od = pathlib.Path(a.out_dir)
    od.mkdir(parents=True, exist_ok=True)
    tag = f"{a.state_fips}_{a.year}_{a.climate}_{a.soil_class}_renew{a.forage_frac_renew:g}"
    paths = {n: outp(od, f"county_year_{n}_{tag}", a.suffix, "csv") for n in
             ("emissions_long", "inputs", "n_budget", "fsom", "forage_removal", "lime_urea_state", "massbalance")}
    pman = outp(od, f"county_year_run_manifest_{tag}", a.suffix, "json")

    p = load_params(a.params)
    ms = v1.mms()
    ms["pullets"] = ms["layers"]
    zones = {r["fips"]: r for r in csv.DictReader(open(v1.ZONES, encoding="utf-8")) if r["fips"].startswith(a.state_fips)}
    if a.fert_csv:
        fert = {r["state"].strip().upper(): float(r["kg_N"]) for r in csv.DictReader(open(a.fert_csv, encoding="utf-8"))}
    elif a.fert_html:
        import pandas as pd
        t = pd.read_html(a.fert_html)[0]
        col = [c for c in t.columns if str(a.fert_year) in c and "1000 kg" in c][0]
        fert = {str(s).strip().upper(): float(v) * 1000.0 for s, v in zip(t["State"], t[col], strict=True)}
    else:
        sys.exit("give --fert-html or --fert-csv")
    county, state = read_census(a.census_tsv, a.year, a.state_fips)
    st = state[a.state_fips]
    ci_all = build_county(p, county, state, a.state_fips, fert, a.fert_year, zones, a.climate)

    # ---- tillage change for F_SOM
    prev_c, prev_s = ({}, {})
    if a.prev_year:
        prev_c, prev_s = read_census(a.prev_census_tsv or a.census_tsv, a.prev_year, a.state_fips)
    s1_state, A_state = till_shares({f"till_{k}_ac": st.get(f"till_{k}_ac", (None, ""))[0] for k in TILL})
    s0_state = None
    if a.prev_year and a.state_fips in prev_s:
        s0_state, _ = till_shares({f"till_{k}_ac": prev_s[a.state_fips].get(f"till_{k}_ac", (None, ""))[0] for k in TILL})
    T_years = (a.year - a.prev_year) if a.prev_year else None
    rows_fsom = []
    fsom_c = {v: {} for v in VERS}
    dC_state = {v: 0.0 for v in VERS}
    for f, ci in ci_all.items():
        s1, A_ac = till_shares({f"till_{k}_ac": ci["ext"][f"till_{k}_ac"] for k in TILL})
        basis = "none"
        s0 = None
        if s1 and a.prev_year:
            pc = prev_c.get(f)
            if pc and all(pc.get(f"till_{k}_ac", (None, ""))[0] is not None for k in TILL):
                s0, _ = till_shares({f"till_{k}_ac": pc[f"till_{k}_ac"][0] for k in TILL})
                basis = "county_both_years"
            elif s0_state and s1_state:
                raw = {k: max(0.0, s1[k] - (s1_state[k] - s0_state[k])) for k in TILL}
                tot = sum(raw.values())
                s0 = {k: v / tot for k, v in raw.items()} if tot > 0 else None
                basis = "county_end_shares_minus_state_share_change"
        for ver in VERS:
            dC = tillage_soc_change_t(p, ver, ci["zone"], a.soil_class, s0, s1, A_ac * AC_HA, T_years) if s0 else 0.0
            dC_state[ver] += dC
            fsom_c[ver][f] = fsom_kg_n(dC, p[f"IPCC{ver}.FSOM.R_cropland_mgmt"])
            rows_fsom.append(dict(fips=f, county=ci["name"], version=ver, zone=ci["zone"], soil_class=a.soil_class,
                                  tillage_area_ha=A_ac * AC_HA, basis=basis,
                                  **{f"share_start_{k}": (s0 or {}).get(k) for k in TILL},
                                  **{f"share_end_{k}": (s1 or {}).get(k) for k in TILL},
                                  dC_t_per_yr=dC, F_SOM_county_losses_only_kg_N=fsom_c[ver][f]))
    # Approach 1 headline: one dC for the state; N only if that net change is a loss; allocated by county losses
    fsom_head = {v: {} for v in VERS}
    for ver in VERS:
        tot_state = fsom_kg_n(dC_state[ver], p[f"IPCC{ver}.FSOM.R_cropland_mgmt"])
        tot_loss = sum(fsom_c[ver].values())
        for f in ci_all:
            fsom_head[ver][f] = tot_state * fsom_c[ver][f] / tot_loss if tot_loss > 0 else 0.0
        for r in rows_fsom:
            if r["version"] == ver:
                r["F_SOM_headline_approach1_kg_N"] = fsom_head[ver][r["fips"]]
                r["state_net_dC_t_per_yr"] = dC_state[ver]

    rows_em, rows_in, rows_nb, rows_fr = [], [], [], []
    for f, ci in sorted(ci_all.items()):
        heads, zone, T = ci["heads"], ci["zone"], ci["T"]
        wet = v1.is_wet(zone)
        fi = forage_inputs(ci["ext"])
        rem, unmapped = removal(p, ci, fi)
        rem_dm, _ = removal(p, ci, fi, dm_correct=True)
        for ver in VERS:
            out, gaps = v2.county_calc(p, ms, ver, heads, ci["fsn"], ci["crops"], T, zone, zone, wet)
            e = efs(p, ver, wet)
            frn = forage_n(p, ver, fi, a.forage_frac_renew)
            extra_n = {f"forage_residue:{k}": v["total"] for k, v in frn.items()}
            extra_n["F_SOM"] = fsom_head[ver][f]
            for src, n in extra_n.items():
                out[("soil_n2o_direct", src, "N2O")] += n * e["ef1o"] * N2O_N
                if e["fl"]:
                    out[("soil_n2o_indirect_leach", src, "N2O")] += n * e["fl"] * e["ef5"] * N2O_N
            for (src, cat, gas), kg in out.items():
                rows_em.append(dict(year=a.year, fips=f, county=ci["name"], ipcc_version=ver, source=src,
                                    category=v2.SRC[src], item=cat, gas=gas, kg_gas=kg, t_CO2e_AR5=kg * GWP[gas] / 1000.0))
            mf = manure_flows(p, ms, ver, heads)
            fcr_annual = sum(v[ver] for v in ci["crops"].values())
            fcr_forage = sum(v["total"] for v in frn.values())
            soy_ag = residue_ag_n(p, "soybeans", *ci["cropin"]["soybeans"], ver) if "soybeans" in ci["cropin"] else 0.0
            bnf = soybean_bnf_kg(rem.get("soybeans", 0.0), soy_ag, p["SALV2008.soy_Ndfa"])
            fsn = ci["fsn"] or 0.0
            prp = mf["prp"]
            vol = fsn * e["fgasf"] + (mf["applied"] + prp) * e["fgasm"]
            leach = e["fl"] * (fsn + mf["applied"] + prp + fcr_annual + fcr_forage + fsom_head[ver][f])
            direct = sum(v for (s, c_, g_), v in out.items() if s == "soil_n2o_direct") / N2O_N
            nb = n_budget(dict(synthetic_N=fsn, manure_N_applied=mf["applied"], PRP_N=prp, BNF_soy_AG=bnf,
                               F_SOM=fsom_head[ver][f], crop_N_removed=sum(rem.values()), soil_volatilised=vol,
                               soil_leached=leach, soil_N2O_N_direct=direct))
            nb_lo = n_budget(dict(nb, BNF_soy_AG=soybean_bnf_kg(rem.get("soybeans", 0.0), soy_ag, 0.50)))
            nb_hi = n_budget(dict(nb, BNF_soy_AG=soybean_bnf_kg(rem.get("soybeans", 0.0), soy_ag, 0.60)))
            ha = (ci["ext"]["cropland_harv_ac"] or 0.0) * AC_HA
            rows_nb.append(dict(year=a.year, fips=f, county=ci["name"], version=ver, zone=zone, wet=wet,
                                **{k: v for k, v in nb.items()},
                                residual_BNF_0p50=nb_lo["residual_unaccounted"], residual_BNF_0p60=nb_hi["residual_unaccounted"],
                                crop_N_removed_dm_corrected=sum(rem_dm.values()),
                                residue_N_recycled_annual_crops=fcr_annual, residue_N_recycled_forage_silage=fcr_forage,
                                soil_leached_from_residue_and_FSOM=e["fl"] * (fcr_annual + fcr_forage + fsom_head[ver][f]),
                                alfalfa_N_removed=rem.get("alfalfa_hay", 0.0) + rem.get("alfalfa_haylage", 0.0),
                                soy_AG_residue_N=soy_ag, N_excreted=mf["excreted"], N_MMS_volatilised=mf["ms_vol"],
                                N_MMS_leached=mf["ms_leach"],
                                manure_closure_error=mf["excreted"] - (mf["prp"] + mf["ms_vol"] + mf["ms_leach"] + mf["applied"]),
                                N_under_EF1=fsn + mf["applied"] + fcr_annual + fcr_forage + fsom_head[ver][f],
                                cropland_harvested_ha=ha, residual_kg_per_ha=nb["residual_unaccounted"] / ha if ha else None,
                                unmapped_removal_crops=";".join(unmapped), gaps=";".join(gaps)))
            for item, v in frn.items():
                rows_fr.append(dict(year=a.year, fips=f, county=ci["name"], version=ver, item=item,
                                    residue_N_AG=v["AG"], residue_N_BG=v["BG"], residue_N_total=v["total"],
                                    N_removed=rem.get(item), N_removed_dm_corrected=rem_dm.get(item)))
        r = dict(year=a.year, fips=f, county=ci["name"], zone_file=ci["zone_file"], zone_used=zone, mean_annual_temp_c=T,
                 F_SN_kg=ci["fsn"], fert_expense_usd=ci["fert_expense"], flags=";".join(ci["flags"]),
                 haylage_dryeq_negative=fi["haylage_dryeq_negative"])
        r.update({f"heads_{k}": v for k, v in heads.items()})
        r.update({f"ext_{k}": v for k, v in ci["ext"].items()})
        r.update({k: v for k, v in fi.items() if k != "haylage_dryeq_negative"})
        for crop, (ac, pr) in ci["cropin"].items():
            r[f"{crop}_ac"], r[f"{crop}_prod_units"] = ac, pr
            r[f"{crop}_N_removed_kg"] = rem.get(crop)
        rows_in.append(r)

    # ---- lime / urea CO2 (state)
    rows_lime = []
    if a.lime_csv:
        for lr in csv.DictReader(open(a.lime_csv, encoding="utf-8")):
            if int(lr["year"]) != a.year:
                continue
            def fl_(k, lr=lr):
                return float(lr[k]) if lr.get(k) not in (None, "") else 0.0
            un = fl_("aglime_unspecified_t")
            for label, ls, dl in (("as_given", fl_("limestone_t"), fl_("dolomite_t")),
                                  ("unspecified_all_limestone", fl_("limestone_t") + un, fl_("dolomite_t")),
                                  ("unspecified_all_dolomite", fl_("limestone_t"), fl_("dolomite_t") + un)):
                co2 = lime_urea_co2_kg(p, ls, dl, fl_("urea_t"))
                for ver in VERS:
                    rows_lime.append(dict(year=a.year, ipcc_version=ver, case=label, limestone_t=ls, dolomite_t=dl,
                                          urea_t=fl_("urea_t"), CO2_lime_kg=co2["CO2_lime_kg"], CO2_urea_kg=co2["CO2_urea_kg"],
                                          source=lr.get("source", ""), note="2019 Ch11 s.11.3/11.4 'No refinement' (p. 11.27)"))
            head = lime_urea_co2_kg(p, fl_("limestone_t") + un, fl_("dolomite_t"), fl_("urea_t"))
            for ver in VERS:
                for item, kg in (("lime", head["CO2_lime_kg"]), ("urea", head["CO2_urea_kg"])):
                    if kg:
                        rows_em.append(dict(year=a.year, fips=a.state_fips + "000", county="STATE", ipcc_version=ver,
                                            source=f"{item}_co2", category="liming_urea_CO2", item=item, gas="CO2",
                                            kg_gas=kg, t_CO2e_AR5=kg / 1000.0))

    # ---- mass-balance checks
    rows_mb = []
    for k in ("hay_alf_ac", "hay_oth_ac", "hay_alf_t", "hay_oth_t", "hh_dry_t", "hh_ac", "haylage_ac", "silage_ac",
              "silage_green_t", "till_full_ac", "till_reduced_ac", "till_no_till_ac", "cropland_harv_ac"):
        stv = st.get(k, (None, ""))[0]
        cs = sum((ci["ext"][k] or 0.0) for ci in ci_all.values())
        rows_mb.append(dict(check=f"county_sum_vs_state:{k}", state=stv, county_sum=cs,
                            pct_diff=None if not stv else 100 * (stv - cs) / stv))
    for ver in VERS:
        nb = [r for r in rows_nb if r["version"] == ver]
        rows_mb.append(dict(check=f"n_budget_identity_max_abs_error_kg:{ver}", state=0.0,
                            county_sum=max(abs(r["closure_error"]) for r in nb)))
        rows_mb.append(dict(check=f"manure_N_closure_pct:{ver}", state=sum(r["N_excreted"] for r in nb),
                            county_sum=sum(r["manure_closure_error"] for r in nb),
                            pct_diff=100 * sum(r["manure_closure_error"] for r in nb) / max(1e-9, sum(r["N_excreted"] for r in nb))))
        em = sum(r["kg_gas"] for r in rows_em if r["ipcc_version"] == ver and r["source"] == "soil_n2o_direct") / N2O_N
        rows_mb.append(dict(check=f"direct_soil_N2O_N_emissions_vs_budget:{ver}", state=em,
                            county_sum=sum(r["soil_N2O_N_direct"] for r in nb)))
        rows_mb.append(dict(check=f"F_SOM_state_net_dC_t_per_yr:{ver}", state=dC_state[ver],
                            county_sum=sum(r["dC_t_per_yr"] for r in rows_fsom if r["version"] == ver)))

    write_csv(paths["emissions_long"], rows_em)
    write_csv(paths["inputs"], rows_in)
    write_csv(paths["n_budget"], rows_nb)
    write_csv(paths["fsom"], rows_fsom)
    write_csv(paths["forage_removal"], rows_fr)
    write_csv(paths["lime_urea_state"], rows_lime)
    write_csv(paths["massbalance"], rows_mb)
    git = lambda *c: subprocess.run(["git", "-C", str(ROOT), *c], capture_output=True, text=True).stdout.strip()  # noqa: E731
    man = dict(created=datetime.datetime.now().isoformat(timespec="seconds"), args=vars(a), ghgsim_head=git("rev-parse", "HEAD"),
               ghgsim_dirty=bool(git("status", "--porcelain")), params_sha256=sha256(a.params),
               inputs_sha256={str(x): sha256(x) for x in list(a.census_tsv) + list(a.prev_census_tsv) + [a.fert_html or a.fert_csv] +
                              ([a.lime_csv] if a.lime_csv else [])},
               outputs=[str(x) for x in paths.values()], n_counties=len(ci_all), state_tillage_shares_end=s1_state,
               state_tillage_shares_start=s0_state, state_tillage_area_ac=A_state)
    json.dump(man, open(pman, "w"), indent=1)
    print(f"ok {tag}: {len(ci_all)} counties, {len(rows_em)} emission rows -> {od}")


if __name__ == "__main__":
    main()
