"""Sobol indices (SALib) per state on the state-aggregated livestock farm: IPCC factors + forks as discrete factors.
Usage (Bubble PC): python scripts\\sobol.py --states all --n 4096 --workers 18 --out G:\\lg\\results
Box test:          python scripts/sobol.py --states VT --n 8 --workers 1 --out /tmp/lgres"""
import argparse, json, os, pathlib, sys
from multiprocessing import Pool
import pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from livingghg.params import ParamTable
from livingghg.forks import load_registry
from livingghg.sobol import sobol_indices
from run_counties import load_counties, farm_for, SUFFIX

FACTORS = {"IPCC2019": [("EF3PRP_CPP", "all"), ("EF4", "all"), ("EF5", "all"), ("FracGASM", "all"), ("Ym", "dairy_medium"), ("Ym", "nondairy_forage_gt75")],
           "IPCC2006": [("EF3PRP_CPP", "all"), ("EF4", "all"), ("EF5", "all"), ("FracGASM", "all"), ("Ym", "dairy"), ("Ym", "other_cattle")]}
FORKS = {"IPCC2019": ["F001", "F008", "F009"], "IPCC2006": ["F009"]}

def run_state(args):
    st, rows, n, out = args
    P = ParamTable(); A = json.loads((ROOT / "scripts" / "county_assumptions_AN_v1.json").read_text())
    tot = {"milk_cows": sum(r["milk_cows"] for r in rows if pd.notna(r.get("milk_cows"))),
           "beef_cows": sum(r["beef_cows"] for r in rows if pd.notna(r.get("beef_cows")))}
    farm = farm_for(tot, A); reg = load_registry(); out_rows = []
    for g in ("IPCC2006", "IPCC2019"):
        names, S1, ST, Y = sobol_indices(farm, g, P, FACTORS[g], reg, FORKS[g], n=n)
        out_rows += [{"state": st, "guideline": g, "factor": a, "S1": b, "ST": c, "n_base": n, "n_evals": len(Y),
                      "note": "county (D) values excluded from state sum"} for a, b, c in zip(names, S1, ST)]
    f = pathlib.Path(out) / f"sobol_{st}{SUFFIX}.csv"; pd.DataFrame(out_rows).to_csv(f, index=False)
    return st, str(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", default="all"); ap.add_argument("--n", type=int, default=1024)
    ap.add_argument("--workers", type=int, default=18); ap.add_argument("--out", default="results")
    ap.add_argument("--nass", default=str(ROOT / "data_nass" / "nass_census2022_county_AN_v1.csv.gz"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    w = load_counties(a.nass)
    states = sorted(w.STATE_ALPHA.unique()) if a.states == "all" else a.states.split(",")
    jobs = [(s, w[w.STATE_ALPHA == s].to_dict("records"), a.n, a.out) for s in states]
    with Pool(a.workers, maxtasksperchild=1) as pool:
        for st, f in pool.imap_unordered(run_state, jobs):
            print(f"{st}: sobol -> {f}", flush=True)

if __name__ == "__main__":
    main()
