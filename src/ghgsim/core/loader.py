"""
YAML model loader.

Models are defined in YAML files that specify which modules to use
and how they connect in a DAG.
"""

from pathlib import Path
from typing import Any

import yaml

from .graph import ExecutionGraph, GraphNode
from .module import Module


def load_model_yaml(yaml_path: Path) -> dict[str, Any]:
    """
    Load a model definition from a YAML file.
    
    Args:
        yaml_path: Path to YAML file
        
    Returns:
        Dictionary with model definition
        
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    if not yaml_path.exists():
        raise FileNotFoundError(f"Model file not found: {yaml_path}")

    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_graph_from_yaml(
    model_def: dict[str, Any], available_modules: dict[str, Module]
) -> ExecutionGraph:
    """
    Build an execution graph from a YAML model definition.
    
    Args:
        model_def: Model definition dictionary from YAML
        available_modules: Dictionary of module_id -> Module instance
        
    Returns:
        ExecutionGraph ready for execution
        
    Raises:
        ValueError: If model definition is invalid
    """
    if "nodes" not in model_def:
        raise ValueError("Model definition must contain 'nodes' key")

    nodes: dict[str, GraphNode] = {}

    for node_id, node_def in model_def["nodes"].items():
        if "module" not in node_def:
            raise ValueError(f"Node '{node_id}' must specify 'module'")

        module_id = node_def["module"]
        if module_id not in available_modules:
            raise ValueError(f"Module '{module_id}' not found in available modules")

        module = available_modules[module_id]

        # Dependencies are other nodes this node depends on
        dependencies = node_def.get("depends_on", [])
        if isinstance(dependencies, str):
            dependencies = [dependencies]

        # What this node provides (outputs)
        provides = {
            output_name: var_spec.units
            for output_name, var_spec in module.outputs.items()
        }

        nodes[node_id] = GraphNode(
            module=module, dependencies=dependencies, provides=provides
        )

    return ExecutionGraph(nodes)
