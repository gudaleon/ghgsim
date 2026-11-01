"""
Sobol global sensitivity analysis service.

Uses SALib to compute first-order, second-order, and total-order
sensitivity indices for model outputs with respect to parameters.
"""

from collections.abc import Mapping
from typing import Any

import numpy as np
from SALib.analyze import sobol as sobol_analyze
from SALib.sample import saltelli


class SobolService:
    """
    Sobol global sensitivity analysis using SALib.
    
    Computes Sobol indices to rank parameter importance for model outputs.
    """

    def __init__(self, seed: int | None = None):
        """
        Initialize Sobol service.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed

    def sample_parameters(
        self,
        param_registry: Any,
        param_keys: list[str],
        n_samples: int,
    ) -> list[dict[str, float]]:
        """
        Generate Sobol samples using Saltelli sampling scheme.
        
        Args:
            param_registry: ParameterRegistry
            param_keys: Parameter keys to analyze
            n_samples: Base sample size (actual samples = n_samples * (2 * n_params + 2))
            
        Returns:
            List of parameter sample dictionaries
        """
        if not param_keys:
            raise ValueError("No parameters to analyze")

        if n_samples < 1:
            raise ValueError("n_samples must be at least 1")

        # Build SALib problem definition
        problem = {
            "num_vars": len(param_keys),
            "names": param_keys,
            "bounds": [],
        }

        for key in param_keys:
            param = param_registry.get(key, for_sampling=True)
            
            # Get distribution bounds
            if param.dist.value in ("uniform", "triangular"):
                if param.dist_params:
                    lower = param.dist_params.get("lower", param.value * 0.5)
                    upper = param.dist_params.get("upper", param.value * 1.5)
                else:
                    # Use ±20% if no bounds specified
                    lower = param.value * 0.8
                    upper = param.value * 1.2
            else:
                # For other distributions, use reasonable bounds
                lower = param.value * 0.5
                upper = param.value * 1.5
                
            problem["bounds"].append([lower, upper])

        # Generate Saltelli samples (n_samples * (2D + 2) samples total)
        # Note: SALib doesn't support seed parameter directly, but uses numpy's random state
        if self.seed is not None:
            np.random.seed(self.seed)
        param_values = saltelli.sample(problem, n_samples, calc_second_order=True)

        # Convert to list of dictionaries
        samples = []
        for row in param_values:
            sample = {param_keys[i]: float(row[i]) for i in range(len(param_keys))}
            samples.append(sample)

        return samples

    def analyze(
        self,
        param_keys: list[str],
        param_samples: list[dict[str, float]],
        output_samples: list[dict[str, float]],
        output_key: str,
        n_samples: int,
    ) -> dict[str, dict[str, float]]:
        """
        Compute Sobol sensitivity indices.
        
        Args:
            param_keys: Parameter keys analyzed
            param_samples: Parameter sample dictionaries
            output_samples: Output sample dictionaries
            output_key: Output variable to analyze
            n_samples: Base sample size used in sampling
            
        Returns:
            Dictionary with Sobol indices:
            {
                "S1": {param: first_order_index},
                "S1_conf": {param: confidence_interval},
                "ST": {param: total_order_index},
                "ST_conf": {param: confidence_interval},
                "S2": {(param1, param2): second_order_index},  # if computed
            }
        """
        if not param_keys:
            raise ValueError("No parameters provided")

        if len(output_samples) != len(param_samples):
            raise ValueError("Output samples must match parameter samples")

        # Build SALib problem
        problem = {
            "num_vars": len(param_keys),
            "names": param_keys,
            "bounds": [],
        }

        # Extract bounds from samples (min/max)
        for key in param_keys:
            values = [sample[key] for sample in param_samples]
            problem["bounds"].append([min(values), max(values)])

        # Extract output values
        Y = np.array([sample[output_key] for sample in output_samples])

        # Compute Sobol indices
        Si = sobol_analyze.analyze(problem, Y, calc_second_order=True)

        # Format results
        results = {
            "S1": {param_keys[i]: float(Si["S1"][i]) for i in range(len(param_keys))},
            "S1_conf": {param_keys[i]: float(Si["S1_conf"][i]) for i in range(len(param_keys))},
            "ST": {param_keys[i]: float(Si["ST"][i]) for i in range(len(param_keys))},
            "ST_conf": {param_keys[i]: float(Si["ST_conf"][i]) for i in range(len(param_keys))},
        }

        # Add second-order indices if available
        if "S2" in Si and Si["S2"] is not None:
            results["S2"] = {}
            n = len(param_keys)
            for i in range(n):
                for j in range(i + 1, n):
                    key_pair = (param_keys[i], param_keys[j])
                    results["S2"][key_pair] = float(Si["S2"][i, j])

        return results

    def rank_importance(
        self,
        sobol_indices: dict[str, dict[str, float]],
        metric: str = "ST",
    ) -> list[tuple[str, float]]:
        """
        Rank parameters by importance.
        
        Args:
            sobol_indices: Results from analyze()
            metric: Index to rank by ("S1" or "ST", default "ST")
            
        Returns:
            List of (parameter_name, index_value) sorted by descending importance
        """
        if metric not in sobol_indices:
            raise ValueError(f"Metric '{metric}' not in results")

        indices = sobol_indices[metric]
        ranked = sorted(indices.items(), key=lambda x: abs(x[1]), reverse=True)
        return ranked


# Update services __init__.py
def update_services_init():
    """Helper to track what needs to be in __init__.py"""
    return ["MonteCarloService", "SobolService", "ForkRegistry"]
