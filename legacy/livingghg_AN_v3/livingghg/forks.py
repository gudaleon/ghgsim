"""Fork registry: load + validate, one-at-a-time screen ranked by |delta CO2e|."""
import json
from importlib.resources import files
from .engine import run_farm

REQUIRED = {"id", "title", "type", "description", "options", "default", "provenance", "status"}
TYPES = {"bug", "code_choice", "input_assumption", "guideline"}

def load_registry(path=None):
    path = path or files("livingghg") / "data" / "forks_AN_v3.json"
    reg = json.loads(open(path).read())
    for fk in reg:
        missing = REQUIRED - fk.keys()
        if missing: raise ValueError(f"{fk.get('id')}: missing {missing}")
        if fk["type"] not in TYPES: raise ValueError(f"{fk['id']}: bad type")
        if fk["default"] not in fk["options"]: raise ValueError(f"{fk['id']}: default not in options")
    return reg

def oat_screen(farm, guideline, P, registry):
    base_forks = {fk["key"]: fk["default"] for fk in registry}
    base = run_farm(farm, guideline, P, base_forks)["CO2e_t"]
    rows = []
    for fk in registry:
        for opt in fk["options"]:
            if opt == fk["default"]: continue
            forks = dict(base_forks, **{fk["key"]: opt})
            if fk.get("needs_unverified"): forks["allow_unverified"] = True
            try:
                v = run_farm(farm, guideline, P, forks)["CO2e_t"]
                rows.append({"fork": fk["id"], "type": fk["type"], "option": opt, "CO2e_t": v,
                             "delta_t": v - base, "delta_pct": 100 * (v - base) / base,
                             "flag": "uses UNVERIFIED" if fk.get("needs_unverified") else ""})
            except (ValueError, KeyError) as e:
                rows.append({"fork": fk["id"], "type": fk["type"], "option": opt, "CO2e_t": None,
                             "delta_t": None, "delta_pct": None, "flag": f"skipped: {e}"})
    rows.sort(key=lambda r: -abs(r["delta_t"] or 0))
    return base, rows
