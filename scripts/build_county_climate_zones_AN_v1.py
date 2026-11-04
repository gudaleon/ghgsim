"""County IPCC climate zones with three methods (AN_v1).

Primary (adopted, DECISIONS_AN_v4 #2): the IPCC 2019 Refinement climate-zone map
(Vol 4 Ch 3 Annex 3A.5, Figure 3A.5.1/3A.5.2 decision tree incl. corrigendum) as
recreated by Lewis (2022), Zenodo doi:10.5281/zenodo.7303808,
IPCC_Climate_Zones_ts_3.25.tif (0.5 deg, CRU TS3.25 1985-2015, CRU Penman-Monteith PET,
frost days, ETOPO1 elevation). Sampled at the 2020 Census Gazetteer county internal
point; if that cell is NoData (coast), the nearest non-NoData cell within 2 cells is used.

Sensitivity columns (nClimDiv 1991-2020, doi:10.7289/V5M32STR):
- zone_hargreaves: MAT + annual P / Hargreaves PE (the AN_v1 county_climate_annual rule).
- zone_thornthwaite: MAT + annual P / Thornthwaite (1948) PE.
Both use the 2006 Annex 3A.5 thresholds; MAT > 18 C is reported as tropical_unresolved
because frost days and elevation are not in nClimDiv (the IPCC tree needs them).

Usage: python scripts/build_county_climate_zones_AN_v1.py --raw C:/ghgsim-data/climate
Refuses to overwrite an existing output.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import pathlib
import sys
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))
import build_county_p_pe_AN_v2 as b2  # noqa: E402

OUT = ROOT / "data" / "county_climate_zones_AN_v1.csv"
MAN = ROOT / "data" / "county_climate_zones_manifest_AN_v1.json"
RASTER_IDS = {1: "tropical_montane", 2: "tropical_wet", 3: "tropical_moist", 4: "tropical_dry",
              5: "warm_temperate_moist", 6: "warm_temperate_dry", 7: "cool_temperate_moist",
              8: "cool_temperate_dry", 9: "boreal_moist", 10: "boreal_dry", 11: "polar_moist",
              12: "polar_dry"}


def sha256(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def rule_zone(t, r):
    wet = "moist" if r > 1.0 else "dry"
    if t <= 0:
        return f"boreal_{wet}"
    if t <= 10:
        return f"cool_temperate_{wet}"
    if t <= 18:
        return f"warm_temperate_{wet}"
    return "tropical_unresolved"


def gazetteer(zpath):
    with zipfile.ZipFile(zpath) as z:
        name = [n for n in z.namelist() if n.endswith(".txt")][0]
        txt = z.read(name).decode("latin-1")
    rd = csv.DictReader(io.StringIO(txt), delimiter="\t")
    out = {}
    for r in rd:
        r = {k.strip(): v.strip() for k, v in r.items()}
        out[r["GEOID"]] = (float(r["INTPTLAT"]), float(r["INTPTLONG"]), r["NAME"], r["USPS"])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="C:/ghgsim-data/climate")
    ap.add_argument("--version-date", default="20261006")
    a = ap.parse_args(argv)
    if OUT.exists():
        sys.exit(f"{OUT} exists; bump the version instead of overwriting")
    import numpy as np
    import rasterio

    raw = pathlib.Path(a.raw)
    nc = raw / "nclimdiv"
    files = {"county_map": nc / "county-to-climdivs.txt",
             "pcp": nc / f"climdiv-pcpncy-v1.0.0-{a.version_date}",
             "tmax": nc / f"climdiv-tmaxcy-v1.0.0-{a.version_date}",
             "tmin": nc / f"climdiv-tmincy-v1.0.0-{a.version_date}",
             "gazetteer": nc / "2020_Gaz_counties_national.zip",
             "ipcc_raster": raw / "ipcc_zones_zenodo7303808" / "IPCC_Climate_Zones_ts_3.25.tif"}
    cm = b2.load_county_map(files["county_map"])
    P = b2.parse_climdiv(files["pcp"].read_text(encoding="latin-1"), "01", cm)
    TX = b2.parse_climdiv(files["tmax"].read_text(encoding="latin-1"), "27", cm)
    TN = b2.parse_climdiv(files["tmin"].read_text(encoding="latin-1"), "28", cm)
    gz = gazetteer(files["gazetteer"])
    src = rasterio.open(files["ipcc_raster"])
    band = src.read(1).astype(float)
    nod = src.nodata
    if nod is not None:
        band[band == nod] = np.nan
    band[(band < 1) | (band > 12)] = np.nan

    def sample(lat, lon):
        r, c = src.index(lon, lat)
        if 0 <= r < band.shape[0] and 0 <= c < band.shape[1] and not np.isnan(band[r, c]):
            return int(band[r, c]), "internal_point_cell"
        for rad in (1, 2):
            best = None
            for dr in range(-rad, rad + 1):
                for dc in range(-rad, rad + 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < band.shape[0] and 0 <= cc < band.shape[1] and not np.isnan(band[rr, cc]):
                        d = dr * dr + dc * dc
                        if best is None or d < best[0]:
                            best = (d, int(band[rr, cc]))
            if best:
                return best[1], f"nearest_cell_within_{rad}"
        return None, "no_cell"

    rows = []
    for f in sorted({f for f, _ in P}):
        if f not in gz:
            continue
        la, lo, name, usps = gz[f]
        py, eh, et, ty = [], [], [], []
        for y in range(1991, 2021):
            p, tx, tn = P.get((f, y)), TX.get((f, y)), TN.get((f, y))
            if not (p and tx and tn) or any(v is None for v in p + tx + tn):
                continue
            tm12 = [(x + n) / 2 for x, n in zip(tx, tn)]
            py.append(sum(p))
            eh.append(sum(b2.hargreaves_month_mm(tx[m], tn[m], la, m + 1) for m in range(12)))
            et.append(sum(b2.thornthwaite_year_mm(tm12, la)))
            ty.append(sum(tm12) / 12)
        if not py:
            continue
        n = len(py)
        pm, hm, tmm, mat = sum(py) / n, sum(eh) / n, sum(et) / n, sum(ty) / n
        rid, how = sample(la, lo)
        zr = RASTER_IDS.get(rid) if rid else None
        zh, zt = rule_zone(mat, pm / hm), rule_zone(mat, pm / tmm)
        rows.append({
            "fips": f, "state": usps, "county": name, "lat_intpt": la, "lon_intpt": lo,
            "mean_annual_temp_c": round(mat, 2), "annual_precip_mm": round(pm, 1),
            "annual_pe_hargreaves_mm": round(hm, 1), "annual_pe_thornthwaite_mm": round(tmm, 1),
            "p_over_pe_hargreaves": round(pm / hm, 3), "p_over_pe_thornthwaite": round(pm / tmm, 3),
            "zone_hargreaves": zh, "zone_thornthwaite": zt,
            "zone_ipcc2019_map": zr or "", "ipcc_map_sample": how,
            "zone_primary": zr or zt, "zone_primary_basis": "ipcc2019_map" if zr else "thornthwaite_fallback",
        })
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    man = {"output": OUT.name, "output_sha256": sha256(OUT), "n_counties": len(rows),
           "inputs": {k: {"file": str(v.name), "sha256": sha256(v)} for k, v in files.items()},
           "ipcc_raster_source": "Lewis M. (2022) IPCC Climate Zones (2019 Refinement), Zenodo doi:10.5281/zenodo.7303808; md5 f4fa673bd3cb4e0992931b0aff555eb8",
           "nclimdiv": f"v1.0.0-{a.version_date}, doi:10.7289/V5M32STR (Vose et al. 2014)"}
    MAN.write_text(json.dumps(man, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({len(rows)})")


if __name__ == "__main__":
    main()
