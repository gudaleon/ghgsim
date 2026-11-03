"""Demo: 2006 vs 2019 delta and ranked fork table for the STYLIZED example farm."""
import json, pathlib
from livingghg.params import ParamTable
from livingghg.engine import run_farm
from livingghg.forks import load_registry, oat_screen
from livingghg.montecarlo import lhs_run
import numpy as np

farm = json.loads((pathlib.Path(__file__).parent / "example_farm_AN_v2.json").read_text())
P = ParamTable()
print("NOTE:", farm["_label"])
r = {g: run_farm(farm, g, P) for g in ("IPCC2006", "IPCC2019")}
for g, v in r.items():
    print(f"{g}: N2O {v['N2O_kg']:.1f} kg, CH4 {v['CH4_kg']:.1f} kg, {v['CO2e_t']:.1f} t CO2e")
d = r["IPCC2019"]["CO2e_t"] - r["IPCC2006"]["CO2e_t"]
print(f"Delta 2019-2006: {d:+.1f} t CO2e ({100*d/r['IPCC2006']['CO2e_t']:+.1f}%)")
base, rows = oat_screen(farm, "IPCC2019", P, load_registry())
print(f"\nOAT fork ranking (IPCC2019 base {base:.1f} t CO2e):")
print(f"{'rank':<5}{'fork':<6}{'type':<17}{'option':<22}{'delta_t':>9}{'delta_%':>9}  flag")
for i, x in enumerate(rows, 1):
    dt = "n/a" if x["delta_t"] is None else f"{x['delta_t']:+.1f}"
    dp = "n/a" if x["delta_pct"] is None else f"{x['delta_pct']:+.1f}"
    print(f"{i:<5}{x['fork']:<6}{x['type']:<17}{x['option']:<22}{dt:>9}{dp:>9}  {x['flag']}")
mc = lhs_run(farm, "IPCC2019", P, [("EF1","wet_synthetic"),("EF1","wet_other"),("EF5","all"),("FracLEACH","wet"),("Ym","dairy_medium")], n=500)
print(f"\nLHS (n=500, uniform placeholder) IPCC2019 CO2e t: median {np.median(mc):.1f}, 2.5-97.5% [{np.percentile(mc,2.5):.1f}, {np.percentile(mc,97.5):.1f}]")
