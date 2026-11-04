# DECISIONS_AN_v13 — GLEAM v0.8.0-alpha as an outside consistency check

Date: 2026-11-03. Author: Alex Neumann. Follows docs/GLEAM_PIN_AN_v1.md.

## Install (PENV, no admin, D: only)
- R 4.6.2 per-user at D:\R\R-4.6.2 (`/VERYSILENT /CURRENTUSER`); installer SHA-256 B0B0053BAA1963B6D8A28C9642D50107EF9CE2F41C8B9A90E952846C8918B38A.
- FAO gleam 0.8.0 from the GitHub codeload tarball of tag v0.8.0-alpha = commit b0937d2, unmodified, into D:\R\library_AN_v1. Tarball SHA-256 2b0bf605dc46d0e04a552a033a025e9db787c06c2582cb7007fbd293aa2d8d75. RemoteSha is null (tarball install, not r-universe); the commit is pinned via tarball hash in the manifest.
- Dependencies: data.table 1.18.6.1, cli 3.6.6, and rlang 1.3.0 — rlang is needed at runtime but not declared in gleam's DESCRIPTION.
- Rtools not needed (gleam is pure R).

## Licence boundary
- gleam is AGPL-3. No gleam code is copied into ghgsim. scripts/run_gleam_stylized_AN_v1.R is our own Apache-2.0 driver calling only exported gleam functions; the Python adapter maps ghgsim inputs to gleam's input tables.

## Mapping assumptions
- Scope: the 9 cattle farms (dairy, beef_cowcalf). Swine and poultry not run (no ration inputs in the stylized spec).
- Cohorts: dairy_cow, beef_cow -> FA; dairy_heifer, dairy_calf, beef_calf -> FS. Each class is its own herd_id; gleam requires 6 cohort rows per herd, so the other 5 are copies flagged mapped=0 and discarded.
- dairy_calf -> FS means gleam applies its own Ym = 9.75 - 0.05*DE% rather than ghgsim's fixed calf Ym; juvenile cohorts (Ym=0) are not used.
- Intake = GE/18.45; dig = DE/100; UE 0.02/0.04 as in ghgsim; ash = ASH%/100; Nex/365 per head per day.
- MMS factors are taken from ghgsim's registry (data/ipcc_params_AN_v10.csv), MCF x100. Gleam has no cover input, so covers are ignored (covered/uncovered farms give identical gleam results).
- 2006 other-cattle liquid FracGas is unpublished; 0 is passed so gleam runs, and that manure N2O is reported blank.
- Manure N2O compared = gleam other-MMS total; pasture (PRP) N2O reported separately because ghgsim books PRP N2O under soil.

## Interpretation
- Consistency checks, not validation. Manure CH4 and N2O agree to 1.000 because VS equation and factors are shared — this is an implementation check only. Enteric differs through gleam's own Ym (ratio 0.87–1.07).
