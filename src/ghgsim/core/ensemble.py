"""
County ensemble runner with multiprocessing.

Runs GHG calculations across many counties in parallel with worker pools.
"""

import logging
import multiprocessing as mp
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from ghgsim.compat.farm import FarmModel
from ghgsim.core.registry import ParameterRegistry

logger = logging.getLogger(__name__)


def run_county(
    county_data: dict[str, Any],
    guideline: str,
    param_registry: ParameterRegistry,
) -> dict[str, Any]:
    """
    Run single county GHG calculation.
    
    Args:
        county_data: County farm specification
        guideline: "IPCC2006" or "IPCC2019"
        param_registry: Parameter registry
        
    Returns:
        Dict with fips, emissions, and metadata
    """
    fips = county_data["fips"]
    
    try:
        model = FarmModel(guideline=guideline)
        result = model.run_farm(county_data, param_registry)
        
        return {
            "fips": fips,
            "status": "success",
            **result,
        }
    except Exception as e:
        logger.warning(f"County {fips} failed: {e}")
        return {
            "fips": fips,
            "status": "error",
            "error": str(e),
        }


class EnsembleRunner:
    """
    Run county ensembles with parallel workers.
    
    Handles multiprocessing pool management, progress tracking,
    and result aggregation.
    """

    def __init__(
        self,
        counties: list[dict[str, Any]],
        param_registry: ParameterRegistry,
        workers: int | str = "auto",
    ):
        """
        Initialize ensemble runner.
        
        Args:
            counties: List of county farm specifications
            param_registry: Parameter registry
            workers: Number of workers ('auto' = cpu_count - 2, min 1)
        """
        self.counties = counties
        self.param_registry = param_registry
        
        if workers == "auto":
            self.workers = max(1, mp.cpu_count() - 2)
        else:
            self.workers = int(workers)
        
        logger.info(f"EnsembleRunner initialized: {len(counties)} counties, {self.workers} workers")

    def run(self, guideline: str = "IPCC2006") -> pd.DataFrame:
        """
        Run ensemble with multiprocessing.
        
        Args:
            guideline: "IPCC2006" or "IPCC2019"
            
        Returns:
            DataFrame with per-county results
        """
        logger.info(f"Starting ensemble run: {guideline}")
        
        # Single worker = no pool overhead
        if self.workers == 1:
            results = [
                run_county(county, guideline, self.param_registry)
                for county in self.counties
            ]
        else:
            # Multiprocessing pool
            with mp.Pool(processes=self.workers) as pool:
                tasks = [
                    pool.apply_async(run_county, (county, guideline, self.param_registry))
                    for county in self.counties
                ]
                results = [task.get() for task in tasks]
        
        logger.info(f"Ensemble complete: {len(results)} results")
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Summary stats
        n_success = (df["status"] == "success").sum()
        n_error = (df["status"] == "error").sum()
        logger.info(f"Success: {n_success}, Errors: {n_error}")
        
        return df

    def run_trial(self, trial_states: list[str] | None = None) -> dict[str, pd.DataFrame]:
        """
        Run trial mode (VT and DE only, both guidelines).
        
        Args:
            trial_states: List of state codes (default: ["VT", "DE"])
            
        Returns:
            Dict mapping guideline to results DataFrame
        """
        if trial_states is None:
            trial_states = ["VT", "DE"]
        
        # Filter to trial states
        trial_counties = [
            c for c in self.counties
            if c.get("state") in trial_states
        ]
        
        logger.info(f"Trial mode: {len(trial_counties)} counties in {trial_states}")
        
        results = {}
        for guideline in ["IPCC2006", "IPCC2019"]:
            logger.info(f"Running {guideline}...")
            
            # Temporarily swap counties
            orig_counties = self.counties
            self.counties = trial_counties
            
            df = self.run(guideline)
            results[guideline] = df
            
            self.counties = orig_counties
        
        return results


def load_counties_stub(data_dir: Path) -> list[dict[str, Any]]:
    """
    Load county data (stub implementation).
    
    Full implementation would:
    1. Load NASS livestock data
    2. Load USGS nitrogen inputs
    3. Load NRCS soil data
    4. Assemble farm specifications
    5. Apply gap-filling for withheld values
    
    Returns:
        List of county farm specifications
    """
    raise NotImplementedError(
        "County data loading not implemented. "
        "Requires NASSLoader, USGSLoader integration plus farm assembly logic."
    )
