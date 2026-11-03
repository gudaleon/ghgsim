# Object-Oriented Design for ghgsim (Reichert 1995 AQUASIM Structure)

**Version:** AN_v1  
**Date:** 2026-11-01  
**Reference:** Reichert, P. (1995). Design techniques of a computer program for the identification of processes and the simulation of water quality in aquatic systems. Environmental Software, 10(3), 199-210.

---

## Executive Summary

This document describes the object-oriented architecture for ghgsim based on Reichert's AQUASIM structure, where users define equations rather than edit hard-coded models. The design separates concerns into four class hierarchies (Variables, Processes, Compartments, Links) and maps them onto ghgsim's existing module protocol and YAML graph system.

---

## Reichert (1995) AQUASIM Structure

### Core Philosophy

> "The problem of model identification... requires a flexible software tool that allows the user to define process rate expressions and stoichiometry rather than being restricted to predefined models."  
> — Reichert (1995), p. 199

### Four Class Hierarchies

1. **Variables**
   - State variables (evolve over time, e.g., animal weight, manure N content)
   - Input variables (external forcing, e.g., diet composition, temperature)
   - Parameter variables (constants or distributions, e.g., Ym, B0, EF1)
   - Program variables (derived/calculated, e.g., GE from net energy, VS from GE)

2. **Processes**
   - Rate expressions with stoichiometry
   - Transform state variables via defined equations
   - Example: Enteric CH4 = GE × Ym / 55.65 × (1 - additive_reduction)

3. **Compartments**
   - Spatial or logical domains where processes occur
   - Examples: Animal group, manure storage, soil field
   - Each compartment has its own state variable values

4. **Links**
   - Connect compartments
   - Transfer material/energy between compartments
   - Example: Manure N from animal → manure store → soil

---

## Mapping to ghgsim

### Current ghgsim Architecture

**Strengths:**
- Module protocol with inputs/parameters/outputs
- YAML graph for connecting modules
- Parameter registry with uncertainty distributions
- Ensemble services (Monte Carlo, Sobol)

**Limitations:**
- Hard-coded equations in Python `compute()` methods
- No user-definable rate expressions
- Compartments implicit, not explicit objects
- Limited stoichiometric tracking

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User-Facing Layer                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   YAML     │  │  Equation  │  │  Parameter │            │
│  │  Workflow  │  │  Defs      │  │   Files    │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  ghgsim Core (Enhanced)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Variable System                                      │  │
│  │  - StateVar, InputVar, ParamVar, ProgVar             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Process System                                       │  │
│  │  - ProcessDef (user equations), Stoichiometry        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Compartment System                                   │  │
│  │  - AnimalGroup, ManureStore, SoilField               │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Link System                                          │  │
│  │  - MaterialFlow, EnergyFlow                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              Existing ghgsim Infrastructure                  │
│  Module Protocol | Registry | Ensemble | Graph | API        │
└─────────────────────────────────────────────────────────────┘
```

---

## Class Design

### 1. Variable Classes

```python
from abc import ABC, abstractmethod
from typing import Any, Optional
from ghgsim.core.units import Unit

class Variable(ABC):
    """Base class for all variables (Reichert 1995 hierarchy)."""
    
    def __init__(self, name: str, unit: Unit, description: str):
        self.name = name
        self.unit = unit
        self.description = description
        self.value: Optional[Any] = None
    
    @abstractmethod
    def get_type(self) -> str:
        """Return variable type (state/input/parameter/program)."""
        pass

class StateVariable(Variable):
    """State variable that evolves over time."""
    
    def __init__(self, name: str, unit: Unit, description: str, initial_value: float):
        super().__init__(name, unit, description)
        self.value = initial_value
        self.history = [initial_value]
    
    def update(self, new_value: float):
        """Update state and record history."""
        self.value = new_value
        self.history.append(new_value)
    
    def get_type(self) -> str:
        return "state"

