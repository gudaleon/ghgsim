"""Paper B paper agent: MCP server exposing ghgsim as tools (AN_v1).

Inspired by Paper2Agent (Miao et al. 2026, Nature, doi:10.1038/s41586-026-11044-y).
Any MCP client (Claude Desktop, Cursor, VS Code, MCP Inspector) can connect and ask
questions about Paper B; every number comes from ghgsim or committed repo data via
agent/paper_agent_tools_AN_v1.py. The server never generates numbers itself.

Run (stdio):            python agent/paper_agent_AN_v1.py
Run (streamable HTTP):  python agent/paper_agent_AN_v1.py --http --port 8765
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper_agent_tools_AN_v1 as T  # noqa: E402
from mcp.server.mcpserver import MCPServer  # noqa: E402

INSTRUCTIONS = (
    "Tools for Paper B (living papers for agricultural GHG models, US-centred). "
    "Answer only with numbers returned by these tools and cite the 'source' block they return. "
    "Comparisons with EPA or field data are consistency checks, not validation. "
    "Results with param_overrides are user what-ifs, not Paper B numbers."
)
mcp = MCPServer(name="ghgsim-paper-b", instructions=INSTRUCTIONS, version="AN_v1")


@mcp.tool()
def list_farms() -> dict:
    """List the stylized farms (data/stylized_farms_AN_v6.yaml) that run_farm can simulate."""
    return T.list_farms()


@mcp.tool()
def list_parameter_files() -> list[str]:
    """List the versioned IPCC parameter registries (data/ipcc_params_AN_v*.csv)."""
    return T.list_parameter_files()


@mcp.tool()
def run_farm(farm_id: str, guideline: str = "both", params_file: str = "latest",
             param_overrides: dict[str, float] | None = None,
             climate_zone_2019: str | None = None, storage_months: int | None = None) -> dict:
    """Run a stylized farm live in ghgsim under IPCC2006, IPCC2019 or both.

    param_overrides: registry key -> value (e.g. {"IPCC2006.EF1.all": 0.005}); the published value
    is reported next to the one used. climate_zone_2019 (e.g. "cool_temperate_moist") and
    storage_months change the 2019 manure MCF lookup (Table 10.17).
    """
    return T.run_farm(farm_id, guideline, params_file, param_overrides, climate_zone_2019, storage_months)


@mcp.tool()
def committed_farm_result(farm_id: str) -> dict:
    """The committed Paper B numbers for a stylized farm (data/ipcc_2006_vs_2019_stylized_AN_v2.csv)."""
    return T.committed_farm_result(farm_id)


@mcp.tool()
def county_results(fips: str | None = None, state: str | None = None, variant: str = "disclosed",
                   by: str = "source_gas") -> dict:
    """US county IPCC 2006 vs 2019 results from the committed full run. Pass a 5-digit FIPS or a
    2-letter state. variant: disclosed or D_allocated. by: source_gas, category or county."""
    return T.county_results(fips, state, variant, by)


@mcp.tool()
def county_climate_zone(fips: str) -> dict:
    """IPCC climate zone (2019 map, Hargreaves and Thornthwaite variants) and climate normals for a county."""
    return T.county_climate_zone(fips)


@mcp.tool()
def explain_parameter(key: str, params_file: str = "latest", history: bool = True) -> dict:
    """Value, units, IPCC table, equation, page and source for a parameter key (exact or substring),
    plus its value in every registry version."""
    return T.explain_parameter(key, params_file, history)


@mcp.tool()
def list_manifests() -> list[str]:
    """List the committed results manifests (results/*.json)."""
    return T.list_manifests()


@mcp.tool()
def provenance(manifest: str = "latest", number_prefix: str | None = None) -> dict:
    """Provenance of a results manifest: commit, parameter file, upstream pins, which outputs
    reproduced, and paper numbers (optionally filtered by key prefix, e.g. "us_county")."""
    return T.provenance(manifest, number_prefix)


@mcp.tool()
def diff_manifests(old: str, new: str, tol: float = 0.005) -> dict:
    """Which Paper B numbers moved between two results manifests, and why (scripts/diff_results_AN_v1.py)."""
    return T.diff_manifests(old, new, tol)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--http", action="store_true")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args(argv)
    if a.http:
        mcp.run(transport="streamable-http", port=a.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
