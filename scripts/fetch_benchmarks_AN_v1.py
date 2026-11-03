#!/usr/bin/env python3
"""Fetch the open N2O benchmark datasets and verify SHA-256 checksums.

Usage:
    python scripts/fetch_benchmarks_AN_v1.py --dest C:/ghgsim-data/benchmarks            # download + verify against manifest
    python scripts/fetch_benchmarks_AN_v1.py --dest ... --write-manifest                # (re)build data/benchmarks_manifest_AN_v1.json

Sources (public, no login):
  * Global N2O Database v1.0, EDI edi.877.1, CC BY 4.0. File URLs are read from the EML
    at https://pasta.lternet.edu/package/metadata/eml/edi/877/1
  * GRACEnet, USDA Ag Data Commons (Figshare article 24660216), CC0. File URLs from
    https://api.figshare.com/v2/articles/24660216 ; Figshare MD5s are checked too.
Standard library only. Data files are NOT committed to the repo.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "benchmarks_manifest_AN_v1.json"
UA = {"User-Agent": "ghgsim-fetch-benchmarks/1"}

EDI = {
    "key": "global_n2o_edi877v1",
    "dataset": "Global N2O Database",
    "version": "1.0 (EDI package edi.877.1, revision 1)",
    "doi": "10.6073/pasta/09a95cf44cd7835db002b0089ed5ffc3",
    "licence": "CC BY 4.0",
    "citation": "Dorich, C.D., R.T. Conant, and D. Wang. 2021. Global N2O Database version 1.0 ver 1. "
                "Environmental Data Initiative. https://doi.org/10.6073/pasta/09a95cf44cd7835db002b0089ed5ffc3",
    "landing_page": "https://portal.edirepository.org/nis/mapbrowse?packageid=edi.877.1",
    "metadata_url": "https://pasta.lternet.edu/package/metadata/eml/edi/877/1",
}
FIG = {
    "key": "gracenet_adc1235557",
    "dataset": "GRACEnet (Greenhouse gas Reduction through Agricultural Carbon Enhancement network)",
    "figshare_article_id": 24660216,
    "doi": "10.15482/USDA.ADC/1235557",
    "licence": "CC0",
    "citation": "Del Grosso, S.J., et al. 2013. Introducing the GRACEnet/REAP Data Contribution, Discovery, "
                "and Retrieval System. J. Environ. Qual. 42:1274-1280. doi:10.2134/jeq2013.03.0097",
    "landing_page": "https://agdatacommons.nal.usda.gov/articles/dataset/GRACEnet_Greenhouse_gas_Reduction_through_Agricultural_Carbon_Enhancement_network_/24660216",
    "metadata_url": "https://api.figshare.com/v2/articles/24660216",
}


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def download(url: str, path: Path) -> tuple[int, str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    sha, md5, n = hashlib.sha256(), hashlib.md5(), 0
    tmp = path.with_suffix(path.suffix + ".part")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk); sha.update(chunk); md5.update(chunk); n += len(chunk)
    tmp.replace(path)
    return n, sha.hexdigest(), md5.hexdigest()


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def edi_files(dest: Path) -> list[dict]:
    eml = get(EDI["metadata_url"])
    (dest / "metadata").mkdir(parents=True, exist_ok=True)
    (dest / "metadata" / "edi.877.1_eml.xml").write_bytes(eml)
    root = ET.fromstring(eml)
    out = []
    for t in root.iter("dataTable"):
        name = t.findtext("physical/objectName") or t.findtext("entityName")
        url = t.findtext("physical/distribution/online/url")
        out.append({"name": name, "url": url.strip(),
                    "entity": t.findtext("entityName"),
                    "records": t.findtext("numberOfRecords")})
    for t in root.iter("otherEntity"):
        name = t.findtext("physical/objectName") or t.findtext("entityName")
        url = t.findtext("physical/distribution/online/url")
        out.append({"name": name, "url": url.strip(), "entity": t.findtext("entityName"), "records": None})
    return out


def fig_files(dest: Path) -> tuple[list[dict], dict]:
    meta = json.loads(get(FIG["metadata_url"]))
    (dest / "metadata").mkdir(parents=True, exist_ok=True)
    (dest / "metadata" / "figshare_24660216.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    files = [{"name": f["name"], "url": f["download_url"], "md5": f.get("computed_md5") or f.get("supplied_md5")}
             for f in meta["files"]]
    return files, meta


def run(dest: Path, write_manifest: bool) -> int:
    today = dt.date.today().isoformat()
    expected = {}
    if MANIFEST.exists() and not write_manifest:
        for d in json.loads(MANIFEST.read_text(encoding="utf-8"))["datasets"]:
            for f in d["files"]:
                expected[(d["key"], f["name"])] = f["sha256"]
    datasets, bad = [], 0

    edest = dest / EDI["key"]
    efiles, edi_status = [], "downloaded"
    try:
        for f in edi_files(edest):
            n, sha, _ = download(f["url"], edest / f["name"])
            efiles.append({"name": f["name"], "entity": f["entity"], "records_eml": f["records"],
                           "size_bytes": n, "sha256": sha, "url": f["url"]})
    except urllib.error.HTTPError as e:
        # Since 2026 EDI/PASTA refuses anonymous API reads (403 "Public Access ... not authorized")
        # and the portal sits behind a login + Cloudflare Turnstile check. Download the package by
        # hand from the landing page into <dest>/global_n2o_edi877v1/ and rerun; files found
        # there are hashed instead.
        print(f"EDI API refused anonymous access ({e.code}). Manual download needed: {EDI['landing_page']}",
              file=sys.stderr)
        edi_status = f"api_http_{e.code}; manual download required"
        for path in sorted(p for p in edest.rglob("*") if p.is_file() and "metadata" not in p.parts):
            efiles.append({"name": str(path.relative_to(edest)).replace("\\", "/"),
                           "size_bytes": path.stat().st_size, "sha256": hash_file(path), "url": None})
        if efiles:
            edi_status = "manual download, hashed locally"
    datasets.append({**EDI, "status": edi_status, "download_date": today if efiles else None,
                     "files": efiles, "metadata_files": ["metadata/edi.877.1_eml.xml"] if edi_status == "downloaded" else []})

    gdest = dest / FIG["key"]
    gf, meta = fig_files(gdest)
    gfiles = []
    for f in gf:
        n, sha, md5 = download(f["url"], gdest / f["name"])
        ok = (f["md5"] is None) or (md5 == f["md5"])
        if not ok:
            bad += 1
            print(f"MD5 MISMATCH {f['name']}", file=sys.stderr)
        gfiles.append({"name": f["name"], "size_bytes": n, "sha256": sha, "figshare_md5": f["md5"],
                       "md5_ok": ok, "url": f["url"]})
    datasets.append({**FIG, "figshare_version": meta.get("version"),
                     "figshare_published_date": meta.get("published_date"),
                     "download_date": today, "files": gfiles,
                     "metadata_files": ["metadata/figshare_24660216.json"]})

    for d in datasets:
        for f in d["files"]:
            e = expected.get((d["key"], f["name"]))
            if e and e != f["sha256"]:
                bad += 1
                print(f"SHA256 MISMATCH {d['key']}/{f['name']}", file=sys.stderr)
        print(f"{d['key']}: {len(d['files'])} files, {sum(f['size_bytes'] for f in d['files'])/1e6:.1f} MB")

    if write_manifest:
        MANIFEST.write_text(json.dumps({"manifest": "benchmarks_manifest_AN_v1", "datasets": datasets},
                                       indent=2) + "\n", encoding="utf-8")
        print(f"wrote {MANIFEST}")
    print("checksums OK" if bad == 0 else f"{bad} checksum problems")
    return 1 if bad else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, default=Path("C:/ghgsim-data/benchmarks"))
    ap.add_argument("--write-manifest", action="store_true")
    a = ap.parse_args()
    sys.exit(run(a.dest, a.write_manifest))
