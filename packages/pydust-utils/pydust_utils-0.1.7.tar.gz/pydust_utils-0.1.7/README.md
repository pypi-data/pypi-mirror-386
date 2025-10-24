# PyDUST Utils

[![PyPI version](https://badge.fury.io/py/pydust-utils.svg)](https://pypi.org/project/pydust-utils/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen.svg)](https://github.com/yourusername/pydust-utils)
[![Tests](https://img.shields.io/badge/tests-156%20passed-brightgreen.svg)](https://github.com/yourusername/pydust-utils)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python utilities for DUST pre- and post-processing.

## Features

- **Mesh Generation**: Create pointwise and parametric meshes for DUST simulations
- **C81 Airfoil Data**: Generate aerodynamic tables using NeuralFoil/AeroSandbox
- **Post-Processing**: Parse and analyze DUST output files (sectional loads, probes, integral forces)
- **Visualization**: 3D visualization of meshes, flow fields, and vortex structures with PyVista

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

### Generation of Pointwise Mesh

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
    Point(
        id=1, 
        coordinates=[0.0, 0.0, 0.0], 
        chord=1.0, 
        twist=0.0, 
        airfoil='naca0012', 
        airfoil_table='naca0012'
    ),
    Point(
        id=2, 
        coordinates=[0.0, 5.0, 0.5], 
        chord=0.8, 
        twist=-2.0, 
        airfoil='naca0012', 
        airfoil_table='naca0012'
    ),
]

# Connect points with lines
lines = [
    Line(
        type='spline', 
        nelem_line=10, 
        end_points=[1, 2], 
        type_span='uniform'
    )
]

# Generate mesh file
mesh = PointwiseMesh(config, points, lines)
mesh.write('wing_pointwise.in')
```

### Generation of Parametric Mesh
```python
from pydust_utils.build_mesh import Section, Region, MeshConfig, ParametricMesh

# Create mesh configuration
config = MeshConfig(
    title='Wing Mesh',
    el_type='v',  # vortex-lattice
    nelem_chord=20,
    type_chord='cosine_le'
)

# Define wing geometry with points
sections = [
    Section(
        chord=1.0, 
        twist=0.0, 
        airfoil='naca0012', 
        airfoil_table='naca0012'
    ),
    Section(
        chord=0.8, 
        twist=-2.0, 
        airfoil='naca0012', 
        airfoil_table='naca0012'
    ),
]

# Connect points with lines
regions = [
    Region(
        sweep=0, 
        dihed=2,
        nelem_span=10, 
        type_span='uniform'
    )
]

# Generate mesh file
mesh = ParametricMesh(config, sections, regions)
mesh.write('wing_parametric.in')
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

### Visualization

```python
import h5py
import pyvista as pv
from pydust_utils import ColorMapManager, FlowPostProcessor, plot_dustpre_pv

# Visualize DUST pre-processor mesh from HDF5 output
with h5py.File('geo_input.h5', 'r') as f:
    rr = f['Components/Comp001/Geometry/rr'][:]
    ee = f['Components/Comp001/Geometry/ee'][:]

plotter = plot_dustpre_pv(rr, ee, title="Blade Mesh", rendering_backend="trame")

# Load custom colormap and create flow post-processor
cm_manager = ColorMapManager('colormaps/cool_warm.json')
flow_viz = FlowPostProcessor(colormap_manager=cm_manager)

# Visualize Q-criterion for vortex identification
flow_data = pv.read('flow_volume.vtr')
plotter = flow_viz.visualize_q_criterion(
    flow_data,
    q_min=0.01,
    q_max=10.0,
    opacity=0.3,
    colormap='cool_warm'
)
plotter.show()

# Visualize vorticity with vector glyphs
flow_slice = pv.read('flow_slice.vtr')
plotter = flow_viz.visualize_vorticity_glyphs(
    flow_slice,
    scale=0.1,
    opacity=0.7,
    glyph_type='arrow'
)
plotter.show()
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

### Visualization (`visualization`)
- **plot_dustpre_pv**: Visualize DUST pre-processor mesh output (HDF5 files)
  - Interactive (trame) and static rendering modes
  - Support for main and virtual mesh elements
  - Customizable colors, edges, and camera settings
- **ColorMapManager**: Load and manage custom colormaps from ParaView/Matplotlib
- **FlowPostProcessor**: Advanced flow field visualization
  - Q-criterion and Lambda2 vortex identification
  - Vorticity magnitude and vector field glyphs
  - Sectional flow visualization with customizable styling


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

**Current Status**: 156 tests, 94% coverage 

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
