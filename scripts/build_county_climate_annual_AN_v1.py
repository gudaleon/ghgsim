"""County annual climate (mean temperature, P, Hargreaves PE, P/PE) and IPCC climate zone (AN v1).

Builds data/county_climate_annual_AN_v1.csv from NOAA nClimDiv county monthly files
(Vose et al. 2014, doi:10.7289/V5M32STR), 1991-2020 by default, reusing the parsing and
Hargreaves-Samani (FAO-56 Eq 52) code of scripts/build_county_p_pe_AN_v2.py.

Per county and year: annual P = sum of 12 monthly P; annual PE = sum of 12 monthly
Hargreaves PE; MAT = mean of 12 monthly (Tmax+Tmin)/2. Values are averaged over complete
years. The IPCC climate zone uses 2006 IPCC GL Vol 4 Ch 3 Annex 3A.5 (as coded in
ghgsim.modules.ipcc2019.manure.climate_zone_2019): boreal MAT<=0, cool temperate 0-10,
warm temperate 10-18 C, moist if P/PE > 1. MAT > 18 C (tropical) needs MAP/elevation classes
not derived here, so ipcc_zone is left blank ("tropical_unresolved").

Usage (Bubble, raw files already downloaded):
  python scripts/build_county_climate_annual_AN_v1.py --raw C:/ghgsim-data/climate/nclimdiv \
      --version-date 20261006
"""
from __future__ import annotations

import argparse, csv, datetime as dt, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))
import build_county_p_pe_AN_v2 as b2  # noqa: E402
from ghgsim.modules.ipcc2019.manure import climate_zone_2019  # noqa: E402


def build(files: dict, start: int, end: int):
    cm = b2.load_county_map(files["county_map"])
    P = b2.parse_climdiv(files["climdiv-pcpncy"].read_text(encoding="latin-1"), "01", cm)
    TX = b2.parse_climdiv(files["climdiv-tmaxcy"].read_text(encoding="latin-1"), "27", cm)
    TN = b2.parse_climdiv(files["climdiv-tmincy"].read_text(encoding="latin-1"), "28", cm)
    lat = b2.load_gazetteer_lat(files["gazetteer"])
    rows, issues = [], {"no_gazetteer_latitude": [], "incomplete_years": [], "tropical_unresolved": []}
    for f in sorted({f for f, _ in P}):
        if f not in lat:
            issues["no_gazetteer_latitude"].append(f)
            continue
        la, name, usps = lat[f]
        py, ey, ty = [], [], []
        for y in range(start, end + 1):
            p, tx, tn = P.get((f, y)), TX.get((f, y)), TN.get((f, y))
            if not (p and tx and tn) or any(v is None for v in p + tx + tn):
                issues["incomplete_years"].append(f"{f}:{y}")
                continue
            py.append(sum(p))
            ey.append(sum(b2.hargreaves_month_mm(tx[m], tn[m], la, m + 1) for m in range(12)))
            ty.append(sum((a + b) / 2 for a, b in zip(tx, tn)) / 12)
        if not py:
            continue
        n = len(py)
        pm, em, tm = sum(py) / n, sum(ey) / n, sum(ty) / n
        ratio = pm / em if em else None
        zone = climate_zone_2019(tm, ratio) if ratio is not None else None
        if zone is None:
            issues["tropical_unresolved"].append(f)
        rows.append({
            "fips": f, "state": usps, "county": name, "lat_intpt": round(la, 4), "n_years": n,
            "period": f"{start}-{end}", "mean_annual_temp_c": round(tm, 2),
            "annual_precip_mm": round(pm, 1), "annual_pe_hargreaves_mm": round(em, 1),
            "annual_p_over_pe": round(ratio, 3) if ratio is not None else "",
            "ipcc_zone": zone or "", "zone_rule": "IPCC2006 Vol4 Ch3 Annex 3A.5 (MAT, MAP/PET)",
        })
    return rows, issues


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="C:/ghgsim-data/climate/nclimdiv")
    ap.add_argument("--version-date", default=None)
    ap.add_argument("--start", type=int, default=1991)
    ap.add_argument("--end", type=int, default=2020)
    ap.add_argument("--out", default="data/county_climate_annual_AN_v1.csv")
    ap.add_argument("--manifest", default="data/county_climate_annual_manifest_AN_v1.json")
    a = ap.parse_args(argv)
    out, man = pathlib.Path(a.out), pathlib.Path(a.manifest)
    for p in (out, man):
        if p.exists():
            sys.exit(f"{p} exists; _AN_vX files are never overwritten. Use a new version.")
    files = b2.fetch(pathlib.Path(a.raw), a.version_date)
    rows, issues = build(files, a.start, a.end)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    zones = {}
    for r in rows:
        zones[r["ipcc_zone"] or "tropical_unresolved"] = zones.get(r["ipcc_zone"] or "tropical_unresolved", 0) + 1
    man.write_text(json.dumps({
        "manifest": man.stem, "created": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "script": "scripts/build_county_climate_annual_AN_v1.py",
        "output": {"path": str(out).replace("\\", "/"), "rows": len(rows), "sha256": b2.sha256(out)},
        "period": [a.start, a.end], "zone_counts": zones,
        "sources": {"nclimdiv": {"doi": b2.DOI, "files": {k: {"name": v.name, "sha256": b2.sha256(v)} for k, v in files.items() if k.startswith("climdiv")}},
                    "county_map": {"sha256": b2.sha256(files["county_map"])},
                    "gazetteer": {"url": b2.GAZ_URL, "sha256": b2.sha256(files["gazetteer"])}},
        "methods": {"annual_pe_hargreaves_mm": "sum of 12 monthly Hargreaves-Samani (FAO-56 Eq 52), uncalibrated",
                    "ipcc_zone": "boreal MAT<=0; cool temperate 0<MAT<=10; warm temperate 10<MAT<=18; moist if P/PE>1; MAT>18 left blank"},
        "issue_counts": {k: len(v) for k, v in issues.items()},
        "issues": {k: v[:200] for k, v in issues.items()},
    }, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} counties; zones {zones}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
