"""APSIM-style run identity (Holzworth et al. 2018 EMS 103:43-51)."""

from ghgsim import __version__
from ghgsim.core.provenance import HOLZWORTH_2018, run_identity


def test_run_identity_logs_release_and_commit():
    identity = run_identity()
    assert identity["release_number"] == __version__
    assert identity["commit_hash"]
    assert len(identity["commit_hash"]) == 40
    assert "Holzworth" in HOLZWORTH_2018
    assert "103" in HOLZWORTH_2018
    assert "43" in HOLZWORTH_2018
    assert "10.1016/j.envsoft.2018.02.002" in identity["apsim_requirement"]
