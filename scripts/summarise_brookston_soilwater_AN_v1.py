import csv
import gzip
import json

D = "results/apsim_brookston_soilwater_AN_v1/"
def ann(n):
    y = {}
    for r in csv.DictReader(gzip.open(D + n + ".Daily.csv.gz", "rt")):
        k = int(r["Clock.Today"][:4]); d = y.setdefault(k, {"n2o": 0, "n2": 0, "dr": 0, "ro": 0, "le": 0, "mz": 0, "sy": 0, "rain": 0})
        f = lambda c: float(r[c] or 0)
        d["n2o"] += f("N2O_N_kgha"); d["n2"] += f("N2_N_kgha"); d["dr"] += f("Drainage_mm"); d["ro"] += f("Runoff_mm"); d["le"] += f("LeachNO3_kgha"); d["rain"] += f("Weather.Rain")
        d["mz"] = max(d["mz"], f("MaizeN_gm2")); d["sy"] = max(d["sy"], f("SoyGrain_kgha"))
    return y
a, z = ann("brookston_soilwater_AN_v1"), ann("brookston_soilwater_0N_AN_v1")
mean = lambda y, k: sum(v[k] for v in y.values()) / len(y)
maize = [k for k in a if k % 2 == 1 and a[k]["mz"] > 0]  # maize in odd years (parity 1); 1994 Jan-Feb is the late-harvested 1993 crop
soy = [k for k, v in a.items() if v["sy"] > 0]
diff = {k: a[k]["n2o"] - z[k]["n2o"] for k in a}; tot = sum(diff.values())
out = {"years": len(a), "maize_years": len(maize), "soy_years_with_grain": len(soy), "maize_year_parity": sorted({k % 2 for k in maize}),
 "N2O_fert": mean(a, "n2o"), "N2O_0N": mean(z, "n2o"), "N2_fert": mean(a, "n2"), "drainage_mm": mean(a, "dr"), "runoff_mm": mean(a, "ro"), "leachNO3_fert": mean(a, "le"), "leachNO3_0N": mean(z, "le"), "rain": mean(a, "rain"),
 "EF_pct": 2 * (mean(a, "n2o") - mean(z, "n2o")) / 172 * 100,
 "soy_share": sum(v for k, v in diff.items() if k not in maize) / tot,
 "EF_maize_year_only_pct": 2 * sum(v for k, v in diff.items() if k in maize) / len(a) / 172 * 100}
out = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out.items()}
json.dump(out, open("results/apsim_brookston_soilwater_summary_AN_v1.json", "w"), indent=1); print(out)