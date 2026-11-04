"""IPCC 2006 vs IPCC 2019 Refinement Tier 1/2 comparison on the stylized farms (AN_v2).

Changes from AN_v1: ipcc2019.manure 2.0 (2019 Table 10.17 MCF by climate zone with
12-month liquid/pit storage, Table 10.16A B0, Table 10.19 Nrate, Table 10.22 FracGasMS
and Table 10.21 EF3 for cattle too); 2006 F_ON = Eq 10.34 with Table 10.23 FracLossMS
(total N loss incl. leaching/runoff) instead of the EF4 back-out.
2019 climate zone: warm_temperate_moist, derived from the spec itself: meta.climate_zone
= 15C (MAT 15 C > 10 C -> warm temperate, 2006 GL Vol4 Ch3 Annex 3A.5) and every field
climate = wet (moist). Not a county observation.

Runs only ghgsim's IPCC modules (ipcc2006.*, ipcc2019.*) with parameters from the
latest data/ipcc_params_AN_v*.csv. No Holos parameters, forks, or MS2 data are used.

Shared activity data (identical for both versions, so only the method differs):
- Cattle GE: IPCC 2006 Eq 10.16 from NE terms of Eq 10.3/10.4/10.8/10.13 and REM
  Eq 10.14 (emissions_sankey.net_energy, inputs from data/stylized_farms_AN_v6.yaml).
- Cattle VS: IPCC 2006 Eq 10.24, ASH and UE as registered in the stylized spec
  (UE = 0.02 if DE >= ue_ipcc_de_threshold else 0.04).
- Nex: EPA Nex override from the stylized spec when present (same both versions);
  otherwise each module derives Nex from its own Nrate x TAM (TAM = spec mass).
- Monogastric VS: stylized spec VS_kg_day; enteric uses each version's Tier 1 EF.
- Managed soil: F_SN, F_SOM, F_CR from the stylized field (F_CR via Eq 11.6
  coefficients as implemented in HolosFieldN with manure linking switched off);
  F_ON = manure N available after MMS losses from each version's own manure run;
  F_PRP_CPP = each version's N_PRP_kg.

Usage: python scripts/compare_ipcc_2006_2019_stylized_AN_v1.py
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import ghgsim.modules.holos  # noqa: F401  (import first: avoids ipcc2006 circular import)
from ghgsim.core.registry import load_parameter_csv
from ghgsim.modules.ipcc2019.crop_residue import TABLE_11_1A_CROPS, IPCC2019CropResidue, crop_coeff_param_keys
from ghgsim.modules.ipcc2006 import IPCC2006SoilN2O
from ghgsim.modules.ipcc2006.enteric import IPCC2006Enteric
from ghgsim.modules.ipcc2006.manure import IPCC2006Manure
from ghgsim.modules.ipcc2019.enteric import IPCC2019Enteric
from ghgsim.modules.ipcc2019.manure import IPCC2019Manure
from ghgsim.modules.ipcc2019.soil_n2o import IPCC2019SoilN2O
from ghgsim.report.emissions_sankey import (
    _const,
    _field_crops,
    _yaml_number,
    animal_mass_kg,
    gwp_from_spec,
    herd_de_tdn,
    load_stylized_spec,
    net_energy,
    nex_kg_yr,
)
from ghgsim.report.fork_diagram import latest_versioned

SPEC = ROOT / "data" / "stylized_farms_AN_v6.yaml"
OUT_CSV = ROOT / "data" / "ipcc_2006_vs_2019_stylized_AN_v2.csv"
CLIMATE_ZONE_2019 = "warm_temperate_moist"  # from spec 15C + wet fields; see docstring
STORAGE_MONTHS = 12  # Alex 2026-11-03 decision (Table 10.17 fn 1 default would be 6)
N2O_N_TO_N2O = 44.0 / 28.0
MONOGASTRIC = {"market_swine", "breeding_swine", "broilers", "layers", "turkeys"}
CATTLE_AT = {"dairy": "dairy", "beef": "other_cattle"}
MODULES = {
    "IPCC2006": (IPCC2006Enteric(), IPCC2006Manure(), IPCC2006SoilN2O()),
    "IPCC2019": (IPCC2019Enteric(), IPCC2019Manure(), IPCC2019SoilN2O()),
}


def resolve(module, reg) -> dict[str, float]:
    """Resolve a module's ParamRefs from the IPCC registry; keep only keys that exist."""
    out = {}
    for name, ref in module.parameters.items():
        try:
            out[name] = float(reg.get_value(ref.key))
        except Exception:
            if ref.fallback is not None:
                out[name] = float(ref.fallback)
    return out


