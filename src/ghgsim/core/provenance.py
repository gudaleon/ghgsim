"""APSIM-style run identity: log release number and commit hash on every run.

Holzworth et al. (2018) require that every simulation record the exact
software version used. ghgsim follows that practice: every run writes
``release_number`` (package version) and ``commit_hash`` (git SHA).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ghgsim import __version__
from ghgsim.core.manifest import get_git_info

HOLZWORTH_2018 = (
    "Holzworth, D. P., Huth, N. I., Fainges, J., Brown, H., Zurcher, E., "
    "Cichota, R., Verrall, S., Herrmann, N. I., Zheng, B., & Snow, V. O. (2018). "
    "APSIM Next Generation: Overcoming challenges in modernising a farming systems model. "
    "Environmental Modelling & Software, 103, 43–51. "
    "https://doi.org/10.1016/j.envsoft.2018.02.002"
)


def run_identity(repo_path: Path | None = None) -> dict[str, Any]:
    """Return release number and commit hash for this run (Holzworth 2018)."""
    git = get_git_info(repo_path)
    return {
        "release_number": __version__,
        "commit_hash": git.commit_sha if git else None,
        "git_branch": git.branch if git else None,
        "git_dirty": git.is_dirty if git else None,
        "remote_url": git.remote_url if git else None,
        "apsim_requirement": HOLZWORTH_2018,
    }
