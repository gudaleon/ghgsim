"""US county IPCC 2006 vs 2019 Tier 1 run (AN_v1).

Inputs (raw, outside repo; hashes written to data/us_county_run_manifest_AN_v1.json):
  --nass  USDA NASS Quick Stats bulk file qs.census2022.txt.gz (2022 Census of Agriculture)
  --fert  EPA ROE "Commercial fertilizer purchased" HTML (AAPFCO state N, 1000 kg N; latest 2017)
  --shp   Census cartographic boundary cb_2022_us_county_20m.zip (map only)
Repo inputs: data/ipcc_params_AN_v9.csv, data/mms_north_america_ipcc2006_AN_v1.csv,
             data/county_climate_zones_AN_v1.csv.

Scope (Tier 1, both versions on identical activity data; see docs/US_COUNTY_RUN_AN_v1.md):
  3A enteric CH4 (cattle, swine), 3B manure CH4 + direct/indirect N2O (cattle, swine, poultry),
  3D direct + indirect soil N2O from synthetic N, managed manure N applied, PRP N.
  Not included: sheep, goats, horses, crop residues, F_SOM, organic soils, rice, liming, urea CO2.
Census (D)/(Z) cells are flagged and left as NaN (no imputation).

Usage: python scripts/run_us_county_2006_vs_2019_AN_v1.py --nass ... --fert ... --shp ...
Refuses to overwrite outputs.
"""
from __future__ import annotations

import argparse, csv, gzip, hashlib, json, math, pathlib, sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "us_county_2006_vs_2019_AN_v1.csv"
OUT_NAT = ROOT / "data" / "us_national_2006_vs_2019_vs_epa_AN_v1.csv"
OUT_SENS = ROOT / "data" / "us_county_zone_sensitivity_AN_v1.csv"
MAN = ROOT / "data" / "us_county_run_manifest_AN_v1.json"
MAP = ROOT / "docs" / "figures" / "us_county_pct_change_2006_2019_AN_v1.png"
PARAMS = ROOT / "data" / "ipcc_params_AN_v9.csv"
MMS = ROOT / "data" / "mms_north_america_ipcc2006_AN_v1.csv"
ZONES = ROOT / "data" / "county_climate_zones_AN_v1.csv"
GWP = {"CH4": 28.0, "N2O": 265.0}  # AR5, as EPA 2025 Inventory
N2O_N = 44.0 / 28.0
# EPA Inventory 1990-2023 (2025 edition), Table 5-1, p. 5-3, year 2022, MMT CO2 Eq. (AR5)
EPA_2022 = {"enteric_CH4": 192.6, "manure_CH4": 64.7, "manure_N2O": 17.0, "soil_N2O": 291.8}

SERIES = {
    "CATTLE, INCL CALVES - INVENTORY": "cattle_total",
    "CATTLE, COWS, MILK - INVENTORY": "dairy",
    "HOGS - INVENTORY": "swine",
    "CHICKENS, LAYERS - INVENTORY": "layers_hens",
    "CHICKENS, PULLETS, REPLACEMENT - INVENTORY": "pullets",
    "CHICKENS, ROOSTERS - INVENTORY": "roosters",
    "CHICKENS, BROILERS - INVENTORY": "broilers",
    "TURKEYS - INVENTORY": "turkeys",
    "FERTILIZER TOTALS, INCL LIME & SOIL CONDITIONERS - EXPENSE, MEASURED IN $": "fert_expense",
}
CLASSES = ["dairy", "other_cattle", "swine", "layers", "broilers", "turkeys"]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def num(v):
    v = v.strip()
    if v == "(Z)":
        return 0.0, v  # less than half the unit shown: treated as 0, flagged
    if v.startswith("("):
        return None, v  # (D) withheld, (Z) <half unit, (NA) etc.
    return float(v.replace(",", "")), ""


def read_nass(path):
    county, state = defaultdict(dict), defaultdict(dict)
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            k = SERIES.get(r["SHORT_DESC"])
            if not k or r["DOMAIN_DESC"] != "TOTAL" or r["YEAR"] != "2022":
                continue
            if r["AGG_LEVEL_DESC"] == "COUNTY" and r["COUNTY_CODE"] != "998":
                county[r["STATE_FIPS_CODE"] + r["COUNTY_CODE"]][k] = num(r["VALUE"])
                county[r["STATE_FIPS_CODE"] + r["COUNTY_CODE"]]["_name"] = (r["STATE_ALPHA"], r["COUNTY_NAME"])
            elif r["AGG_LEVEL_DESC"] == "STATE":
                state[r["STATE_FIPS_CODE"]][k] = num(r["VALUE"])
                state[r["STATE_FIPS_CODE"]]["_name"] = r["STATE_NAME"]
    return county, state


