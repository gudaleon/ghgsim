"""County run v3: dairy + beef cows (enteric, manure, PRP) with EPA-2025 per-state inputs, plus crop-soil N2O
(Falcone 2021 fertiliser N + non-cattle manure N, NASS 2022 crop residue N), IPCC2006 vs IPCC2019.
Withheld (D) county cow counts filled per fork F011. Pipeline forks: data/forks_pipeline_AN_v3.json.
Example: python scripts/run_counties_AN_v3.py --states VT,DE --n 20 --workers 2 --out /tmp/lgres --trial"""
import argparse, json, os, pathlib, sys
from multiprocessing import Pool
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from livingghg.params import ParamTable
from livingghg.engine import run_farm
from livingghg.montecarlo import lhs_run
from livingghg import gapfill
from livingghg.crop_residue import county_f_cr

SUFFIX = "_AN_v3"
MC_FACTORS = [("EF1", "all"), ("EF3PRP_CPP", "all"), ("EF4", "all"), ("FracGASM", "all")]
COWS = {"milk": "CATTLE, COWS, MILK - INVENTORY", "beef": "CATTLE, COWS, BEEF - INVENTORY"}
DN, DU = ROOT / "data_nass", ROOT / "data_us"

def _fips(d):
    return d.STATE_FIPS_CODE.astype(str).str.zfill(2) + d.COUNTY_CODE.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(3)

def load_counties(path, states):
    d = pd.read_csv(path, dtype=str)
    d = d[d.SHORT_DESC.isin(COWS.values()) & d.COUNTY_CODE.notna() & d.STATE_ALPHA.isin(states)].copy()
    d["v"] = pd.to_numeric(d.VALUE.str.replace(",", "").str.strip(), errors="coerce")
    d["fips"] = _fips(d)
    w = d.groupby(["fips", "SHORT_DESC"]).v.first().unstack().reindex(columns=list(COWS.values()))
    w = d.drop_duplicates("fips").set_index("fips")[["STATE_ALPHA", "COUNTY_NAME"]].join(w).reset_index()
    return w.rename(columns={COWS["milk"]: "milk_cows", COWS["beef"]: "beef_cows"})

def apply_fill(w, mode, states):
    for an in ("milk", "beef"):
        col = f"{an}_cows"; w[f"{an}_fill"] = np.where(w[col].isna(), "withheld", "reported")
    if mode == "none":
        return w
    sc = gapfill.prepare(pd.read_csv(DN / "nass2022_cows_sizeclass_AN_v1.csv.gz", dtype=str))
    sc = sc[sc.STATE_ALPHA.isin(states)]
    f = pd.concat([r[0] for st in states for an in ("milk", "beef") if (r := gapfill.fill_state_sizeclass(sc, st, an)) is not None and len(r[0])] or [pd.DataFrame(columns=["fips", "animal", "filled_head", "fill_method", "STATE_ALPHA", "COUNTY_NAME"])])
    if mode == "prior_census" and len(f):
        f = gapfill.fill_prior_census(f, pd.read_csv(DN / "nass_census2002_2017_cows_county_AN_v3.csv.gz", dtype=str))
    for an in ("milk", "beef"):
        m = f[f.animal == an].set_index("fips")
        col = f"{an}_cows"; miss = w[col].isna() & w.fips.isin(m.index)
        w.loc[miss, col] = w.loc[miss, "fips"].map(m.filled_head)
        w.loc[miss, f"{an}_fill"] = w.loc[miss, "fips"].map(m.fill_method)
    return w

def soil_inputs(fips, manure_basis):
    fa = pd.read_csv(DU / "usgs_falcone2021_county_N_2017_AN_v3.csv.gz", dtype={"STCOFIPS": str})
    fa["fips"] = fa.STCOFIPS.str.zfill(5)
    fa = fa.set_index("fips")
    cr = county_f_cr(pd.read_csv(DN / "nass_census2022_crops_county_AN_v3.csv.gz", dtype=str),
                     pd.read_csv(DU / "crop_residue_ipcc2019_AN_v3.csv")).set_index("fips")
    o = pd.DataFrame(index=pd.Index(fips, name="fips"))
    o["F_SN"] = fa["farmfertN-kg-2017"].reindex(o.index)
    o["F_ON"] = (fa[["Hogs_N_kg-2017", "Poultry_N_kg-2017", "Other_N_kg-2017"]].sum(axis=1).reindex(o.index)
                 if manure_basis == "noncattle_excreted" else 0.0)
    o["F_CR"] = cr.F_CR_kgN.reindex(o.index); o["F_CR_flag"] = cr.F_CR_flag.reindex(o.index)
    return o

