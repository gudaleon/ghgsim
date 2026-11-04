"""Stage and deploy the Paper B dashboard as a PRIVATE *static* Hugging Face Space (AN v1).

Free alternative to deploy_space_AN_v2.py (Gradio SDK Spaces on cpu-basic now need HF PRO).
The page dashboard/static_AN_v1/index.html runs dashboard/app_AN_v2.py in the visitor's browser
with Gradio-Lite (Pyodide). This script zips the app, src/, data/, results/, scripts/, agent/*.py,
the newest docs/BUBBLE_SETUP doc and the example farms into bundle.zip next to index.html.

Stage only:  python scripts/deploy_static_space_AN_v1.py --stage-only --stage DIR
Deploy (token from HF_TOKEN or `hf auth login`; never printed):
    python scripts/deploy_static_space_AN_v1.py --repo globaltrotter/paperB-living-dashboard
Creates the Space with space_sdk="static", private=True, and aborts before upload unless the Hub
reports it private. Re-running uploads a new commit to an existing private Space of that name.
No Space secrets or LLM keys are used.
"""
from __future__ import annotations

import argparse, pathlib, re, shutil, subprocess, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP = {"__pycache__"}
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


def _add_tree(z: zipfile.ZipFile, folder: pathlib.Path, arc: str) -> None:
    for f in sorted(folder.rglob("*")):
        if f.is_file() and not SKIP & set(f.parts) and f.suffix != ".pyc":
            z.write(f, f"{arc}/{f.relative_to(folder).as_posix()}")


def stage(dest: pathlib.Path, commit: str) -> pathlib.Path:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    shutil.copy2(ROOT / "dashboard" / "static_AN_v1" / "index.html", dest / "index.html")
    (dest / "README.md").write_text(README.format(commit=commit[:7]), encoding="utf-8")
    with zipfile.ZipFile(dest / "bundle.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.write(ROOT / "dashboard" / "app_AN_v2.py", "app_AN_v2.py")
        for d in ("src", "data", "results", "scripts"):
            _add_tree(z, ROOT / d, d)
        for f in sorted((ROOT / "agent").glob("*.py")):
            z.write(f, f"agent/{f.name}")
        bubble = max((ROOT / "docs").glob("BUBBLE_SETUP_AN_v*.md"), key=_ver)
        z.write(bubble, f"docs/{bubble.name}")
        _add_tree(z, ROOT / "legacy" / "livingghg_AN_v3" / "examples", "legacy/livingghg_AN_v3/examples")
        z.writestr("COMMIT", commit + "\n")
    return dest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default="globaltrotter/paperB-living-dashboard")
    ap.add_argument("--stage", default="C:/ghgsim-data/static_space_stage_AN_v1")
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
                      commit_message=f"Deploy static dashboard AN_v1 at {commit[:7]}")
    print("uploaded; private =", api.space_info(a.repo).private, "url = https://huggingface.co/spaces/" + a.repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
