"""County growing-season (May-October) P and PE from NOAA nClimDiv (AN v1).

Inputs for Holos EF1 option ``holos_liang2020`` (``growing_season_precip_mm``,
``growing_season_pe_mm``). Standard library only.

Sources (recorded in the manifest with SHA-256):
- NOAA nClimDiv county monthly precipitation, Tmax, Tmin
  (Vose et al. 2014, doi:10.7289/V5M32STR), files climdiv-{pcpn,tmax,tmin}cy-v1.0.0-YYYYMMDD.
- US Census 2020 Gazetteer counties (INTPTLAT, internal point latitude) for radiation/day length.

PE methods (no calibration, documented equations):
- Hargreaves-Samani (1985) as in FAO-56 Eq 52, Ra from FAO-56 Eqs 21-25 at mid-month day.
- Thornthwaite (1948) with annual heat index from the same year's 12 monthly means.

Usage:
  python scripts/build_county_p_pe_AN_v1.py --raw C:/ghgsim-data/climate/nclimdiv \
      --start 1980 --end 2010 --out data/county_p_pe_may_oct_AN_v1.csv
"""
from __future__ import annotations

import argparse, csv, datetime as dt, hashlib, io, json, math, pathlib, re, sys, urllib.request, zipfile

NCEI_BASE = "https://www.ncei.noaa.gov/monitoring-content/data/us/climdiv/monthly/current/"
GAZ_URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_counties_national.zip"
DOI = "10.7289/V5M32STR"
MONTHS = (5, 6, 7, 8, 9, 10)
MID_DOY = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]  # non-leap mid-month
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# nClimDiv state codes (county-readme.txt, alphabetical 01-48 CONUS, 49 HI, 50 AK) -> FIPS
NCEI_TO_FIPS = {
    1: "01", 2: "04", 3: "05", 4: "06", 5: "08", 6: "09", 7: "10", 8: "12", 9: "13", 10: "16",
    11: "17", 12: "18", 13: "19", 14: "20", 15: "21", 16: "22", 17: "23", 18: "24", 19: "25",
    20: "26", 21: "27", 22: "28", 23: "29", 24: "30", 25: "31", 26: "32", 27: "33", 28: "34",
    29: "35", 30: "36", 31: "37", 32: "38", 33: "39", 34: "40", 35: "41", 36: "42", 37: "44",
    38: "45", 39: "46", 40: "47", 41: "48", 42: "49", 43: "50", 44: "51", 45: "53", 46: "54",
    47: "55", 48: "56", 49: "15", 50: "02",
}


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def parse_climdiv(text: str, element: str) -> dict:
    """Parse county climdiv text -> {(fips5, year): [12 values or None]}.

    Values converted to SI: precipitation inches -> mm, temperature F -> C.
    Missing sentinels (-9.99, -99.99) -> None.
    """
    out = {}
    for line in text.splitlines():
        if len(line) < 95:
            continue
        st, cty, el, yr = int(line[0:2]), line[2:5], line[5:7], int(line[7:11])
        if el != element:
            raise ValueError(f"unexpected element {el} (want {element})")
        fips = NCEI_TO_FIPS[st] + cty
        vals = []
        for m in range(12):
            v = float(line[11 + 7 * m: 18 + 7 * m])
            if v <= -9.99 + 1e-9 and v in (-9.99, -99.99):
                vals.append(None)
            elif element == "01":
                vals.append(v * 25.4)
            else:
                vals.append((v - 32.0) * 5.0 / 9.0)
        out[(fips, yr)] = vals
    return out


def ra_mj(lat_deg: float, doy: int) -> float:
    """Extraterrestrial radiation, MJ m-2 day-1 (FAO-56 Eqs 21, 23-25)."""
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    delta = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    return 24 * 60 / math.pi * 0.0820 * dr * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))


