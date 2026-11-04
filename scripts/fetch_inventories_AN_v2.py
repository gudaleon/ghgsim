#!/usr/bin/env python3
"""fetch_inventories_AN_v2.py -- (v2: adds EU (EUA) as an extra comparison; accepts _YYYY.xlsx names) reproducible extract of agriculture (CRT sector 3)
numbers from UNFCCC 2026 Common Reporting Table (CRT) submissions.

What it does, per country:
  1. Gets the official CRT zip (one .xlsx per inventory year) from unfccc.int,
     or uses a zip you already downloaded (--zip-dir).
  2. Records the zip's SHA-256 and size in the manifest.
  3. Reads only three sheets from a few year files:
       Table3    sector-3 emissions (enteric CH4, manure CH4/N2O, soils N2O ...)
       Summary3  method tier (T1/T2/T3, CS = country-specific, D = IPCC default)
       Table8s1  recalculation: previous vs latest submission, kt CO2e
  4. Writes small CSV extracts (a few kB) and deletes nothing it did not create.
     The zips themselves (14-45 MB each) are NOT kept unless --keep-zips.

Note on downloading: unfccc.int sits behind a bot-protection layer (Imperva/
Incapsula) that often refuses plain HTTP clients with a small HTML page. The
script detects that (response is not a zip) and tells you to download the zip
in a normal browser from the document page listed in the manifest, then rerun
with --zip-dir. Hashes are of the zip as published.

Usage:
  python scripts/fetch_inventories_AN_v1.py --out data/inventories_AN_v1
  python scripts/fetch_inventories_AN_v1.py --zip-dir C:/ghgsim-data/crt2026 --out data/inventories_AN_v1
Requires: Python >=3.10, openpyxl, requests, py7zr (Canada only).
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, sys, zipfile
from pathlib import Path

SOURCES = {  # UNFCCC "National Inventory Submissions 2026" page, checked 2026-11-03
    "CAN": {"country": "Canada", "doc": "https://unfccc.int/documents/656423",
            "zip": "https://unfccc.int/sites/default/files/resource/CAN-CRT-2026-V2.0.zip"},
    "GBR": {"country": "United Kingdom", "doc": "https://unfccc.int/documents/656567",
            "zip": "https://unfccc.int/sites/default/files/resource/GBRJ-CRT-2026-V1.0.zip"},
    "NZL": {"country": "New Zealand", "doc": "https://unfccc.int/documents/656539",
            "zip": "https://unfccc.int/sites/default/files/resource/NZL-CRT-2026-V1.0_.zip"},
    "IRL": {"country": "Ireland", "doc": "https://unfccc.int/documents/656399",
            "zip": "https://unfccc.int/sites/default/files/resource/IRL-CRT-2026-V1.0.zip"},
    "DEU": {"country": "Germany", "doc": "https://unfccc.int/documents/656483",
            "zip": "https://unfccc.int/sites/default/files/resource/DEU-CRT-2026-V1.0.zip"},
    "AUS": {"country": "Australia", "doc": "https://unfccc.int/documents/656438",
            "zip": "https://unfccc.int/sites/default/files/resource/AUS-CRT-2026-V1.0.zip"},
    # EU: zip supplied by A. Neumann via Drive (EUA_CRT_2026.zip); UNFCCC document URL not yet recorded.
    # Russia: zip supplied by A. Neumann via Drive (RUS-CRT-2026-V1.0_0.zip); UNFCCC document URL not yet recorded.
    "RUS": {"country": "Russian Federation (extra comparison)", "doc": None, "zip": "local:RUS-CRT-2026-V1.0_0.zip"},
    "EUA": {"country": "European Union (extra comparison)", "doc": None, "zip": "local:EUA_CRT_2026.zip"},
}
TABLE3_CODES = ("3.", "3.A.", "3.A.1.", "3.A.2.", "3.B.", "3.B.1.", "3.B.5.", "3.C.", "3.D.", "3.D.1.", "3.D.2.",
                "3.F.", "3.G.", "3.H.")
YEARS_RECALC = (1990, 2005, 2023)  # Table8s1 in year Y compares previous vs latest submission for Y
LATEST = 2024


def norm(s):
    return " ".join(str(s).split()).lower()


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get_zip(iso, zip_dir):
    url = SOURCES[iso]["zip"]
    if url.startswith("local:"):
        return (Path(zip_dir) / url[6:]).read_bytes()
    if zip_dir:
        p = Path(zip_dir) / url.rsplit("/", 1)[1]
        if p.exists():
            return p.read_bytes()
    import requests
    r = requests.get(url, timeout=300, headers={"User-Agent": "Mozilla/5.0 (ghgsim inventory fetch)"})
    if r.content[:2] != b"PK":
        sys.exit(f"[{iso}] unfccc.int returned {len(r.content)} bytes that are not a zip (bot protection). "
                 f"Open {SOURCES[iso]['doc']} in a browser, download the CRT zip into --zip-dir, rerun.")
    if zip_dir:
        Path(zip_dir).mkdir(parents=True, exist_ok=True)
        (Path(zip_dir) / url.rsplit("/", 1)[1]).write_bytes(r.content)
    return r.content


def rows(wb, sheet):
    """Yield (label, values-after-label) with label = first text cell in the first 3 columns."""
    for r in wb[sheet].iter_rows(values_only=True):
        r = list(r)
        for i, c in enumerate(r[:3]):
            if isinstance(c, str) and c.strip():
                yield " ".join(c.split()), [x for x in r[i + 1:] if x not in (None, "")]
                break


def code(label):
    t = label.split(" ")[0]
    return t if t[:2] == "3." else None


def nums(r):
    return [c if isinstance(c, (int, float)) else (c if c not in (None, "") else None) for c in r]


class Archive:
    """CRT zip with one xlsx per year. Canada wraps a single .7z inside the zip (needs py7zr)."""
    def __init__(self, blob):
        z = zipfile.ZipFile(io.BytesIO(blob))
        names = z.namelist()
        if len(names) == 1 and names[0].endswith(".7z"):
            import py7zr  # pip install py7zr
            self.sz = py7zr.SevenZipFile(io.BytesIO(z.read(names[0])))
            self.names = self.sz.getnames(); self.z = None
        else:
            self.z, self.names = z, names

    def find(self, year):
        return next((n for n in self.names if n.endswith((f"-{year}.xlsx", f"_{year}.xlsx"))), None)

    def read(self, name):
        if self.z:
            return self.z.read(name)
        # py7zr>=1.0 removed .read(); extract one member to a temp dir
        import tempfile, pathlib
        with tempfile.TemporaryDirectory() as td:
            self.sz.reset()
            self.sz.extract(path=td, targets=[name])
            return (pathlib.Path(td) / name).read_bytes()


def year_file(z, year):
    return z.find(year)


def extract(iso, blob, out: Path):
    import openpyxl
    z = Archive(blob)
    res = {"table3": [], "summary3": [], "table8": []}
    # Table3 + Summary3 from latest year
    wb = openpyxl.load_workbook(io.BytesIO(z.read(year_file(z, LATEST))), read_only=True, data_only=True)
    for lab, v in rows(wb, "Table3"):
        if code(lab) in TABLE3_CODES:
            # row order: CO2, CH4, N2O (kt), NOx, CO, NMVOC, SOx, Total GHG (kt CO2e, AR5); blank cells dropped
            res["table3"].append({"iso": iso, "year": LATEST, "category": lab,
                                  "values_in_row_order": json.dumps(v, default=str)})
    for lab, v in rows(wb, "Summary3"):
        if code(lab):
            res["summary3"].append({"iso": iso, "year": LATEST, "category": lab,
                                    "method_ef_pairs_CO2_CH4_N2O": json.dumps(v, default=str)})
    wb.close()
    for y in YEARS_RECALC:
        n = year_file(z, y)
        if not n:
            continue
        wb = openpyxl.load_workbook(io.BytesIO(z.read(n)), read_only=True, data_only=True)
        for lab, v in rows(wb, "Table8s1"):
            if code(lab) or lab.lower().startswith("total national"):
                # per gas (CO2, CH4, N2O): previous, latest, difference, %, impact w/o LULUCF %, impact with LULUCF %
                res["table8"].append({"iso": iso, "year": y, "category": lab,
                                      "values_in_row_order": json.dumps(v, default=str)})
        wb.close()
    # one-line recalculation summary for the sector total (sum of CO2, CH4, N2O differences, kt CO2e)
    res["recalc"] = []
    for t in res["table8"]:
        if t["category"].split(" ")[0] == "3." or t["category"].lower().startswith("total national"):
            v = [x if isinstance(x, (int, float)) else None for x in json.loads(t["values_in_row_order"])]
            if not any(x is not None for x in v):  # v2: empty Table8s1 (EU file) -> not reported, no 0 row
                continue
            prev = sum(v[i] or 0 for i in (0, 6, 12) if i < len(v))
            diff = sum(v[i] or 0 for i in (2, 8, 14) if i < len(v))
            res["recalc"].append({"iso": iso, "year": t["year"], "category": t["category"],
                                  "previous_kt_co2e": round(prev, 1), "latest_kt_co2e": round(prev + diff, 1),
                                  "difference_kt_co2e": round(diff, 1),
                                  "difference_pct": round(100 * diff / prev, 3) if prev else None})
    for k, recs in res.items():
        if recs:
            p = out / f"{iso}_{k}_AN_v2.csv"
            with p.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
                w.writeheader(); w.writerows(recs)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/inventories_AN_v2")
    ap.add_argument("--zip-dir", default=None, help="folder with CRT zips (read/write cache)")
    ap.add_argument("--only", nargs="*", default=list(SOURCES))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    man = []
    for iso in a.only:
        blob = get_zip(iso, a.zip_dir)
        extract(iso, blob, out)
        ex = {p.name: sha256(p.read_bytes()) for p in sorted(out.glob(f"{iso}_*_AN_v2.csv"))}
        man.append({**SOURCES[iso], "iso": iso, "zip_sha256": sha256(blob), "zip_bytes": len(blob),
                    "extract_sha256": ex})
        print(iso, "ok", len(blob), "bytes")
    (out / "run_manifest_AN_v2.json").write_text(json.dumps(man, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
