# Liang dry-county fallback – AN_v2

Supersedes `LIANG_DRY_FALLBACK_AN_v1.md` (kept). When a county is dry (P < PE) and FR_Topo is unavailable, Holos/Liang EF1 cannot be computed and soil N2O falls back to an IPCC EF1.

| `dry_fallback_ef1` | EF1 | Status | Source |
|---|---|---|---|
| `ipcc_default` (default) | 0.01 | fallback-IPCC-default | 2006 Vol 4 Ch 11 Table 11.1 |
| `ipcc2019_dry` (sensitivity) | 0.005 | fallback-IPCC2019-dry | 2019 Refinement Vol 4 Ch 11 Table 11.1 (Updated), dry climate (registry key IPCC2019.EF1.dry) |

Any other value raises ValueError. Wet counties and counties with FR_Topo are unaffected. Test: `tests/test_crops_soils.py::test_liang_dry_fallback_ef1_sensitivity_0005`.
