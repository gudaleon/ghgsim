#!/usr/bin/env python3
"""Build data/ipcc_params_AN_v11.csv = every row of v10 unchanged + new rows for the Tier 1 extras.

New rows (all opened in the source PDF on 2026-11-22; pages are the printed page numbers):
  * Forage / hay residue factors: IPCC 2006 Vol4 Ch11 Table 11.2 (pp. 11.17-11.18) and
    IPCC 2019 Refinement Vol4 Ch11 Table 11.1a (New) p. 11.18 + Table 11.2 (Updated) p. 11.19.
  * Soil C stock-change factors for F_SOM: 2006 Vol4 Ch5 Table 5.5 (pp. 5.17-5.18), 2019 Ch5 Table 5.5 (Updated)
    (pp. 5.27-5.28); SOCref 2006 Vol4 Ch2 Table 2.3 (p. 2.31), 2019 Ch2 Table 2.3 (Updated) (p. 2.34);
    D (Eq 2.25, 2006 Ch2 p. 2.30); C:N ratio R (Eq 11.8, 2006 Ch11 p. 11.16; 2019 Ch11 p. 11.20).
  * Crop N concentration in the harvested part: USDA NRCS Agricultural Waste Management Field Handbook,
    Part 651, Chapter 6, Table 6-6 (210-vi-AWMFH, rev. 1, July 1996), pp. 6-19 to 6-22.
  * Soybean share of N from biological fixation: Salvagiotti et al. 2008, Field Crops Res. 108:1-13, abstract.
Refuses to overwrite.
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC, OUT = ROOT / "data" / "ipcc_params_AN_v10.csv", ROOT / "data" / "ipcc_params_AN_v11.csv"
WHO, DAY = "AN agent; PDF text opened 2026-11-22", "2026-11-22"
G06_11, G19_11 = "2006 IPCC GL Vol4 Ch11", "2019 Refinement Vol4 Ch11"
G06_5, G19_5 = "2006 IPCC GL Vol4 Ch5", "2019 Refinement Vol4 Ch5"
G06_2, G19_2 = "2006 IPCC GL Vol4 Ch2", "2019 Refinement Vol4 Ch2"
NRCS = "USDA NRCS AWMFH Part 651 Ch6 (210-vi-AWMFH rev.1 July 1996)"
SALV = "https://doi.org/10.1016/j.fcr.2008.03.001"

rows = []


def add(key, value, units, src, table, eq, page, notes="", status="VERIFIED", dist="fixed", lo="", hi=""):
    rows.append(dict(key=key, value=value, units=units, dist=dist, dist_lower=lo, dist_upper=hi, source_doi_or_url=src,
                     table=table, equation=eq, page=page, region="all", status=status, verified_by=WHO,
                     verified_date=DAY, notes=notes))


# ---- 2006 Table 11.2 forage rows: DRY, slope, intercept, N_AG, R_BG_BIO, N_BG
F06 = {"alfalfa": ((0.90, 0.29, 0, 0.027, 0.40, 0.019), "11.18",
                   "footnote k: AGDM is litter/harvest losses only, excludes stubble (0.165*yield); n: R_BG-BIO is root turnover in perennial systems"),
       "nonlegume_hay": ((0.90, 0.18, 0, 0.015, 0.54, 0.012), "11.18", "footnote n: R_BG-BIO is root turnover in perennial systems"),
       "n_fixing_forages": ((0.90, 0.3, 0, 0.027, 0.40, 0.022), "11.17", ""),
       "non_n_fixing_forages": ((0.90, 0.3, 0, 0.015, 0.54, 0.012), "11.17", ""),
       "perennial_grasses": ((0.90, 0.3, 0, 0.015, 0.80, 0.012), "11.17", ""),
       "grass_clover": ((0.90, 0.3, 0, 0.025, 0.80, 0.016), "11.17", "grass dominates 2:1 over legumes")}
for crop, (vals, page, note) in F06.items():
    for f, v, u in zip(("DRY", "slope", "intercept", "N_AG", "R_BG_BIO", "N_BG"), vals,
                       ("", "", "Mg d.m./ha", "kg N/kg d.m.", "", "kg N/kg d.m."), strict=True):
        add(f"IPCC2006.RES.{crop}.{f}", v, u, G06_11, "Table 11.2", "Eq 11.7A", page, note)

# ---- 2019 Table 11.1a (New) p. 11.18: N_AG, N_BG, R_AG, RS, DRY ; Table 11.2 (Updated) p. 11.19 slope/intercept
F19 = {"alfalfa": (0.027, 0.019, None, 0.40, 0.90), "nonlegume_hay": (0.015, 0.012, None, 0.54, 0.90),
       "n_fixing_forages": (0.027, 0.022, 0.3, 0.40, 0.90), "non_n_fixing_forages": (0.015, 0.012, 0.3, 0.54, 0.90),
       "perennial_grasses": (0.015, 0.012, 0.3, 0.80, 0.90), "grass_clover": (0.025, 0.016, 0.3, 0.80, 0.90)}
for crop, vals in F19.items():
    for f, v in zip(("N_AG", "N_BG", "R_AG", "RS", "DRY"), vals, strict=True):
        if v is None:
            continue  # footnote e: no R_AG estimate; AGDM from Table 11.2 (Updated) instead
        note = "RS footnote g: root turnover in perennial systems" if (f == "RS" and crop in ("alfalfa", "nonlegume_hay")) else ""
        add(f"IPCC2019.RES.{crop}.{f}", v, "", G19_11, "Table 11.1a (New)", "Eq 11.6 (Updated)", "11.18", note)
for crop, slope in (("alfalfa", 0.29), ("nonlegume_hay", 0.18)):
    add(f"IPCC2019.RES.{crop}.slope", slope, "", G19_11, "Table 11.2 (Updated)", "Eq 11.6 (Updated) AGDM alternative", "11.19",
        "Table 11.1a gives no R_AG ('-', footnote e); Eq 11.6 text p. 11.17 allows AGDM from Table 11.2" +
        ("; footnote j: litter/harvest losses, excludes stubble" if crop == "alfalfa" else ""))
    add(f"IPCC2019.RES.{crop}.intercept", 0, "kg d.m./ha", G19_11, "Table 11.2 (Updated)", "Eq 11.6 (Updated) AGDM alternative", "11.19")

# ---- F_SOM: Eq 2.25 D, Eq 11.8 R
add("IPCC2006.SOC.D_years", 20, "yr", G06_2, "Eq 2.25 text", "Equation 2.25", "2.30", "default time dependence of stock change factors")
add("IPCC2006.FSOM.R_cropland_mgmt", 10, "C:N", G06_11, "Eq 11.8 text", "Equation 11.8", "11.16",
    "management change on Cropland Remaining Cropland; range 8-15", dist="uniform", lo=8, hi=15)
add("IPCC2006.FSOM.R_luc_to_cropland", 15, "C:N", G06_11, "Eq 11.8 text", "Equation 11.8", "11.16",
    "land-use change from Forest Land or Grassland to Cropland; range 10-30", dist="uniform", lo=10, hi=30)
add("IPCC2019.FSOM.R_cropland_mgmt", 10, "C:N", G19_11, "Eq 11.8 text", "Equation 11.8", "11.20", "range 8-15", dist="uniform", lo=8, hi=15)
add("IPCC2019.FSOM.R_luc_to_cropland", 15, "C:N", G19_11, "Eq 11.8 text", "Equation 11.8", "11.20", "range 10-30", dist="uniform", lo=10, hi=30)
# SOCref (t C/ha, 0-30 cm)
for k, v in (("cool_temperate_moist|HAC", 95), ("warm_temperate_moist|HAC", 88), ("cool_temperate_dry|HAC", 50),
             ("warm_temperate_dry|HAC", 38), ("cool_temperate_moist|WET", 87), ("warm_temperate_moist|WET", 88),
             ("cool_temperate_dry|WET", 87), ("warm_temperate_dry|WET", 88)):
    add(f"IPCC2006.SOCref.{k}", v, "t C/ha 0-30 cm", G06_2, "Table 2.3", "Equation 2.25", "2.31",
        "2006 label 'Cold temperate' = cool temperate zone; WET = Wetland (aquic) soils; dry-zone Wetland value spans both dry rows in the PDF layout")
for k, v in (("cool_temperate_moist|HAC", 81), ("warm_temperate_moist|HAC", 64), ("cool_temperate_dry|HAC", 43),
             ("warm_temperate_dry|HAC", 24), ("cool_temperate_moist|WET", 128), ("warm_temperate_moist|WET", 135),
             ("cool_temperate_dry|WET", 87), ("warm_temperate_dry|WET", 74)):
    add(f"IPCC2019.SOCref.{k}", v, "t C/ha 0-30 cm", G19_2, "Table 2.3 (Updated)", "Equation 2.25", "2.34", "C1/W1/C2/W2 zones")
# FLU long-term cultivated, FMG tillage, FI medium
for z, v in (("cool_temperate_moist", 0.69), ("warm_temperate_moist", 0.69), ("cool_temperate_dry", 0.80), ("warm_temperate_dry", 0.80)):
    add(f"IPCC2006.FLU.long_term_cultivated|{z}", v, "", G06_5, "Table 5.5", "Equation 2.25", "5.17", "temperate/boreal value")
for z, v in (("cool_temperate_moist", 0.70), ("warm_temperate_moist", 0.69), ("cool_temperate_dry", 0.77), ("warm_temperate_dry", 0.76)):
    add(f"IPCC2019.FLU.long_term_cultivated|{z}", v, "", G19_5, "Table 5.5 (Updated)", "Equation 2.25", "5.27")
for lvl, vals in (("full", (1.00, 1.00, 1.00, 1.00)), ("reduced", (1.08, 1.08, 1.02, 1.02)), ("no_till", (1.15, 1.15, 1.10, 1.10))):
    for z, v in zip(("cool_temperate_moist", "warm_temperate_moist", "cool_temperate_dry", "warm_temperate_dry"), vals, strict=True):
        add(f"IPCC2006.FMG.{lvl}|{z}", v, "", G06_5, "Table 5.5", "Equation 2.25", "5.17", "temperate/boreal value")
for lvl, vals in (("full", (1.00, 1.00, 1.00, 1.00)), ("reduced", (1.04, 1.05, 0.98, 0.99)), ("no_till", (1.09, 1.10, 1.03, 1.04))):
    for z, v in zip(("cool_temperate_moist", "warm_temperate_moist", "cool_temperate_dry", "warm_temperate_dry"), vals, strict=True):
        add(f"IPCC2019.FMG.{lvl}|{z}", v, "", G19_5, "Table 5.5 (Updated)", "Equation 2.25", "5.27")
add("IPCC2006.FI.medium", 1.00, "", G06_5, "Table 5.5 (continued)", "Equation 2.25", "5.18")
add("IPCC2019.FI.medium", 1.00, "", G19_5, "Table 5.5 (Updated) (continued)", "Equation 2.25", "5.28")

# ---- NRCS Table 6-6: N % of harvested material (lb/bu is the table's 'Dry wt. lb/bu' column)
NR = (("corn_grain", 1.61, "dry", "6-19", "Corn 120 bu; lb/bu 56"), ("soybeans", 6.25, "dry", "6-19", "Soybeans 35 bu; lb/bu 60"),
      ("wheat", 2.08, "dry", "6-19", "Wheat 40 bu; lb/bu 60"), ("oats", 1.95, "dry", "6-19", "Oats 80 bu; lb/bu 32"),
      ("barley", 1.82, "dry", "6-19", "Barley 50 bu; lb/bu 48"), ("rye", 2.08, "dry", "6-19", "Rye 30 bu; lb/bu 56"),
      ("sorghum_grain", 1.67, "dry", "6-19", "Sorghum 60 bu; lb/bu 56"), ("rice", 1.39, "dry", "6-19", "Rice 5,500 lb; lb/bu 45"),
      ("peanuts", 3.60, "dry", "6-19", "Peanuts 2,800 lb"),
      ("alfalfa_hay", 2.25, "dry", "6-20", "Forage crops: Alfalfa 4 tons"),
      ("clover_grass_hay", 1.52, "dry", "6-20", "Forage crops: Clover-grass 6 tons"),
      ("timothy_hay", 1.20, "dry", "6-20", "Forage crops: Timothy 2.5 tons (low bracket for non-alfalfa hay)"),
      ("tall_fescue_hay", 1.97, "dry", "6-20", "Forage crops: Tall fescue 3.5 tons (high bracket for non-alfalfa hay)"),
      ("alfalfa_haylage", 2.79, "dry", "6-21", "Silage crops: Alfalfa haylage (50% dm)"),
      ("corn_silage", 1.10, "dry", "6-21", "Silage crops: Corn silage (35% dm)"),
      ("potatoes", 0.33, "fresh", "6-22", "Vegetable crops: Potatoes 14.5 tons"),
      ("beans_dry", 3.13, "fresh", "6-22", "Vegetable crops: Beans, dry 0.5 ton"))
for crop, v, basis, page, note in NR:
    add(f"NRCS.CROPN_pct.{crop}", v, f"% N of {basis} harvested material", NRCS, "Table 6-6", "", page, note)
add("NRCS.DM_frac.corn_silage", 0.35, "fraction", NRCS, "Table 6-6", "", "6-21", "row label 'Corn silage (35% dm)'; typical, not Ohio-specific")
add("NRCS.DM_frac.alfalfa_haylage", 0.50, "fraction", NRCS, "Table 6-6", "", "6-21", "row label 'Alfalfa haylage (50% dm)'")
add("SALV2008.soy_Ndfa", 0.55, "fraction of soybean N demand from BNF", SALV, "abstract", "", "1",
    "abstract: 'On an average, 50-60% of soybean N demand was met by biological N2 fixation'; 0.55 = midpoint",
    dist="uniform", lo=0.50, hi=0.60)

if __name__ == "__main__":
    if OUT.exists():
        sys.exit(f"refusing to overwrite {OUT}")
    base = list(csv.DictReader(open(SRC, encoding="utf-8")))
    have = {r["key"] for r in base}
    dup = [r["key"] for r in rows if r["key"] in have]
    if dup:
        sys.exit(f"keys already in v10: {dup}")
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(base[0].keys()))
        w.writeheader()
        w.writerows(base)
        w.writerows(rows)
    print(f"wrote {OUT} ({len(base)} v10 rows + {len(rows)} new)")
