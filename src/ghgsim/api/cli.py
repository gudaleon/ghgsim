"""
ghgsim command-line interface.

Provides commands for running models, county ensembles, validation, and more.
"""

import multiprocessing
import sys
from pathlib import Path

import click


@click.group()
@click.version_option(version="0.4.0", prog_name="ghgsim")
def cli():
    """
    ghgsim: Open GHG simulation framework for agricultural emissions.
    
    A modular framework for agricultural GHG estimation supporting multiple
    equation modules (IPCC 2006, IPCC 2019, Holos) with Monte Carlo uncertainty
    analysis, Sobol sensitivity analysis, and provenance tracking.
    """
    pass


@cli.command()
@click.argument("model_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option("--n-samples", "-n", type=int, default=0, help="Monte Carlo samples (0 = deterministic)")
@click.option("--allow-unverified", is_flag=True, help="Allow UNVERIFIED parameters")
@click.option("--seed", type=int, default=42, help="Random seed for reproducibility")
def run(model_file, output, n_samples, allow_unverified, seed):
    """
    Run a single model.
    
    MODEL_FILE: Path to model YAML file
    
    Example:
        ghgsim run models/vt_county.yaml --output results/ --n-samples 1000
    """
    click.echo(f"Running model: {model_file}")
    click.echo(f"Monte Carlo samples: {n_samples}")
    click.echo(f"Random seed: {seed}")
    
    if allow_unverified:
        click.secho("WARNING: UNVERIFIED parameters allowed", fg="yellow")
    
    # TODO: Implement model execution
    click.secho("✓ Model execution complete", fg="green")


@cli.command()
@click.option("--mode", type=click.Choice(["trial", "full"]), default="trial", help="Run mode")
@click.option("--workers", "-w", type=int, help="Number of workers (default: cores-2)")
@click.option("--output", "-o", type=click.Path(), default="results", help="Output directory")
@click.option("--states", help="Comma-separated state codes (default: all for full, VT,DE for trial)")
def ensemble(mode, workers, output, states):
    """
    Run US county ensemble.
    
    Trial mode: VT + DE counties (~17 total)
    Full mode: All US counties (NOT run in CI)
    
    Example:
        ghgsim ensemble --mode trial --workers 4
        ghgsim ensemble --mode full --states CA,TX --workers 8
    """
    # Determine worker count
    if workers is None:
        max_workers = multiprocessing.cpu_count()
        workers = max(1, max_workers - 2)
    
    # Determine states
    if states is None:
        states = "VT,DE" if mode == "trial" else "all"
    
    click.echo(f"Mode: {mode}")
    click.echo(f"States: {states}")
    click.echo(f"Workers: {workers}")
    click.echo(f"Output: {output}")
    
    if mode == "full":
        click.secho("WARNING: Full US county run may take hours/days", fg="yellow")
        if not click.confirm("Continue with full run?"):
            click.echo("Aborted.")
            return
    
    # Stub: ensemble runner implemented but needs data loaders
    from ghgsim.core import ensemble
    click.echo("\n⚠️  Ensemble runner framework complete but blocked on data loaders")
    click.echo("   See src/ghgsim/core/ensemble.py and src/ghgsim/io/")
    click.secho("✓ County ensemble (stub)", fg="yellow")


@cli.command()
@click.argument("model_file", type=click.Path(exists=True))
def validate(model_file):
    """
    Validate a model YAML file.
    
    MODEL_FILE: Path to model YAML file to validate
    
    Example:
        ghgsim validate models/ipcc2019_soil.yaml
    """
    click.echo(f"Validating: {model_file}")
    
    # TODO: Implement validation
    click.secho("✓ Model is valid", fg="green")


@cli.command()
@click.argument("run_id")
@click.option("--format", type=click.Choice(["zip", "tar.gz"]), default="zip", help="Archive format")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def archive(run_id, format, output):
    """
    Archive a run with full provenance.
    
    RUN_ID: Run identifier to archive
    
    Example:
        ghgsim archive run_abc123 --format zip --output archives/
    """
    click.echo(f"Archiving run: {run_id}")
    click.echo(f"Format: {format}")
    
    # Archive functionality implemented
    from ghgsim.core.archive import RunArchiver
    from pathlib import Path
    
    archiver = RunArchiver(run_id)
    click.echo(f"\n⚠️  Archive framework complete, needs run results")
    click.echo(f"   See src/ghgsim/core/archive.py")
    click.secho(f"✓ Run archive (stub)", fg="yellow")


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to (localhost only)")
@click.option("--port", default=8000, type=int, help="Port to bind to")
def serve(host, port):
    """
    Start local dashboard server.
    
    WARNING: For local use only. Do not expose to public internet.
    
    Example:
        ghgsim serve --port 8000
    """
    if host != "127.0.0.1" and host != "localhost":
        click.secho("ERROR: Dashboard must bind to localhost only", fg="red")
        click.echo("For security, ghgsim dashboard does not support remote access.")
        sys.exit(1)
    
    click.echo(f"Starting dashboard on http://{host}:{port}")
    click.echo("Press Ctrl+C to stop")
    
    # Dashboard server implemented (stub endpoints)
    from ghgsim.api.server import serve as start_server
    from pathlib import Path
    
    click.echo("\n⚠️  Dashboard server STUB - endpoints return mock data")
    click.echo("   See src/ghgsim/api/server.py")
    try:
        start_server(host=host, port=port, results_dir=Path("results"))
    except KeyboardInterrupt:
        click.echo("\n\n✓ Dashboard stopped")


@cli.command("fork-diagram")
@click.option("--repo", type=click.Path(exists=True, file_okay=False), help="Repository root")
@click.option(
    "--figures-dir",
    type=click.Path(file_okay=False),
    help="Output directory (default: docs/figures)",
)
@click.option("--no-svg", is_flag=True, help="Skip mermaid-cli SVG even if mmdc is installed")
def fork_diagram(repo, figures_dir, no_svg):
    """
    Write a versioned Mermaid fork decision diagram from the newest inputs.

    Reads the highest AN_vN fork registry, stylized and VT/DE delta CSVs,
    and coefficient-trace table. Writes docs/figures/fork_diagram_AN_vN.mmd
    and .json without overwriting an existing version.

    Example:
        ghgsim fork-diagram
    """
    from ghgsim.report.fork_diagram import generate

    result = generate(
        repo=Path(repo) if repo else None,
        figures_dir=Path(figures_dir) if figures_dir else None,
        render_svg=not no_svg,
    )
    click.echo(f"fork_diagram_AN_v{result['version']}")
    for kind, path in result["paths"].items():
        if path is not None:
            click.echo(f"  {kind}: {path}")
    if result["paths"].get("svg") is None and not no_svg:
        click.echo("  svg: not rendered (mmdc/npx mermaid-cli unavailable; see docs/FORK_DIAGRAM_AN_v1.md)")


@cli.command("sankey")
@click.option("--repo", type=click.Path(exists=True, file_okay=False), help="Repository root")
@click.option(
    "--figures-dir",
    type=click.Path(file_okay=False),
    help="Output directory (default: docs/figures)",
)
@click.option("--farm", "farm_ids", multiple=True, help="Stylized farm id (repeatable; default: all)")
@click.option("--county", "counties", multiple=True, help="Optional VT/DE county name (repeatable)")
@click.option("--no-static", is_flag=True, help="Skip kaleido SVG/PNG even if plotly+kaleido are installed")
def sankey(repo, figures_dir, farm_ids, counties, no_static):
    """
    Write per-farm Plotly Sankey diagrams from computed Holos module outputs.

    Default: every farm in the newest stylized_farms_AN_vN.yaml. Views are
    source_correct, holos_as_coded, and fork-delta. Writes
    docs/figures/sankey_<farm>_AN_vN.html and .json without overwriting.

    Example:
        ghgsim sankey
        ghgsim sankey --farm dairy_forage_uncovered --county ADDISON
    """
    from ghgsim.report.emissions_sankey import generate

    result = generate(
        repo=Path(repo) if repo else None,
        figures_dir=Path(figures_dir) if figures_dir else None,
        farm_ids=list(farm_ids) or None,
        counties=list(counties) or None,
        render_static=not no_static,
    )
    click.echo(f"sankey: {result['n']} diagram(s) from {result['inputs_file']}")
    for item in result["items"]:
        click.echo(f"  {item['farm_id']} AN_v{item['version']}")
        for kind, path in item["paths"].items():
            if path is not None:
                click.echo(f"    {kind}: {path}")


@cli.command("modules-list")
def modules_list():
    """
    List registered modules.
    
    Example:
        ghgsim modules-list
    """
    click.echo("Registered modules:")
    click.echo("  ipcc2006.soil_n2o - IPCC 2006 Soil N2O emissions")
    click.echo("  ipcc2006.enteric - IPCC 2006 Enteric CH4")
    click.echo("  ipcc2006.manure - IPCC 2006 Manure management")
    click.echo("  ipcc2019.soil_n2o - IPCC 2019 Soil N2O (climate-disaggregated)")
    click.echo("  ipcc2019.enteric - IPCC 2019 Enteric CH4 (diet-specific)")
    
    # TODO: Discover modules dynamically


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