def ym_categories(animal: dict, farm: dict, diet: dict, milk_kg_yr: float) -> tuple[str, str]:
    """IPCC 2006 Table 10.12 and 2019 Table 10.12 (Updated) categories. Documented mapping."""
    if animal["animal_type"] == "dairy" and animal.get("apply_lactation"):
        # 2019: >8500 kg milk/yr = high producing; NDF not in spec -> forage share proxy.
        if milk_kg_yr > 8500:
            c19 = "dairy_high_ndf_ge35" if float(diet["forage_percent"]["value"]) >= 50 else "dairy_high_ndf_le35"
        elif milk_kg_yr >= 5000:
            c19 = "dairy_medium"
        else:
            c19 = "dairy_low"
        return "dairy", c19
    forage = float(diet["forage_percent"]["value"])
    c19 = "nondairy_forage_gt75" if forage > 75 else "nondairy_mixed"
    return ("dairy" if animal["animal_type"] == "dairy" else "other_cattle"), c19


def ge_eq_10_16(e: dict, de: float) -> float:
    rem_part = (e["NE_m"] + e["NE_a"] + e["NE_l"] + e["NE_work"] + e["NE_p"]) / e["RE_m"]
    reg_part = e["NE_g"] / e["RE_g"] if e["RE_g"] else 0.0
    return (rem_part + reg_part) / (de / 100.0)


def vs_eq_10_24(ge: float, de: float, ash: float, ue: float) -> float:
    return (ge * (1 - de / 100.0) + ue * ge) * ((1 - ash / 100.0) / 18.45)


