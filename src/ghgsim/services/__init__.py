"""Services for ghgsim: Monte Carlo, Sobol, estimation, and forks."""

from .forks import Fork, ForkRegistry

__all__ = [
    "MonteCarloService",
    "SobolService",
    "Fork",
    "ForkRegistry",
]


def __getattr__(name: str):
    if name == "MonteCarloService":
        from .montecarlo import MonteCarloService

        return MonteCarloService
    if name == "SobolService":
        from .sobol import SobolService

        return SobolService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
