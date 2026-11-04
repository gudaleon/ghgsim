# Benchmarks (AN v6): N2O vs N2O-N

Supersedes `BENCHMARKS_AN_v5.md` only on the unit question; everything else in v5 stands.

## Working assumption (2026-11-03)
Global N2O Database (EDI edi.877.1) daily `n2o` (and `n2osd`, `Annual.n2o`, `cumulative.n2o`)
are treated as **N2O-N** (mass of nitrogen). To compare with ghgsim N2O outputs (mass of N2O),
multiply by **44/28**.

## Evidence
- EDI EML: "measured nitrous oxide flux", unit gramsPerHectarePerDay; no N2O / N2O-N basis
  stated (unchanged from v5).
- The database's Field Data **upload template** (xlsx, supplied by Alex 2026-11-03) asks
  contributors for "N2O units: gN2O-N/m2-day", but also says "update units if necessary".
  So contributors were asked for N2O-N, but could deviate; the archived values were converted
  to g/ha/day by the database (per EML).
- Dorich et al. 2020, *COSUST* 47:13-20, doi:10.1016/j.cosust.2020.04.006 (PDF supplied by
  Alex) is the reference the EML points to.

## Status
- Inference, not confirmation. Alex emailed global_n2o_database@lists.colostate.edu asking
  whether values are N2O or N2O-N; no reply yet.
- If the reply says N2O, drop the 44/28 factor (decision #6 in `DECISIONS_AN_v3.md`) and
  write `BENCHMARKS_AN_v7.md`.
- Per-site checks: where a contributing study's paper reports units, compare a few site-years
  before any figure is finalised.
