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
    SectionalData, ProbesData, ChordwiseData, IntegralData, HingeData (with .from_file() class methods)
airfoil : Airfoil data generation (C81 format)
    Airfoil (with Airfoil.generate() class method)
"""

# Import submodules for grouped access
from . import mesh
from . import postpro
from . import airfoil

# Top-level convenience imports (for direct import style)
from .build_mesh import (
    MeshConfig,
    PointwiseMesh,
    ParametricMesh,
)

from .c81generator import (
    Airfoil,
)

from .parse_postpro_files import (
    SectionalData,
    ProbesData,
    ChordwiseData,
    IntegralData,
    HingeData,
)

__version__ = "0.1.8"

__all__ = [
    # Submodules
    "mesh",
    "postpro",
    "airfoil",
    # Mesh building - Main classes
    "MeshConfig",
    "PointwiseMesh",
    "ParametricMesh",
    # Airfoil generation - Data structures
    "Airfoil",
    # Post-processing - Data structures
    "SectionalData",
    "ProbesData",
    "ChordwiseData",
    "IntegralData",
    "HingeData",
]
