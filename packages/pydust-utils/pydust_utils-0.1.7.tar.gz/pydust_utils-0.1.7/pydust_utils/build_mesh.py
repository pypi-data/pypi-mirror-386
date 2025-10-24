"""Build mesh configuration files for DUST simulations.

This module provides functions to write pointwise and parametric mesh files
in the format expected by the DUST solver.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, TextIO

import numpy as np

__all__ = [
    "Point",
    "Line",
    "Section",
    "Region",
    "MeshConfig",
    "PointwiseMesh",
    "ParametricMesh",
    "write_pointwise_mesh",
    "write_parametric_mesh",
]


# Dataclass definitions for better type safety and validation
@dataclass
class Point:
    """Mesh point with geometric and aerodynamic properties.

    Attributes
    ----------
    id : int
        Unique point identifier (1-based index)
    coordinates : list[float]
        Cartesian coordinates [x, y, z] in the component reference frame
    chord : float
        Local chord length
    twist : float
        Local twist angle (degrees)
    airfoil : str
        Airfoil section name (without .dat extension)
    airfoil_table : str
        Airfoil aerodynamic table name (without .c81 extension)
    section_normal : str, optional
        Section normal definition (reference_line, y_axis, y_axis_neg, vector)
    flip_section : bool, optional
        Whether to flip the airfoil section vertically
    """

    id: int
    coordinates: list[float]
    chord: float
    twist: float
    airfoil: str = "interp"
    airfoil_table: Optional[str] = None
    section_normal: str = "reference_line"
    section_normal_vector: Optional[list[float]] = field(
        default_factory=lambda: [0.0, 1.0, 0.0]
    )
    flip_section: bool = False

    def __post_init__(self):
        """Validate point attributes."""
        if self.id <= 0:
            raise ValueError(f"Point id must be positive, got {self.id}")

        if len(self.coordinates) != 3:
            raise ValueError(
                f"Coordinates must be a list of three floats, got {self.coordinates}"
            )

        if self.section_normal not in (
            "reference_line",
            "y_axis",
            "y_axis_neg",
            "vector",
        ):
            raise ValueError(
                f"Invalid section_normal '{self.section_normal}' for point"
            )

        if self.section_normal == "vector":
            if not self.section_normal_vector or len(self.section_normal_vector) != 3:
                raise ValueError(
                    f"section_normal_vector must be a list of three floats when "
                    f"section_normal is 'vector', got {self.section_normal_vector}"
                )


@dataclass
class Line:
    """Line definition for pointwise mesh.

    Attributes
    ----------
    type : str
        Line type ('spline' or 'straight')
    end_points : list[int]
        List of two point IDs defining the line endpoints (1-based indices)
    nelem_line : int
        Number of elements along line
    type_span : str
        Spanwise discretization type: could be 'uniform', 'cosine', 'cosine_ib', 'cosine_ob', 'geoseries', 'geoseries_ob', 'geoseries_ib'
    r_ob : float, optional
        Outer boundary ratio for geoseries
    r_ib : float, optional
        Inner boundary ratio for geoseries
    y_refinement : float, optional
        Refinement location for geoseries [adimensional]
    tangent_vec_1 : list[float], optional
        Tangent vector at the first endpoint (required for 'spline' type)
    tangent_vec_2 : list[float], optional
        Tangent vector at the second endpoint (required for 'spline' type)
    tension : float, optional
        Tension parameter for spline lines
    bias : float, optional
        Bias parameter for spline lines
    """

    type: str
    nelem_line: int
    end_points: list[int] = field(default_factory=lambda: [1, 2])
    type_span: str = "uniform"
    r_ob: Optional[float] = None
    r_ib: Optional[float] = None
    y_refinement: Optional[float] = None
    tangent_vec_1: Optional[list[float]] = field(
        default_factory=lambda: [0.0, 0.0, 0.0]
    )
    tangent_vec_2: Optional[list[float]] = field(
        default_factory=lambda: [0.0, 0.0, 0.0]
    )
    tension: Optional[float] = None
    bias: Optional[float] = None

    def __post_init__(self):
        """Validate line type."""

        if self.type not in ("spline", "straight"):
            raise ValueError(
                f"Line type must be 'spline' or 'straight', got '{self.type}'"
            )

        if self.type_span not in (
            "uniform",
            "cosine",
            "cosine_ib",
            "cosine_ob",
            "geoseries",
            "geoseries_ob",
            "geoseries_ib",
        ):
            raise ValueError(f"Invalid type_span '{self.type_span}' for line")

        if self.nelem_line <= 0:
            raise ValueError(f"nelem_line must be positive, got {self.nelem_line}")

        if self.end_points[0] < 1 or self.end_points[1] < 1:
            raise ValueError(
                f"end_points must be positive 1-based indices, got {self.end_points}"
            )

        # Note: We cannot check if points are coincident here because we don't have
        # access to the Point objects. This is validated in PointwiseMesh.__post_init__
        if self.end_points[0] == self.end_points[1]:
            raise ValueError(
                f"end_points must refer to two different point IDs, got {self.end_points}"
            )

        for attr in ("r_ob", "r_ib", "y_refinement"):
            val = getattr(self, attr)
            if val is None:
                continue
            if not (0.0 < val < 1.0):
                raise ValueError(f"{attr} must be > 0 and < 1, got {val}")


@dataclass
class Section:
    """Section definition for parametric mesh.

    Attributes
    ----------
    chord : float
        Section chord length
    twist : float
        Section twist angle (degrees)
    airfoil : str
        Airfoil section name (without .dat extension)
    airfoil_table : str, optional
        Airfoil aerodynamic table name (without .c81 extension)
    """

    chord: float
    twist: float
    airfoil: str
    airfoil_table: str = ""


@dataclass
class Region:
    """Region definition for parametric mesh.

    Attributes
    ----------
    span : float
        Region span length
    sweep : float
        Sweep angle (degrees)
    dihed : float
        Dihedral angle (degrees)
    nelem_span : int
        Number of elements along span
    type_span : str
        Spanwise discretization type: could be 'uniform', 'cosine', 'cosine_ib', 'cosine_ob', 'geoseries', 'geoseries_ob', 'geoseries_ib'
    r_ob : float, optional
        Outer boundary ratio for geoseries
    r_ib : float, optional
        Inner boundary ratio for geoseries
    y_refinement : float, optional
        Refinement location for geoseries
    """

    span: float
    sweep: float
    dihed: float
    nelem_span: int
    type_span: str = "uniform"
    r_ob: Optional[float] = 0.1
    r_ib: Optional[float] = 0.1
    y_refinement: Optional[float] = 0.5

    def __post_init__(self):
        """Validate region type_span."""

        if self.type_span not in (
            "uniform",
            "cosine",
            "cosine_ib",
            "cosine_ob",
            "geoseries",
            "geoseries_ob",
            "geoseries_ib",
        ):
            raise ValueError(f"Invalid type_span '{self.type_span}' for region")

        if self.nelem_span <= 0:
            raise ValueError(f"nelem_span must be positive, got {self.nelem_span}")

        for attr in ("r_ob", "r_ib", "y_refinement"):
            val = getattr(self, attr)
            if val is None:
                continue
            if not (0.0 < val < 1.0):
                raise ValueError(f"{attr} must be > 0 and < 1, got {val}")


@dataclass
class MeshConfig:
    """Mesh configuration parameters.

    Attributes
    ----------
    title : str
        Mesh title/description
    el_type : str
        Element type ('l' for lifting-line, 'v' for vortex-lattice, 'p' for panel)
    nelem_chord : int
        Number of chordwise elements
    type_chord : str
        Chordwise discretization type can be: 'uniform', 'cosine', 'cosine_le', 'cosine_te', 'geoseries', 'geoseries_le', 'geoseries_te', 'geoseries_hi'
    reference_chord_fraction : float
        Reference chord fraction (default 0.25 [adimensional])
    starting_point : list[float]
        Starting point for mesh generation [x, y, z] [dimensional]
    airfoil_table_correction : bool, optional
        Use airfoil table correction (for 'v' elements)
    y_fountain : float, optional
        Remove wake shedding for y<=y_fountain [dimensional]
    mesh_symmetry : bool, optional
        Enable symmetry plane
    symmetry_point : list[float], optional
        Point on symmetry plane [x, y, z]
    symmetry_normal : list[float], optional
        Normal vector to symmetry plane [nx, ny, nz]
    mesh_mirror : bool, optional
        Enable mirror plane
    mirror_point : list[float], optional
        Point on mirror plane [x, y, z]
    mirror_normal : list[float], optional
        Normal vector to mirror plane [nx, ny, nz]
    r : float, optional
        Outer boundary ratio for geoseries_le or geoseries_te
    r_ob : float, optional
        Outer boundary ratio for geoseries
    r_ib : float, optional
        Inner boundary ratio for geoseries
    r_le_fix : float, optional
        Leading edge fixed ratio for geoseries_hi
    r_te_fix : float, optional
        Trailing edge fixed ratio for geoseries_hi
    r_le_moving : float, optional
        Leading edge moving ratio for geoseries_hi
    r_te_moving : float, optional
        Trailing edge moving ratio for geoseries_hi
    x_refinement : float, optional
        Refinement location for geoseries [adimensional]
    """

    title: str
    el_type: str
    nelem_chord: int
    type_chord: str = "uniform"
    reference_chord_fraction: float = 0.25
    starting_point: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    # Optional fields with defaults
    offset: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    scaling_factor: Optional[float] = 1.0
    airfoil_table_correction: bool = False
    y_fountain: Optional[float] = 0.0
    mesh_symmetry: bool = False
    symmetry_point: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    symmetry_normal: list[float] = field(default_factory=lambda: [0.0, 1.0, 0.0])
    mesh_mirror: bool = False
    mirror_point: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    mirror_normal: list[float] = field(default_factory=lambda: [1.0, 0.0, 0.0])
    r: Optional[float] = 0.125  # required for geoseries_le or geoseries_te
    r_le: Optional[float] = 0.143
    r_te: Optional[float] = 0.066
    r_le_fix: Optional[float] = 0.125  # required for geoseries_hi
    r_te_fix: Optional[float] = 0.143
    r_le_moving: Optional[float] = 0.143
    r_te_moving: Optional[float] = 0.1
    x_refinement: Optional[float] = 0.5

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.el_type not in ("l", "v", "p"):
            raise ValueError(f"el_type must be 'l', 'v', or 'p', got '{self.el_type}'")

        if self.nelem_chord <= 0:
            raise ValueError(f"nelem_chord must be positive, got {self.nelem_chord}")

        if self.type_chord not in (
            "uniform",
            "cosine",
            "cosine_le",
            "cosine_te",
            "geoseries",
            "geoseries_le",
            "geoseries_te",
            "geoseries_hi",
        ):
            raise ValueError(
                f"Invalid type_chord '{self.type_chord}' for mesh configuration"
            )

        for attr in (
            "reference_chord_fraction",
            "r",
            "r_le",
            "r_te",
            "r_le_fix",
            "r_te_fix",
            "r_le_moving",
            "r_te_moving",
            "x_refinement",
        ):
            val = getattr(self, attr)
            if val is None:
                continue
            if not (0.0 < val < 1.0):
                raise ValueError(f"{attr} must be > 0 and < 1, got {val}")


@dataclass
class PointwiseMesh:
    """Container for pointwise mesh data with validation.

    This class groups related mesh data and validates it upon creation.
    It provides a convenient interface for creating and writing meshes.

    Attributes
    ----------
    config : MeshConfig
        Mesh configuration
    points : list[Point]
        List of mesh points
    lines : list[Line]
        List of connecting lines

    Examples
    --------
    >>> config = MeshConfig('Wing', 'v', 20, 'uniform', 0.25)
    >>> points = [Point(0, 0, 0, 1.0, 0, 'naca0012')]
    >>> lines = [Line('straight', 1, 2, 10, 'uniform')]
    >>> mesh = PointwiseMesh(config, points, lines)
    >>> mesh.write('wing.in')
    """

    config: MeshConfig
    points: list[Point]
    lines: list[Line]

    def __post_init__(self):
        """Validate mesh data upon creation."""
        if not self.points:
            raise ValueError("Points list cannot be empty")
        if not self.lines:
            raise ValueError("Lines list cannot be empty")

        # Validate line indices reference existing points
        for i, line in enumerate(self.lines):
            if line.end_points[0] < 1 or line.end_points[1] > len(self.points):
                raise IndexError(
                    f"Line {i + 1} indices ({line.end_points[0]}, {line.end_points[1]}) "
                    f"are out of bounds (valid: 1-{len(self.points)})"
                )

            # Check that line endpoints are not coincident (same coordinates)
            point1 = self.points[line.end_points[0] - 1]
            point2 = self.points[line.end_points[1] - 1]
            if point1.coordinates == point2.coordinates:
                raise ValueError(
                    f"Line {i + 1} has coincident endpoints with same coordinates: "
                    f"point {line.end_points[0]} and point {line.end_points[1]} "
                    f"both at {point1.coordinates}"
                )

        # Validate airfoil tables if needed
        if _is_airfoil_table_needed(self.config):
            for i, point in enumerate(self.points):
                if not point.airfoil_table:
                    raise ValueError(
                        f"Point {i + 1} is missing airfoil_table "
                        f"(required for el_type='{self.config.el_type}')"
                    )

    def write(self, filename: str) -> None:
        """Write mesh to file.

        Args:
            filename: Output file path

        Raises:
            IOError: If file cannot be written

        Example:
            >>> mesh.write('wing.in')
        """
        write_pointwise_mesh(filename, self.points, self.lines, self.config)

    def __repr__(self) -> str:
        """String representation of mesh."""
        return (
            f"PointwiseMesh(title='{self.config.title}', "
            f"n_points={len(self.points)}, n_lines={len(self.lines)})"
        )


@dataclass
class ParametricMesh:
    """Container for parametric mesh data with validation.

    This class groups related mesh data and validates it upon creation.
    It provides a convenient interface for creating and writing meshes.

    Attributes
    ----------
    config : MeshConfig
        Mesh configuration
    sections : list[Section]
        List of wing sections (n+1 sections for n regions)
    regions : list[Region]
        List of regions connecting sections (n regions)

    Examples
    --------
    >>> config = MeshConfig('Wing', 'v', 20, 'uniform', 0.25)
    >>> sections = [Section(1.0, 0, 'naca0012'), Section(0.8, 5, 'naca0012')]
    >>> regions = [Region(5.0, 10.0, 0.0, 10, 'uniform')]
    >>> mesh = ParametricMesh(config, sections, regions)
    >>> mesh.write('wing.in')
    """

    config: MeshConfig
    sections: list[Section]
    regions: list[Region]

    def __post_init__(self):
        """Validate mesh data upon creation."""
        if not self.sections:
            raise ValueError("Sections list cannot be empty")
        if not self.regions:
            raise ValueError("Regions list cannot be empty")

        # Validate section-region count relationship
        if len(self.sections) != len(self.regions) + 1:
            raise ValueError(
                f"Expected {len(self.regions) + 1} sections for {len(self.regions)} regions, "
                f"got {len(self.sections)} sections"
            )

        # Validate airfoil tables if needed
        if _is_airfoil_table_needed(self.config):
            for i, section in enumerate(self.sections):
                if not section.airfoil_table:
                    raise ValueError(
                        f"Section {i + 1} is missing airfoil_table "
                        f"(required for el_type='{self.config.el_type}')"
                    )

    def write(self, filename: str) -> None:
        """Write mesh to file.

        Args:
            filename: Output file path

        Raises:
            IOError: If file cannot be written

        Example:
            >>> mesh.write('wing.in')
        """
        write_parametric_mesh(filename, self.sections, self.regions, self.config)

    def __repr__(self) -> str:
        """String representation of mesh."""
        return (
            f"ParametricMesh(title='{self.config.title}', "
            f"n_sections={len(self.sections)}, n_regions={len(self.regions)})"
        )


def _get_timestamp(file: TextIO) -> None:
    """Write UTC timestamp to mesh file.

    Args:
        file: Output file handle
    """
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    file.write(f"! generated = {timestamp}\n")


def _is_airfoil_table_needed(config: MeshConfig) -> bool:
    """Check if airfoil table files are needed based on element type.
    Args:
        config: Mesh configuration
    Returns:
        True if airfoil tables are required
    """
    return config.el_type == "l" or (
        config.el_type == "v" and config.airfoil_table_correction
    )


def _write_chordwise_settings(config: MeshConfig, file: TextIO) -> None:
    """Write chordwise mesh settings to file.

    Args:
        config: Mesh configuration
        file: Output file handle
    """
    file.write("! Chord-wise settings\n")
    file.write(f"nelem_chord = {config.nelem_chord}\n")
    file.write(f"type_chord = {config.type_chord}\n")
    file.write(f"reference_chord_fraction = {config.reference_chord_fraction}\n\n")

    # Handle geoseries parameters
    if config.type_chord == "geoseries":
        file.write(f"r_le = {config.r_le}\n")
        file.write(f"r_te = {config.r_te}\n")
        file.write(f"x_refinement = {config.x_refinement}\n")
    elif config.type_chord == "geoseries_le":
        file.write(f"r = {config.r}\n")
    elif config.type_chord == "geoseries_te":
        file.write(f"r = {config.r}\n")
    elif config.type_chord == "geoseries_hi":
        file.write(f"r_le_fix = {config.r_le_fix}\n")
        file.write(f"r_te_fix = {config.r_te_fix}\n")
        file.write(f"r_le_moving = {config.r_le_moving}\n")
        file.write(f"r_te_moving = {config.r_te_moving}\n")
        file.write(f"x_refinement = {config.x_refinement}\n")
    file.write("\n")


def _write_symmetry(config: MeshConfig, file: TextIO) -> None:
    """Write symmetry plane settings to file.

    Args:
        config: Mesh configuration
        file: Output file handle
    """
    sym_pt = config.symmetry_point
    sym_norm = config.symmetry_normal
    file.write("! Symmetry settings\n")
    file.write("mesh_symmetry = T\n")
    file.write(
        f"symmetry_point = (/ {sym_pt[0]:.1f}, {sym_pt[1]:.1f}, {sym_pt[2]:.1f} /)\n"
    )
    file.write(
        f"symmetry_normal = (/ {sym_norm[0]:.1f}, {sym_norm[1]:.1f}, {sym_norm[2]:.1f} /)\n"
    )
    file.write("\n")


def _write_mirror(config: MeshConfig, file: TextIO) -> None:
    """Write mirror plane settings to file.

    Args:
        config: Mesh configuration
        file: Output file handle
    """
    mir_pt = config.mirror_point
    mir_norm = config.mirror_normal
    file.write("! Mirror settings\n")
    file.write("mesh_mirror = T\n")
    file.write(
        f"mirror_point = (/ {mir_pt[0]:.1f}, {mir_pt[1]:.1f}, {mir_pt[2]:.1f} /)\n"
    )
    file.write(
        f"mirror_normal = (/ {mir_norm[0]:.1f}, {mir_norm[1]:.1f}, {mir_norm[2]:.1f} /)\n"
    )
    file.write("\n")


def _write_line_discretization(line: Line, file: TextIO) -> None:
    """Write line-specific mesh settings to file.

    Args:
        line: Line object
        file: Output file handle
    """
    file.write(f"  nelem_line = {line.nelem_line}\n")
    file.write(f"  type_span = {line.type_span}\n")

    # Handle geoseries parameters
    if line.type_span == "geoseries":
        file.write(f"  r_ob = {line.r_ob}\n")
        file.write(f"  r_ib = {line.r_ib}\n")
        file.write(f"  y_refinement = {line.y_refinement}\n")
    elif line.type_span == "geoseries_ob":
        file.write(f"  r_ob = {line.r_ob}\n")
    elif line.type_span == "geoseries_ib":
        file.write(f"  r_ib = {line.r_ib}\n")
    file.write("\n")


def _write_point(config: MeshConfig, point: Point, file: TextIO) -> None:
    """Write a single point definition to file.

    Args:
        config: Mesh configuration
        point: Point object
        file: Output file handle
    """
    file.write("Point = {\n")
    file.write(f"  Id = {point.id}\n")
    file.write(
        f"  coordinates = (/{point.coordinates[0]}, {point.coordinates[1]}, {point.coordinates[2]}/)\n"
    )
    file.write(f"  chord = {point.chord}\n")
    file.write(f"  twist = {point.twist}\n")
    file.write(f"  airfoil = {point.airfoil}.dat\n")

    if _is_airfoil_table_needed(config):
        if not point.airfoil_table:
            raise ValueError(
                f"Point {point.id} is missing airfoil_table "
                f"(required for el_type='{config.el_type}')"
            )
        file.write(f"  airfoil_table = {point.airfoil_table}.c81\n")

    file.write(f"  section_normal = {point.section_normal}\n")
    if point.section_normal == "vector":
        if point.section_normal_vector is None:
            raise ValueError(
                f"Point {point.id}: section_normal_vector must be provided when section_normal='vector'"
            )
        file.write(
            f"  section_normal_vector = (/{point.section_normal_vector[0]}, "
            f"{point.section_normal_vector[1]}, {point.section_normal_vector[2]}/)\n"
        )
    file.write(f"  flip_section = {'T' if point.flip_section else 'F'}\n")
    file.write("}\n\n")


def _write_straight(line: Line, points: list[Point], file: TextIO) -> None:
    """Write a straight line definition to file.

    Args:
        line: Line object
        points: List of point objects
        file: Output file handle

    Raises:
        IndexError: If line indices are out of bounds
    """
    # Validate bounds
    if line.end_points[0] < 1 or line.end_points[1] > len(points):
        raise IndexError(
            f"Line indices ({line.end_points[0]}, {line.end_points[1]}) "
            f"are out of bounds (valid: 1-{len(points)})"
        )

    file.write("Line = {\n")
    file.write("  type = straight\n")
    file.write(f"  end_points = (/{line.end_points[0]}, {line.end_points[1]}/)\n")
    _write_line_discretization(line, file)
    file.write("}\n\n")


def _write_spline(line: Line, points: list[Point], file: TextIO) -> None:
    """Write a spline line definition to file.

    Args:
        line: Line object
        points: List of point objects
        file: Output file handle

    Raises:
        IndexError: If line indices are out of bounds
    """
    # Validate bounds
    if line.end_points[0] < 1 or line.end_points[1] > len(points):
        raise IndexError(
            f"Line indices ({line.end_points[0]}, {line.end_points[1]}) "
            f"are out of bounds (valid: 1-{len(points)})"
        )

    file.write("Line = {\n")
    file.write("  type = spline\n")
    file.write(f"  end_points = (/{line.end_points[0]}, {line.end_points[1]}/)\n")
    file.write(f"  tension = {line.tension}\n")
    file.write(f"  bias = {line.bias}\n")
    _write_line_discretization(line, file)
    _write_end_tangents(line, points, file)
    file.write("}\n\n")


def _write_end_tangents(line: Line, points: list[Point], file: TextIO) -> None:
    """Calculate and write tangent vectors at line endpoints.

    Tangents are computed using forward/backward finite differences and normalized.

    Args:
        line: Line object
        points: List of point objects
        file: Output file handle

    Raises:
        IndexError: If tangent calculation would go out of bounds
    """
    pt_start = line.end_points[0] - 1  # Convert to 0-based index
    pt_end = line.end_points[1] - 1

    # Bounds checking
    if pt_start < 0 or pt_end >= len(points):
        raise IndexError(
            f"Invalid line indices: start={line.end_points[0]}, end={line.end_points[1]} "
            f"(valid: 1-{len(points)})"
        )

    if pt_start + 1 >= len(points):
        raise IndexError(
            f"Cannot calculate start tangent: need point at index {line.end_points[0] + 1} "
            f"(have 1-{len(points)})"
        )

    if pt_end - 1 < 0:
        raise IndexError(
            f"Cannot calculate end tangent: need point at index {line.end_points[1] - 1} "
            f"(have 1-{len(points)})"
        )

    # Calculate tangents using finite differences
    tangent_1 = np.array(
        [
            points[pt_start + 1].coordinates[0] - points[pt_start].coordinates[0],
            points[pt_start + 1].coordinates[1] - points[pt_start].coordinates[1],
            points[pt_start + 1].coordinates[2] - points[pt_start].coordinates[2],
        ]
    )
    tangent_2 = np.array(
        [
            points[pt_end].coordinates[0] - points[pt_end - 1].coordinates[0],
            points[pt_end].coordinates[1] - points[pt_end - 1].coordinates[1],
            points[pt_end].coordinates[2] - points[pt_end - 1].coordinates[2],
        ]
    )
    # Check for zero-length tangents
    if np.linalg.norm(tangent_1) == 0.0:
        raise ValueError(
            f"Zero-length tangent vector at start point of line ({line.end_points[0]})"
        )
    if np.linalg.norm(tangent_2) == 0.0:
        raise ValueError(
            f"Zero-length tangent vector at end point of line ({line.end_points[1]})"
        )

    # normalize tangents
    tangent_1 = tangent_1 / np.linalg.norm(tangent_1)
    tangent_2 = tangent_2 / np.linalg.norm(tangent_2)

    # Store as lists (convert from numpy arrays)
    line.tangent_vec_1 = tangent_1.tolist()
    line.tangent_vec_2 = tangent_2.tolist()

    # Write tangents to file
    file.write(
        f"  tangent_vec_1 = (/{line.tangent_vec_1[0]}, {line.tangent_vec_1[1]}, {line.tangent_vec_1[2]}/)\n"
    )
    file.write(
        f"  tangent_vec_2 = (/{line.tangent_vec_2[0]}, {line.tangent_vec_2[1]}, {line.tangent_vec_2[2]}/)\n"
    )


def _write_section(
    section: Section, idx: int, config: MeshConfig, file: TextIO
) -> None:
    """Write a section definition to file.

    Args:
        section: Section object
        idx: Zero-based section index
        config: Mesh configuration
        file: Output file handle
    """
    file.write(f"! Section {idx + 1}\n")
    file.write(f"chord = {section.chord}\n")
    file.write(f"twist = {section.twist}\n")
    file.write(f"airfoil = {section.airfoil}\n")

    if _is_airfoil_table_needed(config):
        if not section.airfoil_table:
            raise ValueError(
                f"Section {idx + 1} is missing airfoil_table "
                f"(required for el_type='{config.el_type}')"
            )
        file.write(f"airfoil_table = {section.airfoil_table}\n")

    file.write("\n")


def _write_region(region: Region, idx: int, file: TextIO) -> None:
    """Write a region definition to file.

    Args:
        region: Region object
        idx: Zero-based region index
        file: Output file handle
    """
    file.write(f"! Region {idx + 1}\n")
    file.write(f"span = {region.span}\n")
    file.write(f"sweep = {region.sweep}\n")
    file.write(f"dihed = {region.dihed}\n")
    _write_region_discretization(region, file)


def _write_region_discretization(region: Any, file: TextIO) -> None:
    """Write region mesh settings to file.

    Args:
        config: Configuration object (MeshConfig, Line, or Region)
        file: Output file handle
    """
    file.write(f"nelem_span = {region.nelem_span}\n")
    file.write(f"type_span = {region.type_span}\n")

    # Handle geoseries parameters
    if region.type_span == "geoseries":
        file.write(f"r_ob = {region.r_ob}\n")
        file.write(f"r_ib = {region.r_ib}\n")
        file.write(f"y_refinement = {region.y_refinement}\n")
    elif region.type_span == "geoseries_ob":
        file.write(f"r_ob = {region.r_ob}\n")
    elif region.type_span == "geoseries_ib":
        file.write(f"r_ib = {region.r_ib}\n")
    file.write("\n")


def write_pointwise_mesh(
    filename: str, points: list[Point], lines: list[Line], config: MeshConfig
) -> None:
    """Write a pointwise mesh configuration file for DUST.

    Args:
        filename: Output file path
        points: List of Point objects
        lines: List of Line objects
        config: MeshConfig object

    Raises:
        ValueError: If inputs are invalid
        IOError: If file cannot be written
        IndexError: If line indices reference non-existent points

    Example:
        >>> from pydust_utils import Point, Line, MeshConfig, write_pointwise_mesh
        >>>
        >>> config = MeshConfig(
        ...     title='Wing Mesh',
        ...     el_type='v',
        ...     nelem_chord=20,
        ...     type_chord='uniform',
        ...     reference_chord_fraction=0.25
        ... )
        >>>
        >>> points = [
        ...     Point(1, [0.0, 0.0, 0.0], 1.0, 0.0, 'naca0012', 'naca0012'),
        ...     Point(2, [1.0, 0.0, 0.0], 1.0, 0.0, 'naca0012', 'naca0012')
        ... ]
        >>>
        >>> lines = [
        ...     Line('straight', [1, 2], 10, 'uniform')
        ... ]
        >>>
        >>> write_pointwise_mesh('mesh.in', points, lines, config)
    """
    # Validate inputs
    if not points:
        raise ValueError("Points list cannot be empty")
    if not lines:
        raise ValueError("Lines list cannot be empty")

    try:
        with open(filename, "w") as file:
            file.write(f"! {config.title}\n")
            _get_timestamp(file)

            file.write("mesh_file_type = pointwise\n")
            file.write(f"el_type = {config.el_type}\n\n")

            # Scaling and offset
            file.write("! Global scaling and offset\n")
            file.write(f"scaling_factor = {config.scaling_factor}\n")
            file.write(
                f"offset = (/{config.offset[0]}, {config.offset[1]}, {config.offset[2]}/)\n\n"
            )

            # Handle airfoil table correction for 'v' elements
            if config.el_type == "v" and config.airfoil_table_correction:
                file.write("airfoil_table_correction = T\n\n")

            _write_chordwise_settings(config, file)

            # Optional parameters (symmetry, mirror, y_fountain)
            if config.mesh_symmetry:
                _write_symmetry(config, file)
            if config.mesh_mirror:
                _write_mirror(config, file)
            if config.y_fountain:
                file.write(f"y_fountain = {config.y_fountain}\n\n")

            # Write points
            for point in points:
                _write_point(config, point, file)

            # Write lines
            for line in lines:
                if line.type == "spline":
                    _write_spline(line, points, file)
                elif line.type == "straight":
                    _write_straight(line, points, file)

    except OSError as e:
        raise OSError(f"Failed to write mesh file {filename}: {e}") from e


def write_parametric_mesh(
    filename: str, sections: list[Section], regions: list[Region], config: MeshConfig
) -> None:
    """Write a parametric mesh configuration file for DUST.

    Args:
        filename: Output file path
        sections: List of Section objects
        regions: List of Region objects
        config: MeshConfig object

    Raises:
        ValueError: If inputs are invalid
        OSError: If file cannot be written

    Example:
        >>> from pydust_utils import Section, Region, MeshConfig, write_parametric_mesh
        >>>
        >>> config = MeshConfig(
        ...     title='Wing Mesh',
        ...     el_type='v',
        ...     nelem_chord=20,
        ...     type_chord='uniform',
        ...     reference_chord_fraction=0.25
        ... )
        >>>
        >>> sections = [
        ...     Section(1.0, 0.0, 'naca0012', 'naca0012'),
        ...     Section(0.8, 5.0, 'naca0012', 'naca0012')
        ... ]
        >>>
        >>> regions = [
        ...     Region(5.0, 10.0, 0.0, 10, 'uniform')
        ... ]
        >>>
        >>> write_parametric_mesh('mesh.in', sections, regions, config)
    """
    # Validate inputs
    if not sections:
        raise ValueError("Sections list cannot be empty")
    if not regions:
        raise ValueError("Regions list cannot be empty")
    if len(sections) != len(regions) + 1:
        raise ValueError(
            f"Expected {len(regions) + 1} sections for {len(regions)} regions, "
            f"got {len(sections)} sections"
        )

    try:
        with open(filename, "w") as file:
            file.write(f"! {config.title}\n")
            _get_timestamp(file)

            file.write("mesh_file_type = parametric\n")
            file.write(f"el_type = {config.el_type}\n\n")
            # Scaling and offset
            file.write("! Global scaling and offset\n")
            file.write(f"scaling_factor = {config.scaling_factor}\n")
            file.write(
                f"offset = (/{config.offset[0]}, {config.offset[1]}, {config.offset[2]}/)\n\n"
            )

            # Handle airfoil table correction for 'v' elements
            if config.el_type == "v" and config.airfoil_table_correction:
                file.write("airfoil_table_correction = T\n\n")

            _write_chordwise_settings(config, file)

            # Optional parameters (symmetry, mirror, y_fountain)
            if config.mesh_symmetry:
                _write_symmetry(config, file)
            if config.mesh_mirror:
                _write_mirror(config, file)
            if config.y_fountain:
                file.write(f"y_fountain = {config.y_fountain}\n\n")

            # Write sections and regions
            for idx, (section, region) in enumerate(zip(sections, regions)):
                _write_section(section, idx, config, file)
                _write_region(region, idx, file)

            # Write final section (no region after it)
            _write_section(sections[-1], len(regions), config, file)

    except OSError as e:
        raise OSError(f"Failed to write mesh file {filename}: {e}") from e