class InputVariable(Variable):
    """External input/forcing variable."""
    
    def get_type(self) -> str:
        return "input"

class ParameterVariable(Variable):
    """Parameter with optional uncertainty distribution."""
    
    def __init__(self, name: str, unit: Unit, description: str, 
                 value: float, distribution: Optional[str] = None,
                 dist_params: Optional[dict] = None):
        super().__init__(name, unit, description)
        self.value = value
        self.distribution = distribution
        self.dist_params = dist_params or {}
    
    def get_type(self) -> str:
        return "parameter"

class ProgramVariable(Variable):
    """Calculated/derived variable from equation."""
    
    def __init__(self, name: str, unit: Unit, description: str, 
                 equation: str, dependencies: list[str]):
        super().__init__(name, unit, description)
        self.equation = equation
        self.dependencies = dependencies
    
    def compute(self, context: dict[str, Any]) -> float:
        """Evaluate equation given context of other variables."""
        # Safe eval with only math operations and context vars
        return eval(self.equation, {"__builtins__": {}}, context)
    
    def get_type(self) -> str:
        return "program"
```

### 2. Process Classes

```python
class ProcessDef:
    """User-definable process with rate expression and stoichiometry."""
    
    def __init__(self, name: str, description: str, rate_equation: str,
                 stoichiometry: dict[str, float]):
        self.name = name
        self.description = description
        self.rate_equation = rate_equation  # User-provided equation string
        self.stoichiometry = stoichiometry  # {"CH4": +1, "GE": -1} etc.
        self.sources = []  # Citation list
    
    def add_source(self, doi_or_url: str, equation: str, page: str):
        """Add citation for traceability."""
        self.sources.append({
            "source": doi_or_url,
            "equation": equation,
            "page": page
        })
    
    def compute_rate(self, variables: dict[str, Any]) -> float:
        """Evaluate rate equation given variable context."""
        # Safe evaluation with math library
        import math
        safe_dict = {"__builtins__": {}, "math": math}
        safe_dict.update(variables)
        return eval(self.rate_equation, safe_dict)
    
    def apply_stoichiometry(self, rate: float, state_vars: dict[str, StateVariable]):
        """Apply stoichiometric changes to state variables."""
        for var_name, coeff in self.stoichiometry.items():
            if var_name in state_vars:
                current = state_vars[var_name].value
                state_vars[var_name].update(current + rate * coeff)


# Example process definitions
enteric_ch4_process = ProcessDef(
    name="enteric_methane",
    description="Enteric CH4 from cattle",
    rate_equation="GE * (Ym / 100.0) * 365.0 / 55.65",
    stoichiometry={"CH4_kg_yr": +1.0}
)
enteric_ch4_process.add_source(
    doi_or_url="IPCC 2006 Vol4 Ch10",
    equation="Equation 10.21",
    page="10.30"
)
```

### 3. Compartment Classes

```python
class Compartment:
    """Spatial/logical domain where processes occur."""
    
    def __init__(self, name: str, compartment_type: str):
        self.name = name
        self.type = compartment_type
        self.state_vars: dict[str, StateVariable] = {}
        self.processes: list[ProcessDef] = []
        self.links: list['Link'] = []
    
    def add_state_variable(self, var: StateVariable):
        """Add a state variable to this compartment."""
        self.state_vars[var.name] = var
    
    def add_process(self, process: ProcessDef):
        """Add a process that acts on this compartment."""
        self.processes.append(process)
    
    def step(self, dt: float, inputs: dict, params: dict):
        """Advance compartment by one time step."""
        # Gather all variable values
        context = {}
        context.update({v.name: v.value for v in self.state_vars.values()})
        context.update(inputs)
        context.update(params)
        
        # Execute each process
        for process in self.processes:
            rate = process.compute_rate(context)
            process.apply_stoichiometry(rate * dt, self.state_vars)


