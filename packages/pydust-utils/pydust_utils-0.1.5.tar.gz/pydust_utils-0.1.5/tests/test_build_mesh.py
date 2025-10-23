"""Tests for build_mesh module."""

import pytest
import tempfile
from pathlib import Path
from pydust_utils.build_mesh import (
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


# Fixtures for common test data
@pytest.fixture
def basic_config():
    """Basic mesh configuration for testing."""
    return MeshConfig(
        title="Test Mesh",
        el_type="v",
        nelem_chord=20,
        type_chord="uniform",
        reference_chord_fraction=0.25,
    )


@pytest.fixture
def lifting_line_config():
    """Lifting-line configuration requiring airfoil tables."""
    return MeshConfig(
        title="Test LL Mesh",
        el_type="l",
        nelem_chord=1,
        type_chord="uniform",
        reference_chord_fraction=0.25,
    )


@pytest.fixture
def basic_points():
    """Basic points for testing."""
    return [
        Point(
            id=1,
            coordinates=[0.0, 0.0, 0.0],
            chord=1.0,
            twist=0.0,
            airfoil="naca0012",
            airfoil_table="naca0012",
        ),
        Point(
            id=2,
            coordinates=[0.2, 2.5, 0.1],
            chord=0.8,
            twist=2.5,
            airfoil="naca0012",
            airfoil_table="naca0012",
        ),
        Point(
            id=3,
            coordinates=[0.4, 5.0, 0.2],
            chord=0.6,
            twist=5.0,
            airfoil="naca0009",
            airfoil_table="naca0009",
        ),
    ]


@pytest.fixture
def basic_lines():
    """Basic lines for testing."""
    return [
        Line(type="spline", end_points=[1, 2], nelem_line=10, type_span="uniform"),
        Line(type="straight", end_points=[2, 3], nelem_line=10, type_span="uniform"),
    ]


@pytest.fixture
def basic_sections():
    """Basic sections for testing."""
    return [
        Section(1.0, 0.0, "naca0012", "naca0012"),
        Section(0.8, 5.0, "naca0012", "naca0012"),
        Section(0.6, 10.0, "naca0009", "naca0009"),
    ]


@pytest.fixture
def basic_regions():
    """Basic regions for testing."""
    return [
        Region(5.0, 10.0, 0.0, 10, "uniform"),
        Region(5.0, 15.0, 5.0, 10, "uniform"),
    ]


# Common simple fixtures for repetitive test patterns
@pytest.fixture
def simple_point():
    """A single simple point at origin."""
    return Point(id=1, coordinates=[0, 0, 0], chord=1.0, twist=0, airfoil="naca0012")


@pytest.fixture
def two_points():
    """Two simple points for basic line tests."""
    return [
        Point(id=1, coordinates=[0, 0, 0], chord=1.0, twist=0, airfoil="naca0012"),
        Point(id=2, coordinates=[0, 1, 0], chord=1.0, twist=0, airfoil="naca0012"),
    ]


@pytest.fixture
def two_points_with_table():
    """Two points with airfoil tables for lifting-line tests."""
    return [
        Point(
            id=1,
            coordinates=[0, 0, 0],
            chord=1.0,
            twist=0,
            airfoil="naca0012",
            airfoil_table="naca0012",
        ),
        Point(
            id=2,
            coordinates=[0, 1, 0],
            chord=1.0,
            twist=0,
            airfoil="naca0012",
            airfoil_table="naca0012",
        ),
    ]


@pytest.fixture
def simple_line():
    """A simple straight line connecting points 1 and 2."""
    return Line(type="straight", end_points=[1, 2], nelem_line=10, type_span="uniform")


@pytest.fixture
def simple_lines(simple_line):
    """List with a single simple line."""
    return [simple_line]


@pytest.fixture
def uniform_config():
    """Simple uniform mesh configuration for quick tests."""
    return MeshConfig(
        title="Test",
        el_type="v",
        nelem_chord=10,
        type_chord="uniform",
        reference_chord_fraction=0.25,
    )


@pytest.fixture
def spanwise_points():
    """Two points with varying chord and twist for spanwise tests."""
    return [
        Point(id=1, coordinates=[0, 0, 0], chord=1.0, twist=0, airfoil="naca0012"),
        Point(id=2, coordinates=[0, 5, 0], chord=0.6, twist=5, airfoil="naca0009"),
    ]


# ============================================================================
# MeshConfig Tests
# ============================================================================


class TestMeshConfig:
    """Tests for MeshConfig dataclass."""

    def test_valid_config(self, basic_config):
        """Test creating valid configuration."""
        assert basic_config.title == "Test Mesh"
        assert basic_config.el_type == "v"
        assert basic_config.nelem_chord == 20

    def test_invalid_el_type(self):
        """Test that invalid element type raises error."""
        with pytest.raises(ValueError, match="el_type must be"):
            MeshConfig("Test", "invalid", 20, "uniform", 0.25)

    def test_negative_nelem_chord(self):
        """Test that negative nelem_chord raises error."""
        with pytest.raises(ValueError, match="nelem_chord must be positive"):
            MeshConfig("Test", "v", -1, "uniform", 0.25)

    def test_invalid_reference_fraction(self):
        """Test that invalid reference fraction raises error."""
        with pytest.raises(ValueError, match="reference_chord_fraction must be"):
            MeshConfig("Test", "v", 20, "uniform", 1.5)


# ============================================================================
# Line Tests
# ============================================================================


class TestLine:
    """Tests for Line dataclass."""

    def test_valid_spline(self):
        """Test creating valid spline line."""
        line = Line(
            type="spline",
            end_points=[1, 2],
            nelem_line=10,
            type_span="uniform",
            tension=0.5,
            bias=0.2,
        )
        assert line.type == "spline"
        assert line.tension == 0.5
        assert line.bias == 0.2

    def test_valid_straight(self):
        """Test creating valid straight line."""
        line = Line(
            type="straight", end_points=[1, 2], nelem_line=10, type_span="uniform"
        )
        assert line.type == "straight"
        assert line.tension is None  # Default

    def test_invalid_line_type(self):
        """Test that invalid line type raises error."""
        with pytest.raises(ValueError, match="Line type must be"):
            Line(type="invalid", end_points=[1, 2], nelem_line=10, type_span="uniform")


# ============================================================================
# PointwiseMesh Tests
# ============================================================================


class TestPointwiseMesh:
    """Tests for PointwiseMesh container class."""

    def test_valid_mesh(self, basic_config, basic_points, basic_lines):
        """Test creating valid pointwise mesh."""
        mesh = PointwiseMesh(basic_config, basic_points, basic_lines)
        assert mesh.config.title == "Test Mesh"
        assert len(mesh.points) == 3
        assert len(mesh.lines) == 2

    def test_empty_points(self, basic_config, basic_lines):
        """Test that empty points list raises error."""
        with pytest.raises(ValueError, match="Points list cannot be empty"):
            PointwiseMesh(basic_config, [], basic_lines)

    def test_empty_lines(self, basic_config, basic_points):
        """Test that empty lines list raises error."""
        with pytest.raises(ValueError, match="Lines list cannot be empty"):
            PointwiseMesh(basic_config, basic_points, [])

    def test_invalid_line_indices(self, basic_config, basic_points):
        """Test that invalid line indices raise error."""
        bad_lines = [
            Line(
                type="straight", end_points=[1, 10], nelem_line=10, type_span="uniform"
            )
        ]  # Point 10 doesn't exist
        with pytest.raises(IndexError, match="out of bounds"):
            PointwiseMesh(basic_config, basic_points, bad_lines)

    def test_missing_airfoil_table_lifting_line(self, lifting_line_config):
        """Test that missing airfoil table raises error for lifting-line."""
        points = [
            Point(id=1, coordinates=[0, 0, 0], chord=1.0, twist=0, airfoil="naca0012"),
            Point(id=2, coordinates=[1, 0, 0], chord=1.0, twist=0, airfoil="naca0012"),
        ]  # No airfoil_table!
        lines = [
            Line(type="straight", end_points=[1, 2], nelem_line=10, type_span="uniform")
        ]

        with pytest.raises(ValueError, match="missing airfoil_table"):
            PointwiseMesh(lifting_line_config, points, lines)

    def test_repr(self, basic_config, basic_points, basic_lines):
        """Test string representation."""
        mesh = PointwiseMesh(basic_config, basic_points, basic_lines)
        repr_str = repr(mesh)
        assert "Test Mesh" in repr_str
        assert "n_points=3" in repr_str
        assert "n_lines=2" in repr_str

    def test_write_creates_file(self, basic_config, basic_points, basic_lines):
        """Test that write method creates file."""
        mesh = PointwiseMesh(basic_config, basic_points, basic_lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            assert Path(filepath).exists()

            # Check file contains expected content
            with open(filepath, "r") as f:
                content = f.read()
                assert "Test Mesh" in content
                assert "mesh_file_type = pointwise" in content
                assert "el_type = v" in content
        finally:
            Path(filepath).unlink()


# ============================================================================
# ParametricMesh Tests
# ============================================================================


class TestParametricMesh:
    """Tests for ParametricMesh container class."""

    def test_valid_mesh(self, basic_config, basic_sections, basic_regions):
        """Test creating valid parametric mesh."""
        mesh = ParametricMesh(basic_config, basic_sections, basic_regions)
        assert mesh.config.title == "Test Mesh"
        assert len(mesh.sections) == 3
        assert len(mesh.regions) == 2

    def test_empty_sections(self, basic_config, basic_regions):
        """Test that empty sections list raises error."""
        with pytest.raises(ValueError, match="Sections list cannot be empty"):
            ParametricMesh(basic_config, [], basic_regions)

    def test_empty_regions(self, basic_config, basic_sections):
        """Test that empty regions list raises error."""
        with pytest.raises(ValueError, match="Regions list cannot be empty"):
            ParametricMesh(basic_config, basic_sections, [])

    def test_section_region_mismatch(self, basic_config, basic_sections):
        """Test that section-region count mismatch raises error."""
        bad_regions = [
            Region(5.0, 10.0, 0.0, 10, "uniform")
        ]  # Only 1 region for 3 sections!
        with pytest.raises(
            ValueError, match="Expected 2 sections for 1 regions, got 3 sections"
        ):
            ParametricMesh(basic_config, basic_sections, bad_regions)

    def test_missing_airfoil_table_lifting_line(self, lifting_line_config):
        """Test that missing airfoil table raises error for lifting-line."""
        sections = [
            Section(1.0, 0, "naca0012"),  # No airfoil_table!
            Section(0.8, 5, "naca0012"),  # No airfoil_table!
        ]
        regions = [Region(5.0, 10.0, 0.0, 10, "uniform")]

        with pytest.raises(ValueError, match="missing airfoil_table"):
            ParametricMesh(lifting_line_config, sections, regions)

    def test_repr(self, basic_config, basic_sections, basic_regions):
        """Test string representation."""
        mesh = ParametricMesh(basic_config, basic_sections, basic_regions)
        repr_str = repr(mesh)
        assert "Test Mesh" in repr_str
        assert "n_sections=3" in repr_str
        assert "n_regions=2" in repr_str

    def test_write_creates_file(self, basic_config, basic_sections, basic_regions):
        """Test that write method creates file."""
        mesh = ParametricMesh(basic_config, basic_sections, basic_regions)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            assert Path(filepath).exists()

            # Check file contains expected content
            with open(filepath, "r") as f:
                content = f.read()
                assert "Test Mesh" in content
                assert "mesh_file_type = parametric" in content
                assert "el_type = v" in content
        finally:
            Path(filepath).unlink()


# ============================================================================
# Functional API Tests (Backward Compatibility)
# ============================================================================


class TestFunctionalAPI:
    """Tests for backward-compatible functional API."""

    def test_write_pointwise_mesh_functional(
        self, basic_config, basic_points, basic_lines
    ):
        """Test functional API for pointwise mesh."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            write_pointwise_mesh(filepath, basic_points, basic_lines, basic_config)
            assert Path(filepath).exists()

            with open(filepath, "r") as f:
                content = f.read()
                assert "Test Mesh" in content
                assert "mesh_file_type = pointwise" in content
        finally:
            Path(filepath).unlink()

    def test_write_parametric_mesh_functional(
        self, basic_config, basic_sections, basic_regions
    ):
        """Test functional API for parametric mesh."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            write_parametric_mesh(filepath, basic_sections, basic_regions, basic_config)
            assert Path(filepath).exists()

            with open(filepath, "r") as f:
                content = f.read()
                assert "Test Mesh" in content
                assert "mesh_file_type = parametric" in content
        finally:
            Path(filepath).unlink()

    def test_functional_validates_empty_inputs(self, basic_config, basic_lines):
        """Test that functional API validates empty inputs."""
        with pytest.raises(ValueError, match="Points list cannot be empty"):
            write_pointwise_mesh("test.in", [], basic_lines, basic_config)


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complete_pointwise_workflow(self):
        """Test complete pointwise mesh creation workflow."""
        # Create configuration
        config = MeshConfig(
            title="Integration Test Wing",
            el_type="v",
            nelem_chord=20,
            type_chord="uniform",
            reference_chord_fraction=0.25,
            mesh_symmetry=True,
        )

        # Create geometry
        points = [
            Point(
                id=1,
                coordinates=[0.0, 0.0, 0.0],
                chord=1.0,
                twist=0.0,
                airfoil="naca0012",
                airfoil_table="naca0012",
            ),
            Point(
                id=2,
                coordinates=[0.2, 5.0, 0.1],
                chord=0.6,
                twist=5.0,
                airfoil="naca0009",
                airfoil_table="naca0009",
            ),
        ]

        lines = [
            Line(
                type="spline",
                end_points=[1, 2],
                nelem_line=20,
                type_span="uniform",
                tension=0.5,
            )
        ]

        # Create mesh
        mesh = PointwiseMesh(config, points, lines)

        # Write to file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)

            # Verify file content
            with open(filepath, "r") as f:
                content = f.read()
                assert "Integration Test Wing" in content
                assert "mesh_symmetry = T" in content
                assert "nelem_chord = 20" in content
                assert "type = spline" in content.lower()  # Case-insensitive check
                assert "tension = 0.5" in content
        finally:
            Path(filepath).unlink()

    def test_complete_parametric_workflow(self):
        """Test complete parametric mesh creation workflow."""
        # Create configuration
        config = MeshConfig(
            title="Integration Test Parametric Wing",
            el_type="v",
            nelem_chord=20,
            type_chord="uniform",
            reference_chord_fraction=0.25,
            airfoil_table_correction=True,
        )

        # Create geometry
        sections = [
            Section(1.0, 0.0, "naca0012", "naca0012"),
            Section(0.8, 5.0, "naca0012", "naca0012"),
            Section(0.6, 10.0, "naca0009", "naca0009"),
        ]

        regions = [
            Region(5.0, 10.0, 0.0, 10, "uniform"),
            Region(5.0, 15.0, 5.0, 10, "uniform"),
        ]

        # Create mesh
        mesh = ParametricMesh(config, sections, regions)

        # Write to file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)

            # Verify file content
            with open(filepath, "r") as f:
                content = f.read()
                assert "Integration Test Parametric Wing" in content
                assert "airfoil_table_correction = T" in content
                assert "mesh_file_type = parametric" in content
                assert "! Section 1" in content
                assert "! Region 1" in content
        finally:
            Path(filepath).unlink()


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_single_point_mesh_fails(self, basic_config):
        """Test that single-point mesh fails (need at least 2 for a line)."""
        points = [
            Point(
                id=1,
                coordinates=[0, 0, 0],
                chord=1.0,
                twist=0,
                airfoil="naca0012",
                airfoil_table="naca0012",
            )
        ]
        lines = [
            Line(type="straight", end_points=[1, 2], nelem_line=10, type_span="uniform")
        ]  # Points to non-existent point 2

        with pytest.raises(IndexError):
            PointwiseMesh(basic_config, points, lines)

    def test_geoseries_parameters(self):
        """Test mesh with geoseries discretization."""
        config = MeshConfig(
            title="Geoseries Test",
            el_type="v",
            nelem_chord=20,
            type_chord="uniform",  # Use uniform for chord, geoseries is for spanwise
            reference_chord_fraction=0.25,
        )

        points = [
            Point(
                id=1,
                coordinates=[0, 0, 0],
                chord=1.0,
                twist=0,
                airfoil="naca0012",
                airfoil_table="naca0012",
            ),
            Point(
                id=2,
                coordinates=[0, 5, 0],
                chord=0.6,
                twist=5,
                airfoil="naca0009",
                airfoil_table="naca0009",
            ),
        ]

        lines = [
            Line(
                type="straight",
                end_points=[1, 2],
                nelem_line=20,
                type_span="geoseries",  # geoseries goes on Line for spanwise
                r_ob=0.15,  # These are Line parameters
                r_ib=0.15,
                y_refinement=0.5,
            )
        ]

        mesh = PointwiseMesh(config, points, lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "r_ob =" in content
                assert "r_ib =" in content
                assert "y_refinement =" in content
        finally:
            Path(filepath).unlink()


# ============================================================================
# Additional Coverage Tests
# ============================================================================


class TestGeometrySeries:
    """Test various geometric series configurations."""

    def test_chordwise_geoseries_le(self, two_points, simple_lines):
        """Test chordwise geoseries_le with leading edge refinement."""
        config = MeshConfig(
            title="Geoseries LE Test",
            el_type="v",
            nelem_chord=15,
            type_chord="geoseries_le",
            r=0.15,  # geoseries_le uses 'r' parameter in the output
            reference_chord_fraction=0.25,
        )

        mesh = PointwiseMesh(config, two_points, simple_lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "type_chord = geoseries_le" in content
                assert "r = 0.15" in content
        finally:
            Path(filepath).unlink()

    def test_chordwise_geoseries_te(self, two_points, simple_lines):
        """Test chordwise geoseries_te with trailing edge refinement."""
        config = MeshConfig(
            title="Geoseries TE Test",
            el_type="v",
            nelem_chord=15,
            type_chord="geoseries_te",
            r=0.12,  # geoseries_te uses 'r' parameter in the output
            reference_chord_fraction=0.25,
        )

        mesh = PointwiseMesh(config, two_points, simple_lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "type_chord = geoseries_te" in content
                assert "r = 0.12" in content
        finally:
            Path(filepath).unlink()

    def test_chordwise_geoseries_hi(self, two_points, simple_lines):
        """Test chordwise geoseries_hi with hinge refinement."""
        config = MeshConfig(
            title="Geoseries HI Test",
            el_type="v",
            nelem_chord=15,
            type_chord="geoseries_hi",
            r_le_fix=0.15,  # geoseries_hi uses r_le_fix, r_te_fix, etc.
            r_te_fix=0.14,
            reference_chord_fraction=0.25,
        )

        mesh = PointwiseMesh(config, two_points, simple_lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "type_chord = geoseries_hi" in content
                assert "r_le_fix = 0.15" in content
                assert "r_te_fix = 0.14" in content
        finally:
            Path(filepath).unlink()

    def test_spanwise_geoseries_ob(self, spanwise_points):
        """Test spanwise geoseries with outboard refinement only."""
        config = MeshConfig(
            title="Spanwise Geoseries OB",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        lines = [
            Line(
                type="straight",
                end_points=[1, 2],
                nelem_line=20,
                type_span="geoseries_ob",
                r_ob=0.3,  # Must be > 0 and < 1
            )
        ]

        mesh = PointwiseMesh(config, spanwise_points, lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "type_span = geoseries_ob" in content
                assert "r_ob = 0.3" in content
        finally:
            Path(filepath).unlink()

    def test_spanwise_geoseries_ib(self, spanwise_points):
        """Test spanwise geoseries with inboard refinement only."""
        config = MeshConfig(
            title="Spanwise Geoseries IB",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        lines = [
            Line(
                type="straight",
                end_points=[1, 2],
                nelem_line=20,
                type_span="geoseries_ib",
                r_ib=0.7,
            )
        ]

        mesh = PointwiseMesh(config, spanwise_points, lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "type_span = geoseries_ib" in content
                assert "r_ib = 0.7" in content
        finally:
            Path(filepath).unlink()


class TestMirrorAndSymmetry:
    """Test mirror and symmetry plane features."""

    def test_mesh_mirror(self, two_points, simple_lines):
        """Test mesh mirroring configuration."""
        config = MeshConfig(
            title="Mirror Test",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
            mesh_mirror=True,
            mirror_point=[0.0, 0.0, 0.0],
            mirror_normal=[0.0, 1.0, 0.0],
        )

        mesh = PointwiseMesh(config, two_points, simple_lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "mesh_mirror = T" in content
                assert "mirror_point" in content
                assert "mirror_normal" in content
        finally:
            Path(filepath).unlink()

    def test_y_fountain(self, two_points, simple_lines):
        """Test y_fountain parameter."""
        config = MeshConfig(
            title="Fountain Test",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
            y_fountain=2.5,
        )

        mesh = PointwiseMesh(config, two_points, simple_lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "y_fountain = 2.5" in content
        finally:
            Path(filepath).unlink()

    def test_airfoil_table_correction(self, two_points_with_table, simple_lines):
        """Test airfoil table correction for vortex lattice elements."""
        config = MeshConfig(
            title="Correction Test",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
            airfoil_table_correction=True,
        )

        mesh = PointwiseMesh(config, two_points_with_table, simple_lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "airfoil_table_correction = T" in content
        finally:
            Path(filepath).unlink()


class TestAirfoilTables:
    """Test airfoil table handling for lifting-line elements."""

    def test_pointwise_with_airfoil_tables(self):
        """Test pointwise mesh with airfoil tables for lifting-line."""
        config = MeshConfig(
            title="LL with tables",
            el_type="l",
            nelem_chord=1,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        points = [
            Point(
                id=1,
                coordinates=[0, 0, 0],
                chord=1.0,
                twist=0,
                airfoil="naca0012",
                airfoil_table="naca0012",
            ),
            Point(
                id=2,
                coordinates=[0, 5, 0],
                chord=0.6,
                twist=5,
                airfoil="naca0009",
                airfoil_table="naca0009",
            ),
        ]

        lines = [
            Line(type="straight", end_points=[1, 2], nelem_line=20, type_span="uniform")
        ]

        mesh = PointwiseMesh(config, points, lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "airfoil_table = naca0012.c81" in content
                assert "airfoil_table = naca0009.c81" in content
        finally:
            Path(filepath).unlink()

    def test_parametric_with_airfoil_tables(self):
        """Test parametric mesh with airfoil tables for lifting-line."""
        config = MeshConfig(
            title="LL Parametric",
            el_type="l",
            nelem_chord=1,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        sections = [
            Section(1.0, 0.0, "naca0012", "naca0012"),
            Section(0.6, 5.0, "naca0009", "naca0009"),
        ]

        regions = [Region(5.0, 0.0, 0.0, 20, "uniform")]

        mesh = ParametricMesh(config, sections, regions)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "airfoil_table = naca0012" in content
                assert "airfoil_table = naca0009" in content
        finally:
            Path(filepath).unlink()


class TestSplineEdgeCases:
    """Test edge cases for spline lines."""

    def test_spline_tangent_calculation(self):
        """Test spline with proper tangent calculation."""
        config = MeshConfig(
            title="Spline Test",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        # Need at least 3 points for tangent calculation
        points = [
            Point(id=1, coordinates=[0, 0, 0], chord=1.0, twist=0, airfoil="naca0012"),
            Point(
                id=2,
                coordinates=[0.2, 2.5, 0.1],
                chord=0.8,
                twist=2.5,
                airfoil="naca0012",
            ),
            Point(
                id=3,
                coordinates=[0.4, 5.0, 0.2],
                chord=0.6,
                twist=5.0,
                airfoil="naca0009",
            ),
        ]

        # Spline from point 1 to point 3 (needs tangents at both ends)
        lines = [
            Line(
                type="spline",
                end_points=[1, 3],
                nelem_line=20,
                type_span="uniform",
                tension=0.5,
                bias=0.0,
            )
        ]

        mesh = PointwiseMesh(config, points, lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "type = spline" in content  # lowercase 'spline'
                assert "tension" in content
                assert "bias" in content
                assert "tangent_vec" in content  # tangent_vec_1 and tangent_vec_2
        finally:
            Path(filepath).unlink()

    def test_spline_out_of_bounds_indices(self, spanwise_points):
        """Test spline with out of bounds indices."""
        config = MeshConfig(
            title="Bad Spline",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        # Invalid: idx_end=3 but only 2 points
        lines = [
            Line(type="spline", end_points=[1, 3], nelem_line=20, type_span="uniform")
        ]

        # Error should be raised during mesh construction, not write
        with pytest.raises(IndexError, match="out of bounds"):
            mesh = PointwiseMesh(config, spanwise_points, lines)

    def test_straight_out_of_bounds_indices(self, spanwise_points):
        """Test straight line with out of bounds indices."""
        config = MeshConfig(
            title="Bad Straight",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        # Invalid: idx_end=5 but only 2 points
        lines = [
            Line(type="straight", end_points=[1, 5], nelem_line=20, type_span="uniform")
        ]

        # Error should be raised during mesh construction, not write
        with pytest.raises(IndexError, match="out of bounds"):
            mesh = PointwiseMesh(config, spanwise_points, lines)


class TestIOErrors:
    """Test I/O error handling."""

    def test_write_to_readonly_directory(self, monkeypatch):
        """Test writing to a read-only location."""
        config = MeshConfig(
            title="Test",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        points = [
            Point(id=1, coordinates=[0, 0, 0], chord=1.0, twist=0, airfoil="naca0012"),
            Point(id=2, coordinates=[0, 1, 0], chord=1.0, twist=0, airfoil="naca0012"),
        ]
        lines = [
            Line(type="straight", end_points=[1, 2], nelem_line=10, type_span="uniform")
        ]

        # Mock open to raise PermissionError
        def mock_open(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr("builtins.open", mock_open)

        with pytest.raises(IOError, match="Failed to write mesh file"):
            write_pointwise_mesh("test.in", points, lines, config)

    def test_parametric_write_io_error(self, monkeypatch):
        """Test parametric mesh write with I/O error."""
        config = MeshConfig(
            title="Test",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        sections = [
            Section(1.0, 0.0, "naca0012"),
            Section(0.6, 5.0, "naca0009"),
        ]

        regions = [Region(5.0, 0.0, 0.0, 20, "uniform")]

        def mock_open(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr("builtins.open", mock_open)

        with pytest.raises(IOError, match="Failed to write mesh file"):
            write_parametric_mesh("test.in", sections, regions, config)


class TestInternalEdgeCases:
    """Test internal function edge cases and dead code paths."""

    def test_tangent_calculation_edge_cases(self):
        """Test edge cases in tangent calculation that bypass __post_init__."""
        # This tests the defensive checks in _write_end_tangents
        # by directly calling the internal functions (for 100% coverage)
        from pydust_utils.build_mesh import _write_end_tangents, _write_spline
        import io

        config = MeshConfig(
            title="Edge Test",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        points = [
            Point(id=1, coordinates=[0, 0, 0], chord=1.0, twist=0, airfoil="naca0012"),
            Point(id=2, coordinates=[0, 5, 0], chord=0.6, twist=5, airfoil="naca0009"),
        ]

        # Test case where pt_start < 0 or pt_end >= len(points)
        # Create a valid line first, then manually override end_points to bypass validation
        line_out_of_bounds = Line(
            type="spline", end_points=[1, 2], nelem_line=10, type_span="uniform"
        )
        # Manually set invalid end_points to test internal function error handling
        line_out_of_bounds.end_points = [0, 1]
        file_obj = io.StringIO()

        with pytest.raises(IndexError, match="Invalid line indices"):
            _write_end_tangents(line_out_of_bounds, points, file_obj)

        # Test case where pt_start + 1 >= len(points)
        line_bad_start = Line(
            type="spline", end_points=[1, 2], nelem_line=10, type_span="uniform"
        )
        # Override to test edge case
        line_bad_start.end_points = [2, 2]  # Start at last point
        file_obj = io.StringIO()

        # This should raise IndexError for tangent calculation
        with pytest.raises(IndexError, match="Cannot calculate start tangent"):
            _write_end_tangents(line_bad_start, points, file_obj)

        # Test case where pt_end - 1 < 0
        line_bad_end = Line(
            type="spline", end_points=[1, 2], nelem_line=10, type_span="uniform"
        )
        # Override to test edge case
        line_bad_end.end_points = [1, 1]  # End at first point
        file_obj = io.StringIO()

        with pytest.raises(IndexError, match="Cannot calculate end tangent"):
            _write_end_tangents(line_bad_end, points, file_obj)

    def test_straight_line_internal_validation(self):
        """Test internal validation in _write_straight."""
        from pydust_utils.build_mesh import _write_straight
        import io

        points = [
            Point(id=1, coordinates=[0, 0, 0], chord=1.0, twist=0, airfoil="naca0012"),
            Point(id=2, coordinates=[0, 1, 0], chord=1.0, twist=0, airfoil="naca0012"),
        ]

        # Test idx_start < 1 - create valid line then override to bypass validation
        line_bad = Line(
            type="straight", end_points=[1, 2], nelem_line=10, type_span="uniform"
        )
        line_bad.end_points = [0, 1]  # Override with invalid value
        file_obj = io.StringIO()

        with pytest.raises(IndexError, match="out of bounds"):
            _write_straight(line_bad, points, file_obj)

        # Test idx_end > len(points)
        line_bad2 = Line(
            type="straight", end_points=[1, 5], nelem_line=10, type_span="uniform"
        )
        file_obj = io.StringIO()

        with pytest.raises(IndexError, match="out of bounds"):
            _write_straight(line_bad2, points, file_obj)

    def test_spline_line_internal_validation(self):
        """Test internal validation in _write_spline."""
        from pydust_utils.build_mesh import _write_spline
        import io

        points = [
            Point(id=1, coordinates=[0, 0, 0], chord=1.0, twist=0, airfoil="naca0012"),
            Point(id=2, coordinates=[0, 1, 0], chord=1.0, twist=0, airfoil="naca0012"),
        ]

        # Test idx_start < 1 - create valid line then override
        line_bad = Line(
            type="spline", end_points=[1, 2], nelem_line=10, type_span="uniform"
        )
        line_bad.end_points = [0, 1]  # Override with invalid value
        file_obj = io.StringIO()

        with pytest.raises(IndexError, match="out of bounds"):
            _write_spline(line_bad, points, file_obj)

        # Test idx_end > len(points)
        line_bad2 = Line(
            type="spline", end_points=[1, 5], nelem_line=10, type_span="uniform"
        )
        file_obj = io.StringIO()

        with pytest.raises(IndexError, match="out of bounds"):
            _write_spline(line_bad2, points, file_obj)

    def test_point_airfoil_table_missing(self):
        """Test missing airfoil_table for lifting-line point."""
        from pydust_utils.build_mesh import _write_point
        import io

        config = MeshConfig(
            title="LL Test",
            el_type="l",  # Lifting line requires airfoil_table
            nelem_chord=1,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        # Point without airfoil_table
        point_no_table = Point(
            id=1, coordinates=[0, 0, 0], chord=1.0, twist=0, airfoil="naca0012"
        )
        file_obj = io.StringIO()

        with pytest.raises(ValueError, match="missing airfoil_table"):
            _write_point(config, point_no_table, file_obj)

    def test_section_airfoil_table_missing(self):
        """Test missing airfoil_table for lifting-line section."""
        from pydust_utils.build_mesh import _write_section
        import io

        config = MeshConfig(
            title="LL Test",
            el_type="l",  # Lifting line requires airfoil_table
            nelem_chord=1,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        # Section without airfoil_table
        section_no_table = Section(1.0, 0.0, "naca0012")
        file_obj = io.StringIO()

        with pytest.raises(ValueError, match="missing airfoil_table"):
            _write_section(section_no_table, 0, config, file_obj)

    def test_pointwise_y_fountain_only(self, two_points, simple_lines):
        """Test y_fountain without symmetry or mirror."""
        config = MeshConfig(
            title="Fountain Only",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
            mesh_symmetry=False,
            mesh_mirror=False,
            y_fountain=2.0,
        )

        mesh = PointwiseMesh(config, two_points, simple_lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "y_fountain = 2.0" in content
                assert "mesh_symmetry" not in content
                assert "mesh_mirror" not in content
        finally:
            Path(filepath).unlink()

    def test_pointwise_none_optional_features(self, two_points, simple_lines):
        """Test pointwise with all optional features disabled."""
        config = MeshConfig(
            title="No Optional",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
            # All optional features default to False/None
        )

        mesh = PointwiseMesh(config, two_points, simple_lines)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                # Should not have any optional features
                assert "mesh_symmetry" not in content
                assert "mesh_mirror" not in content
                assert content.count("y_fountain") == 0  # Should not appear
                assert "airfoil_table_correction" not in content
        finally:
            Path(filepath).unlink()

    def test_parametric_combinations(self):
        """Test various combinations of optional features in parametric mesh."""
        # Test with symmetry only
        config1 = MeshConfig(
            title="Symmetry Only",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
            mesh_symmetry=True,
            symmetry_point=[0, 0, 0],
            symmetry_normal=[1, 0, 0],
        )

        sections = [Section(1.0, 0.0, "naca0012"), Section(0.6, 5.0, "naca0009")]
        regions = [Region(5.0, 0.0, 0.0, 20, "uniform")]

        mesh1 = ParametricMesh(config1, sections, regions)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh1.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "mesh_symmetry = T" in content
        finally:
            Path(filepath).unlink()

        # Test with mirror only
        config2 = MeshConfig(
            title="Mirror Only",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
            mesh_mirror=True,
            mirror_point=[0, 0, 0],
            mirror_normal=[0, 1, 0],
        )

        mesh2 = ParametricMesh(config2, sections, regions)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh2.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "mesh_mirror = T" in content
        finally:
            Path(filepath).unlink()

        # Test with y_fountain only
        config3 = MeshConfig(
            title="Fountain Only",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
            y_fountain=1.5,
        )

        mesh3 = ParametricMesh(config3, sections, regions)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh3.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "y_fountain = 1.5" in content
        finally:
            Path(filepath).unlink()

        # Test with no optional features
        config4 = MeshConfig(
            title="No Optional",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
        )

        mesh4 = ParametricMesh(config4, sections, regions)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh4.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "mesh_symmetry" not in content
                assert "mesh_mirror" not in content
                assert content.count("y_fountain") == 0  # Should not appear
        finally:
            Path(filepath).unlink()


class TestParametricOptionalFeatures:
    """Test optional features in parametric meshes."""

    def test_parametric_with_all_optional_features(self):
        """Test parametric mesh with mirror, symmetry, fountain, and correction."""
        config = MeshConfig(
            title="Full Features",
            el_type="v",
            nelem_chord=10,
            type_chord="uniform",
            reference_chord_fraction=0.25,
            mesh_symmetry=True,
            symmetry_point=[0.0, 0.0, 0.0],
            symmetry_normal=[1.0, 0.0, 0.0],
            mesh_mirror=True,
            mirror_point=[0.0, 0.0, 0.0],
            mirror_normal=[0.0, 1.0, 0.0],
            y_fountain=3.0,
            airfoil_table_correction=True,
        )

        sections = [
            Section(1.0, 0.0, "naca0012", "naca0012"),
            Section(0.6, 5.0, "naca0009", "naca0009"),
        ]

        regions = [Region(5.0, 0.0, 0.0, 20, "uniform")]

        mesh = ParametricMesh(config, sections, regions)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".in") as f:
            filepath = f.name

        try:
            mesh.write(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                assert "mesh_symmetry = T" in content
                assert "mesh_mirror = T" in content
                assert "y_fountain = 3.0" in content
                assert "airfoil_table_correction = T" in content
        finally:
            Path(filepath).unlink()
