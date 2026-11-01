"""
USGS nutrient data loader.

Loads county-level nitrogen inputs from Falcone 2021 dataset.

Source: Falcone, J.A., 2021, Estimates of County-Level Nitrogen and Phosphorus from 
Commercial Fertilizer for the Conterminous United States, 1987-2018: 
U.S. Geological Survey data release, https://doi.org/10.5066/P9IVD0UN
"""

from pathlib import Path

import pandas as pd


class USGSLoader:
    """
    Load USGS Falcone 2021 nitrogen input data.
    
    Provides county-level commercial fertilizer nitrogen (F_SN) estimates.
    """

    def __init__(self, data_dir: Path | None = None):
        """
        Initialize USGS loader.
        
        Args:
            data_dir: Directory containing USGS data (default: data/usgs/)
        """
        self.data_dir = data_dir or Path("data/usgs")

    def load_nitrogen(self, year: int = 2018) -> pd.DataFrame:
        """
        Load county-level nitrogen inputs.
        
        Returns DataFrame with columns:
        - fips: County FIPS code (str)
        - F_SN: Synthetic nitrogen (kg N/yr)
        - year: Data year
        - source: Data source
        
        Raises:
            FileNotFoundError: If data not found
        """
        # Falcone dataset: 1987-2018 time series
        cache_path = self.data_dir / f"falcone_nitrogen_{year}.csv"
        
        if not cache_path.exists():
            raise FileNotFoundError(
                f"USGS nitrogen data not found: {cache_path}\n"
                f"Download from https://doi.org/10.5066/P9IVD0UN\n"
                f"Or run: python scripts/fetch_usgs_data.py"
            )
        
        df = pd.read_csv(cache_path, dtype={"fips": str})
        return df
