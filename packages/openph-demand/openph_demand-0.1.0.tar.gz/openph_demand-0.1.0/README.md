# OpenPH-Demand

**Heating, cooling, and ground demand calculations for PHPP**

Part of the `openph` UV workspace - implements PHPP energy demand calculations with exact numerical fidelity to Excel PHPP.

## Purpose

OpenPH-Demand calculates:
- **Annual Heating Demand**: Transmission and ventilation heat losses, internal/solar gains
- **Annual Cooling Demand**: Solar gains, internal gains, cooling strategies
- **Ground Heat Transfer**: Temperature calculations for ground-coupled surfaces
- **Peak Heating/Cooling Loads**: Design load calculations

## Structure

```
openph-demand/
├── src/
│   └── openph_demand/
│       ├── heating_demand/
│       ├── cooling_demand/
│       ├── ground/
│       ├── get_solvers.py
│       └── solvers.py
├── tests/
└── pyproject.toml
```

## Usage

```python
from openph_demand import get_solvers

# Get demand solvers
heating_solver = get_solvers.get_heating_demand_solver()
cooling_solver = get_solvers.get_cooling_demand_solver()

# Calculate annual demands (kWh/m²·a)
annual_heating = heating_solver.calculate(phpp_model)
annual_cooling = cooling_solver.calculate(phpp_model)
```

## Development

Part of UV workspace - see root `context/ENVIRONMENT.md`:
```bash
uv sync                           # Install all workspace packages
uv run pytest openph-demand/tests/ # Run tests
```