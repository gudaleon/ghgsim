# Decisions AN_v7 (2026-11-03) - CI green, GLEAM pin, paper agent

1. **Lint (ruff, `src/` and `tests/` as in CI):** 94 errors fixed. 70 by `ruff --fix --unsafe-fixes` (unused imports,
   import order, f-strings without placeholders, `Optional[X]` -> `X | None`, unused variables); the 19 left
   (E402 imports after `sys.path`/circular-import guards, B904, E702 one-liners in tests) got `# noqa` via
   `ruff --add-noqa` rather than code moves, because moving the E402 imports in the IPCC modules risks the
   known circular import. No logic changed.
2. **Licence check:** two false positives: sentences that say no GPL code was copied (`holos/liquid_tank.py` docstring,
   `holos/process_defs.py` notes). Fix in `scripts/check_licenses.py`: lines containing "no gpl code",
   "not a translation of the gpl" or "not copied from gpl" are compliance notes, not violations. Also forced UTF-8
   stdout (the emoji crashed on Windows cp1252). Source strings left untouched (they are in a recorded notes field).
3. **No numbers changed:** full Bubble recompute after the fixes (`build/ci_green_full.json`) vs
   `results/results_manifest_AN_v2.json`: 0 paper numbers moved, 121 unchanged; same output hashes; the only
   not-reproduced file is the known `params_file` label of the stylized CSV (DECISIONS_AN_v6 item 5). 275 tests pass, 3 skipped (incl. the new paper-agent tests).
4. **GLEAM pin:** tag `v0.8.0-alpha` is a lightweight tag on commit `b0937d2`; `90e4161` is the r-universe build of
   `main` (38 commits later, same `Version: 0.8.0`). Pin = `b0937d2`. Details: `docs/GLEAM_PIN_AN_v1.md`.
   Corrects DECISIONS_AN_v3 item 7.
5. **Paper agent:** MCP server with the official `mcp` SDK 2.3 (`MCPServer`; FastMCP was renamed in 2.x). Tool logic
   lives in `agent/paper_agent_tools_AN_v1.py` so the MCP server and the dashboard share one code path.
   `run_farm` reuses `scripts/compare_ipcc_2006_2019_stylized_AN_v2.py` (`run_version`) rather than a copy, so the
   agent cannot drift from the paper's script; a test checks that live runs equal the committed CSV.
6. `run_farm` default parameter file = latest (v10). The committed stylized CSV was made with v8; numbers are equal.
   Overrides go through `ParameterRegistry.add_overlay` and are reported with the published value.
   `climate_zone_2019`/`storage_months` temporarily set the script's module constants under a lock, restored after.
7. County tools read the committed full-run CSV (`variant` disclosed by default; `D_allocated` is the sensitivity).
8. Dashboard: new `dashboard/app_AN_v2.py` (v1 kept) with an "Ask the paper" tab calling the same functions; no LLM.
9. CI installs the new `agent` extra (`mcp>=2.3,<3`) so the MCP test runs; tests skip if `mcp` is absent.
