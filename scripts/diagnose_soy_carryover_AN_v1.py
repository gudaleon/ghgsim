"""FINDINGS v10 diagnostic: what drives extra soybean-year N2O (172 N minus 0 N) in APSIM Lake Erie runs.
Uses existing daily outputs only; no new APSIM runs. Maize = odd calendar years, soybean = even (as in summarise_brookston_ssurgo_AN_v1.py).
Refuses to overwrite outputs."""
import os, sys, json, pandas as pd, numpy as np
OUT = "results/soy_carryover_AN_v1"
if os.path.exists(OUT): sys.exit("refusing to overwrite " + OUT)
CASES = {"brookston_ssurgo_tile_1956": "results/apsim_brookston_ssurgo_AN_v1/lake_erie_essex_brookston_ssurgo_tile_1956{n}_AN_v3.Daily.csv.gz",
         "brookston_ssurgo_tile_2rod": "results/apsim_brookston_ssurgo_AN_v1/lake_erie_essex_brookston_ssurgo_tile_2rod{n}_AN_v3.Daily.csv.gz",
         "hoytville_tile_1956": "results/apsim_lake_erie_AN_v3/lake_erie_maumee_hoytville_tile_1956{n}_AN_v3.Daily.csv.gz",
         "hoytville_tile_lt": "results/apsim_lake_erie_AN_v3/lake_erie_maumee_hoytville_tile_lt{n}_AN_v3.Daily.csv.gz"}
def load(p):
    d = pd.read_csv(p, parse_dates=["Clock.Today"]).set_index("Clock.Today"); return d
os.makedirs(OUT); summ, monthly = {}, []
for case, pat in CASES.items():
    f, z = load(pat.format(n="")), load(pat.format(n="_0N"))
    idx = f.index.intersection(z.index); f, z = f.loc[idx], z.loc[idx]
    D = f.select_dtypes("number") - z.select_dtypes("number")
    yr = idx.year; soy = (yr % 2 == 0); maize = ~soy
    nyrs_s, nyrs_m = len(set(yr[soy])), len(set(yr[maize]))
    dN2O_s, dN2O_m = D.N2O_N_kgha[soy].sum()/nyrs_s, D.N2O_N_kgha[maize].sum()/nyrs_m
    m = D[soy].groupby(idx[soy].month)
    mon = (m.N2O_N_kgha.sum()/nyrs_s)
    for k, v in mon.items(): monthly.append({"case": case, "month": k, "dN2O_soy_kgha_yr": round(v, 4)})
    def at(mmdd): # mean difference on a date in soybean years
        sel = [pd.Timestamp(f"{y}-{mmdd}") for y in sorted(set(yr[soy])) if pd.Timestamp(f"{y}-{mmdd}") in D.index]
        return D.loc[sel]
    s = soy
    jan, sow = at("01-01"), at("05-11")
    win = s & (idx.month <= 4); grow = s & (idx.month >= 5) & (idx.month <= 9); late = s & (idx.month >= 10)
    thaw = s & (idx.month <= 4) & (f["Weather.MeanT"].rolling(7).min() <= 0) & (f["Weather.MeanT"] > 0)
    r = np.corrcoef(D.N2O_N_kgha[s], D.NO3_kgha[s])[0, 1]
    rn = np.corrcoef(D.N2O_N_kgha[s], D.NH4_kgha[s])[0, 1]
    summ[case] = {
      "soy_years": nyrs_s,
      "dN2O_soy_kgha_yr": round(dN2O_s, 3), "dN2O_maize_kgha_yr": round(dN2O_m, 3), "soy_share": round(dN2O_s/(dN2O_s+dN2O_m), 3),
      "dN2O_soy_JanApr": round(D.N2O_N_kgha[win].sum()/nyrs_s, 3), "dN2O_soy_thaw_days": round(D.N2O_N_kgha[thaw].sum()/nyrs_s, 3),
      "dN2O_soy_MaySep": round(D.N2O_N_kgha[grow].sum()/nyrs_s, 3), "dN2O_soy_OctDec": round(D.N2O_N_kgha[late].sum()/nyrs_s, 3),
      "dNO3_Jan1_kgha": round(jan.NO3_kgha.mean(), 1), "dNO3_soy_sowing_May11_kgha": round(sow.NO3_kgha.mean(), 1),
      "dNH4_soy_sowing_kgha": round(sow.NH4_kgha.mean(), 2),
      "dMinN_soy_kgha_yr": round(D.MinN_kgha[s].sum()/nyrs_s, 2),
      "dN2_soy_kgha_yr": round(D.N2_N_kgha[s].sum()/nyrs_s, 2),
      "dSoyN_max_kgha": round((f.SoyAbovegroundN_kgha[s].groupby(yr[s]).max() - z.SoyAbovegroundN_kgha[s].groupby(yr[s]).max()).mean(), 1),
      "dTileNO3_soy_kgha_yr": round(D.TileNO3_kgha[s].sum()/nyrs_s, 2),
      "corr_daily_dN2O_dNO3_soy": round(r, 3), "corr_daily_dN2O_dNH4_soy": round(rn, 3),
    }
pd.DataFrame(monthly).to_csv(f"{OUT}/soy_carryover_monthly_AN_v1.csv", index=False)
json.dump(summ, open(f"{OUT}/soy_carryover_summary_AN_v1.json", "w"), indent=1)
print(json.dumps(summ, indent=1)); print(pd.DataFrame(monthly).pivot(index="month", columns="case", values="dN2O_soy_kgha_yr"))