def daylength_h(lat_deg: float, doy: int) -> float:
    phi = math.radians(lat_deg)
    delta = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    return 24 / math.pi * ws


def hargreaves_month_mm(tmax: float, tmin: float, lat: float, month: int) -> float:
    """Hargreaves-Samani monthly PE (FAO-56 Eq 52) in mm/month."""
    tmean = (tmax + tmin) / 2
    rng = max(tmax - tmin, 0.0)
    et0 = 0.0023 * (tmean + 17.8) * math.sqrt(rng) * 0.408 * ra_mj(lat, MID_DOY[month - 1])
    return max(et0, 0.0) * DAYS[month - 1]


def thornthwaite_year_mm(tmean12: list, lat: float) -> list:
    """Thornthwaite (1948) monthly PE in mm for 12 monthly mean temps (C)."""
    heat = sum((t / 5) ** 1.514 for t in tmean12 if t > 0)
    if heat <= 0:
        return [0.0] * 12
    a = 6.75e-7 * heat ** 3 - 7.71e-5 * heat ** 2 + 1.792e-2 * heat + 0.49239
    out = []
    for m, t in enumerate(tmean12):
        if t <= 0:
            out.append(0.0)
            continue
        L = daylength_h(lat, MID_DOY[m])
        out.append(16 * (L / 12) * (DAYS[m] / 30) * (10 * t / heat) ** a)
    return out


def load_gazetteer_lat(path: pathlib.Path) -> dict:
    with zipfile.ZipFile(path) as z:
        name = [n for n in z.namelist() if n.endswith(".txt")][0]
        text = z.read(name).decode("latin-1")
    rows = csv.DictReader(io.StringIO(text), delimiter="\t")
    lat = {}
    for r in rows:
        r = {k.strip(): v for k, v in r.items()}
        lat[r["GEOID"]] = (float(r["INTPTLAT"]), r["NAME"], r["USPS"])
    return lat


def find_latest(base_html: str, stem: str) -> str:
    names = sorted(set(re.findall(rf'href="({re.escape(stem)}-v[0-9.]+-\d{{8}})"', base_html)))
    if not names:
        raise RuntimeError(f"no {stem} file at {NCEI_BASE}")
    return names[-1]


def fetch(raw: pathlib.Path, version_date: str | None) -> dict:
    raw.mkdir(parents=True, exist_ok=True)
    html = urllib.request.urlopen(NCEI_BASE, timeout=60).read().decode("utf-8", "replace")
    files = {}
    for stem in ("climdiv-pcpncy", "climdiv-tmaxcy", "climdiv-tmincy"):
        name = f"{stem}-v1.0.0-{version_date}" if version_date else find_latest(html, stem)
        p = raw / name
        if not p.exists():
            urllib.request.urlretrieve(NCEI_BASE + name, p)
        files[stem] = p
    g = raw / pathlib.Path(GAZ_URL).name
    if not g.exists():
        urllib.request.urlretrieve(GAZ_URL, g)
    files["gazetteer"] = g
    return files


