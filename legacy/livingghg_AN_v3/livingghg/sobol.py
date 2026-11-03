"""Sobol sensitivity (optional dependency: SALib). Continuous IPCC factors use [lower, upper] (uniform placeholder);
forks enter as discrete factors: a U(0,1) draw is mapped to an option index."""
import numpy as np
from .montecarlo import PerturbedParams
from .engine import run_farm

def build_problem(P, guideline, factors, registry=None, fork_ids=None):
    d = P.df; names, bounds, specs = [], [], []
    for fac, dis in factors:
        r = d[(d.guideline == guideline) & (d.factor == fac) & (d.disaggregation == dis) & (d.status == "VERIFIED")].iloc[0]
        names.append(f"{fac}[{dis}]"); bounds.append([float(r.lower), float(r.upper)]); specs.append(("p", fac, dis))
    for fk in (registry or []):
        if fork_ids is None or fk["id"] in fork_ids:
            names.append(f"fork:{fk['id']}"); bounds.append([0.0, 1.0]); specs.append(("f", fk["key"], fk["options"]))
    return {"num_vars": len(names), "names": names, "bounds": bounds}, specs

def evaluate(row, specs, farm, guideline, P, base_forks):
    o, forks = {}, dict(base_forks)
    for x, s in zip(row, specs):
        if s[0] == "p": o[(s[1], s[2])] = x
        else: forks[s[1]] = s[2][min(int(x * len(s[2])), len(s[2]) - 1)]
    return run_farm(farm, guideline, PerturbedParams(P, o), forks)["CO2e_t"]

def sobol_indices(farm, guideline, P, factors, registry=None, fork_ids=None, n=64, seed=1):
    from SALib.sample import sobol as ss
    from SALib.analyze import sobol as sa
    prob, specs = build_problem(P, guideline, factors, registry, fork_ids)
    base = {fk["key"]: fk["default"] for fk in (registry or [])}
    X = ss.sample(prob, n, calc_second_order=False, seed=seed)
    Y = np.array([evaluate(r, specs, farm, guideline, P, base) for r in X])
    S = sa.analyze(prob, Y, calc_second_order=False, seed=seed)
    return prob["names"], S["S1"], S["ST"], Y
