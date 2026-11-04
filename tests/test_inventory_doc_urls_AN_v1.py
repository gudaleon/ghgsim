import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fill", ROOT / "scripts" / "fill_inventory_doc_urls_AN_v1.py")
fill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fill)


def test_manifest_v3_matches_build_and_has_all_docs():
    committed = json.loads((ROOT / "data/inventories_AN_v2/run_manifest_AN_v3.json").read_text(encoding="utf-8"))
    assert committed == fill.build()
    assert all(e["doc"] and e["doc"].startswith("https://unfccc.int/documents/") for e in committed)
