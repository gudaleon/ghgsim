#!/usr/bin/env python3
"""VT/DE county run with Census crops (Eq 11.6) and Falcone hog/poultry N.

NASS county extract in the repo has cattle + crop acres/bushels only — no
poultry or swine inventory. This script does not invent head counts.

- Crops: NASS 2022 acres + bushels → IPCC 2019 Eq 11.6 F_CR (Table 11.1a).
- Poultry/swine: Falcone 2021 excreted N (Hogs_N_kg-2017, Poultry_N_kg-2017)
  as F_ON_other. That is excreted N, not N_MMS_Avb; storage losses are not
  invented.
- Cattle: existing VT/DE runner herds; leftover managed manure N is linked
  once as FAM (Eq 11.4).
- Other_N from Falcone is kept in F_ON_other so the trial F_ON is not dropped.

Baseline is the current Holos VT/DE county assembly (trial CSV soil, no FAM
link, IPCC EF1=0.01). Expanded runs use Eq 11.6 F_CR + Falcone organic N +
cattle FAM. source_correct also applies Rochette EFeco at P_PE=1.0 (published
humid clamp, not a VT weather observation).

Usage (from repository root):
    python3 scripts/holos_vt_de_poultry_crops_AN_v1.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ghgsim.modules.holos import HolosFieldN, HolosSoilN2O  # noqa: E402
from ghgsim.modules.ipcc2019.crop_residue import IPCC2019CropResidue, NASS_SHORT_DESC  # noqa: E402
from ghgsim.report.emissions_sankey import compute_county_flows  # noqa: E402
from ghgsim.report.fork_diagram import latest_versioned  # noqa: E402

COMMAND = "python3 scripts/holos_vt_de_poultry_crops_AN_v1.py"
DETAIL_CSV = ROOT / "data" / "holos_vt_de_poultry_crops_AN_v1.csv"
SUMMARY_CSV = ROOT / "data" / "holos_vt_de_poultry_crops_summary_AN_v1.csv"
META_JSON = ROOT / "data" / "holos_vt_de_poultry_crops_AN_v1.meta.json"
NASS_CROPS = ROOT / "legacy" / "livingghg_AN_v3" / "data_nass" / "nass_census2022_crops_county_AN_v3.csv.gz"
NASS_CATTLE = ROOT / "legacy" / "livingghg_AN_v3" / "data_nass" / "nass_census2022_county_AN_v1.csv.gz"
FALCONE = ROOT / "legacy" / "livingghg_AN_v3" / "data_us" / "usgs_falcone2021_county_N_2017_AN_v3.csv.gz"
GWP_N2O = 265.0


def _fips(frame: pd.DataFrame) -> pd.Series:
    return (
        frame.STATE_FIPS_CODE.astype(str).str.zfill(2)
        + frame.COUNTY_CODE.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(3)
    )


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "").str.strip(), errors="coerce")


def census_poultry_swine_gap() -> dict[str, object]:
    """Confirm the repo NASS cattle extract has no poultry/swine inventory."""
    cattle = pd.read_csv(NASS_CATTLE, dtype=str)
    desc = cattle.SHORT_DESC.dropna().unique().tolist()
    poultry_swine = [
        item
        for item in desc
        if any(token in item.upper() for token in ("BROILER", "LAYER", "TURKEY", "HOG", "PIG", "CHICKEN"))
    ]
    return {
        "nass_cattle_file": NASS_CATTLE.name,
        "short_desc": sorted(desc),
        "poultry_or_swine_inventory_rows": poultry_swine,
        "census_head_invented": False,
        "note": (
            "nass_census2022_county_AN_v1.csv.gz is cattle inventory only. "
            "Poultry and swine enter as Falcone 2017 excreted N, not Census heads."
        ),
    }


def county_f_cr(params: dict[str, float]) -> pd.DataFrame:
    crops = pd.read_csv(NASS_CROPS, dtype=str)
    crops = crops[crops.STATE_ALPHA.isin(["VT", "DE"])].copy()
    crops["v"] = _numeric(crops.VALUE)
    crops["fips"] = _fips(crops)
    residue = IPCC2019CropResidue()
    acre_to_ha = float(params["ACRE_TO_HA"])
    kg_per_bu = {
        "maize": float(params["kg_per_bu_maize"]),
        "soybeans": float(params["kg_per_bu_soybeans"]),
        "wheat": float(params["kg_per_bu_wheat"]),
    }
    out: dict[str, float] = {}
    flags: dict[str, str] = {}
    for crop, short in (("maize", NASS_SHORT_DESC["maize"]), ("soybeans", NASS_SHORT_DESC["soybeans"]), ("wheat", NASS_SHORT_DESC["wheat"])):
        acres = crops[crops.SHORT_DESC == f"{short} - ACRES HARVESTED"].set_index("fips").v
        bushels = crops[crops.SHORT_DESC == f"{short} - PRODUCTION, MEASURED IN BU"].set_index("fips").v
        for fips in acres.index.union(bushels.index):
            area_ac = acres.get(fips)
            qty = bushels.get(fips)
            if pd.notna(area_ac) and pd.notna(qty) and float(area_ac) > 0:
                ha = float(area_ac) * acre_to_ha
                yield_fresh = float(qty) * kg_per_bu[crop] / ha
                piece = residue.compute(
                    {"crop": crop, "area_ha": ha, "yield_fresh_kg_ha": yield_fresh},
                    params,
                )
                out[fips] = out.get(fips, 0.0) + float(piece["F_CR"])
            else:
                flags[fips] = flags.get(fips, "") + f"{crop}:withheld_or_missing;"
                out.setdefault(fips, 0.0)
    return pd.DataFrame(
        {"fips": list(out), "F_CR_kgN": list(out.values()), "F_CR_flag": [flags.get(f, "") for f in out]}
    )


def falcone_n() -> pd.DataFrame:
    fa = pd.read_csv(FALCONE, dtype={"STCOFIPS": str})
    fa["fips"] = fa.STCOFIPS.str.zfill(5)
    return fa.set_index("fips")[
        ["farmfertN-kg-2017", "Hogs_N_kg-2017", "Poultry_N_kg-2017", "Other_N_kg-2017"]
    ]


def _soil_n2o(farm: dict, params: dict[str, float], forks: dict[str, str], *, p_pe: float | None) -> dict[str, float]:
    soil = HolosSoilN2O()
    inputs = {
        "F_SN": float(farm["soil"]["F_SN"] or 0.0),
        "F_ON": float(farm["soil"]["F_ON"] or 0.0),
        "F_CR": float(farm["soil"]["F_CR"] or 0.0),
        "F_SOM": float(farm["soil"].get("F_SOM") or 0.0),
        "F_PRP_CPP": float(farm["soil"].get("F_PRP_CPP") or 0.0),
        "climate": farm["soil"]["climate"],
        "forks": forks,
    }
    if p_pe is not None:
        inputs["P_PE"] = p_pe
    out = soil.compute(inputs, params)
    return {key: float(out[key]) for key in ("N2O_total", "N2O_direct", "EF1_used")}


def main() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from holos_vt_de_runner_AN_v1 import (  # noqa: PLC0415
        holos_compute_params,
        load_epa_assumptions,
        load_registries,
        load_vt_de_counties,
        v3_farm_from_row,
    )
    gap = census_poultry_swine_gap()
    regs = load_registries()
    params = holos_compute_params(regs, mcf_set="ipcc15C")
    epa = load_epa_assumptions()
    counties = load_vt_de_counties()
    residue = county_f_cr(params)
    falcone = falcone_n()
    linker = HolosFieldN()
    rows: list[dict] = []

    for _, row in counties.iterrows():
        fips = str(row["fips"]).zfill(5)
        name = str(row["COUNTY_NAME"])
        baseline = compute_county_flows(ROOT, name, {}, run="baseline")
        farm = v3_farm_from_row(row, epa)
        n_mms = sum(group.n_mms_avb_kg for group in baseline.groups)
        n_prp = sum(group.n_prp_kg for group in baseline.groups)

        fa = falcone.reindex([fips])
        hogs = float(fa["Hogs_N_kg-2017"].iloc[0] or 0.0) if fips in falcone.index else 0.0
        poultry = float(fa["Poultry_N_kg-2017"].iloc[0] or 0.0) if fips in falcone.index else 0.0
        other = float(fa["Other_N_kg-2017"].iloc[0] or 0.0) if fips in falcone.index else 0.0
        fert = float(fa["farmfertN-kg-2017"].iloc[0] or 0.0) if fips in falcone.index else 0.0
        cr_row = residue.set_index("fips").reindex([fips])
        f_cr = float(cr_row["F_CR_kgN"].iloc[0] or 0.0) if fips in set(residue.fips) else 0.0
        f_cr_flag = "" if cr_row["F_CR_flag"].isna().all() else str(cr_row["F_CR_flag"].iloc[0] or "")
        trial_f_cr = 0.0 if pd.isna(row.get("F_CR")) else float(row["F_CR"])
        trial_f_on = 0.0 if pd.isna(row.get("F_ON")) else float(row["F_ON"])

        field = linker.compute(
            {
                "N_MMS_Avb_kg": n_mms,
                "N_PRP_kg": n_prp,
                "F_SN": fert if fert == fert else 0.0,
                "F_ON_other_kg": hogs + poultry + other,
                "F_CR": f_cr,
                "link_manure_n": True,
            },
            params,
        )
        expanded_farm = {
            "soil": {
                "F_SN": field["F_SN"],
                "F_ON": field["F_ON"],
                "F_CR": field["F_CR"],
                "F_SOM": 0.0,
                "F_PRP_CPP": field["F_PRP_CPP"],
                "climate": farm["soil"]["climate"],
            }
        }
        ipcc_ef1 = _soil_n2o(expanded_farm, params, {"HOLOS.N2O.ef1": "holos_as_coded"}, p_pe=1.0)
        rochette = _soil_n2o(expanded_farm, params, {}, p_pe=1.0)

        animal_n2o = baseline.n2o_direct_kg + baseline.n2o_indirect_kg
        animal_ch4 = baseline.ch4_kg
        animal_co2e = animal_ch4 * 28.0 + animal_n2o * GWP_N2O
        base_soil = baseline.soil_n2o_kg
        exp_ipcc_soil = ipcc_ef1["N2O_total"]
        exp_roc_soil = rochette["N2O_total"]
        base_co2e_t = baseline.co2e_t
        exp_ipcc_co2e_t = (animal_ch4 * 28.0 + (animal_n2o + exp_ipcc_soil) * GWP_N2O) / 1000.0
        exp_roc_co2e_t = (animal_ch4 * 28.0 + (animal_n2o + exp_roc_soil) * GWP_N2O) / 1000.0

        rows.append(
            {
                "command": COMMAND,
                "fips": fips,
                "state": str(row["STATE_ALPHA"]),
                "county": name,
                "milk_cows": row.get("milk_cows"),
                "beef_cows": row.get("beef_cows"),
                "census_poultry_swine_heads": "",
                "census_gap": "no poultry/swine inventory in nass_census2022_county_AN_v1",
                "Falcone_Hogs_N_kg": hogs,
                "Falcone_Poultry_N_kg": poultry,
                "Falcone_Other_N_kg": other,
                "F_SN_kg": field["F_SN"],
                "F_ON_trial_kg": trial_f_on,
                "F_ON_expanded_kg": field["F_ON"],
                "F_AM_cattle_kg": field["F_AM_kg"],
                "F_CR_trial_kg": trial_f_cr,
                "F_CR_eq116_kg": f_cr,
                "F_CR_flag": f_cr_flag,
                "baseline_soil_N2O_kg": base_soil,
                "expanded_ipcc_EF1_soil_N2O_kg": exp_ipcc_soil,
                "expanded_rochette_soil_N2O_kg": exp_roc_soil,
                "baseline_CO2e_t": base_co2e_t,
                "expanded_ipcc_EF1_CO2e_t": exp_ipcc_co2e_t,
                "expanded_rochette_CO2e_t": exp_roc_co2e_t,
                "dCO2e_t_ipcc_EF1_minus_baseline": exp_ipcc_co2e_t - base_co2e_t,
                "dCO2e_t_rochette_minus_baseline": exp_roc_co2e_t - base_co2e_t,
                "dCO2e_t_rochette_minus_ipcc_EF1": exp_roc_co2e_t - exp_ipcc_co2e_t,
                "EF1_ipcc": ipcc_ef1["EF1_used"],
                "EF1_rochette_P_PE_1": rochette["EF1_used"],
                "evidence": "MEASURED",
            }
        )

    detail = pd.DataFrame(rows)
    detail.to_csv(DETAIL_CSV, index=False)
    summary = pd.DataFrame(
        [
            {
                "scope": "VT+DE",
                "n_counties": int(detail["fips"].nunique()),
                "baseline_CO2e_t": float(detail["baseline_CO2e_t"].sum()),
                "expanded_ipcc_EF1_CO2e_t": float(detail["expanded_ipcc_EF1_CO2e_t"].sum()),
                "expanded_rochette_CO2e_t": float(detail["expanded_rochette_CO2e_t"].sum()),
                "dCO2e_t_ipcc_EF1_minus_baseline": float(detail["dCO2e_t_ipcc_EF1_minus_baseline"].sum()),
                "dCO2e_t_rochette_minus_baseline": float(detail["dCO2e_t_rochette_minus_baseline"].sum()),
                "dCO2e_t_rochette_minus_ipcc_EF1": float(detail["dCO2e_t_rochette_minus_ipcc_EF1"].sum()),
                "F_AM_cattle_kg": float(detail["F_AM_cattle_kg"].sum()),
                "F_CR_eq116_kg": float(detail["F_CR_eq116_kg"].sum()),
                "F_CR_trial_kg": float(detail["F_CR_trial_kg"].sum()),
                "Falcone_Hogs_N_kg": float(detail["Falcone_Hogs_N_kg"].sum()),
                "Falcone_Poultry_N_kg": float(detail["Falcone_Poultry_N_kg"].sum()),
            }
        ]
    )
    summary.to_csv(SUMMARY_CSV, index=False)
    META_JSON.write_text(
        json.dumps(
            {
                "command": COMMAND,
                "date": date.today().isoformat(),
                "census_gap": gap,
                "P_PE": {
                    "value": 1.0,
                    "note": "Rochette 2008 humid clamp (EFeco=0.017). Not a VT/DE weather observation.",
                },
                "sources": {
                    "nass_crops": NASS_CROPS.name,
                    "nass_cattle": NASS_CATTLE.name,
                    "falcone": FALCONE.name,
                    "ipcc_params": latest_versioned(ROOT / "data", "ipcc_params", ".csv").name,
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(f"wrote {DETAIL_CSV}")
    print(f"wrote {SUMMARY_CSV}")
    print(summary.to_string(index=False))
    print("census_gap", gap["note"])


if __name__ == "__main__":
    main()
