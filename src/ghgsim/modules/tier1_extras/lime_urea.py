"""Tier 1 CO2 from liming and urea for both guideline versions.

2006 Vol4 Ch11 Eq 11.12 / 11.13 (pp. 11.27, 11.32) via :class:`IPCC2006LimeUreaCO2`. The 2019 Refinement Vol4 Ch11
sections 11.3 (liming) and 11.4 (urea) read 'No refinement' (p. 11.27), so the same equations and EFs apply.
"""
from __future__ import annotations

import ghgsim.modules.holos  # noqa: F401  (load order: avoids the holos <-> ipcc2006 lime_urea import cycle)
from ghgsim.modules.ipcc2006.lime_urea import IPCC2006LimeUreaCO2

_MOD = IPCC2006LimeUreaCO2()


def lime_urea_co2_kg(p, limestone_t: float = 0.0, dolomite_t: float = 0.0, urea_t: float = 0.0) -> dict[str, float]:
    """kg CO2 from limestone, dolomite and urea (tonnes applied). Identical for ver '2006' and '2019'."""
    params = {k: p[ref.key] for k, ref in _MOD.parameters.items()}
    return _MOD.compute({"M_limestone_t": limestone_t, "M_dolomite_t": dolomite_t, "M_urea_t": urea_t}, params)
