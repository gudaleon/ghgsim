"""Fetch EPA U.S. GHG Inventory editions and extract agriculture tables (AN_v1).

Editions: 2024 edition (1990-2022, EPA 430-R-24-004) and 2025 edition (1990-2023,
EPA 430-R-25-003). No 2026 EPA edition exists (checked 2026-11-03).
Values are parsed from the PDF text layer (PyMuPDF); nothing is typed by hand.
Usage: python scripts/fetch_epa_ghgi_AN_v1.py --pdf-dir C:/ghgsim-data/epa_ghgi --out data/inventories_US_AN_v1
"""
import argparse, csv, hashlib, json, os, re, sys, urllib.request
import pymupdf

EDITIONS = {
    "2024": dict(file="ghgi_2024_main.pdf", report="EPA 430-R-24-004", years_cov="1990-2022",
                 url="https://www.epa.gov/system/files/documents/2024-04/us-ghg-inventory-2024-main-text_04-18-2024.pdf"),
    "2025": dict(file="ghgi_2025_nepis.pdf", report="EPA 430-R-25-003", years_cov="1990-2023",
                 url="https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=P101EZHC.PDF"),
}
ROWS = ["CO2", "Urea Fertilization", "Liming", "CH4", "Enteric Fermentation", "Manure Management",
        "Rice Cultivation", "Field Burning of Agricultural Residues", "N2O",
        "Agricultural Soil Management", "Manure Management", "Field Burning of Agricultural Residues", "Total"]
GAS_OF = {}
NUM = re.compile(r"^\(?[\d,]+\.\d\)?$|^\+$|^\(\+\)$|^NC$|^\(?0\.0\)?$")

def num(s):
    s = s.strip()
    if s in ("NC",): return 0.0
    if s in ("+", "(+)"): return None  # |value| < 0.05, not reported numerically
    neg = s.startswith("(")
    v = float(s.strip("()").replace(",", ""))
    return -v if neg else v

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def pages(pdf):
    d = pymupdf.open(pdf)
    return [p.get_text() for p in d]

def label(txt):  # printed page label, e.g. "5-3"
    m = re.search(r"\b((?:ES|\d{1,2})-\d{1,3})\b", txt[:200])
    return m.group(1) if m else ""

def table_lines(pg, title):
    for i, t in enumerate(pg):
        j = t.find(title)
        if j >= 0 and "...." not in t[j:j + 200]:
            lines = [l.strip() for l in t[j:].splitlines() if l.strip()]
            return i, lines
    raise SystemExit(f"table not found: {title}")

def parse_rows(lines, rowlabels, ncol, stop):
    """Walk the table: each known row label is followed by ncol value tokens (order-independent)."""
    labels, out, k = set(rowlabels), [], 0
    while k < len(lines) and lines[k] != stop:
        if lines[k] in labels:
            out.append((lines[k], [num(v) for v in lines[k + 1:k + 1 + ncol]])); k += 1 + ncol
        else: k += 1
    if len(out) != len(rowlabels): raise SystemExit(f"expected {len(rowlabels)} rows, got {len(out)}")
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--pdf-dir", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); os.makedirs(a.pdf_dir, exist_ok=True); os.makedirs(a.out, exist_ok=True)
    manifest = {"version": "AN_v1", "checked": "2026-11-03", "gwp": "AR5 100-yr (CH4 28, N2O 265), both editions", "files": []}
    t51 = {}
    for ed, m in EDITIONS.items():
        p = os.path.join(a.pdf_dir, m["file"])
        if not os.path.exists(p):
            req = urllib.request.Request(m["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as r, open(p, "wb") as f: f.write(r.read())
        pg = pages(p)
        manifest["files"].append(dict(edition=ed, report=m["report"], coverage=m["years_cov"], url=m["url"],
                                      file=m["file"], bytes=os.path.getsize(p), sha256=sha256(p), pdf_pages=len(pg)))
        i, lines = table_lines(pg, "Table 5-1:  Emissions from Agriculture (MMT")
        hdr = lines[lines.index("Gas/Source") + 1:lines.index("Gas/Source") + 8]
        rows = parse_rows(lines, ROWS, 7, "Table 5-2:  Emissions from Agriculture (kt)")
        gas = None; rec = []
        for lab, vals in rows:
            if lab in ("CO2", "CH4", "N2O", "Total"): gas = lab; key = lab if lab != "Total" else "Total"
            else: key = f"{gas}:{lab}"
            for y, v in zip(hdr, vals): rec.append(dict(edition=ed, report=m["report"], key=key, year=int(y), mmt_co2e=v,
                                                     source=f"Table 5-1, p. {label(pg[i])} (PDF p. {i+1})"))
        t51[ed] = rec
        with open(os.path.join(a.out, f"EPA{ed}_table5-1_AN_v1.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rec[0])); w.writeheader(); w.writerows(rec)
        if ed == "2025":
            i, lines = table_lines(pg, "Table 9-2: Overall Impact of Recalculations by Sector")
            k = lines.index("Agriculture"); vals = lines[k + 1:k + 8]
            yrs = ["1990", "2005", "2019", "2020", "2021", "2022", "avg"]
            with open(os.path.join(a.out, "EPA2025_table9-2_agriculture_AN_v1.csv"), "w", newline="") as f:
                w = csv.writer(f); w.writerow(["year", "recalc_mmt_co2e", "source"])
                for y, v in zip(yrs, vals): w.writerow([y, num(v), f"EPA 2025 Table 9-2, p. {label(pg[i])} (PDF p. {i+1})"])
    # recalculation 2025 vs 2024 edition from Table 5-1 (rounded to 0.1 MMT)
    idx = {(r["key"], r["year"]): r["mmt_co2e"] for r in t51["2024"]}
    out = []
    for r in t51["2025"]:
        if r["year"] in (1990, 2005, 2022) and (r["key"], r["year"]) in idx:
            old, new = idx[(r["key"], r["year"])], r["mmt_co2e"]
            d = None if old is None or new is None else round(new - old, 1)
            out.append(dict(key=r["key"], year=r["year"], ed2024=old, ed2025=new, diff_mmt=d,
                            diff_pct=None if d is None or not old else round(100 * d / old, 2)))
    with open(os.path.join(a.out, "US_recalc_2024to2025_AN_v1.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    with open(os.path.join(a.out, "..", "inventories_US_manifest_AN_v1.json"), "w") as f: json.dump(manifest, f, indent=2)
    print("ok", len(out), "recalc rows")

if __name__ == "__main__": main()