def farm_for(row, S, climate):
    herds = []
    for kind, col in (("dairy", "milk_cows"), ("beef", "beef_cows")):
        h = row.get(col)
        if h is not None and not pd.isna(h) and h > 0:
            herds.append(dict(S[kind], head=float(h)))
    soil = {"climate": climate}
    for k in ("F_SN", "F_ON", "F_CR"):
        v = row.get(k); soil[k] = 0.0 if v is None or pd.isna(v) else float(v)
    return {"soil": soil, "herds": herds}

def run_state(args):
    st, rows, n, out, forks, A, factor = args
    P = ParamTable(); S = A["states"][st]
    res = []
    for row in rows:
        for c in ("milk_cows", "beef_cows"):
            if pd.notna(row.get(c)): row[c] = row[c] * factor
        farm = farm_for(row, S, A["climate"])
        rec = {k: row.get(k) for k in ("fips", "STATE_ALPHA", "COUNTY_NAME", "milk_cows", "beef_cows", "milk_fill", "beef_fill", "F_SN", "F_ON", "F_CR", "F_CR_flag")}
        for g in ("IPCC2006", "IPCC2019"):
            r = run_farm(farm, g, P, forks)
            rec[f"{g}_CO2e_t"], rec[f"{g}_CH4_kg"], rec[f"{g}_N2O_kg"] = r["CO2e_t"], r["CH4_kg"], r["N2O_kg"]
            if n:
                mc = lhs_run(farm, g, P, MC_FACTORS, n=n, seed=int(row["fips"]))
                rec[f"{g}_p2.5"], rec[f"{g}_p50"], rec[f"{g}_p97.5"] = np.percentile(mc, [2.5, 50, 97.5])
        res.append(rec)
    f = pathlib.Path(out) / f"counties_{st}{SUFFIX}.csv"
    pd.DataFrame(res).to_csv(f, index=False)
    return st, len(res), str(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", default="all"); ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=2); ap.add_argument("--out", default="results")
    ap.add_argument("--withheld-fill", default="sizeclass", choices=["sizeclass", "prior_census", "none"])
    ap.add_argument("--manure-n-basis", default="noncattle_excreted", choices=["noncattle_excreted", "none"])
    ap.add_argument("--unpermitted-facility-factor", type=float, default=1.0)
    ap.add_argument("--allow-watershed-factor", action="store_true", help="F010 is watershed-only; never use for NASS county totals")
    ap.add_argument("--trial", action="store_true", help="label outputs as TRIAL")
    ap.add_argument("--nass", default=str(DN / "nass_census2022_county_AN_v1.csv.gz"))
    a = ap.parse_args()
    if a.unpermitted_facility_factor != 1.0 and not a.allow_watershed_factor:
        sys.exit("F010 unpermitted_facility_factor is a watershed-only sensitivity (Kast et al. 2019); refusing to apply it to NASS county totals without --allow-watershed-factor")
    os.makedirs(a.out, exist_ok=True)
    A = json.loads((ROOT / "scripts" / "county_assumptions_AN_v3.json").read_text())
    states = sorted(A["states"]) if a.states == "all" else a.states.split(",")
    w = apply_fill(load_counties(a.nass, states), a.withheld_fill, states)
    w = w.join(soil_inputs(w.fips, a.manure_n_basis), on="fips")
    forks = {fk["key"]: fk["default"] for fk in json.loads((ROOT / "livingghg" / "data" / "forks_AN_v3.json").read_text())}
    jobs = [(s, w[w.STATE_ALPHA == s].to_dict("records"), a.n, a.out, forks, A, a.unpermitted_facility_factor) for s in states]
    meta = {"label": "TRIAL RUN - not results" if a.trial else "run", "args": vars(a), "suffix": SUFFIX}
    (pathlib.Path(a.out) / f"run_meta{SUFFIX}.json").write_text(json.dumps(meta, indent=1))
    with Pool(a.workers, maxtasksperchild=1) as pool:
        for st, k, f in pool.imap_unordered(run_state, jobs):
            print(f"{st}: {k} counties -> {f}", flush=True)

if __name__ == "__main__":
    main()