# Example compartments
animal_group = Compartment("dairy_herd", "AnimalGroup")
animal_group.add_state_variable(StateVariable("weight", Unit("kg"), "Animal weight", 687))
animal_group.add_state_variable(StateVariable("CH4_cumulative", Unit("kg"), "Cumulative CH4", 0))
animal_group.add_process(enteric_ch4_process)
```

### 4. Link Classes

```python
class Link:
    """Transfer between compartments."""
    
    def __init__(self, name: str, from_comp: Compartment, to_comp: Compartment,
                 transfer_var: str, transfer_equation: str):
        self.name = name
        self.from_comp = from_comp
        self.to_comp = to_comp
        self.transfer_var = transfer_var
        self.transfer_equation = transfer_equation
    
    def execute_transfer(self, dt: float, context: dict):
        """Transfer material/energy between compartments."""
        amount = eval(self.transfer_equation, {"__builtins__": {}}, context) * dt
        
        # Remove from source
        if self.transfer_var in self.from_comp.state_vars:
            current = self.from_comp.state_vars[self.transfer_var].value
            self.from_comp.state_vars[self.transfer_var].update(current - amount)
        
        # Add to destination
        if self.transfer_var in self.to_comp.state_vars:
            current = self.to_comp.state_vars[self.transfer_var].value
            self.to_comp.state_vars[self.transfer_var].update(current + amount)


# Example link
manure_n_link = Link(
    name="manure_to_soil",
    from_comp=animal_group,
    to_comp=soil_field,
    transfer_var="N_kg",
    transfer_equation="Nex_rate * head"
)
```

---

## Integration with Existing ghgsim

### Backwards Compatibility Layer

```python
class LegacyModuleAdapter:
    """Wrap existing hard-coded modules as Compartments."""
    
    def __init__(self, module_class):
        self.module = module_class()
        self.compartment = self._build_compartment()
    
    def _build_compartment(self) -> Compartment:
        """Convert module inputs/outputs to compartment state vars."""
        comp = Compartment(self.module.id, "LegacyModule")
        
        # Inputs → InputVariables
        for name, spec in self.module.inputs.items():
            var = InputVariable(name, spec.units, spec.description)
            # Store for later
        
        # Outputs → StateVariables (simplified)
        for name, spec in self.module.outputs.items():
            var = StateVariable(name, spec.units, spec.description, 0.0)
            comp.add_state_variable(var)
        
        return comp
    
    def step(self, dt: float, inputs: dict, params: dict):
        """Execute legacy module compute() method."""
        result = self.module.compute(inputs, params)
        for name, value in result.items():
            if name in self.compartment.state_vars:
                self.compartment.state_vars[name].update(value)
```

### YAML Workflow Format (Extended)

```yaml
# Example: User-defined cattle model
compartments:
  - name: dairy_herd
    type: AnimalGroup
    state_variables:
      - name: weight
        unit: kg
        initial: 687
      - name: CH4_total
        unit: kg
        initial: 0
    
    processes:
      - name: enteric_ch4
        rate_equation: "GE * (Ym / 100.0) / 55.65"
        stoichiometry:
          CH4_total: +1.0
        sources:
          - doi: "IPCC 2006 Vol4 Ch10"
            equation: "Equation 10.21"
            page: "10.30"
      
      - name: weight_gain
        rate_equation: "ADG"
        stoichiometry:
          weight: +1.0
    
    program_variables:
      - name: GE
        unit: MJ/day
        equation: "(NE_m + NE_a + NE_l) / RE_m / (TDN / 100.0)"
        dependencies: [NE_m, NE_a, NE_l, RE_m, TDN]

links:
  - name: manure_n_flow
    from: dairy_herd
    to: manure_store
    variable: N_kg
    equation: "Nex_rate * head * (1 - FracPRP)"

