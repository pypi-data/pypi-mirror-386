# OpenPH-Solar

**Solar radiation and shading calculations for PHPP**

Part of the `openph` UV workspace - provides solar calculations matching PHPP methodology.

## Purpose

OpenPH-Solar calculates:
- Solar radiation on window surfaces
- Shading factors and obstructions
- Solar heat gains for heating/cooling demand
- Monthly and hourly calculation periods

## Structure

```
openph-solar/
├── src/
│   └── openph_solar/
│       ├── calc_periods.py
│       ├── get_solvers.py
│       └── solvers.py
├── tests/
└── pyproject.toml
```

## Usage

```python
from openph_solar import get_solvers, solvers

# Get available solar solvers
solar_solver = get_solvers.get_solar_solver()

# Calculate solar radiation
radiation = solar_solver.calculate(window, climate_data)
```

## Development

Part of UV workspace - see root `context/ENVIRONMENT.md`:
```bash
uv sync                           # Install all workspace packages
uv run pytest openph-solar/tests/ # Run tests
```