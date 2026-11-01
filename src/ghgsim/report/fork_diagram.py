"""
Auto-generated Holos fork decision diagram for the living paper.

Reads the newest versioned fork registry, measured fork-delta CSVs, and
coefficient-trace table (selected by AN_vN, never hard-coded). Emits a
Mermaid flowchart plus dashboard JSON. Does not overwrite existing
fork_diagram_AN_vN files; the next free version is used.
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

VERSION_RE = re.compile(r"^(.+)_AN_v(\d+)(\.[^.]+)$")

SKIP_FORK_IDS = frozenset({"BASELINE", "COMBINED"})

# Calculation flow. Prefixes assign forks to a stage; unknown prefixes
# land in "other" (before N2O). Within a stage, preferred ids come first.
STAGE_FLOW = (
    "GE",
    "enteric_Ym",
    "VS",
    "manure_CH4",
    "N_excretion",
    "other",
    "N2O",
    "CO2e",
)
STAGE_PREFIXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("GE", ("HOLOS.GE.",)),
    ("enteric_Ym", ("HOLOS.ENTERIC.", "HOLOS.YM.")),
    ("VS", ("HOLOS.VS.",)),
    ("manure_CH4", ("HOLOS.CH4.",)),
    ("N_excretion", ("HOLOS.NEX.",)),
    ("N2O", ("HOLOS.N2O.",)),
)
STAGE_PREFERRED_IDS: dict[str, tuple[str, ...]] = {
    "GE": ("HOLOS.GE.digestibility",),
    "enteric_Ym": ("HOLOS.ENTERIC.calf_zero", "HOLOS.YM.dairy"),
    "VS": ("HOLOS.VS.digestibility", "HOLOS.VS.urinary_energy", "HOLOS.VS.calf_coeff"),
    "manure_CH4": ("HOLOS.CH4.cover_reduction",),
    "N_excretion": ("HOLOS.NEX.calf_nrate",),
}

STATUS_CLASS = {
    "VERIFIED": "verified",
    "SOURCE-TRACED": "sourcetraced",
    "HOLOS-ONLY": "holosonly",
    "UNVERIFIED": "unverified",
}

# Strongest first. A fork that maps to several coefficients shows the weakest.
CANONICAL_STATUSES = ("VERIFIED", "SOURCE-TRACED", "HOLOS-ONLY", "UNVERIFIED")
STATUS_WEAKNESS = {name: index for index, name in enumerate(CANONICAL_STATUSES)}
STATUS_COLUMN_RE = re.compile(r"^v(\d+)\s+status$", re.IGNORECASE)

PCT_DECIMALS = 3


def an_version(name: str) -> int | None:
    """Return N from a '*_AN_vN.ext' filename, or None."""
    match = VERSION_RE.match(Path(name).name)
    return int(match.group(2)) if match else None


def latest_versioned(directory: Path, prefix: str, suffix: str) -> Path:
    """
    Pick the highest AN_vN file named '{prefix}_AN_vN{suffix}'.

    The match is exact on prefix and suffix so a summary CSV cannot
    shadow a detail CSV that shares a longer name.
    """
    directory = Path(directory)
    pattern = re.compile(rf"^{re.escape(prefix)}_AN_v(\d+){re.escape(suffix)}$")
    matches: list[tuple[int, Path]] = []
    for path in directory.iterdir():
        match = pattern.match(path.name)
        if match:
            matches.append((int(match.group(1)), path))
    if not matches:
        raise FileNotFoundError(f"No {prefix}_AN_vN{suffix} under {directory}")
    matches.sort(key=lambda item: item[0])
    return matches[-1][1]


def next_an_version(directory: Path, prefix: str, suffix: str) -> int:
    """Return 1, or one more than the highest existing AN_vN for this stem."""
    directory = Path(directory)
    if not directory.exists():
        return 1
    pattern = re.compile(rf"^{re.escape(prefix)}_AN_v(\d+){re.escape(suffix)}$")
    versions = [int(match.group(1)) for path in directory.iterdir() if (match := pattern.match(path.name))]
    return (max(versions) + 1) if versions else 1


def repo_root(start: Path | None = None) -> Path:
    """Find the repository root that contains data/holos_forks_AN_v*.json."""
    candidates: list[Path] = []
    if start is not None:
        candidates.append(Path(start).resolve())
    candidates.append(Path.cwd().resolve())
    candidates.append(Path(__file__).resolve().parents[3])
    seen: set[Path] = set()
    for base in candidates:
        for path in (base, *base.parents):
            if path in seen:
                continue
            seen.add(path)
            if any(path.joinpath("data").glob("holos_forks_AN_v*.json")):
                return path
    raise FileNotFoundError("Could not locate data/holos_forks_AN_v*.json")


def mermaid_id(fork_id: str) -> str:
    """Stable Mermaid node id (no dots)."""
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", fork_id)
    return f"F_{cleaned}"


def _round_pct(value: float) -> float:
    return round(float(value), PCT_DECIMALS)


def _format_pct_range(lo: float, hi: float) -> str:
    lo_r, hi_r = _round_pct(lo), _round_pct(hi)
    if lo_r == hi_r:
        return f"{lo_r:+.{PCT_DECIMALS}f}% CO2e"
    return f"{lo_r:+.{PCT_DECIMALS}f} to {hi_r:+.{PCT_DECIMALS}f}% CO2e"


def _stage_for(fork_id: str) -> str:
    for stage, prefixes in STAGE_PREFIXES:
        if any(fork_id.startswith(prefix) for prefix in prefixes):
            return stage
    return "other"


def _order_forks(forks: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    by_id = {str(fork["id"]): fork for fork in forks}
    ordered: list[Mapping[str, Any]] = []
    remaining = set(by_id)
    for stage in STAGE_FLOW:
        stage_ids = [fid for fid in remaining if _stage_for(fid) == stage]
        preferred = [fid for fid in STAGE_PREFERRED_IDS.get(stage, ()) if fid in stage_ids]
        rest = sorted(fid for fid in stage_ids if fid not in set(preferred))
        for fid in (*preferred, *rest):
            ordered.append(by_id[fid])
            remaining.remove(fid)
    for fid in sorted(remaining):
        ordered.append(by_id[fid])
    return ordered


def _alt_option(fork: Mapping[str, Any]) -> str:
    default = str(fork["default"])
    options = list(fork["options"])
    for option in options:
        if option != default:
            return str(option)
    return default


def load_forks_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Fork registry {path} must be a JSON list")
    return data


def normalize_trace_status(raw: str) -> str:
    """Take the leftmost canonical token from a status cell (parentheticals dropped)."""
    text = str(raw or "").strip()
    if not text:
        return ""
    found: list[tuple[int, int, str]] = []
    for token in CANONICAL_STATUSES:
        idx = text.find(token)
        if idx >= 0:
            found.append((idx, -len(token), token))
    if not found:
        return "UNVERIFIED"
    found.sort()
    return found[0][2]


def newest_status_column(fieldnames: Sequence[str] | None) -> str:
    """Highest `vN status` column, else the unversioned `status` field."""
    versioned: list[tuple[int, str]] = []
    status_col = "status"
    for name in fieldnames or ():
        stripped = str(name).strip()
        match = STATUS_COLUMN_RE.match(stripped)
        if match:
            versioned.append((int(match.group(1)), name))
        elif stripped.lower() == "status":
            status_col = name
    if versioned:
        versioned.sort(key=lambda item: item[0])
        return versioned[-1][1]
    return status_col


def row_trace_status(row: Mapping[str, str], fieldnames: Sequence[str] | None = None) -> str:
    """Newest non-empty versioned status on a row, normalized to a canonical token."""
    names = list(fieldnames if fieldnames is not None else row.keys())
    versioned: list[tuple[int, str]] = []
    status_col: str | None = None
    for name in names:
        stripped = str(name).strip()
        match = STATUS_COLUMN_RE.match(stripped)
        if match:
            versioned.append((int(match.group(1)), name))
        elif stripped.lower() == "status":
            status_col = name
    versioned.sort(key=lambda item: item[0], reverse=True)
    for _, name in versioned:
        raw = str(row.get(name, "")).strip()
        if raw:
            return normalize_trace_status(raw)
    if status_col:
        raw = str(row.get(status_col, "")).strip()
        if raw:
            return normalize_trace_status(raw)
    return "UNVERIFIED"


def load_trace_table(path: Path) -> list[dict[str, str]]:
    """Load param / where-used / newest-column status from a coefficient-trace CSV."""
    rows: list[dict[str, str]] = []
    with Path(path).open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        for row in reader:
            key = str(row.get("param", "")).strip()
            if not key:
                continue
            rows.append(
                {
                    "param": key,
                    "where_used": str(row.get("where used", "")),
                    "status": row_trace_status(row, fieldnames),
                    "note": str(row.get("note", "")),
                }
            )
    return rows


def load_trace_status(path: Path) -> dict[str, str]:
    """Map coefficient-trace param id -> newest-column status."""
    return {row["param"]: row["status"] for row in load_trace_table(path)}


def weakest_status(statuses: Sequence[str]) -> str:
    """Weakest canonical status in `statuses`, or UNVERIFIED if none map."""
    mapped = [normalize_trace_status(item) or "UNVERIFIED" for item in statuses if str(item).strip()]
    if not mapped:
        return "UNVERIFIED"
    return max(mapped, key=lambda item: STATUS_WEAKNESS.get(item, len(STATUS_WEAKNESS)))


def _row_maps_to_fork(row: Mapping[str, str], fork_id: str) -> bool:
    param = str(row.get("param", "")).strip()
    where = str(row.get("where_used", row.get("where used", "")))
    if param == fork_id or param.startswith(f"{fork_id}|"):
        return True
    return fork_id in where


def fork_status_from_trace(fork_id: str, rows: Sequence[Mapping[str, str]]) -> str:
    """Weakest newest-column status among every coefficient that maps to `fork_id`."""
    matched = [str(row["status"]) for row in rows if _row_maps_to_fork(row, fork_id)]
    return weakest_status(matched)


def map_fork_statuses(
    fork_ids: Sequence[str],
    rows: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    return {fork_id: fork_status_from_trace(fork_id, rows) for fork_id in fork_ids}


def _status_for(fork_id: str, trace: Mapping[str, str]) -> str:
    if fork_id in trace:
        return normalize_trace_status(trace[fork_id]) or "UNVERIFIED"
    return "UNVERIFIED"


def _pct_field(row: Mapping[str, str]) -> float | None:
    for name in ("delta_CO2e_pct", "sum_delta_CO2e_pct"):
        raw = row.get(name)
        if raw not in (None, ""):
            return float(raw)
    return None


def load_delta_observations(
    paths: Sequence[Path],
    *,
    source_labels: Sequence[str],
) -> dict[str, list[dict[str, Any]]]:
    """Collect per-fork MEASURED % CO2e observations from delta CSVs."""
    collected: dict[str, list[dict[str, Any]]] = {}
    for path, source in zip(paths, source_labels, strict=True):
        with Path(path).open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                fork_id = str(row.get("fork_id", "")).strip()
                if not fork_id or fork_id in SKIP_FORK_IDS:
                    continue
                pct = _pct_field(row)
                if pct is None:
                    continue
                place = str(row.get("farm_id") or row.get("county") or row.get("fips") or "")
                pathway = str(row.get("pathway") or row.get("manure_id") or "")
                collected.setdefault(fork_id, []).append(
                    {
                        "source": source,
                        "place": place,
                        "pathway": pathway,
                        "delta_co2e_pct": _round_pct(pct),
                    }
                )
    for fork_id, rows in collected.items():
        rows.sort(key=lambda item: (item["source"], item["place"], item["pathway"], item["delta_co2e_pct"]))
        collected[fork_id] = rows
    return collected


def _delta_summary(observations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    values = [float(item["delta_co2e_pct"]) for item in observations]
    return {
        "co2e_pct_min": min(values) if values else None,
        "co2e_pct_max": max(values) if values else None,
        "n_obs": len(values),
        "sources": sorted({str(item["source"]) for item in observations}),
        "observations": list(observations),
    }


def build_fork_diagram(
    forks: Sequence[Mapping[str, Any]],
    *,
    observations: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    trace_status: Mapping[str, str] | None = None,
    sources: Mapping[str, str] | None = None,
    output_version: str = "AN_v1",
) -> dict[str, Any]:
    """
    Build the dashboard payload (nodes, edges, deltas, status).

    `forks` is the registry list. Observations and trace are optional so
    tests can inject a dummy fork without writing CSVs.
    """
    ordered = _order_forks(forks)
    obs = observations or {}
    trace = trace_status or {}
    deltas = {fork["id"]: _delta_summary(obs.get(str(fork["id"]), [])) for fork in ordered}
    status = {str(fork["id"]): _status_for(str(fork["id"]), trace) for fork in ordered}

    nodes: list[dict[str, Any]] = [
        {
            "id": "start",
            "mermaid_id": "start",
            "type": "start",
            "stage": "GE",
            "label": "Inputs",
        }
    ]
    for fork in ordered:
        fork_id = str(fork["id"])
        nodes.append(
            {
                "id": fork_id,
                "mermaid_id": mermaid_id(fork_id),
                "type": "fork",
                "stage": _stage_for(fork_id),
                "label": fork_id,
                "description": str(fork.get("description", "")),
                "default": str(fork["default"]),
                "alt": _alt_option(fork),
                "options": dict(fork["options"]),
                "status": status[fork_id],
                "issue_ref": str(fork.get("issue_ref", "")),
                "label_kind": str(fork.get("label", "")),
            }
        )
    nodes.append(
        {
            "id": "N2O",
            "mermaid_id": "N2O",
            "type": "stage",
            "stage": "N2O",
            "label": "N2O",
        }
    )
    nodes.append(
        {
            "id": "CO2e",
            "mermaid_id": "CO2e",
            "type": "sink",
            "stage": "CO2e",
            "label": "CO2e",
        }
    )

    chain = [str(fork["id"]) for fork in ordered] + ["N2O", "CO2e"]
    edges: list[dict[str, Any]] = []
    first = chain[0]
    edges.append({"from": "start", "to": first, "kind": "flow", "option": None})
    for current, nxt in zip(chain, chain[1:], strict=False):
        if current in {"N2O", "CO2e"}:
            edges.append({"from": current, "to": nxt, "kind": "flow", "option": None})
            continue
        fork = next(item for item in ordered if item["id"] == current)
        summary = deltas[current]
        edges.append(
            {
                "from": current,
                "to": nxt,
                "kind": "default",
                "option": str(fork["default"]),
                "delta_co2e_pct_min": None,
                "delta_co2e_pct_max": None,
                "status": status[current],
            }
        )
        edges.append(
            {
                "from": current,
                "to": nxt,
                "kind": "alternate",
                "option": _alt_option(fork),
                "delta_co2e_pct_min": summary["co2e_pct_min"],
                "delta_co2e_pct_max": summary["co2e_pct_max"],
                "status": status[current],
                "n_obs": summary["n_obs"],
            }
        )

    return {
        "schema": "ghgsim.fork_diagram.v1",
        "version": output_version,
        "generated_from": dict(sources or {}),
        "flow": list(STAGE_FLOW),
        "nodes": nodes,
        "edges": edges,
        "deltas": deltas,
        "status": status,
    }


def render_mermaid(payload: Mapping[str, Any]) -> str:
    """Deterministic Mermaid flowchart from a diagram payload."""
    lines = [
        "flowchart TD",
        "    classDef verified fill:#C8E6C9,stroke:#2E7D32,color:#1B5E20",
        "    classDef sourcetraced fill:#FFE082,stroke:#F9A825,color:#374400",
        "    classDef holosonly fill:#FFCDD2,stroke:#C62828,color:#7F1D1D",
        "    classDef unverified fill:#CFD8DC,stroke:#546E7A,color:#263238",
        "    classDef stage fill:#ECEFF1,stroke:#546E7A,color:#263238",
        "    start[\"Inputs\"]",
    ]
    class_lines: list[str] = ["    class start,N2O,CO2e stage"]

    fork_nodes = [node for node in payload["nodes"] if node["type"] == "fork"]
    for node in fork_nodes:
        status = node["status"]
        label = f"{node['label']}<br/>{status}"
        lines.append(f'    {node["mermaid_id"]}{{"{label}"}}')
        css = STATUS_CLASS.get(status, "unverified")
        class_lines.append(f"    class {node['mermaid_id']} {css}")

    lines.append("    N2O[\"N2O\"]")
    lines.append("    CO2e[\"CO2e\"]")

    id_to_mermaid = {node["id"]: node["mermaid_id"] for node in payload["nodes"]}
    for edge in payload["edges"]:
        src = id_to_mermaid[edge["from"]]
        dst = id_to_mermaid[edge["to"]]
        kind = edge["kind"]
        if kind == "flow":
            lines.append(f"    {src} --> {dst}")
            continue
        option = str(edge["option"])
        if kind == "default":
            label = option
        else:
            lo, hi = edge.get("delta_co2e_pct_min"), edge.get("delta_co2e_pct_max")
            if lo is None or hi is None:
                range_text = "no MEASURED Δ"
            else:
                range_text = _format_pct_range(float(lo), float(hi))
            label = f"{option}<br/>{range_text} · {edge.get('status', '')}"
        lines.append(f"    {src} -->|\"{label}\"| {dst}")

    lines.extend(class_lines)
    return "\n".join(lines) + "\n"


def _puppeteer_config_path() -> Path | None:
    """Chrome path + no-sandbox args for mermaid-cli in this VM."""
    chrome = (
        shutil.which("google-chrome")
        or shutil.which("google-chrome-stable")
        or shutil.which("chromium")
        or shutil.which("chromium-browser")
    )
    if not chrome:
        return None
    path = Path(tempfile.mkdtemp(prefix="ghgsim-mmdc-")) / "puppeteer.json"
    path.write_text(
        json.dumps({"executablePath": chrome, "args": ["--no-sandbox", "--disable-setuid-sandbox"]}),
        encoding="utf-8",
    )
    return path


def try_render_mermaid(mmd_path: Path, dest: Path) -> dict[str, Any]:
    """
    Render SVG or PNG with mermaid-cli when mmdc/npx is on PATH.

    CI (`.github/workflows/ci.yml`) is Python-only and does not install
    mermaid-cli. Callers should treat a miss as documented, not fatal.
    """
    dest = Path(dest)
    if dest.exists():
        return {"rendered": False, "reason": f"exists {dest}"}
    puppeteer = _puppeteer_config_path()
    extra: list[str] = ["-b", "white"]
    if puppeteer is not None:
        extra.extend(["-p", str(puppeteer)])
    commands: list[list[str]] = []
    mmdc = shutil.which("mmdc")
    if mmdc:
        commands.append([mmdc, "-i", str(mmd_path), "-o", str(dest), *extra])
    npx = shutil.which("npx")
    if npx:
        commands.append(
            [npx, "--yes", "@mermaid-js/mermaid-cli", "-i", str(mmd_path), "-o", str(dest), *extra]
        )
    if not commands:
        return {"rendered": False, "reason": "mmdc/npx not on PATH"}
    errors: list[str] = []
    for command in commands:
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            errors.append(str(exc))
            continue
        if dest.exists():
            return {"rendered": True, "reason": command[0]}
    return {"rendered": False, "reason": "; ".join(errors) or "render failed"}


def try_render_svg(mmd_path: Path, svg_path: Path) -> dict[str, Any]:
    """Backward-compatible SVG wrapper around try_render_mermaid."""
    return try_render_mermaid(mmd_path, svg_path)


def render_existing_fork_diagrams(figures_dir: Path) -> list[dict[str, Any]]:
    """Write missing SVG/PNG for every fork_diagram_AN_vN.mmd. Never overwrites."""
    figures_dir = Path(figures_dir)
    results: list[dict[str, Any]] = []
    for mmd_path in sorted(figures_dir.glob("fork_diagram_AN_v*.mmd")):
        if re.match(r"^fork_diagram_AN_v\d+\.mmd$", mmd_path.name) is None:
            continue
        for suffix in (".svg", ".png"):
            dest = mmd_path.with_suffix(suffix)
            if dest.exists():
                results.append({"path": dest, "wrote": False, "reason": "exists"})
                continue
            result = try_render_mermaid(mmd_path, dest)
            results.append(
                {
                    "path": dest,
                    "wrote": bool(result["rendered"]),
                    "reason": result["reason"],
                }
            )
    return results


def discover_inputs(data_dir: Path) -> dict[str, Path]:
    """Select newest versioned registry, delta CSVs, and coefficient trace."""
    return {
        "forks": latest_versioned(data_dir, "holos_forks", ".json"),
        "stylized": latest_versioned(data_dir, "holos_fork_deltas_stylized", ".csv"),
        "vt_de": latest_versioned(data_dir, "holos_fork_deltas_vt_de", ".csv"),
        "coefficient_trace": latest_versioned(data_dir, "coefficient_trace", ".csv"),
    }


def build_from_data_dir(data_dir: Path, *, output_version: str) -> dict[str, Any]:
    paths = discover_inputs(data_dir)
    forks = load_forks_json(paths["forks"])
    observations = load_delta_observations(
        [paths["stylized"], paths["vt_de"]],
        source_labels=["stylized", "vt_de"],
    )
    root = data_dir.parent

    def _rel(path: Path) -> str:
        resolved = path.resolve()
        try:
            return resolved.relative_to(root.resolve()).as_posix()
        except ValueError:
            return resolved.as_posix()

    rows = load_trace_table(paths["coefficient_trace"])
    trace_status = map_fork_statuses([str(fork["id"]) for fork in forks], rows)
    return build_fork_diagram(
        forks,
        observations=observations,
        trace_status=trace_status,
        sources={key: _rel(path) for key, path in paths.items()},
        output_version=output_version,
    )


def write_fork_diagram(
    payload: Mapping[str, Any],
    mermaid: str,
    figures_dir: Path,
    *,
    version: int,
    render_svg: bool = True,
) -> dict[str, Path | None]:
    """Write versioned .mmd / .json / optional .svg. Never overwrites."""
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    stem = f"fork_diagram_AN_v{version}"
    mmd_path = figures_dir / f"{stem}.mmd"
    json_path = figures_dir / f"{stem}.json"
    svg_path = figures_dir / f"{stem}.svg"
    for path in (mmd_path, json_path, svg_path):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
    mmd_path.write_text(mermaid, encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written: dict[str, Path | None] = {"mmd": mmd_path, "json": json_path, "svg": None}
    if render_svg:
        result = try_render_svg(mmd_path, svg_path)
        if result["rendered"]:
            written["svg"] = svg_path
    return written


def generate(
    *,
    repo: Path | None = None,
    figures_dir: Path | None = None,
    render_svg: bool = True,
) -> dict[str, Any]:
    """Discover latest inputs, bump output version, write figure files."""
    root = repo_root(repo)
    data_dir = root / "data"
    out_dir = Path(figures_dir) if figures_dir is not None else root / "docs" / "figures"
    version = next_an_version(out_dir, "fork_diagram", ".mmd")
    payload = build_from_data_dir(data_dir, output_version=f"AN_v{version}")
    mermaid = render_mermaid(payload)
    written = write_fork_diagram(payload, mermaid, out_dir, version=version, render_svg=render_svg)
    return {"version": version, "payload": payload, "mermaid": mermaid, "paths": written}
