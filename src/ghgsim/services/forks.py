"""
Fork registry for equation alternatives and debugging.

Forks are named equation variants that can be toggled to test
alternative assumptions or implementations. Importance ranking
based on Sobol sensitivity analysis identifies high-impact forks.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Fork:
    """
    A fork represents an equation alternative or assumption.
    
    Attributes:
        id: Unique fork identifier (e.g., "F007", "F011")
        description: Human-readable description
        affects: List of modules or parameters affected
        default: Default fork option
        options: Available fork options with descriptions
        importance: Importance ranking (higher = more impact)
    """

    id: str
    description: str
    affects: list[str]
    default: str
    options: dict[str, str]
    importance: float = 0.0


class ForkRegistry:
    """
    Registry of equation forks with importance ranking.
    
    Forks can be loaded from JSON, ranked by sensitivity analysis,
    and applied to model runs for debugging or comparison.
    """

    def __init__(self):
        """Initialize empty fork registry."""
        self._forks: dict[str, Fork] = {}

    def register(self, fork: Fork) -> None:
        """
        Register a fork.
        
        Args:
            fork: Fork to register
        """
        self._forks[fork.id] = fork

    def get(self, fork_id: str) -> Fork:
        """
        Get fork by ID.
        
        Args:
            fork_id: Fork identifier
            
        Returns:
            Fork
            
        Raises:
            ValueError: If fork not found
        """
        if fork_id not in self._forks:
            raise ValueError(f"Fork '{fork_id}' not found in registry")
        return self._forks[fork_id]

    def list_forks(self, sort_by: str = "importance") -> list[Fork]:
        """
        List all forks.
        
        Args:
            sort_by: Sort key ("importance", "id", "none")
            
        Returns:
            List of forks
        """
        forks = list(self._forks.values())
        
        if sort_by == "importance":
            forks.sort(key=lambda f: f.importance, reverse=True)
        elif sort_by == "id":
            forks.sort(key=lambda f: f.id)
        elif sort_by != "none":
            raise ValueError(f"Unknown sort_by: {sort_by}")
            
        return forks

    def set_importance(self, fork_id: str, importance: float) -> None:
        """
        Set fork importance from sensitivity analysis.
        
        Args:
            fork_id: Fork identifier
            importance: Importance score (e.g., Sobol total-order index)
        """
        fork = self.get(fork_id)
        fork.importance = importance

    def rank_by_sobol(self, sobol_results: dict[str, Any]) -> list[tuple[str, float]]:
        """
        Rank forks by Sobol sensitivity indices.
        
        Args:
            sobol_results: Results from SobolService.analyze()
            
        Returns:
            List of (fork_id, importance) sorted by descending importance
        """
        # Extract total-order indices
        st_indices = sobol_results.get("ST", {})
        
        # Map parameters to forks
        fork_importance = {}
        for fork in self._forks.values():
            # Sum importance across affected parameters
            importance = 0.0
            for param_key in fork.affects:
                importance += st_indices.get(param_key, 0.0)
            fork_importance[fork.id] = importance
            self.set_importance(fork.id, importance)
        
        # Sort by importance
        ranked = sorted(fork_importance.items(), key=lambda x: x[1], reverse=True)
        return ranked

    def load_from_json(self, json_path: Path) -> None:
        """
        Load forks from JSON file.
        
        JSON format:
        [
            {
                "id": "F007",
                "description": "Ym category for dairy cattle",
                "affects": ["IPCC2019.Ym.dairy_*"],
                "default": "dairy_medium",
                "options": {
                    "dairy_high_ndf_le35": "High NDF, <35% milk fat",
                    "dairy_medium": "Medium forage diet"
                }
            }
        ]
        
        Args:
            json_path: Path to JSON file
        """
        with open(json_path) as f:
            data = json.load(f)
        
        for item in data:
            fork = Fork(
                id=item["id"],
                description=item["description"],
                affects=item["affects"],
                default=item["default"],
                options=item["options"],
                importance=item.get("importance", 0.0),
            )
            self.register(fork)

    def save_to_json(self, json_path: Path) -> None:
        """
        Save forks to JSON file.
        
        Args:
            json_path: Path to JSON file
        """
        data = []
        for fork in self._forks.values():
            data.append({
                "id": fork.id,
                "description": fork.description,
                "affects": fork.affects,
                "default": fork.default,
                "options": fork.options,
                "importance": fork.importance,
            })
        
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

    def apply_forks(
        self,
        fork_settings: dict[str, str],
        base_config: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Apply fork settings to configuration.
        
        Args:
            fork_settings: Dictionary of {fork_id: option}
            base_config: Base configuration dictionary
            
        Returns:
            Modified configuration with fork settings applied
        """
        config = dict(base_config)
        
        for fork_id, option in fork_settings.items():
            fork = self.get(fork_id)
            if option not in fork.options:
                raise ValueError(f"Invalid option '{option}' for fork '{fork_id}'")
            
            # Apply fork to config (implementation-specific)
            # For now, just record the fork setting
            if "forks" not in config:
                config["forks"] = {}
            config["forks"][fork_id] = option
        
        return config
