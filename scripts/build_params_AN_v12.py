#!/usr/bin/env python3
"""Build data/ipcc_params_AN_v12.csv = every row of v11 unchanged + new rows for the N-budget closure inputs (AN_v1).

New rows (every source was opened this session; see docs/DECISIONS_AN_v29.md):
  * Soybean below-ground share of total plant N, Salvagiotti et al. 2008 abstract.
  * Soybean whole-plant BNF per kg grain and below-ground share, Gelfand & Robertson 2015 (open access full text).
  * Soybean and alfalfa fixed N per ha, Russelle & Birr 2004 (abstract, via Crossref).
  * Alfalfa fixation per ton, Peterson & Russelle 1991 as quoted in the NuGIS Methods Documentation (secondary).
  * Ohio on-farm N removal per bushel, OSU Extension ANR-74 (Culman et al. 2019) Table A3.
  * NuGIS crop N removal coefficients (Methods Documentation Table 3.1), used as an independent comparator.
Refuses to overwrite.
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC, OUT = ROOT / "data" / "ipcc_params_AN_v11.csv", ROOT / "data" / "ipcc_params_AN_v12.csv"
WHO, DAY = "AN agent; source opened 2026-11-22", "2026-11-22"
SALV = "https://doi.org/10.1016/j.fcr.2008.03.001"
GEL = "https://doi.org/10.1007/s10533-014-0061-4"
RUS = "https://doi.org/10.2134/agronj2004.1754"
NUG = "https://www.nutrienttools.org/wp-content/uploads/2026/09/NuGIS_Methods_Documentation_9_2026_PUBLIC.pdf"
ANR74 = "https://ohioline.osu.edu/factsheet/anr-74"
rows = []


def add(key, value, units, src, table, page, notes="", status="VERIFIED", dist="fixed", lo="", hi=""):
    rows.append(dict(key=key, value=value, units=units, dist=dist, dist_lower=lo, dist_upper=hi, source_doi_or_url=src,
                     table=table, equation="", page=page, region="all", status=status, verified_by=WHO,
                     verified_date=DAY, notes=notes))


add("SALV2008.soy_BG_share_total_N", 0.24, "fraction of total plant N", SALV, "abstract", "1",
    "abstract: 'average estimated below-ground N contribution of 24% of total plant N'. Same Ndfa is assumed for below-ground N (assumption, not stated in the abstract)",
    dist="uniform", lo=0.04, hi=0.40)
add("GELFAND2015.soy_BG_share_total_N_measured", 0.04, "fraction of total plant N", GEL, "Table 1 (as quoted in Discussion)", "open access full text",
    "Gelfand & Robertson 2015: 'our measured contribution of ~4% (Table 1)'; single site (KBS, Michigan, 2012 drought year); used as the LOW bound of the below-ground share")
add("ROCHESTER_UNKOVICH.soy_BG_share_total_N_high", 0.40, "fraction of total plant N", GEL, "Introduction (secondary)", "open access full text",
    "Gelfand & Robertson 2015 Introduction: below-ground BNF share 'range from ~24 to ~40 % for irrigated and dryland soybeans in Australia (Rochester et al. 1998; Unkovich and Pate, 2000)'; secondary citation; HIGH bound only",
    status="SOURCE-TRACED")
add("GELFAND2015.soy_BNF_g_N_per_kg_grain", 43, "g N fixed (whole plant, unfertilised) per kg grain", GEL, "Results (Table 2)", "open access full text",
    "'80 +/- 11 kg Nr/ha ... translates to 43 +/- 6 g Nr per kg grain'; grain moisture basis not stated; cross-check only", dist="uniform", lo=37, hi=49)
add("GELFAND2015.US_soy_BNF_Tg_N", 3.5, "Tg N / yr (US, 2002-2012 mean production)", GEL, "Abstract", "open access full text", "comparator only")
add("HERRIDGE2008.US_soy_BNF_Tg_N", 5.7, "Tg N / yr (US, 2005 yields)", "https://doi.org/10.1007/s11104-008-9668-3", "abstract", "1",
    "Plant Soil 311:1-18 abstract: 'U.S., Brazil and Argentina ... 5.7, 4.6 and 3.4 Tg'; comparator only")
add("RUSSELLE2004.alfalfa_fixed_N_kg_per_ha", 152, "kg N/ha (basin mean, harvested fixed N)", RUS, "abstract", "1754",
    "Agron J 96:1754-1760 abstract; Mississippi River Basin spatial mean; range 45-470 is spatial range, not an uncertainty interval",
    dist="uniform", lo=45, hi=470)
add("RUSSELLE2004.soy_fixed_N_kg_per_ha", 84, "kg N/ha (basin mean, harvested fixed N)", RUS, "abstract", "1754",
    "same abstract; spatial range 0-185; comparator only")
add("PETERSON1991.alfalfa_fixed_N_lb_per_ton", 61, "lb N per ton alfalfa", NUG, "Section 3 text", "6",
    "NuGIS Methods Documentation: 'Alfalfa N fixation in the Corn Belt has been estimated at 61 pounds per ton (Peterson and Russelle, 1991)'; secondary; primary not opened",
    status="SOURCE-TRACED")
add("OHIO_ANR74.N_lb_per_bu.corn", 0.74, "lb N per bu corn", ANR74, "Table A3 (slope, N removal vs yield)", "online",
    "Culman et al. 2019, >300 on-farm trials 2014-2018, 39 Ohio counties; as-sampled grain moisture not stated; 0.74 = 56 lb x 1.33% N (Table A1)")
add("OHIO_ANR74.N_lb_per_bu.soybeans", 3.55, "lb N per bu soybean", ANR74, "Table A3", "online", "= 60 lb x 5.91% N (Table A1)")
add("OHIO_ANR74.N_lb_per_bu.wheat", 0.96, "lb N per bu wheat", ANR74, "Table A3", "online", "= 60 lb x 1.60% N (Table A1)")
for k, v, u in (("corn", 0.67, "bu"), ("soybeans", 3.25, "bu"), ("wheat_other_states", 1.16, "bu"),
                ("alfalfa", 51, "ton"), ("other_hay", 29, "ton"), ("corn_silage", 9.7, "ton")):
    add(f"NUGIS.N_removal_lb_per_{u}.{k}", v, f"lb N per {u}", NUG, "Table 3.1", "6-7", "comparator: TFI NuGIS removal coefficient (moisture basis not stated)")

if __name__ == "__main__":
    if OUT.exists():
        sys.exit(f"refusing to overwrite {OUT}")
    base = list(csv.DictReader(open(SRC, encoding="utf-8")))
    have = {r["key"] for r in base}
    dup = [r["key"] for r in rows if r["key"] in have]
    if dup:
        sys.exit(f"keys already in v11: {dup}")
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(base[0].keys()))
        w.writeheader()
        w.writerows(base)
        w.writerows(rows)
    print(f"wrote {OUT} ({len(base)} v11 rows + {len(rows)} new)")