def read_fert(path):
    import pandas as pd
    t = pd.read_html(path)[0]
    col = [c for c in t.columns if "2017" in c and "1000 kg" in c][0]
    return {str(s).strip().upper(): float(v) * 1000.0 for s, v in zip(t["State"], t[col])}  # kg N


def impute_withheld(county, state):
    """Sensitivity only: allocate each state's withheld residual (state total minus disclosed counties)
    across that state's (D) counties, proportional to county total cattle inventory for dairy, and in
    equal shares otherwise. Documented in DECISIONS_AN_v4 #7; primary outputs do not use it."""
    out = {}
    for k in SERIES:
        k = SERIES[k]
        for sf, sd in state.items():
            st = sd.get(k, (None, ""))[0]
            cs = [f for f in county if f[:2] == sf]
            dcs = [f for f in cs if county[f].get(k, (0.0, ""))[0] is None]
            if st is None or not dcs:
                continue
            resid = max(0.0, st - sum(county[f][k][0] for f in cs if county[f].get(k, (None, ""))[0] is not None))
            if k == "dairy":
                wts = {f: (county[f].get("cattle_total", (None, ""))[0] or 0.0) for f in dcs}
            else:
                wts = {f: 1.0 for f in dcs}
            tw = sum(wts.values())
            for f in dcs:
                out[(f, k)] = resid * (wts[f] / tw if tw else 1.0 / len(dcs))
    return out


def P():
    return {r["key"]: float(r["value"]) for r in csv.DictReader(open(PARAMS, encoding="utf-8"))}


def mms():
    out = {}
    for r in csv.DictReader(open(MMS, encoding="utf-8-sig")):
        sh = {k: float(r[k]) for k in ("lagoon", "liquid_slurry", "solid_storage", "dry_lot", "pasture",
                                       "daily_spread", "other_deep_pit", "pit_gt1mo") if r.get(k)}
        out[r["fips_class"]] = {k: v for k, v in sh.items() if v > 0}
    out["swine"] = out["market_swine"]
    out["layers"] = {"poultry_without_litter": 1.0}
    out["broilers"] = {"poultry_with_litter": 1.0}
    out["turkeys"] = {"poultry_with_litter": 1.0}
    return out


CLS6 = {"dairy": "dairy", "other_cattle": "other_cattle", "swine": "market_swine",
        "layers": "layers", "broilers": "broilers", "turkeys": "turkeys"}
B0_19 = {"dairy": "dairy", "other_cattle": "other_cattle", "swine": "swine", "layers": "layers",
         "broilers": "other_poultry", "turkeys": "other_poultry"}
FG = {"dairy": "dairy", "other_cattle": "other_cattle", "swine": "swine",
      "layers": "poultry", "broilers": "poultry", "turkeys": "poultry"}


def mcf(p, ver, sysk, T, zone):
    """Return (MCF, basis)."""
    tc = f"T{min(28, max(10, int(round(T))))}C"
    if ver == "2006" or zone is None:
        k = {"liquid_slurry": "liquid_nocrust", "other_deep_pit": "pit_gt1mo"}.get(sysk, sysk)
        return p[f"IPCC2006.MCF.{k}|{tc}"], f"2006:{tc}"
    grp = {"cool_temperate_moist": "cool", "cool_temperate_dry": "cool", "boreal_moist": "cool", "boreal_dry": "cool",
           "warm_temperate_moist": "temperate", "warm_temperate_dry": "temperate"}.get(zone, "warm")
    if sysk == "lagoon":
        return p[f"IPCC2019.MCF.lagoon|{zone}"], zone
    if sysk in ("liquid_slurry", "pit_gt1mo", "other_deep_pit"):
        return p[f"IPCC2019.MCF.liquid_12mo|{zone}"], zone  # DECISIONS_AN_v4: 12-month retention
    if sysk == "pasture":
        return p["IPCC2019.MCF.pasture|all"], "all"
    if sysk.startswith("poultry"):
        return p["IPCC2019.MCF.poultry_litter|all"], "all"
    return p[f"IPCC2019.MCF.{sysk}|{grp}"], grp


def ef3(p, ver, sysk):
    k = {"liquid_slurry": "liquid_nocrust", "pit_gt1mo": "pit", "other_deep_pit": "pit"}.get(sysk, sysk)
    return p[f"IPCC{ver}.EF3.{k}"]


