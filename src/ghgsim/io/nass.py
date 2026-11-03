"""
USDA NASS Census data loader.

Loads agricultural census data (milk cows, beef cattle, cropland) by county.
Includes provenance tracking and data refresh capability.
"""

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd


class NASSLoader:
    """
    Load USDA NASS Census data with hash verification.
    
    Data sources:
    - NASS QuickStats API: https://quickstats.nass.usda.gov/api
    - Census of Agriculture: https://www.nass.usda.gov/AgCensus/
    """

    def __init__(self, data_dir: Path | None = None, api_key: str | None = None):
        """
        Initialize NASS loader.
        
        Args:
            data_dir: Directory containing cached NASS data (default: data/nass/)
            api_key: NASS API key (optional, for refresh operations)
        """
        self.data_dir = data_dir or Path("data/nass")
        self.api_key = api_key
        self._manifest_path = self.data_dir / "manifest.yaml"

    def load_livestock(self, year: int = 2022) -> pd.DataFrame:
        """
        Load county-level livestock inventory.
        
        Returns DataFrame with columns:
        - fips: County FIPS code (str)
        - state: State abbreviation
        - county: County name
        - milk_cows: Dairy cows inventory (head)
        - beef_cows: Beef cows inventory (head)
        - source: Data source
        - year: Census year
        
        Raises:
            FileNotFoundError: If cached data not found
            ValueError: If hash verification fails
        """
        cache_path = self.data_dir / f"livestock_{year}.csv"
        
        if not cache_path.exists():
            raise FileNotFoundError(
                f"NASS livestock data not found: {cache_path}\n"
                f"Run: python scripts/fetch_nass_data.py --year {year}"
            )
        
        # Verify hash
        self._verify_hash(cache_path)
        
        # Load data
        df = pd.read_csv(cache_path, dtype={"fips": str})
        return df

    def load_cropland(self, year: int = 2022) -> pd.DataFrame:
        """
        Load county-level cropland data.
        
        Returns DataFrame with columns:
        - fips: County FIPS code (str)
        - corn_acres: Corn harvested acres
        - soybean_acres: Soybean harvested acres
        - wheat_acres: Wheat harvested acres
        - source: Data source
        """
        cache_path = self.data_dir / f"cropland_{year}.csv"
        
        if not cache_path.exists():
            raise FileNotFoundError(f"NASS cropland data not found: {cache_path}")
        
        self._verify_hash(cache_path)
        df = pd.read_csv(cache_path, dtype={"fips": str})
        return df

    def _verify_hash(self, path: Path) -> None:
        """
        Verify file hash against manifest.
        
        Raises:
            ValueError: If hash mismatch detected
        """
        # Compute actual hash
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual_hash = sha256.hexdigest()
        
        # Load manifest
        if not self._manifest_path.exists():
            # No manifest = no verification (dev mode)
            return
        
        import yaml
        with open(self._manifest_path) as f:
            manifest = yaml.safe_load(f)
        
        filename = path.name
        if filename not in manifest.get("files", {}):
            return  # Not in manifest = skip verification
        
        expected_hash = manifest["files"][filename]["sha256"]
        if actual_hash != expected_hash:
            raise ValueError(
                f"Hash mismatch for {filename}:\n"
                f"  Expected: {expected_hash}\n"
                f"  Actual:   {actual_hash}\n"
                f"Data may be corrupted. Run refresh script."
            )

    def refresh(self, year: int, category: str) -> None:
        """
        Refresh data from NASS API.
        
        Args:
            year: Census year
            category: 'livestock' or 'cropland'
            
        Raises:
            ValueError: If API key not set
            NotImplementedError: Stub implementation
        """
        if not self.api_key:
            raise ValueError("NASS API key required for refresh. Set NASS_API_KEY env var.")
        
        raise NotImplementedError(
            "NASS refresh not yet implemented. "
            "Use scripts/fetch_nass_data.py to download data manually."
        )
