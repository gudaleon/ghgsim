# ghgsim

Open, Apache-2.0 GHG simulation framework for agricultural greenhouse gas estimation.

## About

**ghgsim** is a modular framework for agricultural GHG simulation that supports:
- Multiple equation modules (IPCC 2006, IPCC 2019, and more)
- Parameter provenance tracking
- Monte Carlo uncertainty analysis
- Sobol sensitivity analysis
- Fork registry for importance-ranked debugging

This project builds on the livingghg v3 engine, extending it into a general framework where users can define equation modules while the framework provides simulation, parameter estimation, sensitivity, and uncertainty services.

## Installation

### Local Installation

```bash
pip install -e .
```

For development with all extras:

```bash
pip install -e .[dev,test,sobol]
```

### GitHub Codespaces

This repository includes a dev container configuration for GitHub Codespaces. To get started:

1. Open the repository in GitHub
2. Click the "Code" button and select "Open with Codespaces"
3. Create a new codespace or connect to an existing one

The environment will automatically:
- Set up Python 3.12
- Install the package with dev, test, and sobol extras
- Configure VS Code with Python, Ruff, and Mypy extensions
- Be ready to run tests with `pytest tests/v3/`

The dev container uses the exact Python version and dependencies specified in `pyproject.toml`.

## Quick Start

The legacy livingghg v3 code is preserved in `legacy/livingghg_v3/` and all 21 original tests pass through a compatibility layer.

Run the v3 tests:

```bash
pytest tests/v3/
```

## Repository Structure

```
ghgsim/
  src/ghgsim/           # Main package
    core/               # Module contract, registry, graph, runner
    services/           # Monte Carlo, Sobol, estimation, forks
    modules/            # IPCC 2006, IPCC 2019, and other modules
    io/                 # Data loaders (NASS, USGS, EPA)
    api/                # CLI and server
    compat/             # Compatibility layer for v3
  legacy/livingghg_v3/  # Original v3 code (read-only)
  tests/                # New tests
  tests/v3/             # V3 compatibility tests
  docs/                 # Documentation
  data/                 # Small data files
```

## Development

This is a research project under active development at the University of Toronto.

**License:** Apache-2.0  
**Author:** Alex Neumann, University of Toronto

## Citation

If you use this software in your research, please cite it using the metadata in `CITATION.cff`.

## Contributing

This is currently a private research repository. For questions, contact the author.

## US county IPCC 2006 vs 2019 run (AN_v1)
See `docs/US_COUNTY_RUN_AN_v1.md` (inputs, hashes, headline numbers, gaps), `docs/CLIMATE_ZONES_AN_v1.md` and `docs/DECISIONS_AN_v4.md`.
Parameters: `data/ipcc_params_AN_v9.csv` (adds 2019 Table 10.17 boreal/tropical MCFs, 2006 per-degree MCFs, Tier 1 cattle enteric EFs).
