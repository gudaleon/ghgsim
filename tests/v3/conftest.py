"""
Pytest configuration for v3 compatibility tests.

This ensures that the legacy livingghg package is properly set up
before running any tests by adding the legacy directory to sys.path.
"""

import sys
from pathlib import Path

# Go from tests/v3/conftest.py -> tests/v3 -> tests -> workspace root
legacy_root = Path(__file__).parents[2] / "legacy" / "livingghg_AN_v3"

if str(legacy_root) not in sys.path:
    sys.path.insert(0, str(legacy_root))

# Force import of livingghg to ensure it's available for all tests
try:
    import livingghg
except ImportError as e:
    raise ImportError(
        f"Failed to import livingghg from {legacy_root}. "
        f"Ensure legacy/livingghg_AN_v3/livingghg exists."
    ) from e
