#!/usr/bin/env python3
"""
Fetch USDA NASS Census data.

Downloads livestock and cropland data by county and caches with hash verification.

Usage:
    python scripts/fetch_nass_data.py --year 2022 --categories livestock,cropland
    
Environment:
    NASS_API_KEY: NASS QuickStats API key (get from https://quickstats.nass.usda.gov/api)
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path

import pandas as pd
import yaml


def fetch_livestock(api_key: str, year: int) -> pd.DataFrame:
    """
    Fetch county-level livestock inventory from NASS API.
    
    Stub implementation - actual implementation would:
    1. Query NASS QuickStats API for milk cows, beef cows
    2. Filter for county-level data
    3. Handle (D) withheld values with gap-filling
    4. Standardize FIPS codes
    """
    raise NotImplementedError(
        "NASS API integration not implemented. "
        "Manual implementation required:\n"
        "1. Download data from https://quickstats.nass.usda.gov/\n"
        "2. Query: 'CATTLE, COWS, MILK - INVENTORY' and 'CATTLE, COWS, BEEF - INVENTORY'\n"
        "3. Filter: Year={year}, Geographic Level=COUNTY\n"
        "4. Save to data/nass/livestock_{year}.csv with columns: fips, state, county, milk_cows, beef_cows\n"
        "5. Run this script with --compute-hashes to update manifest"
    )


def fetch_cropland(api_key: str, year: int) -> pd.DataFrame:
    """Fetch county-level cropland data."""
    raise NotImplementedError("See fetch_livestock for manual process")


def compute_hash(path: Path) -> str:
    """Compute SHA-256 hash of file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def update_manifest(data_dir: Path) -> None:
    """Update data manifest with file hashes."""
    manifest_path = data_dir / "manifest.yaml"
    
    manifest = {"files": {}, "source": "USDA NASS QuickStats", "generated_by": __file__}
    
    for csv_file in data_dir.glob("*.csv"):
        file_hash = compute_hash(csv_file)
        manifest["files"][csv_file.name] = {
            "sha256": file_hash,
            "size_bytes": csv_file.stat().st_size,
        }
    
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=True)
    
    print(f"✓ Updated manifest: {manifest_path}")
    print(f"  Files: {len(manifest['files'])}")


def main():
    parser = argparse.ArgumentParser(description="Fetch NASS data")
    parser.add_argument("--year", type=int, default=2022, help="Census year")
    parser.add_argument("--categories", default="livestock,cropland", help="Comma-separated categories")
    parser.add_argument("--compute-hashes", action="store_true", help="Only compute hashes for existing files")
    args = parser.parse_args()
    
    data_dir = Path("data/nass")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    if args.compute_hashes:
        update_manifest(data_dir)
        return
    
    api_key = os.getenv("NASS_API_KEY")
    if not api_key:
        print("ERROR: NASS_API_KEY environment variable not set", file=sys.stderr)
        print("Get API key from: https://quickstats.nass.usda.gov/api", file=sys.stderr)
        sys.exit(1)
    
    categories = args.categories.split(",")
    
    for category in categories:
        if category == "livestock":
            print(f"Fetching livestock data for {args.year}...")
            df = fetch_livestock(api_key, args.year)
        elif category == "cropland":
            print(f"Fetching cropland data for {args.year}...")
            df = fetch_cropland(api_key, args.year)
        else:
            print(f"WARNING: Unknown category '{category}'", file=sys.stderr)
            continue
        
        output_path = data_dir / f"{category}_{args.year}.csv"
        df.to_csv(output_path, index=False)
        print(f"✓ Saved: {output_path}")
    
    # Update manifest
    update_manifest(data_dir)


if __name__ == "__main__":
    main()
