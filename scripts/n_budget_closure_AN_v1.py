#!/usr/bin/env python3
"""N-budget closure step (Paper B Phase 4): adds atmospheric N deposition, alfalfa BNF, full soybean BNF (incl.
below-ground), a moisture-corrected crop N removal and a budget-consistent leaching base to the Tier 1 county-year
N budget produced by scripts/run_county_year_tier1_AN_v1.py.

It READS the runner's county ``n_budget`` table (nothing is re-estimated for manure, F_SN, F_PRP, F_SOM or the soil
N2O emissions; those are unchanged) and rebuilds the NASS activity data with the runner's own functions so that
removal, soybean N and alfalfa area can be recomputed. Every recomputed v3 quantity is compared with the runner's
value and the maximum difference is written to the checks table (the closure is only reported if they agree).

The residual is inputs - outputs, reported and never tuned. Refuses to overwrite.
"""
import argparse
import csv
import datetime
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
_s = importlib.util.spec_from_file_location("ghgsim_run_t1", ROOT / "scripts" / "run_county_year_tier1_AN_v1.py")
rt = importlib.util.module_from_spec(_s)
sys.modules["ghgsim_run_t1"] = rt
_s.loader.exec_module(rt)

from ghgsim.modules.tier1_extras import (  # noqa: E402
    alfalfa_bnf_kg,
    deposition_n_kg,
    leach_budget_kg,
    n_budget_v2,
    soybean_bnf_full_kg,
    soybean_bnf_per_grain_kg,
)
from ghgsim.modules.tier1_extras.crop_n_removal import LB_KG  # noqa: E402

PARAMS = ROOT / "data" / "ipcc_params_AN_v12.csv"
AC_HA, TON_LB, VERS = rt.AC_HA, rt.TON_LB, rt.VERS
BU_CROPS_OHIO74 = {"corn_grain": "corn", "soybeans": "soybeans", "wheat_winter": "wheat", "wheat_spring": "wheat",
                   "wheat_durum": "wheat"}

