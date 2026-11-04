"""Stage and deploy the Paper B dashboard as a PRIVATE Hugging Face Space (AN v1).

Stage only (no network):  python scripts/deploy_space_AN_v1.py --stage-only
Deploy (needs `hf auth login` with a write token for the owner account, typed by the user):
    python scripts/deploy_space_AN_v1.py --repo globaltrotter/ghgsim-paperb-dashboard

The Space is created with private=True and the script aborts unless the Hub reports it
private before anything is uploaded. It never reads or prints the token.
Bundle: dashboard app at the Space root, src/, data/, docs/, legacy/livingghg_AN_v3/examples,
requirements.txt (ghgsim runtime deps + dashboard deps). Space variables: GHGSIM_ROOT=. (as
/home/user/app), GHGSIM_COMMIT=<HEAD sha>, GRADIO_SERVER_NAME=0.0.0.0.
"""
from __future__ import annotations

import argparse, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEPS = ["numpy>=1.20", "pandas>=1.3", "scipy>=1.7", "pint>=0.20", "pyyaml>=6.0", "click>=8.0",
        "gradio>=5,<6", "plotly>=6"]


def stage(dest: pathlib.Path, commit: str) -> pathlib.Path:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    shutil.copy2(ROOT / "dashboard" / "app_AN_v1.py", dest / "app_AN_v1.py")
    shutil.copy2(ROOT / "dashboard" / "README.md", dest / "README.md")
    ign = shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info")
    shutil.copytree(ROOT / "src", dest / "src", ignore=ign)
    shutil.copytree(ROOT / "data", dest / "data", ignore=ign)
    shutil.copytree(ROOT / "docs", dest / "docs", ignore=ign)
    shutil.copytree(ROOT / "legacy" / "livingghg_AN_v3" / "examples", dest / "legacy" / "livingghg_AN_v3" / "examples", ignore=ign)
    for extra in ("LICENSE", "NOTICE"):
        if (ROOT / extra).exists():
            shutil.copy2(ROOT / extra, dest / extra)
    (dest / "requirements.txt").write_text("\n".join(DEPS) + "\n", encoding="utf-8")
    (dest / "COMMIT").write_text(commit + "\n", encoding="utf-8")
    return dest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default="globaltrotter/ghgsim-paperb-dashboard")
    ap.add_argument("--stage", default="C:/ghgsim-data/space_stage_AN_v1")
    ap.add_argument("--stage-only", action="store_true")
    a = ap.parse_args(argv)
    commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    dest = stage(pathlib.Path(a.stage), commit)
    print(f"staged {sum(1 for _ in dest.rglob('*') if _.is_file())} files at {dest} (commit {commit[:7]})")
    if a.stage_only:
        return 0
    from huggingface_hub import HfApi
    api = HfApi()
    print("authenticated as", api.whoami()["name"])
    if api.repo_exists(a.repo, repo_type="space"):
        sys.exit(f"{a.repo} already exists; refusing to reuse it (check its privacy by hand).")
    api.create_repo(a.repo, repo_type="space", space_sdk="gradio", private=True)
    info = api.space_info(a.repo)
    if not info.private:
        sys.exit(f"ABORT: {a.repo} is not private; nothing uploaded. Fix visibility first.")
    print("created PRIVATE space", a.repo)
    for k, v in {"GHGSIM_ROOT": "/home/user/app", "GHGSIM_COMMIT": commit, "GRADIO_SERVER_NAME": "0.0.0.0"}.items():
        api.add_space_variable(a.repo, k, v)
    api.upload_folder(folder_path=str(dest), repo_id=a.repo, repo_type="space",
                      commit_message=f"Deploy ghgsim dashboard AN_v1 at {commit[:7]}")
    print("uploaded; private =", api.space_info(a.repo).private, "url = https://huggingface.co/spaces/" + a.repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