def build(files: dict, start: int, end: int) -> tuple[list, dict]:
    P = parse_climdiv(files["climdiv-pcpncy"].read_text(encoding="latin-1"), "01")
    TX = parse_climdiv(files["climdiv-tmaxcy"].read_text(encoding="latin-1"), "27")
    TN = parse_climdiv(files["climdiv-tmincy"].read_text(encoding="latin-1"), "28")
    lat = load_gazetteer_lat(files["gazetteer"])
    counties = sorted({f for f, _ in P})
    rows, issues = [], {"no_gazetteer_latitude": [], "incomplete_years": []}
    for f in counties:
        if f not in lat:
            issues["no_gazetteer_latitude"].append(f)
            continue
        la, name, usps = lat[f]
        p_y, h_y, t_y = [], [], []
        for y in range(start, end + 1):
            p, tx, tn = P.get((f, y)), TX.get((f, y)), TN.get((f, y))
            if not (p and tx and tn) or any(v is None for v in p + tx + tn):
                issues["incomplete_years"].append(f"{f}:{y}")
                continue
            tm = [(a + b) / 2 for a, b in zip(tx, tn)]
            th = thornthwaite_year_mm(tm, la)
            p_y.append(sum(p[m - 1] for m in MONTHS))
            h_y.append(sum(hargreaves_month_mm(tx[m - 1], tn[m - 1], la, m) for m in MONTHS))
            t_y.append(sum(th[m - 1] for m in MONTHS))
        if not p_y:
            continue
        n = len(p_y)
        pm, hm, tm_ = sum(p_y) / n, sum(h_y) / n, sum(t_y) / n
        rows.append({
            "fips": f, "state": usps, "county": name, "lat_intpt": round(la, 4),
            "n_years": n, "period": f"{start}-{end}",
            "growing_season_precip_mm": round(pm, 1),
            "pe_hargreaves_mm": round(hm, 1), "pe_thornthwaite_mm": round(tm_, 1),
            "p_over_pe_hargreaves": round(pm / hm, 3) if hm else "",
            "p_over_pe_thornthwaite": round(pm / tm_, 3) if tm_ else "",
        })
    return rows, issues


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="C:/ghgsim-data/climate/nclimdiv")
    ap.add_argument("--version-date", default=None, help="nClimDiv file date YYYYMMDD (default: latest listed)")
    ap.add_argument("--start", type=int, default=1980)
    ap.add_argument("--end", type=int, default=2010)
    ap.add_argument("--out", default="data/county_p_pe_may_oct_AN_v1.csv")
    ap.add_argument("--manifest", default="data/county_p_pe_manifest_AN_v1.json")
    a = ap.parse_args(argv)
    out, man = pathlib.Path(a.out), pathlib.Path(a.manifest)
    for p in (out, man):
        if p.exists():
            sys.exit(f"{p} exists; _AN_vX files are never overwritten. Use a new version.")
    files = fetch(pathlib.Path(a.raw), a.version_date)
    rows, issues = build(files, a.start, a.end)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    man.write_text(json.dumps({
        "manifest": man.stem, "created": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "script": "scripts/build_county_p_pe_AN_v1.py", "output": {"path": str(out).replace("\\", "/"), "rows": len(rows), "sha256": sha256(out)},
        "period": [a.start, a.end], "months": list(MONTHS),
        "sources": {
            "nclimdiv": {"name": "NOAA Monthly U.S. Climate Divisional Database (NClimDiv), county files",
                          "citation": "Vose, R.S., Applequist, S., Squires, M., Durre, I., Menne, M.J., Williams, C.N. Jr., Fenimore, C., Gleason, K., Arndt, D. (2014). NOAA Monthly U.S. Climate Divisional Database (NClimDiv). NOAA National Climatic Data Center.",
                          "doi": DOI, "base_url": NCEI_BASE,
                          "files": {k: {"name": v.name, "sha256": sha256(v), "size_bytes": v.stat().st_size} for k, v in files.items() if k != "gazetteer"}},
            "gazetteer": {"name": "US Census Bureau 2020 Gazetteer Files, counties", "url": GAZ_URL,
                           "sha256": sha256(files["gazetteer"]), "field": "INTPTLAT"},
        },
        "methods": {"pe_hargreaves_mm": "Hargreaves & Samani (1985), FAO-56 Eq 52; Ra FAO-56 Eqs 21-25 at mid-month DOY; uncalibrated",
                    "pe_thornthwaite_mm": "Thornthwaite (1948); heat index from same-year 12 monthly means; no T>26.5C correction"},
        "issues": {k: v[:200] + (["..."] if len(v) > 200 else []) for k, v in issues.items()},
        "issue_counts": {k: len(v) for k, v in issues.items()},
    }, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} counties -> {out}; issues {[(k, len(v)) for k, v in issues.items()]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
