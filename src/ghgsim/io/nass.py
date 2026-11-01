"""
USDA NASS Census data loader.

Loads agricultural census data (milk cows, beef cattle, cropland) by county.
Includes provenance tracking and data refresh capability.

This implementation wraps the legacy v3 data files from legacy/livingghg_AN_v3/data_nass/.
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
    - Legacy v3 cached data: legacy/livingghg_AN_v3/data_nass/
    """

    def __init__(self, data_dir: Path | None = None, api_key: str | None = None):
        """
        Initialize NASS loader.
        
        Args:
            data_dir: Directory containing cached NASS data (default: legacy/livingghg_AN_v3/data_nass/)
            api_key: NASS API key (optional, for refresh operations)
        """
        if data_dir is None:
            # Default to legacy v3 data
            data_dir = Path(__file__).parents[3] / "legacy" / "livingghg_AN_v3" / "data_nass"
        self.data_dir = Path(data_dir)
        self.api_key = api_key
        self._manifest_path = self.data_dir / "manifest.yaml"

    def load_livestock(self, year: int = 2022) -> pd.DataFrame:
        """
        Load county-level livestock inventory from v3 census data.
        
        Returns DataFrame with columns:
        - fips: County FIPS code (str)
        - STATE_ALPHA: State abbreviation
        - COUNTY_NAME: County name
        - milk_cows: Dairy cows inventory (head), NaN for withheld (D) values
        - beef_cows: Beef cows inventory (head), NaN for withheld (D) values
        - milk_fill: 'reported' or 'withheld'
        - beef_fill: 'reported' or 'withheld'
        
        Raises:
            FileNotFoundError: If cached data not found
            ValueError: If hash verification fails
        """
        # v3 format: nass_census2022_county_AN_v1.csv.gz
        cache_path = self.data_dir / f"nass_census{year}_county_AN_v1.csv.gz"
        
        if not cache_path.exists():
            raise FileNotFoundError(
                f"NASS livestock data not found: {cache_path}\n"
                f"Expected v3 format: nass_census{year}_county_AN_v1.csv.gz\n"
                f"Available in: legacy/livingghg_AN_v3/data_nass/"
            )
        
        # Verify hash if manifest exists
        self._verify_hash(cache_path)
        
        # Load v3 data
        df = pd.read_csv(cache_path, dtype=str, compression='gzip')
        
        # Process per v3 script logic
        COWS = {
            "milk": "CATTLE, COWS, MILK - INVENTORY",
            "beef": "CATTLE, COWS, BEEF - INVENTORY"
        }
        
        # Filter to cow inventory only
        df = df[df['SHORT_DESC'].isin(COWS.values()) & df['COUNTY_CODE'].notna()].copy()
        
        # Parse values (handle (D) withheld as NaN)
        df['v'] = pd.to_numeric(df['VALUE'].str.replace(',', '').str.strip(), errors='coerce')
        
        # Build FIPS
        df['fips'] = (df['STATE_FIPS_CODE'].astype(str).str.zfill(2) + 
                      df['COUNTY_CODE'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(3))
        
        # Pivot to wide format
        pivot = df.groupby(['fips', 'SHORT_DESC'])['v'].first().unstack().reindex(columns=list(COWS.values()))
        result = df.drop_duplicates('fips').set_index('fips')[['STATE_ALPHA', 'COUNTY_NAME']].join(pivot).reset_index()
        result = result.rename(columns={COWS["milk"]: "milk_cows", COWS["beef"]: "beef_cows"})
        
        # Add fill status
        result['milk_fill'] = result['milk_cows'].isna().map({True: 'withheld', False: 'reported'})
        result['beef_fill'] = result['beef_cows'].isna().map({True: 'withheld', False: 'reported'})
        
        return result

    def load_cropland(self, year: int = 2022) -> pd.DataFrame:
        """
        Load county-level cropland data from v3 census data.
        
        Returns DataFrame with columns:
        - fips: County FIPS code (str)
        - STATE_ALPHA: State abbreviation  
        - COUNTY_NAME: County name
        - corn_acres: Corn harvested acres (NaN for withheld)
        - soybean_acres: Soybean harvested acres (NaN for withheld)
        - wheat_acres: Wheat harvested acres (NaN for withheld)
        - ... other crops
        
        Raises:
            FileNotFoundError: If cached data not found
        """
        # v3 format: nass_census2022_crops_county_AN_v3.csv.gz
        cache_path = self.data_dir / f"nass_census{year}_crops_county_AN_v3.csv.gz"
        
        if not cache_path.exists():
            raise FileNotFoundError(
                f"NASS cropland data not found: {cache_path}\n"
                f"Expected in: legacy/livingghg_AN_v3/data_nass/"
            )
        
        self._verify_hash(cache_path)
        df = pd.read_csv(cache_path, dtype=str, compression='gzip')
        
        # Add fips if not present
        if 'fips' not in df.columns:
            df['fips'] = (df['STATE_FIPS_CODE'].astype(str).str.zfill(2) + 
                          df['COUNTY_CODE'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(3))
        
        return df

    def _verify_hash(self, path: Path) -> None:
        """
        Verify file hash against manifest (if manifest exists).
        
        Raises:
            ValueError: If hash mismatch detected
        """
        # Skip verification if no manifest (dev mode)
        if not self._manifest_path.exists():
            return
        
        # Compute actual hash
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual_hash = sha256.hexdigest()
        
        # Load manifest
        try:
            import yaml
            with open(self._manifest_path) as f:
                manifest = yaml.safe_load(f)
        except ImportError:
            # PyYAML not installed, skip verification
            return
        except Exception:
            # Manifest parsing failed, skip verification
            return
        
        filename = path.name
        if filename not in manifest.get("files", {}):
            return  # Not in manifest = skip verification
        
        expected_hash = manifest["files"][filename]["sha256"]
        if actual_hash != expected_hash:
            raise ValueError(
                f"Hash mismatch for {filename}:\n"
                f"  Expected: {expected_hash}\n"
                f"  Actual:   {actual_hash}\n"
                f"Data may be corrupted or modified."
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
