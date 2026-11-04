"""Build data/ipcc_params_AN_v10.csv = v9 + new rows (AN_v10). Refuses to overwrite.

New rows were read from the IPCC PDFs (page images and text checked 2026-11-03):
  2019 Refinement Vol4 Ch10: Table 10.13A (p10.56) VS rates, Table 10A.5 (p10.117) live weights,
    Table 10.10 Updated (p10.38) enteric, Table 10.14 Updated (pp10.61-10.62) manure CH4 EF per kg VS,
    Table 10.19 Updated (p10.83) Nrate.
  2006 GL Vol4 Ch10: Table 10.10 (p10.28) enteric, Table 10.15 (p10.40) manure CH4 EF per head,
    Table 10.19 (p10.59) Nrate, Table 10A-9 (p10.82) mass.
  2006 GL Vol4 Ch11: Table 11.1 (p11.11) EF1FR, Table 11.2 (pp11.17-11.18) crop residue factors.
  2019 Refinement Vol4 Ch11: Table 11.1 Updated (p11.13) EF1FR, Table 11.1a New (p11.18) crop residues.
Rows whose table cell is NA / '-' are filled from the named generic row and given status SUBSTITUTE.
"""
import csv, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
V9, V10 = ROOT / "data/ipcc_params_AN_v9.csv", ROOT / "data/ipcc_params_AN_v10.csv"
D = "2026-11-03"; WHO = "AN agent; IPCC PDF page image + text read 2026-11-03"
G06_10, G19_10 = "2006 IPCC GL Vol4 Ch10", "2019 Refinement Vol4 Ch10"
G06_11, G19_11 = "2006 IPCC GL Vol4 Ch11", "2019 Refinement Vol4 Ch11"
rows = []
def add(key, val, units, src, table, page, notes="", status="VERIFIED", eq=""):
    rows.append(dict(key=key, value=val, units=units, dist="fixed", dist_lower="", dist_upper="", source_doi_or_url=src,
                     table=table, equation=eq, page=page, region="north_america" if "north_america" in key else "all",
                     status=status, verified_by=WHO, verified_date=D, notes=notes))
# 2019 VS rates (kg VS / 1000 kg mass / day), North America column
for k, v in [("dairy", 9.2), ("other_cattle", 7.6), ("swine", 3.3), ("market_swine", 3.9), ("breeding_swine", 1.8),
             ("chicken", 14.5), ("layers", 9.4), ("pullets", 5.9), ("broilers", 16.8), ("turkeys", 10.3), ("ducks", 7.4),
             ("sheep", 8.2), ("goats", 9.0), ("horses", 5.65), ("mules_asses", 7.2)]:
    n = {"market_swine": "Swine Finishing row", "breeding_swine": "Swine Breeding row", "layers": "Hens >=1 yr row",
         "sheep": "single value spanning NA/WEur/EEur/Oceania", "goats": "single value spanning NA/WEur/EEur/Oceania",
         "horses": "single value spanning NA/WEur/EEur/Oceania", "turkeys": "all regions", "mules_asses": "all regions",
         "ducks": "all regions"}.get(k, "North America column")
    add(f"IPCC2019.VSrate.{k}|north_america", v, "kg VS/(1000 kg mass)/day", G19_10, "Table 10.13A (New)", "10.56", n, eq="Eq 10.22A")
# 2019 live weights (kg)
for k, v in [("dairy", 650), ("other_cattle", 407), ("swine", 77), ("market_swine", 61), ("breeding_swine", 184),
             ("chicken", 1.4), ("layers", 1.5), ("pullets", 1.2), ("broilers", 1.4), ("turkeys", 6.8), ("ducks", 2.7),
             ("sheep", 40), ("goats", 41), ("horses", 377), ("mules_asses", 130)]:
    n = {"market_swine": "Finishing row", "breeding_swine": "Breeding row", "layers": "Hens >=1 yr row",
         "sheep": "value spanning NA/WEur/EEur", "horses": "value spanning NA/WEur/EEur/Oceania"}.get(k, "North America column")
    add(f"IPCC2019.TAM.{k}|north_america", v, "kg", G19_10, "Table 10A.5 (New)", "10.117", n)
