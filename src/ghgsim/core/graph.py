"""
Model graph construction and execution.

A model is a directed acyclic graph (DAG) of modules. The graph resolver
checks for cycles, missing inputs, and unit compatibility before execution.
"""

from dataclasses import dataclass
from typing import Any

from .module import Module
from .units import check_compatible


@dataclass
class GraphNode:
    """
    Node in the execution graph.
    
    Attributes:
        module: The module instance
        dependencies: List of upstream node names
        provides: Dict of output_name -> units
    """

    module: Module
    dependencies: list[str]
    provides: dict[str, str]


class ExecutionGraph:
    """
    Execution graph for a model (DAG of modules).
    
    Validates dependencies, checks for cycles, and ensures unit compatibility.
    """

    def __init__(self, nodes: dict[str, GraphNode]):
        """
        Initialize the execution graph.
        
        Args:
            nodes: Dictionary of node_id -> GraphNode
            
        Raises:
            ValueError: If graph is invalid (cycles, missing deps, unit mismatch)
        """
        self.nodes = nodes
        self._validate()

    def _validate(self) -> None:
        """Validate the graph for cycles, missing dependencies, and unit mismatches."""
        # Check for cycles using DFS
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            node = self.nodes[node_id]
            for dep in node.dependencies:
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    raise ValueError(f"Cycle detected in graph involving node: {node_id}")

        # Check for missing dependencies
        all_provided: dict[str, tuple[str, str]] = {}
        for node_id, node in self.nodes.items():
            for output_name, units in node.provides.items():
                if output_name in all_provided:
                    prev_node, prev_units = all_provided[output_name]
                    raise ValueError(
                        f"Output '{output_name}' provided by multiple nodes: "
                        f"{prev_node} and {node_id}"
                    )
                all_provided[output_name] = (node_id, units)

        # Check that all required inputs are satisfied (by other modules or external)
        # We can't check external inputs here, so we only verify that if an input
        # is NOT in all_provided, it must be supplied externally at runtime
        for node_id, node in self.nodes.items():
            for input_name, var_spec in node.module.inputs.items():
                if not var_spec.required:
                    continue

                # If another module provides this input, check unit compatibility
                if input_name in all_provided:
                    provider_node, provider_units = all_provided[input_name]
                    if not check_compatible(provider_units, var_spec.units):
                        raise ValueError(
                            f"Unit mismatch: node '{node_id}' expects '{input_name}' "
                            f"in {var_spec.units}, but '{provider_node}' provides {provider_units}"
                        )
                # Otherwise, it will need to be provided as an external input at runtime

    def topological_sort(self) -> list[str]:
        """
        Return a topological ordering of nodes for execution.
        
        Returns:
            List of node IDs in execution order
        """
        # Build in-degree map
        in_degree = {node_id: len(node.dependencies) for node_id, node in self.nodes.items()}

        # Start with nodes that have no dependencies
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            # Find nodes that depend on this one and reduce their in-degree
            for other_id, other_node in self.nodes.items():
                if node_id in other_node.dependencies:
                    in_degree[other_id] -= 1
                    if in_degree[other_id] == 0:
                        queue.append(other_id)

        if len(result) != len(self.nodes):
            raise ValueError("Graph has cycles (topological sort failed)")

        return result

    def execute(
        self, external_inputs: dict[str, Any], parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute the graph in topological order.
        
        Args:
            external_inputs: External inputs to the graph
            parameters: Parameter values for all modules
            
        Returns:
            Dictionary of all outputs from all modules
        """
        execution_order = self.topological_sort()
        all_outputs = dict(external_inputs)

        for node_id in execution_order:
            node = self.nodes[node_id]
            module = node.module

            # Gather inputs for this module
            module_inputs = {}
            for input_name in module.inputs:
                if input_name in all_outputs:
                    module_inputs[input_name] = all_outputs[input_name]

            # Gather parameters for this module
            module_params = {}
            for param_name, param_ref in module.parameters.items():
                if param_ref.key in parameters:
                    module_params[param_name] = parameters[param_ref.key]
                elif param_ref.fallback is not None:
                    module_params[param_name] = param_ref.fallback
                else:
                    raise ValueError(
                        f"Required parameter '{param_ref.key}' not found for module '{node_id}'"
                    )

            # Execute module
            outputs = module.compute(module_inputs, module_params)

            # Store outputs
            for output_name, value in outputs.items():
                all_outputs[output_name] = value

        return all_outputs
