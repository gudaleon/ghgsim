"""Run a farm (soil + herds incl. optional manure) and convert to CO2e.
GWP100 is a user setting (default AR5 CH4 28, N2O 265; not from the IPCC parameter table)."""
from .soil_n2o import soil_n2o
from .enteric import enteric_ch4
from .manure import manure_emissions

def run_farm(farm, guideline, P, forks=None, gwp=None):
    gwp = gwp or {"CH4": 28.0, "N2O": 265.0}
    forks = forks or {}
    ch4 = sum(enteric_ch4(h, guideline, P, forks)["total"] for h in farm["herds"])
    ch4_m = n2o_m = 0.0; soil = dict(farm["soil"])
    if forks.get("manure", "include") == "include":
        clim = forks.get("climate", soil.get("climate", "wet"))
        for h in farm["herds"]:
            if "manure" in h:
                r = manure_emissions(h, guideline, P, forks, clim)
                ch4_m += r["CH4"]; n2o_m += r["N2O_total"]
                soil["F_PRP_CPP"] = soil.get("F_PRP_CPP", 0.0) + r["N_PRP_kg"]
    n2o = soil_n2o(soil, guideline, P, forks)["total"]
    N2O, CH4 = n2o + n2o_m, ch4 + ch4_m
    return {"N2O_kg": N2O, "CH4_kg": CH4, "CH4_manure_kg": ch4_m, "N2O_manure_kg": n2o_m,
            "CO2e_t": (N2O * gwp["N2O"] + CH4 * gwp["CH4"]) / 1000.0}
