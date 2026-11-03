"""Latin hypercube Monte Carlo over IPCC ranges (phase 1: uniform within [lower, upper] as a placeholder;
distribution fitting to 2.5/97.5 percentiles and Sobol indices are phase 2)."""
import numpy as np
from scipy.stats import qmc
from .engine import run_farm

class PerturbedParams:
    def __init__(self, P, overrides):
        self.P, self.o = P, overrides
    def get(self, guideline, factor, disagg="all", field="default", allow_unverified=False):
        k = (factor, disagg)
        if field == "default" and k in self.o: return self.o[k]
        return self.P.get(guideline, factor, disagg, field, allow_unverified)

def lhs_run(farm, guideline, P, factors, n=1000, seed=1, forks=None):
    d = P.df
    specs = []
    for fac, dis in factors:
        r = d[(d.guideline == guideline) & (d.factor == fac) & (d.disaggregation == dis) & (d.status == "VERIFIED")].iloc[0]
        specs.append((fac, dis, r.lower, r.upper))
    u = qmc.LatinHypercube(d=len(specs), seed=seed).random(n)
    out = np.empty(n)
    for i in range(n):
        o = {(f, s): lo + u[i, j] * (hi - lo) for j, (f, s, lo, hi) in enumerate(specs)}
        out[i] = run_farm(farm, guideline, PerturbedParams(P, o), forks)["CO2e_t"]
    return out