# enteric, other species
for k, v6, v19 in [("sheep", 8, 9), ("goats", 5, 9), ("horses", 18, 18), ("mules_asses", 10, 10)]:
    add(f"IPCC2006.EF_enteric.{k}|developed", v6, "kg CH4/head/yr", G06_10, "Table 10.10", "10.28", "Developed countries")
    add(f"IPCC2019.EF_enteric.{k}|high_productivity", v19, "kg CH4/head/yr", G19_10, "Table 10.10 (Updated)", "10.38",
        "High productivity; fn 1: NA uses high-productivity Tier 1 values" if k in ("sheep", "goats") else "single value")
# 2006 manure CH4 per head, developed
for k, c, t, w in [("sheep", .19, .28, .37), ("goats", .13, .20, .26), ("horses", 1.56, 2.34, 3.13), ("mules_asses", .76, 1.10, 1.52)]:
    for g, v in (("cool", c), ("temperate", t), ("warm", w)):
        add(f"IPCC2006.EF_manureCH4.{k}|developed_{g}", v, "kg CH4/head/yr", G06_10, "Table 10.15", "10.40",
            "cool <15 C, temperate 15-25 C, warm >25 C")
# 2019 manure CH4 per kg VS (high productivity)
for k, ss, dl, pg in [("sheep", (2.5, 5.1, 6.4), (1.3, 1.9, 2.5), "10.61"), ("goats", (2.4, 4.8, 6.0), (1.2, 1.8, 2.4), "10.61"),
                      ("horses", (4.0, 8.0, 10.1), (2.0, 3.0, 4.0), "10.62"), ("mules_asses", (4.4, 8.8, 11.1), (2.2, 3.3, 4.4), "10.62")]:
    for sysk, vals in (("solid_storage", ss), ("dry_lot", dl)):
        for g, v in zip(("cool", "temperate", "warm"), vals):
            add(f"IPCC2019.EF_manureCH4_VS.{k}|{sysk}|{g}", v, "g CH4/kg VS", G19_10, "Table 10.14 (Updated)", pg, "High productivity")
add("IPCC2019.EF_manureCH4_VS.all|pasture", 0.6, "g CH4/kg VS", G19_10, "Table 10.14 (Updated)", "10.62", "All animals, PRP")
# Nrate other species
for k, v6, v19 in [("sheep", .42, .35), ("goats", .45, .46), ("horses", .30, .30), ("mules_asses", .30, .30), ("pullets", .62, .77)]:
    add(f"IPCC2006.Nrate.{k}|north_america", v6, "kg N/(1000 kg)/day", G06_10, "Table 10.19", "10.59", "horses row = horses and mules, asses")
    add(f"IPCC2019.Nrate.{k}|north_america", v19, "kg N/(1000 kg)/day", G19_10, "Table 10.19 (Updated)", "10.83", "horses row = horses and mules and asses")
# 2006 mass, Table 10A-9 developed
for k, v in [("sheep", 48.5), ("goats", 38.5), ("horses", 377), ("mules_asses", 130)]:
    add(f"IPCC2006.TAM.{k}|north_america", v, "kg", G06_10, "Table 10A-9", "10.82", "Developed countries column")
