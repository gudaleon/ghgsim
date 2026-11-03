"""Build per-state cattle per-head inputs (county_assumptions_AN_v3.json) from data_us/epa_cattle_state_AN_v3.csv.
Every value is either read from EPA (2025) Annex 3.11 (VERIFIED) or a labelled mapping ASSUMPTION."""
import json, pathlib
import pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
LB = 0.45359237
WMS_MAP = {"pasture": "pasture", "daily_spread": "daily_spread", "dry_lot": "dry_lot", "solid_storage": "solid_storage",
           "liquid_slurry": "liquid_nocrust", "anaerobic_lagoon": "lagoon", "deep_pit": "liquid_nocrust"}
ASSUMPTIONS = {
    "liquid_slurry->liquid_nocrust": "ASSUMED: EPA 'liquid/slurry' mapped to IPCC liquid slurry without natural crust",
    "deep_pit->liquid_nocrust": "ASSUMED: EPA 'deep pit' mapped to IPCC liquid slurry (6-month, 2019) because pit storage is not a livingghg system",
    "anaerobic_digester": "ASSUMED: EPA anaerobic-digester share removed and remaining shares renormalised (digester CH4 not modelled)",
    "mcf_zone": "ASSUMED: one MCF zone for all states (IPCC2006 15C; IPCC2019 cool_temperate_moist); state climate not yet mapped",
    "ym_category": "IPCC table category used only if fork F013 = ipcc_default",
    "scope": "Mature cows only (milk cows; beef cows = EPA 'beef NOF cows'). Heifers, steers, calves, bulls, feedlot cattle NOT included.",
}

def build():
    e = pd.read_csv(ROOT / "data_us" / "epa_cattle_state_AN_v3.csv")
    out = {"_label": "Per-state cattle inputs from EPA (2025) Inventory 1990-2023 (EPA 430-R-25-003) Annex 3.11, 2022 values. Replaces v1 placeholders.",
           "_assumptions": ASSUMPTIONS, "climate": "wet", "states": {}}
    for r in e.to_dict("records"):
        w = {WMS_MAP[k]: 0.0 for k in WMS_MAP}
        for k, s in WMS_MAP.items():
            w[s] += r[f"dairy_wms_pct_{k}"]
        tot = sum(w.values())
        w = {k: v / tot for k, v in w.items() if v > 0}
        out["states"][r["state"]] = {
            "dairy": {"GE_MJ_day": r["dairy_GE_MJ_day_derived"], "Ym_pct": r["dairy_Ym_pct"],
                      "ym_category": {"IPCC2006": "dairy", "IPCC2019": "dairy_medium"},
                      "epa_EF_kgCH4_head_yr": r["dairy_EF_kgCH4_head_yr_2022"], "DE_pct": r["dairy_DE_pct"],
                      "milk_lb_cow_yr": r["dairy_milk_lb_cow_yr_2022"],
                      "manure": {"animal": "dairy", "region": "north_america", "TAM_kg": round(r["dairy_cow_mass_lb_2022"] * LB, 1),
                                 "VS_kg_day": round(r["dairy_VS_kg_yr"] / 365.0, 4), "Nex_kg_yr": r["dairy_Nex_kg_yr"],
                                 "systems": w, "digester_share_removed_pct": r["dairy_wms_pct_anaerobic_digester"],
                                 "mcf_zone": {"IPCC2006": "15C", "IPCC2019": "cool_temperate_moist"}}},
            "beef": {"GE_MJ_day": r["beef_GE_MJ_day_derived"], "Ym_pct": r["beef_cow_Ym_pct"],
                     "ym_category": {"IPCC2006": "other_cattle", "IPCC2019": "nondairy_forage_gt75"},
                     "epa_EF_kgCH4_head_yr": r["beef_cow_EF_kgCH4_head_yr_2022"], "DE_pct": r["beef_cow_DE_pct"],
                     "manure": {"animal": "other_cattle", "region": "north_america", "TAM_kg": round(r["beef_cow_mass_lb_2022"] * LB, 1),
                                "VS_kg_day": round(r["beef_cow_VS_kg_yr"] / 365.0, 4), "Nex_kg_yr": r["beef_cow_Nex_kg_yr"],
                                "systems": {"pasture": r["beef_nof_wms_pct_pasture"] / 100.0},
                                "mcf_zone": {"IPCC2006": "15C", "IPCC2019": "cool_temperate_moist"}}},
            "provenance": {"source": r["source"], "tables": r["tables"], "status": r["status"],
                           "dairy_region": r["dairy_region"], "foraging_region": r["foraging_region"]}}
    p = ROOT / "scripts" / "county_assumptions_AN_v3.json"
    p.write_text(json.dumps(out, indent=1))
    return p

if __name__ == "__main__":
    print(build())