def run_version(version, spec, farm, reg, const):
    ent_m, man_m, soil_m = MODULES[version]
    pe, pm, ps = resolve(ent_m, reg), resolve(man_m, reg), resolve(ps_m := soil_m, reg)
    manure_cfg = spec["manure_variants"][farm["manure_id"]] if farm.get("manure_id") else {"systems": {}}
    zone = spec["meta"]["climate_zone"]
    res = {"enteric_CH4": 0.0, "manure_CH4": 0.0, "manure_N2O": 0.0, "soil_N2O": 0.0}
    n_avb = n_prp = 0.0
    notes = []
    for cid in farm.get("herds") or []:
        a = spec["animal_classes"][cid]
        head = float(a["head"]["value"])
        at = str(a["animal_type"])
        nex = nex_kg_yr(spec, a, const)
        if at in MONOGASTRIC:
            ent = ent_m.compute({"head": head, "animal_type": at}, pe)
            man_in = {"head": head, "animal_type": at, "region": "north_america",
                      "VS_kg_day": float(a["VS_kg_day"]["value"]),
                      "TAM_kg": animal_mass_kg(spec, a), "mcf_zone": zone,
                      "systems": dict(manure_cfg["systems"])}
        else:
            diet = spec["diets"][farm["diet_id"]]
            de, _tdn, _f = herd_de_tdn(spec, farm, a, diet)
            e = net_energy(spec, a, const, de)
            ge = ge_eq_10_16(e, de)
            ue = 0.02 if de >= const["ue_ipcc_de_threshold"] else 0.04
            vs = vs_eq_10_24(ge, de, const["ASH_percent"], ue)
            milk = float(a.get("milk_lb_cow_yr", {}).get("value", 0.0)) * float(spec["meta"]["lb_to_kg"])
            c06, c19 = ym_categories(a, farm, diet, milk)
            cat = c06 if version == "IPCC2006" else c19
            ent = ent_m.compute({"GE_MJ_day": ge, "head": head, "ym_category": cat,
                                 "animal_type": CATTLE_AT[at]}, pe)
            man_in = {"head": head, "animal_type": CATTLE_AT[at], "region": "north_america",
                      "VS_kg_day": vs, "TAM_kg": e["weight_kg"],
                      "mcf_zone": zone, "systems": dict(manure_cfg["systems"])}
        if "Nex_kg_yr_override" in a:
            man_in["Nex_kg_yr"] = nex
        if version == "IPCC2019":
            man_in["include_leach"] = True
            man_in["climate_zone_2019"] = CLIMATE_ZONE_2019
            man_in["storage_months"] = STORAGE_MONTHS
        pm_run = dict(pm)
        for sysname in man_in["systems"]:
            key = f"FracGasMS_{man_in['animal_type']}_{'liquid_slurry' if sysname.startswith('liquid') else sysname}"
            if version == "IPCC2006" and key in man_m.parameters and key not in pm_run:
                # No published cell (e.g. 2006 Table 10.22 has no other-cattle liquid row):
                # NaN keeps CH4 computable and makes the N2O result explicitly missing.
                pm_run[key] = math.nan
                notes.append(f"{cid}: {man_m.parameters[key].key} not published -> N2O NaN")
        try:
            man = man_m.compute(man_in, pm_run)
        except Exception as exc:  # missing published cell -> report, never invent
            notes.append(f"{cid}: manure not computable ({exc})")
            res["manure_CH4"] = res["manure_N2O"] = math.nan
            res["enteric_CH4"] += float(ent["CH4_total"])
            continue
        res["enteric_CH4"] += float(ent["CH4_total"])
        res["manure_CH4"] += float(man["CH4"])
        res["manure_N2O"] += float(man["N2O_total"])
        n_prp += float(man["N_PRP_kg"])
        # Both versions: Eq 10.34 N_MMS_Avb (2006 Table 10.23 FracLossMS; 2019 FracGasMS+FracLeachMS)
        n_avb += float(man["N_MMS_Avb_kg"])
        if version == "IPCC2006" and math.isnan(float(man["N_MMS_Avb_kg"])) and float(man["N_managed_kg"]) > 0:
            notes.append(f"{cid}: IPCC2006 Table 10.23 FracLossMS not published for this system -> F_ON NaN")
        if version == "IPCC2019":
            notes.append(f"{cid}: MCF {man['MCF_basis']}")
    fid = farm.get("field_id")
    if fid:
        f = spec["fields"][fid]
        crm = IPCC2019CropResidue()
        pcr = resolve(crm, reg)
        for ck in TABLE_11_1A_CROPS:
            for name, key in crop_coeff_param_keys(ck).items():
                pcr[f"{name}_{ck}"] = float(reg.get_value(key))
        f_cr = _yaml_number(f.get("F_CR"))
        for crop in _field_crops(f):
            f_cr += float(crm.compute(crop, pcr)["F_CR"])
        fn = {"F_SN": _yaml_number(f.get("F_SN")), "F_SOM": _yaml_number(f.get("F_SOM")),
              "F_ON": _yaml_number(f.get("F_ON_other_kg")), "F_CR": f_cr}
        link = bool(f.get("link_manure_n", True))
        soil = soil_m.compute({
            "F_SN": fn["F_SN"], "F_ON": fn["F_ON"] + (n_avb if link else 0.0), "F_CR": fn["F_CR"],
            "F_SOM": fn["F_SOM"],
            "F_PRP_CPP": n_prp + _yaml_number(f.get("F_PRP_extra_kg")),
            "climate": str(f.get("climate") or "wet")}, ps)
        res["soil_N2O"] = float(soil["N2O_total"])
    return res, notes


def main() -> None:
    spec = load_stylized_spec(SPEC)
    const = _const(spec)
    gwp = gwp_from_spec(spec)
    params_csv = latest_versioned(ROOT / "data", "ipcc_params", ".csv")
    reg = load_parameter_csv(params_csv, allow_unverified=False)
    gas = {"enteric_CH4": "CH4", "manure_CH4": "CH4", "manure_N2O": "N2O", "soil_N2O": "N2O"}
    rows = []
    for farm in spec["farms"]:
        r06, n06 = run_version("IPCC2006", spec, farm, reg, const)
        r19, n19 = run_version("IPCC2019", spec, farm, reg, const)
        for src in gas:
            a, b = r06[src], r19[src]
            g = gwp[gas[src]]
            rows.append({
                "farm_id": farm["id"], "source": src, "gas": gas[src],
                "ipcc2006_kg": round(a, 4), "ipcc2019_kg": round(b, 4),
                "ipcc2006_tCO2e": round(a * g / 1000, 4), "ipcc2019_tCO2e": round(b * g / 1000, 4),
                "diff_tCO2e_2019_minus_2006": round((b - a) * g / 1000, 4),
                "pct_change": round((b - a) / a * 100, 2) if a and not math.isnan(a) and not math.isnan(b) else "",
                "gwp_ar5": g, "params_file": params_csv.name, "spec_file": SPEC.name,
                "notes": "; ".join(sorted(set(n06 + n19))),
            })
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT_CSV} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
