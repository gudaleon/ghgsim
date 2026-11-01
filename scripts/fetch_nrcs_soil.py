#!/usr/bin/env python3
"""
Fetch NRCS gSSURGO soil data and aggregate to county level.

Downloads gSSURGO data via Soil Data Access and aggregates organic carbon,
texture, and pH to county level for GHG modeling.

Usage:
    python scripts/fetch_nrcs_soil.py --states VT,DE --output data/soil/sample_vt_de.csv
    
This script is designed for heavy Windows machines with sufficient disk/RAM.
CI uses pre-built VT/DE sample.

Data Source: NRCS Soil Data Access
    https://sdmdataaccess.nrcs.usda.gov/
    https://nrcs.app.box.com/v/soils (gSSURGO/gNATSGO downloads)
"""

import argparse
import hashlib
from pathlib import Path

import pandas as pd


def fetch_soil_data(states: list[str]) -> pd.DataFrame:
    """
    Fetch and aggregate soil data for specified states.
    
    Process:
    1. Download gSSURGO data for each state (~500MB-2GB per state)
    2. Query mapunit and component tables for organic carbon, texture, pH
    3. Spatially join with county boundaries
    4. Aggregate to county level (area-weighted means)
    5. Return county-level soil properties
    
    Stub implementation - actual implementation would:
    - Use Soil Data Access REST API or download state geodatabases
    - Process raster/vector data with geopandas/rasterio
    - Implement area-weighted aggregation
    - Handle no-data values appropriately
    """
    raise NotImplementedError(
        "Soil data fetching not implemented. Manual process:\n"
        "1. Download gSSURGO from https://nrcs.app.box.com/v/soils\n"
        "2. Extract state geodatabases\n"
        "3. Query mapunit and component tables\n"
        "4. Aggregate to county level\n"
        "5. Save to data/soil/ with columns: fips, soc_pct, clay_pct, ph, texture_class\n"
        "For CI: use pre-built data/soil/sample_vt_de.csv"
    )


def compute_hash(path: Path) -> str:
    """Compute SHA-256 hash."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Fetch NRCS soil data")
    parser.add_argument("--states", required=True, help="Comma-separated state codes (e.g., VT,DE)")
    parser.add_argument("--output", type=Path, required=True, help="Output CSV path")
    args = parser.parse_args()
    
    states = args.states.split(",")
    
    print(f"Fetching soil data for: {', '.join(states)}")
    df = fetch_soil_data(states)
    
    # Save
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    
    # Compute and print hash for CI verification
    file_hash = compute_hash(args.output)
    print(f"\n✓ Saved: {args.output}")
    print(f"  SHA-256: {file_hash}")
    print(f"  Size: {args.output.stat().st_size:,} bytes")
    print(f"\nAdd to CI with:")
    print(f"  - name: {args.output.name}")
    print(f"    sha256: {file_hash}")


if __name__ == "__main__":
    main()