# scenario = (removal basis, soybean choice, alfalfa choice, deposition choice, leach base, fertiliser scale key)
BASE = dict(removal="dm", soy="salv_mid", alf="rb_mean", dep="tdep_total", leach="budget_inputs", fert="as_v3")
SCENARIOS = {
    "HEADLINE_v4": {},
    "v3_replica": dict(removal="nrcs_asis", soy="salv_ag_only_asis", alf="none", dep="none", leach="ipcc_full"),
    "removal_nrcs_asis": dict(removal="nrcs_asis"),
    "removal_ohio_anr74": dict(removal="ohio74"),
    "soy_salv_low": dict(soy="salv_low"),
    "soy_salv_high": dict(soy="salv_high"),
    "soy_ag_only": dict(soy="salv_ag_only"),
    "soy_gelfand_per_grain": dict(soy="gelfand"),
    "alf_none": dict(alf="none"),
    "alf_russelle_min45": dict(alf="rb_min"),
    "alf_peterson61lb_per_ton": dict(alf="pr61"),
    "dep_wet_only": dict(dep="tdep_wet"),
    "dep_none": dict(dep="none"),
    "leach_ipcc_full_Eq11.10": dict(leach="ipcc_full"),
    "leach_net_surplus_nonIPCC": dict(leach="net_surplus"),
    "fert_falcone2017_ohio_total": dict(fert="falcone"),
    "fert_nugis2016_ohio_total": dict(fert="nugis2016"),
    "ALL_LOW_inputs": dict(soy="salv_low", alf="rb_min", dep="tdep_wet"),
    "ALL_HIGH_inputs": dict(soy="salv_high", alf="pr61", dep="tdep_total"),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def outp(d, name, suffix):
    path = d / f"{name}{suffix}.csv"
    if path.exists():
        sys.exit(f"refusing to overwrite {path}")
    return path


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def county_inputs(p, ci):
    """Recompute the runner's per-county removal (both bases) and the soybean / alfalfa activity data."""
    fi = rt.forage_inputs(ci["ext"])
    rem, _ = rt.removal(p, ci, fi)
    rem_dm, _ = rt.removal(p, ci, fi, dm_correct=True)
    ohio = dict(rem_dm)
    for crop, key in BU_CROPS_OHIO74.items():
        if crop in ci["cropin"]:
            ohio[crop] = ci["cropin"][crop][1] * p[f"OHIO_ANR74.N_lb_per_bu.{key}"] * LB_KG
    soy_bu = ci["cropin"]["soybeans"][1] if "soybeans" in ci["cropin"] else 0.0
    soy_ha = ci["cropin"]["soybeans"][0] * AC_HA if "soybeans" in ci["cropin"] else 0.0
    alf_ha = (fi["hay_alf_ac"] + fi["haylage_alf_ac"]) * AC_HA
    alf_t = fi["hay_alf_t"] + fi["haylage_alf_dryeq_t"]
    soy_ag_res = None
    return dict(fi=fi, rem=rem, rem_dm=rem_dm, rem_ohio=ohio, soy_bu=soy_bu, soy_ha=soy_ha, alf_ha=alf_ha, alf_t=alf_t,
                other_hay_N_removed_asis=rem.get("other_hay", 0.0) + rem.get("other_haylage", 0.0), soy_ag_res=soy_ag_res)


def terms_for(cfg, p, ver, v3, act, dep, fert_ratio, e):
    """Return the budget dict for one county under scenario ``cfg`` (kg N)."""
    g = lambda k: float(v3[k] or 0.0)  # noqa: E731
    fsn_v3, applied, prp, fsom = g("synthetic_N"), g("manure_N_applied"), g("PRP_N"), g("F_SOM")
    fsn = fsn_v3 * (fert_ratio if cfg["fert"] != "as_v3" else 1.0)
    soy_ag_res = g("soy_AG_residue_N")
    seed_dm, seed_asis = act["rem_dm"].get("soybeans", 0.0), act["rem"].get("soybeans", 0.0)
    ndfa_mid, bg_mid = p["SALV2008.soy_Ndfa"], p["SALV2008.soy_BG_share_total_N"]
    s = cfg["soy"]
    if s == "salv_mid":
        soy = soybean_bnf_full_kg(seed_dm, soy_ag_res, ndfa_mid, bg_mid)["BNF_total"]
    elif s == "salv_low":
        soy = soybean_bnf_full_kg(seed_dm, soy_ag_res, 0.50, p["GELFAND2015.soy_BG_share_total_N_measured"])["BNF_total"]
    elif s == "salv_high":
        soy = soybean_bnf_full_kg(seed_dm, soy_ag_res, 0.60, p["ROCHESTER_UNKOVICH.soy_BG_share_total_N_high"])["BNF_total"]
    elif s == "salv_ag_only":
        soy = soybean_bnf_full_kg(seed_dm, soy_ag_res, ndfa_mid, 0.0)["BNF_total"]
    elif s == "salv_ag_only_asis":
        soy = soybean_bnf_full_kg(seed_asis, soy_ag_res, ndfa_mid, 0.0)["BNF_total"]
    elif s == "gelfand":
        soy = soybean_bnf_per_grain_kg(act["soy_bu"] * 60 * LB_KG, p["GELFAND2015.soy_BNF_g_N_per_kg_grain"])
    else:
        raise ValueError(s)
    a = cfg["alf"]
    if a == "rb_mean":
        alf = alfalfa_bnf_kg(act["alf_ha"], p["RUSSELLE2004.alfalfa_fixed_N_kg_per_ha"])
    elif a == "rb_min":
        alf = alfalfa_bnf_kg(act["alf_ha"], 45.0)
    elif a == "pr61":
        alf = act["alf_t"] * p["PETERSON1991.alfalfa_fixed_N_lb_per_ton"] * LB_KG
    elif a == "none":
        alf = 0.0
    else:
        raise ValueError(a)
    d = cfg["dep"]
    ha = g("cropland_harvested_ha")
    dep_ = {"tdep_total": deposition_n_kg(dep["total"], ha), "tdep_wet": deposition_n_kg(dep["wet"], ha), "none": 0.0}[d]
    r = cfg["removal"]
    removal = {"dm": sum(act["rem_dm"].values()), "nrcs_asis": sum(act["rem"].values()), "ohio74": sum(act["rem_ohio"].values())}[r]
    dfsn = fsn - fsn_v3
    vol = g("soil_volatilised") + dfsn * e["fgasf"]
    n2o = g("soil_N2O_N_direct")
    l_full = g("soil_leached") + dfsn * e["fl"]
    l_budget = leach_budget_kg(e["fl"], fsn, applied, prp, fsom)
    inputs_pre = fsn + applied + prp + soy + alf + dep_ + fsom
    lc = cfg["leach"]
    if lc == "budget_inputs":
        leach = l_budget
    elif lc == "ipcc_full":
        leach = l_full
    elif lc == "net_surplus":
        leach = e["fl"] * max(0.0, inputs_pre - removal - vol)
    else:
        raise ValueError(lc)
    nb = n_budget_v2(dict(synthetic_N=fsn, manure_N_applied=applied, PRP_N=prp, BNF_soy_total=soy, BNF_alfalfa=alf,
                          N_deposition=dep_, F_SOM=fsom, crop_N_removed=removal, soil_volatilised=vol, soil_leached=leach,
                          soil_N2O_N_direct=n2o))
    nb["leach_if_budget_inputs"], nb["leach_if_ipcc_full"] = l_budget, l_full
    return nb


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--state-fips", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--census-tsv", nargs="+", required=True)
    ap.add_argument("--v3-n-budget", required=True, help="runner county n_budget CSV for this year/config")
    ap.add_argument("--fert-html", required=True)
    ap.add_argument("--fert-year", type=int, default=2017)
    ap.add_argument("--tdep-csv", required=True, help="columns year,fips,N_dep_total_kgN_ha,N_dep_wet_kgN_ha")
    ap.add_argument("--fert-alt-csv", help="CSV key,kg_N_state with keys falcone,nugis2016 (state totals, kg N)")
    ap.add_argument("--climate", choices=("zones", "all_wet"), default="all_wet")
    ap.add_argument("--forage-frac-renew", type=float, default=1.0)
    ap.add_argument("--params", default=str(PARAMS))
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--suffix", default="_AN_v1")
    a = ap.parse_args(argv)
    od = pathlib.Path(a.out_dir)
    od.mkdir(parents=True, exist_ok=True)
    tag = f"{a.state_fips}_{a.year}_{a.climate}"
    paths = {n: outp(od, f"n_budget_closure_{n}_{tag}", a.suffix) for n in ("county", "state_scenarios", "bridge_v3_to_v4", "checks")}
    p = rt.load_params(a.params)
    zones = {r["fips"]: r for r in csv.DictReader(open(rt.v1.ZONES, encoding="utf-8")) if r["fips"].startswith(a.state_fips)}
    import pandas as pd
    t = pd.read_html(a.fert_html)[0]
    col = [c for c in t.columns if str(a.fert_year) in c and "1000 kg" in c][0]
    fert = {str(s).strip().upper(): float(v) * 1000.0 for s, v in zip(t["State"], t[col], strict=True)}
    county, state = rt.read_census(a.census_tsv, a.year, a.state_fips)
    ci_all = rt.build_county(p, county, state, a.state_fips, fert, a.fert_year, zones, a.climate)
    v3_rows = {(r["fips"], r["version"]): r for r in read_csv(a.v3_n_budget) if str(r["year"]) == str(a.year)}
    tdep = {r["fips"]: dict(total=float(r["N_dep_total_kgN_ha"]), wet=float(r["N_dep_wet_kgN_ha"]))
            for r in read_csv(a.tdep_csv) if str(r["year"]) == str(a.year)}
    alt = {r["key"]: float(r["kg_N_state"]) for r in read_csv(a.fert_alt_csv)} if a.fert_alt_csv else {}
    fsn_state_v3 = sum(float(r["synthetic_N"] or 0.0) for (f, v), r in v3_rows.items() if v == "2006")

    # --- recompute checks against the runner's own v3 numbers
    chk = {"removal_asis": 0.0, "removal_dm": 0.0, "soy_BNF_AG_v3": 0.0, "leach_full_v3": 0.0, "county_missing_tdep": 0}
    acts = {}
    for f, ci in sorted(ci_all.items()):
        act = county_inputs(p, ci)
        acts[f] = act
        for ver in VERS:
            v3 = v3_rows[(f, ver)]
            chk["removal_asis"] = max(chk["removal_asis"], abs(sum(act["rem"].values()) - float(v3["crop_N_removed"])))
            chk["removal_dm"] = max(chk["removal_dm"], abs(sum(act["rem_dm"].values()) - float(v3["crop_N_removed_dm_corrected"])))
            bnf3 = soybean_bnf_full_kg(act["rem"].get("soybeans", 0.0), float(v3["soy_AG_residue_N"]), p["SALV2008.soy_Ndfa"], 0.0)["BNF_total"]
            chk["soy_BNF_AG_v3"] = max(chk["soy_BNF_AG_v3"], abs(bnf3 - float(v3["BNF_soy_AG"])))
            e = rt.efs(p, ver, v3["wet"] in ("True", "true", "1"))
            base = sum(float(v3[k] or 0.0) for k in ("synthetic_N", "manure_N_applied", "PRP_N", "residue_N_recycled_annual_crops",
                                                    "residue_N_recycled_forage_silage", "F_SOM"))
            chk["leach_full_v3"] = max(chk["leach_full_v3"], abs(e["fl"] * base - float(v3["soil_leached"])))
        if f not in tdep:
            chk["county_missing_tdep"] += 1

    rows_c, rows_s = [], []
    state_sum = {}
    for scen, over in SCENARIOS.items():
        cfg = dict(BASE, **over)
        for ver in VERS:
            tot, ha_tot, max_err = {}, 0.0, 0.0
            for f, ci in sorted(ci_all.items()):
                v3 = v3_rows[(f, ver)]
                e = rt.efs(p, ver, v3["wet"] in ("True", "true", "1"))
                ratio = (alt[cfg["fert"]] / fsn_state_v3) if cfg["fert"] in alt else 1.0
                nb = terms_for(cfg, p, ver, v3, acts[f], tdep.get(f, dict(total=0.0, wet=0.0)), ratio, e)
                max_err = max(max_err, abs(nb["closure_error"]))
                ha = float(v3["cropland_harvested_ha"])
                ha_tot += ha
                for k, v in nb.items():
                    if isinstance(v, (int, float)):
                        tot[k] = tot.get(k, 0.0) + v
                if scen == "HEADLINE_v4":
                    act = acts[f]
                    rows_c.append(dict(year=a.year, fips=f, county=ci["name"], version=ver, cropland_harvested_ha=ha,
                                       **{k: v for k, v in nb.items()},
                                       residual_kg_per_ha=nb["residual_unaccounted"] / ha if ha else None,
                                       N_dep_total_kg_ha=tdep.get(f, {}).get("total"), N_dep_wet_kg_ha=tdep.get(f, {}).get("wet"),
                                       alfalfa_ha=act["alf_ha"], soybean_ha=act["soy_ha"], soybean_grain_bu=act["soy_bu"],
                                       alfalfa_N_removed_dm=act["rem_dm"].get("alfalfa_hay", 0.0) + act["rem_dm"].get("alfalfa_haylage", 0.0),
                                       other_hay_N_removed_asis=act["other_hay_N_removed_asis"],
                                       v3_residual_unaccounted=float(v3["residual_unaccounted"]),
                                       v3_residual_kg_per_ha=float(v3["residual_unaccounted"]) / ha if ha else None))
            tot["cropland_harvested_ha"] = ha_tot
            tot["max_abs_closure_error_kg"] = max_err
            state_sum[(scen, ver)] = tot
            rows_s.append(dict(year=a.year, scenario=scen, version=ver, **{f"{k}_GgN": v / 1e6 for k, v in tot.items()
                              if k not in ("cropland_harvested_ha", "max_abs_closure_error_kg", "NUE_removed_over_inputs", "closure_error")},
                               cropland_harvested_ha=ha_tot, residual_kg_per_ha=tot["residual_unaccounted"] / ha_tot,
                               NUE_removed_over_inputs=tot["crop_N_removed"] / tot["inputs_total"],
                               max_abs_closure_error_kg=max_err, **{f"cfg_{k}": v for k, v in cfg.items()}))

    # --- bridge v3 -> v4 (every step is additive and independent of the others, so order does not matter)
    rows_b = []
    for ver in VERS:
        h, r3 = state_sum[("HEADLINE_v4", ver)], state_sum[("v3_replica", ver)]
        v3_sum = sum(float(r["residual_unaccounted"]) for (f, v), r in v3_rows.items() if v == ver)
        steps = [
            ("v3 residual (runner, as published)", v3_sum),
            ("replica of v3 recomputed here (check = 0)", r3["residual_unaccounted"] - v3_sum),
            ("+ atmospheric N deposition (TDep total x harvested cropland ha)", h["N_deposition"]),
            ("+ alfalfa BNF (Russelle & Birr 2004 mean x alfalfa ha)", h["BNF_alfalfa"]),
            ("+ soybean BNF: below-ground added (Salvagiotti 24 %) and DM-corrected seed N",
             h["BNF_soy_total"] - r3["BNF_soy_total"]),
            ("+ moisture correction: crop N removal DM basis (smaller removal)", r3["crop_N_removed"] - h["crop_N_removed"]),
            ("+ leaching base without recycled residue N (smaller leaching)", r3["soil_leached"] - h["soil_leached"]),
        ]
        cum = 0.0
        for i, (name, v) in enumerate(steps):
            cum = v if i == 0 else cum + v
            rows_b.append(dict(year=a.year, version=ver, step=name, change_GgN=v / 1e6, cumulative_residual_GgN=cum / 1e6))
        rows_b.append(dict(year=a.year, version=ver, step="v4 headline residual (state sum of counties)", change_GgN="",
                           cumulative_residual_GgN=h["residual_unaccounted"] / 1e6))
        rows_b.append(dict(year=a.year, version=ver, step="bridge check: cumulative - v4 headline (must be ~0)", change_GgN="",
                           cumulative_residual_GgN=(cum - h["residual_unaccounted"]) / 1e6))
    rows_k = [dict(year=a.year, check=k, value=v) for k, v in chk.items()]
    rows_k += [dict(year=a.year, check=f"max_abs_closure_error_kg:{s}:{v}", value=state_sum[(s, v)]["max_abs_closure_error_kg"])
               for (s, v) in state_sum]
    rt.write_csv(paths["county"], rows_c)
    rt.write_csv(paths["state_scenarios"], rows_s)
    rt.write_csv(paths["bridge_v3_to_v4"], rows_b)
    rt.write_csv(paths["checks"], rows_k)
    try:
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True).stdout.strip())
    except Exception:  # noqa: BLE001
        head, dirty = "", None
    man = od / f"n_budget_closure_run_manifest_{tag}{a.suffix}.json"
    if man.exists():
        sys.exit(f"refusing to overwrite {man}")
    man.write_text(json.dumps(dict(created=datetime.datetime.now().isoformat(), ghgsim_head=head, worktree_dirty=dirty,
                                   params=a.params, params_sha256=sha256(a.params), v3_n_budget=a.v3_n_budget,
                                   v3_sha256=sha256(a.v3_n_budget), tdep_csv=a.tdep_csv, tdep_sha256=sha256(a.tdep_csv),
                                   scenarios=SCENARIOS, base=BASE, checks=chk), indent=1))
    print("wrote", ", ".join(p_.name for p_ in paths.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
