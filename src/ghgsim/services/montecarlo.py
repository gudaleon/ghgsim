"""
Monte Carlo simulation service with Latin Hypercube Sampling.

Performs uncertainty analysis by sampling parameter distributions
and running the model N times to estimate output variability.
"""

from collections.abc import Mapping
from typing import Any

import numpy as np
from scipy.stats import qmc


class MonteCarloService:
    """
    Monte Carlo simulation with Latin Hypercube Sampling.
    
    Uses scipy.stats.qmc.LatinHypercube for efficient parameter space coverage.
    """

    def __init__(self, seed: int | None = None):
        """
        Initialize Monte Carlo service.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def sample_parameters(
        self,
        param_registry: Any,  # ParameterRegistry
        param_keys: list[str],
        n_samples: int,
    ) -> list[dict[str, float]]:
        """
        Generate parameter samples using Latin Hypercube Sampling.
        
        Args:
            param_registry: ParameterRegistry with parameter distributions
            param_keys: List of parameter keys to sample
            n_samples: Number of samples to generate
            
        Returns:
            List of parameter dictionaries (one per sample)
        """
        if not param_keys:
            raise ValueError("No parameters to sample")

        if n_samples < 1:
            raise ValueError("n_samples must be at least 1")

        # Create LHS sampler
        n_params = len(param_keys)
        sampler = qmc.LatinHypercube(d=n_params, seed=self.seed)
        
        # Generate samples in [0, 1]^d
        lhs_samples = sampler.random(n=n_samples)

        # Transform to parameter distributions
        param_samples = []
        for i in range(n_samples):
            sample = {}
            for j, key in enumerate(param_keys):
                param = param_registry.get(key, for_sampling=True)
                
                # Transform uniform [0,1] to parameter distribution
                u = lhs_samples[i, j]
                
                if param.dist.value == "uniform":
                    # Uniform distribution
                    if param.dist_params is None:
                        # Use value as point estimate
                        sample[key] = param.value
                    else:
                        lower = param.dist_params.get("lower", param.value)
                        upper = param.dist_params.get("upper", param.value)
                        sample[key] = lower + u * (upper - lower)
                        
                elif param.dist.value == "triangular":
                    # Triangular distribution
                    if param.dist_params is None:
                        sample[key] = param.value
                    else:
                        lower = param.dist_params.get("lower", param.value)
                        upper = param.dist_params.get("upper", param.value)
                        mode = param.value
                        # Transform via inverse CDF
                        if u < (mode - lower) / (upper - lower):
                            sample[key] = lower + np.sqrt(u * (upper - lower) * (mode - lower))
                        else:
                            sample[key] = upper - np.sqrt((1 - u) * (upper - lower) * (upper - mode))
                            
                elif param.dist.value == "normal":
                    # Normal distribution (clipped to bounds if provided)
                    if param.dist_params is None:
                        sample[key] = param.value
                    else:
                        # Standard normal inverse CDF
                        from scipy.stats import norm
                        mean = param.value
                        std = param.dist_params.get("std", mean * 0.1)  # Default 10% CV
                        sample[key] = norm.ppf(u, loc=mean, scale=std)
                        
                elif param.dist.value == "lognormal":
                    # Lognormal distribution
                    if param.dist_params is None:
                        sample[key] = param.value
                    else:
                        from scipy.stats import lognorm
                        mean = param.value
                        cv = param.dist_params.get("cv", 0.1)  # Coefficient of variation
                        # Lognormal parameters from mean and CV
                        sigma = np.sqrt(np.log(1 + cv**2))
                        mu = np.log(mean) - 0.5 * sigma**2
                        sample[key] = lognorm.ppf(u, s=sigma, scale=np.exp(mu))
                        
                else:  # fixed
                    sample[key] = param.value
                    
            param_samples.append(sample)

        return param_samples

    def run_ensemble(
        self,
        compute_fn: Any,  # Callable[[dict], dict]
        fixed_inputs: dict[str, Any],
        param_registry: Any,
        param_keys: list[str],
        n_samples: int,
    ) -> tuple[list[dict[str, float]], list[dict[str, float]]]:
        """
        Run Monte Carlo ensemble.
        
        Args:
            compute_fn: Function that takes (inputs, params) and returns outputs
            fixed_inputs: Fixed input values
            param_registry: ParameterRegistry
            param_keys: Parameter keys to sample
            n_samples: Number of Monte Carlo samples
            
        Returns:
            Tuple of (param_samples, output_samples)
        """
        param_samples = self.sample_parameters(param_registry, param_keys, n_samples)
        
        output_samples = []
        for param_sample in param_samples:
            # Get all parameter values (sampled + fixed)
            params = {}
            for key in param_registry._params.keys():
                if key in param_sample:
                    params[key] = param_sample[key]
                else:
                    params[key] = param_registry.get_value(key)
            
            # Run model
            outputs = compute_fn(fixed_inputs, params)
            output_samples.append(outputs)
            
        return param_samples, output_samples

    def summarize_outputs(
        self,
        output_samples: list[dict[str, float]],
        output_keys: list[str] | None = None,
    ) -> dict[str, dict[str, float]]:
        """
        Summarize Monte Carlo output distributions.
        
        Args:
            output_samples: List of output dictionaries
            output_keys: Keys to summarize (None = all keys)
            
        Returns:
            Dictionary of {output_key: {statistic: value}}
            Statistics: mean, median, std, cv, p2.5, p97.5, min, max
        """
        if not output_samples:
            return {}

        if output_keys is None:
            output_keys = list(output_samples[0].keys())

        summary = {}
        for key in output_keys:
            values = np.array([sample[key] for sample in output_samples])
            
            summary[key] = {
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "std": float(np.std(values)),
                "cv": float(np.std(values) / np.mean(values)) if np.mean(values) != 0 else 0.0,
                "p2.5": float(np.percentile(values, 2.5)),
                "p50": float(np.percentile(values, 50)),
                "p97.5": float(np.percentile(values, 97.5)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
            }

        return summary
