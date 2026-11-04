"""Record an example paper-agent session by calling the MCP server over stdio (AN_v1).

python agent/record_session_AN_v1.py --out agent/example_session_AN_v1.md   (refuses to overwrite)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
CALLS = [
    ("What farms can I run?", "list_farms", {}),
    ("Run the forage dairy farm under both guidelines (parameter file used for the committed Paper B CSV).",
     "run_farm", {"farm_id": "dairy_forage_uncovered", "params_file": "ipcc_params_AN_v8.csv"}),
    ("Do those match the committed Paper B numbers?", "committed_farm_result", {"farm_id": "dairy_forage_uncovered"}),
    ("What if storage were 6 months instead of 12 (Table 10.17 fn 1 default)?", "run_farm",
     {"farm_id": "dairy_forage_uncovered", "guideline": "IPCC2019", "storage_months": 6}),
    ("Where does EF1 come from?", "explain_parameter", {"key": "IPCC2006.EF1.all"}),
    ("What-if: EF1 = 0.005 on the crop farm.", "run_farm",
     {"farm_id": "__FIELD_FARM__", "guideline": "IPCC2006", "param_overrides": {"IPCC2006.EF1.all": 0.005}}),
    ("Fresno County: climate zone?", "county_climate_zone", {"fips": "06019"}),
    ("Fresno County: 2006 vs 2019 by source.", "county_results", {"fips": "06019"}),
    ("Iowa totals.", "county_results", {"state": "IA"}),
    ("Provenance of the latest results manifest (US county numbers).", "provenance", {"number_prefix": "us_county"}),
    ("What moved between results manifest v1 and v2?", "diff_manifests",
     {"old": "results_manifest_AN_v1.json", "new": "results_manifest_AN_v2.json"}),
]


def _parse(content):
    out = []
    for c in content:
        try:
            out.append(json.loads(c.text))
        except (ValueError, AttributeError):
            out.append(getattr(c, "text", str(c)))
    return out[0] if len(out) == 1 else out


def _short(obj, n=3500):
    s = json.dumps(obj, indent=1, default=str)
    return s if len(s) <= n else s[:n] + f"\n... [{len(s) - n} more characters truncated in this transcript only]"


async def main(out: Path) -> None:
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "paper_agent_AN_v1.py")])
    L = ["# Paper B paper agent: example session (AN_v1)", "",
         "Produced by `agent/record_session_AN_v1.py`, which starts `agent/paper_agent_AN_v1.py` as an MCP",
         "stdio server and calls its tools through the official `mcp` client. Outputs are verbatim tool",
         "results (long ones truncated here only). No language model was involved in producing the numbers.", ""]
    async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        tools = await s.list_tools()
        L += ["## Tools advertised", ""] + [f"- `{t.name}`: {(t.description or '').splitlines()[0]}" for t in tools.tools] + [""]
        field_farm = None
        for q, name, args in CALLS:
            if args.get("farm_id") == "__FIELD_FARM__":
                args = {**args, "farm_id": field_farm}
            res = await s.call_tool(name, args)
            data = res.structured_content if res.structured_content is not None else _parse(res.content)
            if name == "list_farms":
                d = data.get("result", data)
                field_farm = next(f["farm_id"] for f in d["farms"] if f["field_id"])
            L += [f"## Q: {q}", "", f"`{name}({json.dumps(args)})`" + (" -> ERROR" if res.is_error else ""), "",
                  "```json", _short(data), "```", ""]
    out.write_text("\n".join(L), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "example_session_AN_v1.md"))
    o = Path(ap.parse_args().out)
    if o.exists():
        sys.exit(f"refusing to overwrite {o}")
    asyncio.run(main(o))
