"""
pydust_utils: Custom tools for DUST preprocessing and postprocessing.

This package provides utilities for:
- Mesh generation (pointwise and parametric)
- Airfoil data generation (C81 format)
- Post-processing file parsing

Usage Styles
------------

**Style 1: Grouped imports (recommended for multiple items)**
    >>> from pydust_utils import mesh
    >>> config = mesh.MeshConfig('Wing', 'v', 20, 'uniform', 0.25)
    >>> point = mesh.Point(0, 0, 0, 1.0, 0, 'naca0012')
    >>> my_mesh = mesh.PointwiseMesh(config, [point], [line])

**Style 2: Direct imports (recommended for few items)**
    >>> from pydust_utils import PointwiseMesh, Point, Line
    >>> point = Point(0, 0, 0, 1.0, 0, 'naca0012')

**Style 3: Module-level access**
    >>> import pydust_utils.mesh as dm
    >>> point = dm.Point(0, 0, 0, 1.0, 0, 'naca0012')

Submodules
----------
mesh : Mesh building utilities
    Point, Line, Section, Region, MeshConfig, PointwiseMesh, ParametricMesh
postpro : Post-processing parsers
    read_sectional, read_probes, read_chordwise, read_integral, read_hinge
airfoil : Airfoil data generation (C81 format)
    Airfoil, generate_airfoil_data
visualization : Visualization utilities
    ColorMapManager, FlowPostProcessor, plot_dustpre_pv
"""

# Import submodules for grouped access
from . import mesh
from . import postpro
from . import airfoil
from . import visualization

# Top-level convenience imports (for direct import style)
from .build_mesh import (
    Point,
    Line,
    Section,
    Region,
    MeshConfig,
    PointwiseMesh,
    ParametricMesh,
    write_pointwise_mesh,
    write_parametric_mesh,
)

from .c81generator import (
    Airfoil,
    generate_airfoil_data,
)

from .parse_postpro_files import (
    SectionalData,
    ProbesData,
    ChordwiseData,
    IntegralData,
    HingeData,
    read_sectional,
    read_probes,
    read_chordwise,
    read_integral,
    read_hinge,
)

from .visualization import (
    ColorMapManager,
    FlowPostProcessor,
    plot_dustpre_pv,
)

__version__ = "0.1.7"

__all__ = [
    # Submodules
    "mesh",
    "postpro",
    "airfoil",
    "visualization",
    # Mesh building - Data structures
    "Point",
    "Line",
    "Section",
    "Region",
    "MeshConfig",
    # Mesh building - Containers
    "PointwiseMesh",
    "ParametricMesh",
    # Mesh building - Functions
    "write_pointwise_mesh",
    "write_parametric_mesh",
    # Airfoil generation - Data structures
    "Airfoil",
    # Airfoil generation - Functions
    "generate_airfoil_data",
    # Post-processing - Data structures
    "SectionalData",
    "ProbesData",
    "ChordwiseData",
    "IntegralData",
    "HingeData",
    # Post-processing - Functions
    "read_sectional",
    "read_probes",
    "read_chordwise",
    "read_integral",
    "read_hinge",
    # Visualization - Classes
    "ColorMapManager",
    "FlowPostProcessor",
    # Visualization - Functions
    "plot_dustpre_pv",
]
