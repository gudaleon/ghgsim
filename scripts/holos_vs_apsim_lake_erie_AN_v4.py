"""Holos CLI vs APSIM, Lake Erie direct fertiliser N2O EF table (AN_v4). Consistency check, not validation.

Holos values are transcribed from the Holos CLI run outputs at the commits listed in the `holos_source` column
(holos_lakeerie_ef_summary_AN_v2.csv, holos_berrien_sens_ef_summary_AN_v1.csv, holos_hoyt_sens_ef_summary_AN_v1.csv).
APSIM values are read from this repo's results files.
"""
import csv
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1] / "results"
hv = {(r["mode"], r["site"], r["case"]): r for r in csv.DictReader(open(R / "holos_vs_apsim_lake_erie_AN_v3.csv"))}
bs = json.load(open(R / "apsim_brookston_soilwater_summary_AN_v1.json"))
H = {  # site: (texture class used by Holos, EF direct %, EF direct+indirect %, mean May-Oct P/PE, source)
    "maumee_hoytville": ("Fine", 3.008, 3.352, 0.775, "2405da8 sens_hoyt_AN_v1/holos_hoyt_sens_ef_summary_AN_v1.csv case base"),
    "essex_berrien": ("Coarse", 0.370, 0.718, 0.684, "ec6d67a sens_AN_v1/holos_berrien_sens_ef_summary_AN_v1.csv case base"),
    "essex_parkhill_loam": ("Medium", 0.370, 0.672, 0.684, "75352e0 essex_loam_AN_v2/holos_lakeerie_ef_summary_AN_v2.csv"),
    "essex_brookston": ("Fine", 1.925, 2.227, 0.684, "75352e0 essex_loam_AN_v2/holos_lakeerie_ef_summary_AN_v2.csv"),
}
rows = []
for site, (tx, ef, efi, ppe, src) in H.items():
    ap = [r for k, r in hv.items() if k[1] == site]
    base = {"site": site, "holos_texture_class": tx, "holos_EF_direct_pct": ef, "holos_EF_direct_plus_indirect_pct": efi,
            "holos_mean_P_over_PE": ppe, "holos_drainage_term": "none", "holos_source": src}
    if site == "essex_brookston":
        rows.append(base | {"apsim_water_model": "SoilWater (cascade)", "apsim_mode": "eo n/a", "apsim_case": "undrained",
                            "apsim_EF_pct": bs["EF_pct"], "apsim_EF_maize_year_only_pct": bs["EF_maize_year_only_pct"],
                            "apsim_soybean_year_share": bs["soy_share"], "apsim_source": "apsim_brookston_soilwater_summary_AN_v1.json"})
    elif not ap:
        rows.append(base | {"apsim_water_model": "not run", "apsim_mode": "", "apsim_case": "", "apsim_EF_pct": "",
                            "apsim_EF_maize_year_only_pct": "", "apsim_soybean_year_share": "", "apsim_source": ""})
    for r in ap:
        rows.append(base | {"apsim_water_model": "SWIM3", "apsim_mode": r["mode"], "apsim_case": r["case"], "apsim_EF_pct": r["apsim_EF_pct"],
                            "apsim_EF_maize_year_only_pct": r["apsim_EF_maize_year_only_pct"],
                            "apsim_soybean_year_share": r["soybean_year_share_of_extra_N2O"], "apsim_source": "holos_vs_apsim_lake_erie_AN_v3.csv"})
with open(R / "holos_vs_apsim_lake_erie_AN_v4.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
for s in H:
    v = [float(r["apsim_EF_pct"]) for r in rows if r["site"] == s and r["apsim_EF_pct"] != ""]
    print(s, H[s][1], (min(v), max(v)) if v else None)