add("IPCC2006.EF1FR.all", 0.003, "kg N2O-N/kg N", G06_11, "Table 11.1", "11.11")
add("IPCC2019.EF1FR.all", 0.004, "kg N2O-N/kg N", G19_11, "Table 11.1 (Updated)", "11.13", "aggregated value")
# crop residues 2006 Table 11.2: DRY, slope, intercept, NAG, RBG_BIO, NBG
R06 = {"grains": (.88, 1.09, .88, .006, .22, .009), "beans_pulses": (.91, 1.13, .85, .008, .19, .008),
       "root_crops_other": (.94, 1.07, 1.54, .016, .20, .014), "maize": (.87, 1.03, .61, .006, .22, .007),
       "winter_wheat": (.89, 1.61, .40, .006, .23, .009), "spring_wheat": (.89, 1.29, .75, .006, .28, .009),
       "rice": (.89, .95, 2.46, .007, .16, None), "barley": (.89, .98, .59, .007, .22, .014), "oats": (.89, .91, .89, .007, .25, .008),
       "millet": (.90, 1.43, .14, .007, None, None), "sorghum": (.89, .88, 1.33, .007, None, .006), "rye": (.88, 1.09, .88, .005, None, .011),
       "soybeans": (.91, .93, 1.35, .008, .19, .008), "dry_bean": (.90, .36, .68, .01, None, .01), "potato": (.22, .10, 1.06, .019, .20, .014),
       "peanut": (.94, 1.07, 1.54, .016, None, None)}
SUB06 = {"dry_bean": "beans_pulses", "peanut": "root_crops_other"}
F06 = ("DRY", "slope", "intercept", "N_AG", "R_BG_BIO", "N_BG")
for crop, vals in R06.items():
    for f, v in zip(F06, vals):
        pg = "11.18" if crop in ("soybeans", "dry_bean", "potato", "peanut") else "11.17"
        if v is None:
            s = SUB06.get(crop, "grains"); v = R06[s][F06.index(f)]
            add(f"IPCC2006.RES.{crop}.{f}", v, "", G06_11, "Table 11.2", pg, f"cell NA in table; filled from '{s}' row", status="SUBSTITUTE", eq="Eq 11.7A")
        else:
            add(f"IPCC2006.RES.{crop}.{f}", v, "", G06_11, "Table 11.2", pg, "", eq="Eq 11.7A")
# 2019 Table 11.1a: NAG, NBG, RAG, RS, DRY
R19 = {"generic": (.008, .009, 1.0, .22, .85), "grains": (.006, .009, 1.3, .22, .88), "winter_wheat": (.006, .009, 1.3, .23, .89),
       "spring_wheat": (.006, .009, 1.3, .28, .89), "barley": (.007, .014, 1.2, .22, .89), "oats": (.007, .008, 1.3, .25, .89),
       "maize": (.006, .007, 1.0, .22, .87), "rye": (.005, .011, 1.6, None, .88), "rice": (.007, None, 1.4, .16, .89),
       "millet": (.007, None, 1.4, None, .90), "sorghum": (.007, .006, 1.4, None, .89), "beans_pulses": (.008, .008, 2.1, .19, .91),
       "soybeans": (.008, .008, 2.1, .19, .91), "potatoes_tubers": (.019, .014, 0.4, .20, .22), "peanuts": (.016, None, 1.0, None, .94)}
F19 = ("N_AG", "N_BG", "R_AG", "RS", "DRY")
for crop, vals in R19.items():
    for f, v in zip(F19, vals):
        if v is None:
            s = "generic" if crop == "peanuts" else "grains"; v = R19[s][F19.index(f)]
            add(f"IPCC2019.RES.{crop}.{f}", v, "", G19_11, "Table 11.1a (New)", "11.18", f"cell '-' (fn e: use most appropriate generic); filled from '{s}' row", status="SUBSTITUTE", eq="Eq 11.6 (Updated)")
        else:
            add(f"IPCC2019.RES.{crop}.{f}", v, "", G19_11, "Table 11.1a (New)", "11.18", "", eq="Eq 11.6 (Updated)")
if __name__ == "__main__":
    if V10.exists():
        sys.exit(f"refusing to overwrite {V10}")
    old = list(csv.DictReader(open(V9, encoding="utf-8")))
    have = {r["key"] for r in old}
    dup = [r["key"] for r in rows if r["key"] in have]
    if dup:
        sys.exit(f"keys already in v9: {dup}")
    with open(V10, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(old[0])); w.writeheader(); w.writerows(old + rows)
    print(f"v10: {len(old)} v9 rows + {len(rows)} new = {len(old) + len(rows)}")
