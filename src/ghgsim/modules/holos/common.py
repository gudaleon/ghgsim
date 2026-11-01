"""Shared helpers for Holos Route A modules (no GPL code)."""

from collections.abc import Mapping
from typing import Any

from ghgsim.modules.holos.forks import resolve_option

# Molecular weight conversion N2O-N -> N2O. IPCC 2006 Vol 4 Ch 10 Eq 10.25.
N2ON_TO_N2O = 44.0 / 28.0

# IPCC 2006 Vol 4 Ch 10 p. 10.54: high-digestibility exception is DE% > ~80.
IPCC_DE_HIGH_THRESHOLD_PERCENT = 80.0

# Holos-as-coded grain threshold for the UE switch (SOURCE-TRACED; not IPCC).
HOLOS_UE_GRAIN_THRESHOLD_PERCENT = 85.0


def forks_from_inputs(inputs: Mapping[str, Any]) -> dict[str, str]:
    """Extract fork_id -> option from module inputs (empty if omitted)."""
    raw = inputs.get("forks")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("inputs['forks'] must be a dict of fork_id -> option")
    return {str(k): str(v) for k, v in raw.items()}


def option_is(fork_id: str, expected: str, fork_settings: dict[str, str] | None) -> bool:
    """True if the resolved option for fork_id equals expected."""
    return resolve_option(fork_id, fork_settings) == expected