def fracgas(p, ver, cls, sysk):
    if ver == "2006":
        k = {"pit_gt1mo": "pit", "other_deep_pit": "pit"}.get(sysk, sysk)
        return p.get(f"IPCC2006.FracGasMS.{FG[cls]}|{k}"), 0.0
    k = {"liquid_slurry": "liquid_nocrust", "pit_gt1mo": "pit", "other_deep_pit": "pit"}.get(sysk, sysk)
    return p.get(f"IPCC2019.FracGasMS.{FG[cls]}|{k}"), p.get(f"IPCC2019.FracLeachMS.{FG[cls]}|{k}", 0.0)


def county_calc(p, ms, ver, heads, fsn, T, zone19, wet):
    """Return dict (source, category, gas) -> kg gas, plus list of gap notes."""
    out, gaps = defaultdict(float), []
    nprp = nman_applied = 0.0
    for cls in CLASSES:
        h = heads.get(cls)
        if h is None:
            continue
        # enteric
        if cls in ("dairy", "other_cattle"):
            ef = p[f"IPCC{ver}.EF_enteric.{cls}|north_america"]
        elif cls == "swine":
            ef = p["IPCC2006.EF_enteric.swine|developed"] if ver == "2006" else p["IPCC2019.EF_enteric.swine|high_productivity"]
        else:
            ef = 0.0
        out[("enteric", cls, "CH4")] += h * ef
        c6 = CLS6[cls]
        vs = p[f"IPCC2006.VS.{c6}|north_america"]
        tam = p[f"IPCC2006.TAM.{c6}|north_america"]
        nrate = p[f"IPCC{ver}.Nrate.{c6}|north_america"]
        nex = nrate * tam / 1000.0 * 365.0  # kg N/head/yr (Eq 10.30)
        b0 = p[f"IPCC2006.B0.{c6}|north_america"] if ver == "2006" else p[f"IPCC2019.B0.{B0_19[cls]}|north_america"]
        for sysk, sh in ms[cls].items():
            m, _ = mcf(p, ver, sysk, T, zone19)
            b = p["IPCC2019.B0.prp|all"] if (ver == "2019" and sysk == "pasture") else b0
            out[("manure_ch4", cls, "CH4")] += h * vs * 365.0 * b * p["BOTH.CH4_M3_TO_KG.all"] * m * sh
            n = h * nex * sh
            if sysk == "pasture":
                nprp += n
                continue
            out[("manure_n2o_direct", cls, "N2O")] += n * ef3(p, ver, sysk) * N2O_N
            fg, fl = fracgas(p, ver, cls, sysk)
            if fg is None:
                gaps.append(f"{ver}:FracGasMS {cls}|{sysk} not published")
                continue
            ef4 = p["IPCC2006.EF4.all"] if ver == "2006" else p["IPCC2019.EF4." + ("wet" if wet else "dry")]
            out[("manure_n2o_indirect", cls, "N2O")] += (n * fg * ef4 + n * fl * p[f"IPCC{ver}.EF5.all"]) * N2O_N
            nman_applied += n * (1.0 - fg - fl)
    # soils
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
    ef5 = p[f"IPCC{ver}.EF5.all"]
    if fsn is not None:
        out[("soil_n2o_direct", "synthetic_N", "N2O")] += fsn * ef1s * N2O_N
        out[("soil_n2o_indirect", "synthetic_N", "N2O")] += (fsn * fgasf * ef4 + fsn * fl * ef5) * N2O_N
    out[("soil_n2o_direct", "manure_N_applied", "N2O")] += nman_applied * ef1o * N2O_N
    out[("soil_n2o_indirect", "manure_N_applied", "N2O")] += nman_applied * (fgasm * ef4 + fl * ef5) * N2O_N
    out[("soil_n2o_direct", "PRP_N", "N2O")] += nprp * ef3prp * N2O_N
    out[("soil_n2o_indirect", "PRP_N", "N2O")] += nprp * (fgasm * ef4 + fl * ef5) * N2O_N
    return out, sorted(set(gaps))


