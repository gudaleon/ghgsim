# Paper B paper agent (AN_v1)

An MCP (Model Context Protocol) server that turns Paper B's code and data into tools an AI assistant can call,
following the Paper2Agent idea (Miao et al. 2026, *Nature*, doi:10.1038/s41586-026-11044-y). MCP is an open
standard that lets an assistant (Claude Desktop, Cursor, VS Code, ...) call outside tools.

**Rule:** every number comes from ghgsim (a live run) or a committed repo file. Each answer has a `source` block
with the files used and their SHA-256. The server has no language model and makes up nothing.

## Files

| File | What |
|---|---|
| `paper_agent_AN_v1.py` | the MCP server (official `mcp` Python SDK 2.x, `MCPServer`) |
| `paper_agent_tools_AN_v1.py` | the plain functions behind the tools; also used by `dashboard/app_AN_v2.py` ("Ask the paper" tab) |
| `record_session_AN_v1.py` | starts the server over stdio and calls the tools through the MCP client |
| `example_session_AN_v1.md` | transcript made by that script (real tool outputs) |
| `../tests/test_paper_agent_AN_v1.py` | tests (incl. live runs reproduce `data/ipcc_2006_vs_2019_stylized_AN_v2.csv`) |

## Tools

| Tool | Answers from |
|---|---|
| `list_farms`, `list_parameter_files`, `list_manifests` | `data/stylized_farms_AN_v6.yaml`, `data/ipcc_params_AN_v*.csv`, `results/*.json` |
| `run_farm(farm_id, guideline, params_file, param_overrides, climate_zone_2019, storage_months)` | live ghgsim IPCC 2006 / 2019 modules via `scripts/compare_ipcc_2006_2019_stylized_AN_v2.py` |
| `committed_farm_result(farm_id)` | `data/ipcc_2006_vs_2019_stylized_AN_v2.csv` |
| `county_results(fips or state, variant, by)` | `data/us_county_2006_vs_2019_AN_v2.csv.gz` |
| `county_climate_zone(fips)` | `data/county_climate_zones_AN_v1.csv` |
| `explain_parameter(key)` | parameter registry: value, units, IPCC table, equation, page, source, history across versions |
| `provenance(manifest, number_prefix)` | `results/results_manifest_AN_vN.json` |
| `diff_manifests(old, new)` | `scripts/diff_results_AN_v1.py` |

Overrides are what-ifs: the answer lists the published value next to the one used.

## Install

```
cd C:\ghgsim
.venv\Scripts\pip install -e .[agent]      # mcp>=2.3,<3 ; Python 3.10+
```

## Connect

**Claude Desktop / Cursor / VS Code (stdio).** Add to the client's MCP config (`claude_desktop_config.json`,
`.cursor/mcp.json`, ...):

```json
{
  "mcpServers": {
    "ghgsim-paper-b": {
      "command": "C:\\ghgsim\\.venv\\Scripts\\python.exe",
      "args": ["C:\\ghgsim\\agent\\paper_agent_AN_v1.py"]
    }
  }
}
```

**HTTP (streamable-http):** `python agent/paper_agent_AN_v1.py --http --port 8765`, then point the client at
`http://127.0.0.1:8765/mcp`.

**Inspector:** `npx @modelcontextprotocol/inspector C:\ghgsim\.venv\Scripts\python.exe agent\paper_agent_AN_v1.py`.

**No assistant:** the dashboard's "Ask the paper" tab (`python dashboard/app_AN_v2.py`) calls the same functions.

## Reproduce the transcript

```
python agent/record_session_AN_v1.py --out agent/example_session_AN_v2.md   # refuses to overwrite
python -m pytest tests/test_paper_agent_AN_v1.py -q
```

Set `GHGSIM_ROOT` if the agent folder is moved out of the repo.
