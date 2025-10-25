"""Convenience module for mesh building.

This module provides all mesh-related classes and functions in one place.

The module structure has been reorganized:
- MeshConfig: Shared configuration class
- PointwiseMesh: Main class with nested Point and Line classes
- ParametricMesh: Main class with nested Section and Region classes

Example:
    >>> from pydust_utils import mesh
    >>> config = mesh.MeshConfig('Wing', 'v', 20, 'uniform', 0.25)
    >>> point = mesh.PointwiseMesh.Point(1, [0, 0, 0], 1.0, 0, 'naca0012')
    >>> line = mesh.PointwiseMesh.Line('straight', 10, [1, 2], 'uniform')
    >>> my_mesh = mesh.PointwiseMesh(config, [point], [line])
"""

from .build_mesh import (
    MeshConfig,
    PointwiseMesh,
    ParametricMesh,
)

__all__ = [
    "MeshConfig",
    "PointwiseMesh",
    "ParametricMesh",
]
