"""Stage and deploy the Paper B dashboard (app_AN_v2, with "Ask the paper") as a PRIVATE HF Space (AN v2).

AN_v1 is unchanged. v2 fixes: ships dashboard/app_AN_v2.py (v1 shipped app_AN_v1), adds agent/,
scripts/ and results/ (read by the paper-agent tools), ships only the newest docs/BUBBLE_SETUP doc,
rewrites the README front matter for app_AN_v2.py, and picks a free Space name if the default is taken.

Stage only (no network):  python scripts/deploy_space_AN_v2.py --stage-only --stage DIR
Deploy (reads the token from HF_TOKEN or `hf auth login`; never prints it):
    python scripts/deploy_space_AN_v2.py --repo globaltrotter/paperB-living-dashboard
The Space is created with private=True; the script aborts before upload unless the Hub reports it
private. The "Ask the paper" tab calls ghgsim tools directly; no LLM and no Space secrets are needed.
"""
from __future__ import annotations

import argparse, pathlib, re, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = "app_AN_v2.py"
DEPS = ["numpy>=1.20", "pandas>=1.3", "scipy>=1.7", "pint>=0.20", "pyyaml>=6.0", "click>=8.0",
        "gradio>=5,<6", "plotly>=6"]


def _ver(p: pathlib.Path) -> int:
    m = re.search(r"_AN_v(\d+)", p.name)
    return int(m.group(1)) if m else -1


def stage(dest: pathlib.Path, commit: str) -> pathlib.Path:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    shutil.copy2(ROOT / "dashboard" / APP, dest / APP)
    readme = (ROOT / "dashboard" / "README.md").read_text(encoding="utf-8")
    readme = re.sub(r"(?m)^app_file:.*$", f"app_file: {APP}", readme)
    readme = re.sub(r"(?m)^emoji:.*$", "emoji: \U0001F33E", readme)
    (dest / "README.md").write_text(readme, encoding="utf-8")
    ign = shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info")
    for d in ("src", "data", "results", "scripts"):
        shutil.copytree(ROOT / d, dest / d, ignore=ign)
    (dest / "agent").mkdir()
    for f in (ROOT / "agent").glob("*.py"):
        shutil.copy2(f, dest / "agent" / f.name)
    (dest / "docs").mkdir()
    bubble = max((ROOT / "docs").glob("BUBBLE_SETUP_AN_v*.md"), key=_ver)
    shutil.copy2(bubble, dest / "docs" / bubble.name)
    ex = pathlib.Path("legacy") / "livingghg_AN_v3" / "examples"
    shutil.copytree(ROOT / ex, dest / ex, ignore=ign)
    for extra in ("LICENSE", "NOTICE"):
        if (ROOT / extra).exists():
            shutil.copy2(ROOT / extra, dest / extra)
    (dest / "requirements.txt").write_text("\n".join(DEPS) + "\n", encoding="utf-8")
    (dest / "COMMIT").write_text(commit + "\n", encoding="utf-8")
    return dest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default="globaltrotter/paperB-living-dashboard")
    ap.add_argument("--stage", default="C:/ghgsim-data/space_stage_AN_v2")
    ap.add_argument("--commit", default=None, help="commit SHA when ROOT is not a git checkout")
    ap.add_argument("--stage-only", action="store_true")
    a = ap.parse_args(argv)
    commit = a.commit or subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    dest = stage(pathlib.Path(a.stage), commit)
    print(f"staged {sum(1 for _ in dest.rglob('*') if _.is_file())} files at {dest} (commit {commit[:7]})")
    if a.stage_only:
        return 0
    from huggingface_hub import HfApi
    api = HfApi()
    print("authenticated as", api.whoami()["name"])
    repo, n = a.repo, 1
    while api.repo_exists(repo, repo_type="space"):
        n += 1
        repo = f"{a.repo}-{n}"
    api.create_repo(repo, repo_type="space", space_sdk="gradio", space_hardware="cpu-basic", private=True)
    if not api.space_info(repo).private:
        sys.exit(f"ABORT: {repo} is not private; nothing uploaded.")
    print("created PRIVATE space", repo)
    for k, v in {"GHGSIM_ROOT": "/home/user/app", "GHGSIM_COMMIT": commit, "GRADIO_SERVER_NAME": "0.0.0.0"}.items():
        api.add_space_variable(repo, k, v)
    api.upload_folder(folder_path=str(dest), repo_id=repo, repo_type="space",
                      commit_message=f"Deploy ghgsim dashboard AN_v2 at {commit[:7]}")
    print("uploaded; private =", api.space_info(repo).private, "url = https://huggingface.co/spaces/" + repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
