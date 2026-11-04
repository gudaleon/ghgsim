# DECISIONS AN_v22 (2026-11-04)

D22.1 GLEAM rerun against the corrected ghgsim EF4. `scripts/run_gleam_stylized_AN_v3.py` wraps AN_v2 unchanged
(same unmodified GLEAM v0.8.0-alpha commit b0937d2, same R driver) and passes GLEAM, for IPCC2019 managed manure,
the EF4 ghgsim's ipcc2019.manure 2.1.0 applies (`_ef4`, warm_temperate_moist -> wet, 0.014; DECISIONS_AN_v21).
Reference: data/ipcc_2006_vs_2019_stylized_AN_v3.csv. Result: GLEAM 2019 managed-manure N2O equals ghgsim
(ratio 1.000; dairy 204.3 kg, beef cow-calf 95.2 kg); manure CH4 and pasture N2O (164.1 kg) unchanged and equal;
enteric CH4 unchanged (GLEAM Ym/GE differences). 2006 rows unchanged. Consistency check, not validation.

D22.2 docs/HESTIA_MATCHED_AN_v4.md corrects "3-44%" to "0-44%" (turkeys and breeding swine unchanged). AN_v3 kept.

D22.3 HESTIA version cited in the paper: HESTIA Community Edition 7.1.0 container with hestia-earth-models 0.90.0,
which is what ran (manifest data/hestia_matched_manifest_AN_v3.json). The draft no longer cites Engine Models v0.93.3.
