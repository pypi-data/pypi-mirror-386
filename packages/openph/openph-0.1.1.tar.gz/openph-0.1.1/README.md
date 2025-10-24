# OpenPH

**Core PHPP data models and table view generation**

Part of the `openph` UV workspace - a Python implementation of Passive House Planning Package (PHPP) calculations with exact numerical fidelity to Excel PHPP.

## Purpose

OpenPH provides:
- **Data Models**: Python classes representing PHPP building components (areas, constructions, rooms, climate, HVAC systems)
- **Table Views**: Generate formatted output tables (.txt, .html) matching PHPP worksheet layouts for validation
- **HBJSON Import**: Convert Honeybee-PH JSON models to OpenPH data structures

## Structure

```
openph/
├── src/
│   └── openph/         # Main package module
│       ├── model/      # PHPP data classes
│       ├── table_views/# PHPP-formatted output tables
│       ├── from_HBJSON/# Honeybee-PH JSON import
│       └── phpp.py     # Main PHPP container class
├── tests/
└── pyproject.toml
```

## Usage

```python
from openph.phpp import OpPhPHPP

# Create PHPP model
phpp = OpPhPHPP()

# Access model components
phpp.climate
phpp.areas
phpp.rooms

# Generate PHPP-style table outputs for validation
from openph.table_views import heating_demand
table = heating_demand.generate_table(phpp)
```

## Development

Part of UV workspace - see root `context/ENVIRONMENT.md`:
```bash
uv sync                      # Install all workspace packages
uv run pytest openph/tests/  # Run tests
```