def is_wet(zone):
    return zone is not None and not zone.endswith("_dry")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--nass", required=True); ap.add_argument("--fert", required=True); ap.add_argument("--shp")
    a = ap.parse_args(argv)
    for o in (OUT, OUT_NAT, OUT_SENS, MAN, MAP):
        if o.exists():
            sys.exit(f"refusing to overwrite {o}")
    p, ms = P(), mms()
    zones = {r["fips"]: r for r in csv.DictReader(open(ZONES, encoding="utf-8"))}
    county, state = read_nass(a.nass)
    fert = read_fert(a.fert)
    imp = impute_withheld(county, state)
    nat_imp = defaultdict(float)
    for impute in (True, False):
      rows, nat = [], defaultdict(float)
      sens = defaultdict(float)
      nflags = defaultdict(int)
      for fips in sorted(county):
          c = county[fips]; st, cname = c["_name"]
          flags = []
          def g(k):
              v = c.get(k)
              if v is None:
                  return 0.0  # series absent for county = no animals reported
              if v[1]:
                  flags.append(f"{k}{v[1]}")
              if v[0] is None and impute:
                  return imp.get((fips, k))
              return v[0]
          tot, dairy = g("cattle_total"), g("dairy")
          heads = {"dairy": dairy, "other_cattle": None if (tot is None or dairy is None) else max(0.0, tot - dairy),
                   "swine": g("swine"), "broilers": g("broilers"), "turkeys": g("turkeys")}
          lay = [g("layers_hens"), g("pullets"), g("roosters")]
          heads["layers"] = None if any(x is None for x in lay) else sum(lay)
          if tot is None and dairy is not None:
              flags.append("other_cattle=NaN(total withheld)")
          # fertilizer N: state 2017 AAPFCO N x county share of state 2022 fertilizer expense
          sname = state[fips[:2]]["_name"]
          sexp = state[fips[:2]].get("fert_expense", (None, ""))[0]
          ce = g("fert_expense")
          fsn = None if (ce is None or not sexp or sname not in fert) else fert[sname] * ce / sexp
          if sname not in fert:
              flags.append("no_state_fert_N")
          z = zones.get(fips)
          if z is None:
              flags.append("no_climate_zone")
              zone, T = None, float("nan")
          else:
              zone, T = z["zone_primary"], float(z["mean_annual_temp_c"])
          zone19 = zone if (zone and not zone.startswith("polar")) else None
          if zone and zone.startswith("polar"):
              flags.append("polar->2006_MCF")
          for f in flags:
              nflags[f.split("(")[0]] += 1
          if z is None:
              res = {}
          else:
              res = {v: county_calc(p, ms, v, heads, fsn, T, zone19, is_wet(zone)) for v in ("2006", "2019")}
              for alt in ("zone_thornthwaite", "zone_hargreaves"):
                  za = z[alt]
                  za19 = za if za in ("cool_temperate_moist", "cool_temperate_dry", "warm_temperate_moist", "warm_temperate_dry",
                                      "boreal_moist", "boreal_dry") else zone19  # tropical_unresolved -> map zone
                  wa = is_wet(za) if za in ("cool_temperate_moist", "cool_temperate_dry", "warm_temperate_moist",
                                            "warm_temperate_dry", "boreal_moist", "boreal_dry") else is_wet(zone)
                  o, _ = county_calc(p, ms, "2019", heads, fsn, T, za19, wa)
                  for (s, cat, gas), kg in o.items():
                      sens[(alt, s, gas)] += kg * GWP[gas] / 1e9
              for (s, cat, gas), kg in res["2019"][0].items():
                  sens[("zone_primary", s, gas)] += kg * GWP[gas] / 1e9
          keys = sorted(set(res.get("2006", ({},))[0]) | set(res.get("2019", ({},))[0]))
          gaps = sorted(set(res["2006"][1] + res["2019"][1])) if res else []
          for k in keys:
              v6, v9 = res["2006"][0].get(k, 0.0), res["2019"][0].get(k, 0.0)
              gas = k[2]
              rows.append({"fips": fips, "state": st, "county": cname, "zone_primary": zone or "", "mat_c": "" if math.isnan(T) else round(T, 2),
                           "source": k[0], "category": k[1], "gas": gas,
                           "kg_2006": round(v6, 3), "kg_2019": round(v9, 3),
                           "t_co2e_2006": round(v6 * GWP[gas] / 1000, 4), "t_co2e_2019": round(v9 * GWP[gas] / 1000, 4),
                           "pct_change": "" if v6 == 0 else round(100 * (v9 - v6) / v6, 3),
                           "census_flags": ";".join(flags), "param_gaps": ";".join(gaps)})
              src = {"enteric": "enteric_CH4", "manure_ch4": "manure_CH4", "manure_n2o_direct": "manure_N2O",
                     "manure_n2o_indirect": "manure_N2O", "soil_n2o_direct": "soil_N2O", "soil_n2o_indirect": "soil_N2O"}[k[0]]
              nat[(src, "2006")] += v6 * GWP[gas] / 1e9
              nat[(src, "2019")] += v9 * GWP[gas] / 1e9
      if impute:
          nat_imp = nat
    cols = list(rows[0])
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
    with open(OUT_NAT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["category", "ghgsim_2006_MMT_CO2e", "ghgsim_2019_MMT_CO2e", "pct_change_2019_vs_2006",
                    "EPA_2025ed_Table5-1_2022_MMT_CO2e", "ghgsim_2019_over_EPA"])
        for s in ("enteric_CH4", "manure_CH4", "manure_N2O", "soil_N2O"):
            a6, a9 = nat[(s, "2006")], nat[(s, "2019")]
            w.writerow([s, round(a6, 3), round(a9, 3), round(100 * (a9 - a6) / a6, 2), EPA_2022[s], round(a9 / EPA_2022[s], 3)])
        t6 = sum(v for (s, ver), v in nat.items() if ver == "2006"); t9 = sum(v for (s, ver), v in nat.items() if ver == "2019")
        te = sum(EPA_2022.values())
        w.writerow(["total_in_scope", round(t6, 3), round(t9, 3), round(100 * (t9 - t6) / t6, 2), round(te, 1), round(t9 / te, 3)])
        w.writerow([]); w.writerow(["# sensitivity: (D) cells imputed by state-residual method (DECISIONS_AN_v4 #7); not used in county CSV"])
        for s_ in ("enteric_CH4", "manure_CH4", "manure_N2O", "soil_N2O"):
            a6, a9 = nat_imp[(s_, "2006")], nat_imp[(s_, "2019")]
            w.writerow([s_ + "_Dimputed", round(a6, 3), round(a9, 3), round(100 * (a9 - a6) / a6, 2), EPA_2022[s_], round(a9 / EPA_2022[s_], 3)])
    with open(OUT_SENS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["zone_method", "source", "gas", "ghgsim_2019_MMT_CO2e"])
        for k in sorted(sens):
            w.writerow([*k, round(sens[k], 4)])
    # map
    if a.shp:
        import geopandas as gpd, pandas as pd, matplotlib
        matplotlib.use("Agg"); import matplotlib.pyplot as plt
        df = pd.DataFrame(rows)
        agg = df.groupby("fips")[["t_co2e_2006", "t_co2e_2019"]].sum()
        agg["pct"] = 100 * (agg.t_co2e_2019 - agg.t_co2e_2006) / agg.t_co2e_2006
        shp = gpd.read_file(f"zip://{a.shp}")
        shp = shp[~shp.STATEFP.isin(["02", "15", "60", "66", "69", "72", "78"])].merge(agg, left_on="GEOID", right_index=True, how="left")
        fig, ax = plt.subplots(figsize=(12, 7))
        shp.plot(column="pct", ax=ax, cmap="RdBu_r", vmin=-40, vmax=40, legend=True, linewidth=0.05, edgecolor="grey",
                 missing_kwds={"color": "lightgrey", "label": "no data / withheld"},
                 legend_kwds={"label": "% change in-scope CO2e, IPCC 2019 vs 2006 Tier 1 (colour clipped at +/-40%)", "shrink": 0.6})
        ax.set_axis_off(); ax.set_title("US counties (CONUS): IPCC 2019 Refinement vs 2006 Tier 1, 2022 Census activity (ghgsim AN_v1)")
        MAP.parent.mkdir(parents=True, exist_ok=True); fig.savefig(MAP, dpi=150, bbox_inches="tight")
    man = {"inputs": {"nass": {"path": a.nass, "sha256": sha256(a.nass)}, "fert": {"path": a.fert, "sha256": sha256(a.fert)},
                      "shp": {"path": a.shp, "sha256": sha256(a.shp)} if a.shp else None,
                      "params": {"path": str(PARAMS.relative_to(ROOT)), "sha256": sha256(PARAMS)},
                      "mms": {"path": str(MMS.relative_to(ROOT)), "sha256": sha256(MMS)},
                      "zones": {"path": str(ZONES.relative_to(ROOT)), "sha256": sha256(ZONES)}},
           "n_counties": len({r["fips"] for r in rows}), "n_rows": len(rows), "flag_counts": dict(nflags),
           "national_MMT_CO2e": {f"{s}|{v}": round(x, 4) for (s, v), x in nat.items()},
           "national_MMT_CO2e_Dimputed_sensitivity": {f"{s}|{v}": round(x, 4) for (s, v), x in nat_imp.items()},
           "gwp": GWP, "epa_reference": "EPA Inventory of U.S. GHG Emissions and Sinks 1990-2023 (2025), Table 5-1 p.5-3, 2022 column"}
    MAN.write_text(json.dumps(man, indent=2), encoding="utf-8")
    print(json.dumps(man["national_MMT_CO2e"], indent=1)); print(dict(nflags))


if __name__ == "__main__":
    main()
