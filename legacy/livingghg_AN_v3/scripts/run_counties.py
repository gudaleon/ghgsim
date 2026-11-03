"""County livestock run (enteric + manure, incl. PRP N2O) for IPCC2006 and IPCC2019, split by state, multiprocess.
Inputs: NASS 2022 Census county inventory (milk cows, beef cows). Per-head inputs are ASSUMED (see county_assumptions).
Usage (Bubble PC): python scripts\\run_counties.py --states all --n 10000 --workers 18 --out G:\\lg\\results
Box test:          python scripts/run_counties.py --states VT,DE --n 20 --workers 2 --out /tmp/lgres"""
import argparse, json, os, pathlib, sys
from multiprocessing import Pool
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from livingghg.params import ParamTable
from livingghg.engine import run_farm
from livingghg.montecarlo import lhs_run

SUFFIX = "_AN_v2"
MC_FACTORS = [("EF1", "all"), ("EF3PRP_CPP", "all"), ("EF4", "all"), ("FracGASM", "all")]
COWS = {"milk": "CATTLE, COWS, MILK - INVENTORY", "beef": "CATTLE, COWS, BEEF - INVENTORY"}

def load_counties(path):
    d = pd.read_csv(path, dtype=str)
    d = d[d.SHORT_DESC.isin(COWS.values())].copy()
    d["v"] = pd.to_numeric(d.VALUE.str.replace(",", "").str.strip(), errors="coerce")  # (D) -> NaN (suppressed)
    w = d.pivot_table(index=["STATE_ALPHA", "STATE_FIPS_CODE", "COUNTY_CODE", "COUNTY_NAME"], columns="SHORT_DESC", values="v", aggfunc="first").reset_index()
    return w.rename(columns={COWS["milk"]: "milk_cows", COWS["beef"]: "beef_cows"})

def farm_for(row, A):
    herds = []
    for kind, col in (("dairy", "milk_cows"), ("beef", "beef_cows")):
        h = row.get(col)
        if h is not None and not pd.isna(h) and h > 0:
            herds.append(dict(A[kind], head=float(h)))
    return {"soil": {"climate": A["climate"]}, "herds": herds}

def run_state(args):
    st, rows, n, out = args
    P = ParamTable(); A = json.loads((ROOT / "scripts" / "county_assumptions_AN_v1.json").read_text())
    res = []
    for row in rows:
        farm = farm_for(row, A); rec = {k: row[k] for k in ("STATE_ALPHA", "STATE_FIPS_CODE", "COUNTY_CODE", "COUNTY_NAME")}
        rec["milk_cows"], rec["beef_cows"] = row.get("milk_cows"), row.get("beef_cows")
        rec["suppressed_D"] = any(pd.isna(row.get(c)) for c in ("milk_cows", "beef_cows"))
        for g in ("IPCC2006", "IPCC2019"):
            r = run_farm(farm, g, P) if farm["herds"] else {"CO2e_t": 0.0, "CH4_kg": 0.0, "N2O_kg": 0.0}
            rec[f"{g}_CO2e_t"], rec[f"{g}_CH4_kg"], rec[f"{g}_N2O_kg"] = r["CO2e_t"], r["CH4_kg"], r["N2O_kg"]
            if n and farm["herds"]:
                mc = lhs_run(farm, g, P, MC_FACTORS, n=n, seed=int(row["STATE_FIPS_CODE"]) * 1000 + int(row["COUNTY_CODE"]))
                rec[f"{g}_p2.5"], rec[f"{g}_p50"], rec[f"{g}_p97.5"] = np.percentile(mc, [2.5, 50, 97.5])
        res.append(rec)
    f = pathlib.Path(out) / f"counties_{st}{SUFFIX}.csv"
    pd.DataFrame(res).to_csv(f, index=False)
    return st, len(res), str(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", default="all"); ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=18); ap.add_argument("--out", default="results")
    ap.add_argument("--nass", default=str(ROOT / "data_nass" / "nass_census2022_county_AN_v1.csv.gz"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    w = load_counties(a.nass)
    states = sorted(w.STATE_ALPHA.unique()) if a.states == "all" else a.states.split(",")
    jobs = [(s, w[w.STATE_ALPHA == s].to_dict("records"), a.n, a.out) for s in states]
    # one state per task keeps per-worker memory small (~<300 MB each; 18 workers << 24 GB cap)
    with Pool(a.workers, maxtasksperchild=1) as pool:
        for st, k, f in pool.imap_unordered(run_state, jobs):
            print(f"{st}: {k} counties -> {f}", flush=True)

if __name__ == "__main__":
    main()
