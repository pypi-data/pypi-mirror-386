# PyDUST Utils

[![PyPI version](https://badge.fury.io/py/pydust-utils.svg)](https://pypi.org/project/pydust-utils/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python utilities for DUST pre- and post-processing.

## Features

- **Mesh Generation**: Create pointwise and parametric meshes for DUST simulations
- **C81 Airfoil Data**: Generate aerodynamic tables using NeuralFoil/AeroSandbox
- **Post-Processing**: Parse and analyze DUST output files (sectional loads, probes, integral forces)
- **Type-Safe**: Full type hints with mypy compliance
- **Well-Tested**: 95% test coverage with 111+ tests

## Installation

**Simple installation from PyPI:**

```bash
pip install pydust-utils
```

**For development:**

```bash
git clone git@gitlab.com:Alecocco.1994/dust-private.git
cd dust-private/pydust_utils
pip install -e ".[dev,docs]"
```

## Quick Start

### Mesh Generation

```python
from pydust_utils.build_mesh import Point, Line, MeshConfig, PointwiseMesh

# Create mesh configuration
config = MeshConfig(
    title='Wing Mesh',
    el_type='v',  # vortex-lattice
    nelem_chord=20,
    type_chord='cosine_le'
)

# Define wing geometry with points
points = [
    Point(1, [0.0, 0.0, 0.0], 1.0, 0.0, 'naca0012', 'naca0012'),
    Point(2, [0.0, 5.0, 0.5], 0.8, -2.0, 'naca0012', 'naca0012'),
]

# Connect points with lines
lines = [
    Line('spline', 10, [1, 2], 'uniform')
]

# Generate mesh file
mesh = PointwiseMesh(config, points, lines)
mesh.write('wing.in')
```

### C81 Airfoil Data Generation

```python
from pydust_utils.c81generator import generate_airfoil_data

# Generate C81 aerodynamic table
airfoil = generate_airfoil_data(
    file_name='naca0012',
    pathprofile='airfoils/',
    reynolds=1e6,
    mach_range=(0.0, 0.3),
    n_mach=10,
    mbdynformat=False  # Use DUST format
)
```

### Post-Processing

```python
from pydust_utils import read_sectional, read_probes, read_integral

# Read sectional loads
sectional_data = read_sectional('sectional_loads.dat')
print(sectional_data.sec.shape)  # (n_time, n_sec)

# Read probe velocities
probe_data = read_probes('probes_velocity.dat')
print(probe_data.velocities.shape)  # (n_time, n_probes, 3)

# Read integral loads
integral_data = read_integral('integral_loads.dat')
lift = integral_data.forces[:, 2]  # Extract lift force
```

## Available Features

### Mesh Generation (`build_mesh`)
- **Pointwise meshes**: Define geometry with specific control points
- **Parametric meshes**: Use sections and regions for automatic interpolation
- **Multiple element types**: Vortex-lattice ('v'), lifting-line ('l'), panel ('p')
- **Advanced distributions**: Uniform, cosine, geometric series with refinement options

### Airfoil Data (`c81generator`)
- **C81 table generation**: Create aerodynamic coefficient tables
- **NeuralFoil integration**: Use neural networks for predictions
- **Multiple Reynolds numbers**: Support for Re-dependent tables
- **DUST and MBDyn formats**: Compatible with multiple solvers

### Post-Processing (`parse_postpro_files`)
- `read_sectional` - Sectional aerodynamic loads
- `read_probes` - Velocity probe data
- `read_chordwise` - Chordwise pressure distributions
- `read_integral` - Integral loads and forces
- `read_hinge` - Hinge loads for control surfaces

## Documentation

- **PyPI**: https://pypi.org/project/pydust-utils/
- **Online Docs**: https://alecocco.1994.gitlab.io/dust-private/ (GitLab Pages)

Build documentation locally:

```bash
cd pydust_utils
pip install -e ".[docs]"
sphinx-build -b html docs/source docs/build/html
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

**Current Status**: 111 tests, 95% coverage ✅

## Contributing

This package is developed and maintained by the DUST team at Politecnico di Milano.

## Publishing

Build and upload to PyPI (maintainers only):

```bash
# Build distribution
pip install build
python -m build

# Upload to PyPI
pip install twine
twine upload dist/*
```

## Links

- **PyPI Package**: https://pypi.org/project/pydust-utils/
- **Documentation**: https://alecocco.1994.gitlab.io/dust-private/
- **DUST Homepage**: https://www.dust.polimi.it/
- **Repository**: https://public.gitlab.polimi.it/DAER/dust

## License

MIT License - Copyright (c) 2025 Alessandro Cocco, Politecnico di Milano

---

**Made with ❤️ by the DUST team at Politecnico di Milano**
