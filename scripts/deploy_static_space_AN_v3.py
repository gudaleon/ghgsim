"""Stage and deploy the Paper B dashboard as a PRIVATE *static* Hugging Face Space (AN v1).

Free alternative to deploy_space_AN_v2.py (Gradio SDK Spaces on cpu-basic now need HF PRO).
The page dashboard/static_AN_v2/index.html runs dashboard/app_AN_v3.py in the visitor's browser
with Gradio-Lite (Pyodide). v3 bundles only the files the tabs read (bundle_files); this script zips src/, data/, results/, scripts/, agent/*.py,
the newest docs/BUBBLE_SETUP doc and the example farms into bundle.zip next to index.html.

Stage only:  python scripts/deploy_static_space_AN_v3.py --stage-only --stage DIR
Deploy (token from HF_TOKEN or `hf auth login`; never printed):
    python scripts/deploy_static_space_AN_v3.py --repo globaltrotter/paperB-living-dashboard
Creates the Space with space_sdk="static", private=True, and aborts before upload unless the Hub
reports it private. Re-running uploads a new commit to an existing private Space of that name.
No Space secrets or LLM keys are used.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
README = """---
title: Paper B living-paper dashboard
emoji: \U0001F33E
colorFrom: green
colorTo: blue
sdk: static
pinned: false
license: apache-2.0
---

Paper B living-paper dashboard (ghgsim commit {commit}). Static Gradio-Lite build: ghgsim runs in
the browser via Pyodide. PRIVATE until submission.
"""


def _ver(p: pathlib.Path) -> int:
    m = re.search(r"_AN_v(\d+)", p.name)
    return int(m.group(1)) if m else -1


def _tracked() -> set[pathlib.Path]:
    out = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"], text=True)
    return {(ROOT / p).resolve() for p in out.split("\0") if p}


# Files the dashboard tabs read (traced from app_AN_v2 + app_AN_v3 tab functions). Everything else,
# e.g. APSIM daily outputs, run folders, county weather and inventories, is left out.
DATA_GLOBS = ("ipcc_params_AN_v*.csv", "*manifest_AN_v*.json", "county_p_pe_may_oct_AN_v*.csv",
              "county_climate_zones_AN_v1.csv", "ipcc_2006_vs_2019_stylized_AN_v2.csv",
              "mms_north_america_ipcc2006_AN_v1.csv", "stylized_farms_AN_v6.yaml",
              "us_county_2006_vs_2019_AN_v2.csv.gz")
SCRIPTS_USED = ("diff_results_AN_v1.py", "compare_ipcc_2006_2019_stylized_AN_v2.py")
FINDINGS = range(4, 10)


def _manifest_files(manifest: pathlib.Path):
    """Repo files a data manifest lists with a sha256 (the Provenance tab re-hashes them)."""
    def walk(n):
        if isinstance(n, dict):
            if isinstance(n.get("sha256"), str):
                yield n.get("path") or n.get("name")
            for v in n.values():
                yield from walk(v)
        elif isinstance(n, list):
            for v in n:
                yield from walk(v)
    for rel in walk(json.loads(manifest.read_text(encoding="utf-8"))):
        if rel and (ROOT / rel).is_file():
            yield ROOT / rel


def bundle_files() -> dict[str, pathlib.Path]:
    """arcname -> source path for every file in bundle.zip (git-tracked only)."""
    tracked = _tracked()
    files: dict[str, pathlib.Path] = {}

    def add(p: pathlib.Path, arc: str | None = None):
        p = p.resolve()
        if p in tracked and p.is_file() and p.suffix != ".pyc" and "__pycache__" not in p.parts:
            files[arc or p.relative_to(ROOT.resolve()).as_posix()] = p

    for app in ("app_AN_v2.py", "app_AN_v3.py"):
        add(ROOT / "dashboard" / app, app)
    for f in (ROOT / "src").rglob("*"):
        add(f)
    for f in (ROOT / "agent").glob("*.py"):
        add(f)
    for g in DATA_GLOBS:
        for f in (ROOT / "data").glob(g):
            add(f)
            if "manifest" in f.name:
                for m in _manifest_files(f):
                    add(m)
    for f in (ROOT / "results").glob("*.json"):
        add(f)
    for s in SCRIPTS_USED:
        add(ROOT / "scripts" / s)
    add(max((ROOT / "docs").glob("BUBBLE_SETUP_AN_v*.md"), key=_ver))
    for v in FINDINGS:
        add(ROOT / "docs" / f"FINDINGS_AN_v{v}.md")
    spec = importlib.util.spec_from_file_location("app_AN_v3_figs", ROOT / "dashboard" / "app_AN_v3.py")
    a3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a3)
    for figs in a3.FIGS.values():
        for f in figs:
            add(ROOT / "docs" / "figures" / f)
    for f in (ROOT / "legacy" / "livingghg_AN_v3" / "examples").glob("example_farm_AN_v*.json"):
        add(f)
    return dict(sorted(files.items()))


def stage(dest: pathlib.Path, commit: str) -> pathlib.Path:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    shutil.copy2(ROOT / "dashboard" / "static_AN_v2" / "index.html", dest / "index.html")
    (dest / "README.md").write_text(README.format(commit=commit[:7]), encoding="utf-8")
    with zipfile.ZipFile(dest / "bundle.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for arc, src in bundle_files().items():
            z.write(src, arc)
        z.writestr("COMMIT", commit + "\n")
    return dest

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default="globaltrotter/paperB-living-dashboard")
    ap.add_argument("--stage", default="C:/ghgsim-data/static_space_stage_AN_v3")
    ap.add_argument("--commit", default=None)
    ap.add_argument("--stage-only", action="store_true")
    a = ap.parse_args(argv)
    commit = a.commit or subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    dest = stage(pathlib.Path(a.stage), commit)
    print(f"staged {dest} (bundle {(dest / 'bundle.zip').stat().st_size // 1024} KB, commit {commit[:7]})")
    if a.stage_only:
        return 0
    from huggingface_hub import HfApi
    api = HfApi()
    print("authenticated as", api.whoami()["name"])
    if api.repo_exists(a.repo, repo_type="space"):
        if not api.space_info(a.repo).private:
            sys.exit(f"ABORT: {a.repo} exists and is public; nothing uploaded.")
    else:
        api.create_repo(a.repo, repo_type="space", space_sdk="static", private=True)
    if not api.space_info(a.repo).private:
        sys.exit(f"ABORT: {a.repo} is not private; nothing uploaded.")
    api.upload_folder(folder_path=str(dest), repo_id=a.repo, repo_type="space",
                      commit_message=f"Deploy static dashboard AN_v3 at {commit[:7]}")
    print("uploaded; private =", api.space_info(a.repo).private, "url = https://huggingface.co/spaces/" + a.repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