parameters:
  Ym:
    value: 5.6
    unit: "% GE"
    distribution: uniform
    dist_lower: 5.5
    dist_upper: 5.7
    source: "Holos Table 18/26; ECCC 2022"
```

---

## Implementation Phases

### Phase 1: Core Variable System (Immediate)
- Implement Variable class hierarchy
- Add to `src/ghgsim/core/variables.py`
- Test with simple examples

### Phase 2: Process System (Next)
- Implement ProcessDef with safe equation evaluation
- Add stoichiometry tracking
- Integrate with existing modules

### Phase 3: Compartment System (Then)
- Implement Compartment class
- Build LegacyModuleAdapter
- Test side-by-side with hard-coded modules

### Phase 4: Link System (Finally)
- Implement Link class
- Extend YAML parser for new format
- Full user-defined workflow support

---

## Benefits

1. **User Flexibility:** Define custom equations without editing code
2. **Traceability:** Every process links to source DOI/URL/page
3. **Modularity:** Compartments are independent, reusable
4. **Testability:** Each process can be unit-tested
5. **Extensibility:** Add new compartments/processes via YAML
6. **Backwards Compatibility:** Legacy modules work via adapter

---

## Example: Dairy Farm Model

```python
# User-defined dairy farm with Reichert structure

# Define compartments
dairy_cows = Compartment("lactating_cows", "AnimalGroup")
dairy_cows.add_state_variable(StateVariable("weight", Unit("kg"), "Weight", 687))
dairy_cows.add_state_variable(StateVariable("CH4", Unit("kg"), "CH4", 0))
dairy_cows.add_state_variable(StateVariable("N_manure", Unit("kg"), "Manure N", 0))

manure_tank = Compartment("liquid_manure", "ManureStore")
manure_tank.add_state_variable(StateVariable("N_stored", Unit("kg"), "Stored N", 0))
manure_tank.add_state_variable(StateVariable("CH4", Unit("kg"), "CH4", 0))

corn_field = Compartment("field_1", "SoilField")
corn_field.add_state_variable(StateVariable("N_applied", Unit("kg"), "Applied N", 0))
corn_field.add_state_variable(StateVariable("N2O", Unit("kg"), "N2O", 0))

# Define processes
enteric = ProcessDef("enteric_ch4", "...", "GE * Ym / 55.65", {"CH4": +1})
manure_n = ProcessDef("n_excretion", "...", "Nrate * weight / 1000", {"N_manure": +1})
manure_ch4 = ProcessDef("manure_ch4", "...", "VS * B0 * MCF * 0.67", {"CH4": +1})
soil_n2o = ProcessDef("soil_n2o", "...", "N_applied * EF1 * 44/28", {"N2O": +1})

dairy_cows.add_process(enteric)
dairy_cows.add_process(manure_n)
manure_tank.add_process(manure_ch4)
corn_field.add_process(soil_n2o)

# Define links
n_to_tank = Link("excreta", dairy_cows, manure_tank, "N_manure", "N_manure")
n_to_field = Link("application", manure_tank, corn_field, "N_stored", "N_stored * 0.8")

# Run simulation
for day in range(365):
    dairy_cows.step(1.0, inputs, params)
    manure_tank.step(1.0, inputs, params)
    n_to_tank.execute_transfer(1.0, {})
    # ... application event
    n_to_field.execute_transfer(1.0, {})
    corn_field.step(1.0, inputs, params)
```

---

## Conclusion

This OOP design follows Reichert (1995) principles while maintaining compatibility with ghgsim's existing infrastructure. Users can now define models via YAML equations rather than editing Python code, enabling true model flexibility and scientific traceability.

**Next Steps:**
1. Implement Phase 1 (Variable system)
2. Update Holos modules to use new structure
3. Document user workflow examples
4. Extend YAML schema

---

**Document:** OOP_DESIGN_AN_v1.md  
**Reference:** Reichert (1995), Environmental Software 10(3):199-210  
**Date:** 2026-11-01
