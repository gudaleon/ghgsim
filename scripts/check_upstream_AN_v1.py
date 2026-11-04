"""Weekly upstream check (AN_v1): has any source behind a Paper B number changed?

    python scripts/check_upstream_AN_v1.py --report build/upstream_report.md --json build/upstream.json
    python scripts/check_upstream_AN_v1.py --baseline data/upstream_sources_AN_v2.json   # write new pins (new version)

Pins live in the latest data/upstream_sources_AN_v*.json. For each source a small fingerprint is fetched (no large raw
downloads, except the four IPCC chapter PDFs, ~2-7 MB each) and compared with the pin:
  ipcc_*            SHA-256 of the IPCC chapter PDF that data/ipcc_params_AN_v*.csv cites
  epa_ghgi_editions titles of the GHGI editions listed on EPA's inventory page
  nass_census2022   Content-Length + Last-Modified of the QuickStats bulk file qs.census2022.txt.gz
  nclimdiv          newest climdiv-pcpncy version tag in the NCEI directory (updates monthly; we pin one)
  unfccc_crt_2026   CRT zip links for CAN/GBR/NZL/IRL/DEU/AUS on the UNFCCC 2026 submissions page
  gleam_release     newest tag of github.com/un-fao/GLEAM (we pin v0.8.0-alpha, 90e4161)
Exit 0 = no change, 2 = at least one source changed, 3 = only "unreachable" sources (no issue opened).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

import requests
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "ghgsim-living-paper-check/1 (University of Toronto; research reproducibility)"}
ISOS = ("CAN", "GBR", "NZL", "IRL", "DEU", "AUS")
IPCC = {
    "ipcc_2006_v4_ch10": "https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_10_Ch10_Livestock.pdf",
    "ipcc_2006_v4_ch11": "https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_11_Ch11_N2O%26CO2.pdf",
    "ipcc_2019r_v4_ch10": "https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4/19R_V4_Ch10_Livestock.pdf",
    "ipcc_2019r_v4_ch11": "https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4/19R_V4_Ch11_Soils_N2O_CO2.pdf",
}
EPA = "https://www.epa.gov/ghgemissions/inventory-us-greenhouse-gas-emissions-and-sinks"
NASS = "https://www.nass.usda.gov/datasets/qs.census2022.txt.gz"
NCEI = "https://www.ncei.noaa.gov/pub/data/cirs/climdiv/"
UNFCCC = "https://unfccc.int/ghg-inventories-annex-i-parties/2026"
GLEAM = "https://api.github.com/repos/un-fao/GLEAM/tags"


def get(url, **kw):
    r = requests.get(url, headers=UA, timeout=120, **kw)
    r.raise_for_status()
    return r


def fp_pdf(url):
    r = get(url)
    return {"sha256": hashlib.sha256(r.content).hexdigest(), "bytes": len(r.content)}


def fp_epa():
    t = html.fromstring(get(EPA).content).text_content()
    eds = sorted(set(re.findall(r"1990\s*[-\u2013\u2014]\s*(20\d\d)", t)))
    return {"time_series_end_years_listed": eds, "latest": eds[-1] if eds else None}


def fp_nass():
    r = requests.head(NASS, headers=UA, timeout=60, allow_redirects=True)
    r.raise_for_status()
    return {"content_length": r.headers.get("Content-Length"), "last_modified": r.headers.get("Last-Modified")}


def fp_nclimdiv():
    v = sorted(set(re.findall(r"climdiv-pcpncy-(v\d+\.\d+\.\d+-\d{8})", get(NCEI).text)))
    return {"latest": v[-1] if v else None}


def fp_unfccc():
    links = html.fromstring(get(UNFCCC).content).xpath("//a/@href")
    z = sorted({h.rsplit("/", 1)[-1] for h in links if "-CRT-2026-" in h and h.rsplit("/", 1)[-1][:3] in ISOS})
    if not z:
        raise RuntimeError("no CRT links parsed: unfccc.int serves a bot-challenge page to scripts; check by hand")
    return {"crt_zips": z}


def fp_gleam():
    tags = get(GLEAM).json()
    return {"latest_tag": tags[0]["name"], "sha": tags[0]["commit"]["sha"][:7], "n_tags": len(tags)} if tags else {}


def fingerprints():
    out = {}
    jobs = {**{k: (lambda u=u: fp_pdf(u)) for k, u in IPCC.items()}, "epa_ghgi_editions": fp_epa,
            "nass_census2022": fp_nass, "nclimdiv": fp_nclimdiv, "unfccc_crt_2026": fp_unfccc, "gleam_release": fp_gleam}
    for k, f in jobs.items():
        try:
            out[k] = {"status": "ok", "fingerprint": f()}
        except Exception as e:  # network/bot block: reported, never treated as a change
            out[k] = {"status": "unreachable", "error": repr(e)[:300]}
    return out


def latest_pins():
    c = [(int(m.group(1)), p) for p in (ROOT / "data").glob("upstream_sources_AN_v*.json")
         if (m := re.search(r"_AN_v(\d+)\.json$", p.name))]
    return max(c)[1] if c else None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", help="write current fingerprints as a NEW pins file (refuses to overwrite)")
    ap.add_argument("--report", default="build/upstream_report_AN_v1.md")
    ap.add_argument("--json", default="build/upstream_check_AN_v1.json")
    a = ap.parse_args(argv)
    now = fingerprints()
    if a.baseline:
        p = Path(a.baseline)
        if p.exists():
            sys.exit(f"refusing to overwrite {p}")
        pins = {"created": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                "note": "Fingerprints of upstream sources behind Paper B numbers; compared weekly by "
                        "scripts/check_upstream_AN_v1.py (.github/workflows/upstream_check_AN_v1.yml).",
                "urls": {**IPCC, "epa_ghgi_editions": EPA, "nass_census2022": NASS, "nclimdiv": NCEI,
                         "unfccc_crt_2026": UNFCCC, "gleam_release": GLEAM},
                "sources": {k: v.get("fingerprint") for k, v in now.items()}}
        p.write_text(json.dumps(pins, indent=2), encoding="utf-8")
        print("wrote", p, {k: v["status"] for k, v in now.items()})
        return 0
    pf = latest_pins()
    pins = json.loads(pf.read_text(encoding="utf-8"))["sources"]
    res, changed, unreach = {}, [], []
    for k, v in now.items():
        old = pins.get(k)
        if v["status"] != "ok":
            st = "unreachable"
            unreach.append(k)
        elif old is None:
            st = "unpinned"
            changed.append(k)
        else:
            st = "unchanged" if v["fingerprint"] == old else "CHANGED"
            if st == "CHANGED":
                changed.append(k)
        res[k] = {"status": st, "pinned": old, "now": v.get("fingerprint"), "error": v.get("error")}
    lines = [f"# Upstream source check ({dt.date.today().isoformat()})", "",
             f"Pins: `{pf.relative_to(ROOT).as_posix()}`. Changed: {', '.join(changed) or 'none'}. "
             f"Unreachable: {', '.join(unreach) or 'none'}.", "", "| source | status | pinned | now |", "|---|---|---|---|"]
    for k, r in res.items():
        lines.append(f"| {k} | {r['status']} | `{json.dumps(r['pinned'])[:120]}` | `{json.dumps(r['now'] or r['error'])[:120]}` |")
    lines += ["", "If a source CHANGED: run `python scripts/recompute_all_AN_v1.py --profile full` on Bubble with the new",
              "upstream data, then `python scripts/diff_results_AN_v1.py OLD NEW` to see which paper numbers moved, and",
              "pin the new fingerprints with `--baseline data/upstream_sources_AN_v<next>.json`."]
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path(a.json).write_text(json.dumps({"changed": changed, "unreachable": unreach, "results": res}, indent=2), encoding="utf-8")
    print("\n".join(lines))
    return 2 if changed else (3 if unreach else 0)


if __name__ == "__main__":
    sys.exit(main())