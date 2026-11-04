"""Write data/inventories_AN_v2/run_manifest_AN_v3.json: run_manifest_AN_v2.json plus UNFCCC document URLs
for the Russian Federation and European Union extra comparisons (doc was null in v2).

URLs and listed sizes are from https://unfccc.int/ghg-inventories-annex-i-parties/2026 and the document
pages, read 2026-11-03. Each listing shows one CRT for the Party; the local zip size is checked against the
listed MB size (the UNFCCC page does not publish a hash). Never overwrites.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "inventories_AN_v2" / "run_manifest_AN_v2.json"
OUT = ROOT / "data" / "inventories_AN_v2" / "run_manifest_AN_v3.json"
LISTING = "https://unfccc.int/ghg-inventories-annex-i-parties/2026"
DOCS = {
    "RUS": {"doc": "https://unfccc.int/documents/659495", "nid": "https://unfccc.int/documents/659493",
            "nid_annex": "https://unfccc.int/documents/659494", "crt_submitted": "2026-06-25",
            "crt_published": "2026-06-26", "listed_size_MB": 39.50},
    "EUA": {"doc": "https://unfccc.int/documents/656557", "nid": "https://unfccc.int/documents/656551",
            "nid_annex": "https://unfccc.int/documents/656553", "crt_submitted": "2026-04-15",
            "crt_published": "2026-04-17", "listed_size_MB": 20.71},
}


def build() -> list[dict]:
    man = json.loads(SRC.read_text(encoding="utf-8"))
    for e in man:
        d = DOCS.get(e["iso"])
        if not d:
            continue
        mib = round(e["zip_bytes"] / 2**20, 2)
        if mib != d["listed_size_MB"]:
            raise SystemExit(f"{e['iso']}: local zip {mib} MB != UNFCCC listed {d['listed_size_MB']} MB")
        e.update(d)
        e["listing"] = LISTING
        e["size_check"] = f"local zip {e['zip_bytes']} bytes = {mib} MB matches UNFCCC listing"
    return man


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"{OUT} exists; bump the version")
    OUT.write_text(json.dumps(build(), indent=2), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
