"""Living-paper and dashboard report helpers."""

from ghgsim.report.emissions_sankey import generate as generate_sankey
from ghgsim.report.fork_diagram import (
    build_fork_diagram,
    latest_versioned,
    render_mermaid,
    write_fork_diagram,
)

__all__ = [
    "build_fork_diagram",
    "generate_sankey",
    "latest_versioned",
    "render_mermaid",
    "write_fork_diagram",
]
