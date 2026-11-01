"""
Compatibility layer for livingghg v3.

This module redirects imports from 'livingghg' to 'legacy.livingghg_AN_v3.livingghg'
so that all v3 tests can run unchanged.
"""

import importlib
import sys
from pathlib import Path

_legacy_root = Path(__file__).parents[3] / "legacy" / "livingghg_AN_v3"

if str(_legacy_root) not in sys.path:
    sys.path.insert(0, str(_legacy_root))


def setup_v3_compat():
    """
    Set up import hooks to redirect 'livingghg' to legacy v3 code.
    """
    if "livingghg" not in sys.modules:
        try:
            legacy_livingghg = importlib.import_module("livingghg")
            sys.modules["livingghg"] = legacy_livingghg
        except ImportError as e:
            raise ImportError(
                f"Failed to import legacy livingghg from {_legacy_root}. "
                "Ensure legacy/livingghg_AN_v3/ exists and contains the livingghg package."
            ) from e
