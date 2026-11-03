"""
USGS nutrient data loader.

Loads county-level nitrogen inputs from Falcone 2021 dataset.

Source: Falcone, J.A., 2021, Estimates of County-Level Nitrogen and Phosphorus from 
Commercial Fertilizer for the Conterminous United States, 1987-2018: 
U.S. Geological Survey data release, https://doi.org/10.5066/P9IVD0UN

This implementation wraps the legacy v3 data file from legacy/livingghg_AN_v3/data_us/.
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
            data_dir: Directory containing USGS data (default: legacy/livingghg_AN_v3/data_us/)
        """
        if data_dir is None:
            # Default to legacy v3 data
            data_dir = Path(__file__).parents[3] / "legacy" / "livingghg_AN_v3" / "data_us"
        self.data_dir = Path(data_dir)

    def load_nitrogen(self, year: int = 2017) -> pd.DataFrame:
        """
        Load county-level nitrogen inputs from Falcone 2021 dataset.
        
        Returns DataFrame with columns:
        - fips: County FIPS code (str, 5 digits)
        - F_SN: Synthetic nitrogen from commercial fertilizer (kg N/yr)
        - F_ON: Organic nitrogen from non-cattle manure (hogs, poultry, other) (kg N/yr)
        - farmfertN-kg-{year}: Total farm fertilizer N
        - Cattle_N_kg-{year}: Cattle manure N (not used for F_SN)
        - Hogs_N_kg-{year}, Poultry_N_kg-{year}, Other_N_kg-{year}
        - year: Data year
        
        Note: 2017 is latest year in Falcone 2021 dataset (1987-2018 coverage).
        
        Raises:
            FileNotFoundError: If data not found
        """
        # v3 format: usgs_falcone2021_county_N_{year}_AN_v3.csv.gz
        cache_path = self.data_dir / f"usgs_falcone2021_county_N_{year}_AN_v3.csv.gz"
        
        if not cache_path.exists():
            raise FileNotFoundError(
                f"USGS nitrogen data not found: {cache_path}\n"
                f"Expected in: legacy/livingghg_AN_v3/data_us/\n"
                f"Download from https://doi.org/10.5066/P9IVD0UN"
            )
        
        # Load v3 data
        df = pd.read_csv(cache_path, dtype={"STCOFIPS": str}, compression='gzip')
        
        # Standardize FIPS column
        df['fips'] = df['STCOFIPS'].str.zfill(5)
        df = df.set_index('fips')
        
        # Rename columns for clarity
        result = pd.DataFrame(index=df.index)
        result['F_SN'] = df[f'farmfertN-kg-{year}']  # Commercial fertilizer N
        
        # F_ON: Non-cattle manure N (hogs + poultry + other)
        result['F_ON'] = (df[f'Hogs_N_kg-{year}'] + 
                          df[f'Poultry_N_kg-{year}'] + 
                          df[f'Other_N_kg-{year}'])
        
        # Keep all columns for reference
        for col in df.columns:
            if col not in result.columns and col != 'STCOFIPS':
                result[col] = df[col]
        
        result['year'] = year
        result = result.reset_index()
        
        return result
