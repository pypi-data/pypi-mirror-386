"""Tests for C81 aerodynamic table generation."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from pydust_utils.c81generator import (
    Airfoil,
    generate_airfoil_data,
)


# Fixtures
@pytest.fixture
def test_airfoil_path():
    """Path to test airfoil data files."""
    return Path(__file__).parent / "dat_files"


@pytest.fixture
def single_re_airfoil():
    """Create a simple airfoil with single Reynolds number for testing."""
    mach = np.array([0.0, 0.3, 0.6])
    aoa = np.array([-10.0, 0.0, 10.0, 20.0])
    re = 1e6

    # Create simple test data (3 mach x 4 aoa)
    cl = np.array(
        [
            [-0.5, 0.0, 1.0, 1.5],
            [-0.4, 0.1, 1.1, 1.6],
            [-0.3, 0.2, 1.2, 1.7],
        ]
    )
    cd = np.array(
        [
            [0.01, 0.015, 0.02, 0.03],
            [0.012, 0.017, 0.022, 0.032],
            [0.014, 0.019, 0.024, 0.034],
        ]
    )
    cm = np.array(
        [
            [-0.05, -0.03, -0.01, 0.01],
            [-0.04, -0.02, 0.0, 0.02],
            [-0.03, -0.01, 0.01, 0.03],
        ]
    )

    return Airfoil(
        name="test_airfoil",
        mach=mach,
        aoa=aoa,
        re=re,
        cl=cl,
        cd=cd,
        cm=cm,
    )


@pytest.fixture
def multi_re_airfoil():
    """Create an airfoil with multiple Reynolds numbers for testing."""
    mach = np.array([0.0, 0.3])
    aoa = np.array([-5.0, 0.0, 5.0])
    re = np.array([1e5, 5e5, 1e6])

    # Create test data (3 re x 2 mach x 3 aoa)
    cl = np.array(
        [
            [[-0.3, 0.0, 0.8], [-0.2, 0.1, 0.9]],  # Re=1e5
            [[-0.4, 0.0, 1.0], [-0.3, 0.1, 1.1]],  # Re=5e5
            [[-0.5, 0.0, 1.2], [-0.4, 0.1, 1.3]],  # Re=1e6
        ]
    )
    cd = np.array(
        [
            [[0.015, 0.012, 0.020], [0.017, 0.014, 0.022]],
            [[0.013, 0.010, 0.018], [0.015, 0.012, 0.020]],
            [[0.011, 0.008, 0.016], [0.013, 0.010, 0.018]],
        ]
    )
    cm = np.array(
        [
            [[-0.02, -0.01, 0.0], [-0.01, 0.0, 0.01]],
            [[-0.03, -0.02, -0.01], [-0.02, -0.01, 0.0]],
            [[-0.04, -0.03, -0.02], [-0.03, -0.02, -0.01]],
        ]
    )

    return Airfoil(
        name="test_airfoil_multi",
        mach=mach,
        aoa=aoa,
        re=re,
        cl=cl,
        cd=cd,
        cm=cm,
    )


# Test Airfoil validation
class TestAirfoilValidation:
    """Test Airfoil dataclass validation."""

    def test_valid_single_re(self, single_re_airfoil):
        """Test that valid single Re airfoil is created."""
        assert single_re_airfoil.re == 1e6
        assert single_re_airfoil.cl.shape == (3, 4)
        assert single_re_airfoil.cd.shape == (3, 4)
        assert single_re_airfoil.cm.shape == (3, 4)

    def test_valid_multi_re(self, multi_re_airfoil):
        """Test that valid multi Re airfoil is created."""
        assert len(multi_re_airfoil.re) == 3
        assert multi_re_airfoil.cl.shape == (3, 2, 3)
        assert multi_re_airfoil.cd.shape == (3, 2, 3)
        assert multi_re_airfoil.cm.shape == (3, 2, 3)

    def test_negative_reynolds_single(self):
        """Test that negative Reynolds number raises error."""
        with pytest.raises(ValueError, match="Reynolds number must be positive"):
            Airfoil(
                name="bad",
                mach=np.array([0.0]),
                aoa=np.array([0.0]),
                re=-1e6,
                cl=np.array([[1.0]]),
                cd=np.array([[0.01]]),
                cm=np.array([[-0.01]]),
            )

    def test_negative_reynolds_multi(self):
        """Test that negative Reynolds in array raises error."""
        with pytest.raises(ValueError, match="All Reynolds numbers must be positive"):
            Airfoil(
                name="bad",
                mach=np.array([0.0]),
                aoa=np.array([0.0]),
                re=np.array([1e5, -5e5, 1e6]),
                cl=np.array([[[1.0]], [[1.0]], [[1.0]]]),
                cd=np.array([[[0.01]], [[0.01]], [[0.01]]]),
                cm=np.array([[[-0.01]], [[-0.01]], [[-0.01]]]),
            )

    def test_mismatched_shape_single_re(self):
        """Test that mismatched coefficient shape raises error."""
        with pytest.raises(ValueError, match="cl matrix shape"):
            Airfoil(
                name="bad",
                mach=np.array([0.0, 0.3]),
                aoa=np.array([0.0, 5.0]),
                re=1e6,
                cl=np.array([[1.0]]),  # Wrong shape: should be (2, 2)
                cd=np.array([[0.01, 0.01], [0.01, 0.01]]),
                cm=np.array([[-0.01, -0.01], [-0.01, -0.01]]),
            )

    def test_mismatched_shape_multi_re(self):
        """Test that mismatched coefficient shape with multi Re raises error."""
        with pytest.raises(ValueError, match="cl matrix shape"):
            Airfoil(
                name="bad",
                mach=np.array([0.0]),
                aoa=np.array([0.0]),
                re=np.array([1e5, 1e6]),
                cl=np.array([[1.0]]),  # Wrong shape: should be (2, 1, 1)
                cd=np.array([[[0.01]], [[0.01]]]),
                cm=np.array([[[-0.01]], [[-0.01]]]),
            )


# Test file generation
class TestFileGeneration:
    """Test C81 file generation for different formats."""

    def test_dust_format_single_re(self, single_re_airfoil):
        """Test DUST format file generation for single Re."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = single_re_airfoil.generate_c81_file(
                mbdynformat=False, pathout=tmpdir
            )

            assert output_path.exists()
            assert output_path.suffix == ".c81"
            assert "dust" in output_path.stem
            assert "Re_1000000" in output_path.stem

            # Check file content
            with open(output_path) as f:
                content = f.read()

            assert "1 0 0" in content  # Single Re header
            assert "0 1" in content
            assert "0.158 0.158" in content
            assert "1000000" in content  # Reynolds number
            assert " 0304" in content  # 03 mach, 04 aoa for each coef

    def test_dust_format_multi_re(self, multi_re_airfoil):
        """Test DUST format file generation for multiple Re."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = multi_re_airfoil.generate_c81_file(
                mbdynformat=False, pathout=tmpdir
            )

            assert output_path.exists()
            assert "Re_100000_to_1000000" in output_path.stem

            # Check file content
            with open(output_path) as f:
                content = f.read()

            assert "3 0 0" in content  # Three Re tables
            assert "100000" in content  # First Re
            assert "500000" in content  # Second Re
            assert "1000000" in content  # Third Re

    def test_mbdyn_format_single_re(self, single_re_airfoil):
        """Test MBDyn format file generation for single Re."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = single_re_airfoil.generate_c81_file(
                mbdynformat=True, pathout=tmpdir
            )

            assert output_path.exists()
            assert "mbdyn" in output_path.stem

            # Check file content
            with open(output_path) as f:
                content = f.read()

            # MBDyn format starts with airfoil name padded to 30 chars
            lines = content.split("\n")
            assert len(lines[0]) >= 30
            # Format is: name (30 chars) + repeated "03040304" for CL/CD/CM counts
            assert "0304" in lines[0]  # Mach/AoA counts present

    def test_mbdyn_format_rejects_multi_re(self, multi_re_airfoil):
        """Test that MBDyn format rejects multiple Re."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(
                ValueError, match="MBDyn format does not support multiple Reynolds"
            ):
                multi_re_airfoil.generate_c81_file(mbdynformat=True, pathout=tmpdir)

    def test_output_directory_creation(self, single_re_airfoil):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "output" / "dir"
            output_path = single_re_airfoil.generate_c81_file(pathout=nested_path)

            assert nested_path.exists()
            assert output_path.exists()

    def test_filename_generation(self, single_re_airfoil):
        """Test that filename attribute is set correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            single_re_airfoil.generate_c81_file(pathout=tmpdir)

            assert single_re_airfoil.filename == "test_airfoil_dust_Re_1000000"


# Test plotting
class TestPlotting:
    """Test C81 table plotting functionality."""

    def test_plot_single_re(self, single_re_airfoil):
        """Test plotting for single Re."""
        with tempfile.TemporaryDirectory() as tmpdir:
            single_re_airfoil.plot_c81_table(save_fig=True, pathout=tmpdir)

            plot_file = Path(tmpdir) / "test_airfoil_Re_1000000.png"
            assert plot_file.exists()

    def test_plot_multi_re_specific(self, multi_re_airfoil):
        """Test plotting specific Re from multi Re airfoil."""
        with tempfile.TemporaryDirectory() as tmpdir:
            multi_re_airfoil.plot_c81_table(save_fig=True, pathout=tmpdir, re_index=0)

            plot_file = Path(tmpdir) / "test_airfoil_multi_Re_100000.png"
            assert plot_file.exists()

    def test_plot_multi_re_all(self, multi_re_airfoil):
        """Test plotting all Re from multi Re airfoil."""
        with tempfile.TemporaryDirectory() as tmpdir:
            multi_re_airfoil.plot_c81_table(
                save_fig=True, pathout=tmpdir, re_index=None
            )

            plot_file = Path(tmpdir) / "test_airfoil_multi_Re_all.png"
            assert plot_file.exists()

    def test_plot_return_figure(self, single_re_airfoil):
        """Test that plot returns figure when save_fig=False."""
        fig = single_re_airfoil.plot_c81_table(save_fig=False)

        assert fig is not None
        assert len(fig.axes) == 3  # CL, CD, CM subplots

    def test_plot_invalid_re_index(self, multi_re_airfoil):
        """Test that invalid re_index raises error."""
        with pytest.raises(IndexError, match="re_index .* out of bounds"):
            multi_re_airfoil.plot_c81_table(save_fig=False, re_index=10)

    def test_plot_custom_aoa_limits(self, single_re_airfoil):
        """Test plotting with custom AoA limits."""
        fig = single_re_airfoil.plot_c81_table(save_fig=False, aoa_limits=(-20, 30))

        for ax in fig.axes:
            xlim = ax.get_xlim()
            assert xlim[0] == -20
            assert xlim[1] == 30


# Test integration with real airfoil data
class TestIntegration:
    """Test with real NACA0012 airfoil data."""

    @pytest.mark.skipif(
        not Path(__file__).parent.joinpath("dat_files/test_c81.dat").exists(),
        reason="test_c81.dat file not found",
    )
    def test_generate_single_re_from_file(self, test_airfoil_path):
        """Test generating C81 table from real airfoil file."""
        # This test requires aerosandbox, skip if not available
        try:
            airfoil = generate_airfoil_data(
                file_name="test_c81",
                pathprofile=test_airfoil_path,
                reynolds=1e6,
                mach_range=(0.0, 0.3),
                n_mach=3,
                aoa_range=(-10.0, 10.0),
                model_size="small",  # Use smallest model for faster testing
            )

            assert airfoil.name == "test_c81"
            assert airfoil.re == 1e6
            assert len(airfoil.mach) == 3
            assert airfoil.cl.shape[0] == 3  # 3 mach numbers

            # Verify reasonable CL values at zero AoA
            zero_aoa_idx = np.argmin(np.abs(airfoil.aoa))
            # Near zero for symmetric airfoil (allow ±0.25 tolerance for neural net)
            assert -0.25 < airfoil.cl[0, zero_aoa_idx] < 0.25

        except ImportError:
            pytest.skip("aerosandbox not available")

    @pytest.mark.skipif(
        not Path(__file__).parent.joinpath("dat_files/test_c81.dat").exists(),
        reason="test_c81.dat file not found",
    )
    def test_generate_multi_re_from_file(self, test_airfoil_path):
        """Test generating multi-Re C81 table from real airfoil file."""
        try:
            airfoil = generate_airfoil_data(
                file_name="test_c81",
                pathprofile=test_airfoil_path,
                reynolds=[1e5, 1e6],
                mach_range=(0.0, 0.3),
                n_mach=2,
                aoa_range=(-5.0, 5.0),
                model_size="small",
            )

            assert airfoil.name == "test_c81"
            assert len(airfoil.re) == 2
            assert np.array_equal(airfoil.re, [1e5, 1e6])
            assert airfoil.cl.shape == (2, 2, airfoil.aoa.shape[0])

            # Verify CD decreases with Re (lower Re = higher drag)
            zero_aoa_idx = np.argmin(np.abs(airfoil.aoa))
            cd_low_re = airfoil.cd[0, 0, zero_aoa_idx]
            cd_high_re = airfoil.cd[1, 0, zero_aoa_idx]
            assert cd_low_re > cd_high_re  # Lower Re has higher drag

        except ImportError:
            pytest.skip("aerosandbox not available")

    def test_file_not_found_error(self, test_airfoil_path):
        """Test that missing airfoil file raises error."""
        with pytest.raises(FileNotFoundError, match="Airfoil file not found"):
            generate_airfoil_data(
                file_name="nonexistent_airfoil",
                pathprofile=test_airfoil_path,
                reynolds=1e6,
            )

    def test_invalid_reynolds_error(self, test_airfoil_path):
        """Test that invalid Reynolds number raises error."""
        with pytest.raises(ValueError, match="All Reynolds numbers must be positive"):
            generate_airfoil_data(
                file_name="test_c81",
                pathprofile=test_airfoil_path,
                reynolds=-1e6,
            )

    def test_invalid_mach_range_error(self, test_airfoil_path):
        """Test that invalid Mach range raises error."""
        with pytest.raises(ValueError, match="Invalid Mach range"):
            generate_airfoil_data(
                file_name="test_c81",
                pathprofile=test_airfoil_path,
                reynolds=1e6,
                mach_range=(0.5, 0.3),  # Min > Max
            )

    def test_empty_reynolds_array_error(self, test_airfoil_path):
        """Test that empty Reynolds array raises error."""
        with pytest.raises(ValueError, match="Reynolds number array cannot be empty"):
            generate_airfoil_data(
                file_name="test_c81",
                pathprofile=test_airfoil_path,
                reynolds=[],
            )

    @pytest.mark.skipif(
        not Path(__file__).parent.joinpath("dat_files/NACA2411.dat").exists(),
        reason="NACA2411.dat file not found",
    )
    @pytest.mark.skipif(
        not Path(__file__).parent.joinpath("dat_files/NACA2411.c81").exists(),
        reason="NACA2411.c81 reference file not found",
    )
    def test_naca2411_comparison(self, test_airfoil_path):
        """Test NACA2411 generation and compare with reference C81 file."""
        try:
            # Generate C81 data at the exact Reynolds number from reference file
            reynolds = 44352.222405255954
            airfoil = generate_airfoil_data(
                file_name="NACA2411",
                pathprofile=test_airfoil_path,
                reynolds=reynolds,
                mach_range=(0.0, 0.9),
                n_mach=10,  # 10 Mach numbers (0.0 to 0.9)
                aoa_range=(-180.0, 180.0),
                model_size="xxxlarge",  # Use largest model for best accuracy
            )

            # Read reference C81 file
            ref_file = test_airfoil_path / "NACA2411.c81"
            with open(ref_file) as f:
                lines = f.readlines()

            # Parse header info from reference file
            assert lines[0].strip() == "1 0 0"  # Single Re table
            re_line = lines[4].strip().split()
            ref_reynolds = float(re_line[0])
            assert abs(ref_reynolds - reynolds) < 1e-6

            # Parse matrix size indicator
            matrix_size_line = lines[5].strip()
            # Format is: "109910991099" = "10" "99" "10" "99" "10" "99" (CL, CD, CM tables)
            # Each coefficient table has n_mach x n_aoa dimensions
            n_mach_ref = int(matrix_size_line[0:2])  # First 2 chars: "10"
            n_aoa_ref = int(matrix_size_line[2:4])  # Next 2 chars: "99"

            # Verify generated data dimensions
            assert airfoil.re == reynolds
            # Generated data should have 10 Mach numbers
            assert len(airfoil.mach) == n_mach_ref  # Should match reference (10)
            # AoA count might differ due to sampling, but should be reasonable
            assert airfoil.aoa.shape[0] > 0

            # Parse reference Mach numbers
            mach_line = lines[6].strip().split()
            ref_mach = np.array([float(m) for m in mach_line])
            assert len(ref_mach) == n_mach_ref

            # Verify Mach number consistency (should be similar)
            np.testing.assert_allclose(
                airfoil.mach,
                ref_mach,
                rtol=0.05,
                atol=0.01,
                err_msg="Generated Mach numbers differ from reference",
            )

            # Parse a few reference CL values at key AoA points
            # Find specific AoA lines for comparison
            ref_data = {}
            current_line = 7
            for i in range(n_aoa_ref):
                data_line = lines[current_line + i].strip().split()
                aoa = float(data_line[0])
                cl_values = np.array([float(v) for v in data_line[1:]])
                ref_data[aoa] = {"cl": cl_values}

            # Compare at key angles: 0°, 5°, 10°, -5°, -10°
            test_angles = [0.0, 5.0, 10.0, -5.0, -10.0]
            for test_aoa in test_angles:
                if test_aoa in ref_data:
                    # Find closest AoA in generated data
                    gen_idx = np.argmin(np.abs(airfoil.aoa - test_aoa))
                    gen_aoa = airfoil.aoa[gen_idx]

                    # Only compare if AoA is very close (within 0.5 degrees)
                    if abs(gen_aoa - test_aoa) < 0.5:
                        gen_cl = airfoil.cl[:, gen_idx]
                        ref_cl = ref_data[test_aoa]["cl"]

                        # Allow larger tolerance due to NeuralFoil vs reference differences
                        # We're testing that the general trend is similar
                        np.testing.assert_allclose(
                            gen_cl,
                            ref_cl,
                            rtol=0.3,
                            atol=0.2,
                            err_msg=f"CL mismatch at AoA={test_aoa}°",
                        )

            # Test file generation with correct naming
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = airfoil.generate_c81_file(
                    mbdynformat=False, pathout=tmpdir
                )

                assert output_path.exists()
                assert "NACA2411" in output_path.stem
                assert "Re_44352" in output_path.stem

                # Verify generated file structure matches reference
                with open(output_path) as f:
                    gen_lines = f.readlines()

                # Check header structure
                assert gen_lines[0].strip() == "1 0 0"
                assert gen_lines[1].strip() == "0 1"
                assert gen_lines[2].strip() == "0.158 0.158"

                # Check Reynolds number in file
                assert "44352" in gen_lines[4]

        except ImportError:
            pytest.skip("aerosandbox not available")


# Test data format consistency
class TestDataFormatConsistency:
    """Test that generated C81 files have correct format."""

    def test_dust_matrix_format(self, single_re_airfoil):
        """Test that DUST format matrices have correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = single_re_airfoil.generate_c81_file(pathout=tmpdir)

            with open(output_path) as f:
                lines = f.readlines()

            # Find the first matrix (CL)
            matrix_start = None
            for i, line in enumerate(lines):
                if "0304" in line:  # Matrix size indicator
                    matrix_start = i + 1
                    break

            assert matrix_start is not None

            # Check Mach header line (should have 3 values, 7 spaces indent + 3*7 chars)
            mach_line = lines[matrix_start].strip()
            mach_values = mach_line.split()
            assert len(mach_values) == 3

            # Check AoA data lines (should have 4 rows for 4 AoA values)
            # Each row: AoA value (7 chars) + 3 coefficient values (7 chars each)
            for i in range(4):
                data_line = lines[matrix_start + 1 + i]
                values = data_line.split()
                assert len(values) == 4  # AoA + 3 mach points

    def test_dust_multi_re_structure(self, multi_re_airfoil):
        """Test that DUST multi-Re format has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = multi_re_airfoil.generate_c81_file(pathout=tmpdir)

            with open(output_path) as f:
                content = f.read()

            # Count number of Re values (should appear 3 times)
            re_count_100k = content.count("100000")
            re_count_500k = content.count("500000")
            re_count_1m = content.count("1000000")

            assert re_count_100k >= 1  # At least once for Re=1e5
            assert re_count_500k >= 1  # At least once for Re=5e5
            assert re_count_1m >= 1  # At least once for Re=1e6

    def test_mbdyn_line_wrapping(self):
        """Test that MBDyn format wraps lines correctly at 9 columns."""
        # Create airfoil with 20 Mach numbers (> 9, will trigger wrapping)
        mach = np.linspace(0.0, 0.9, 20)
        aoa = np.array([0.0, 5.0])
        airfoil = Airfoil(
            name="wrap_test",
            mach=mach,
            aoa=aoa,
            re=1e6,
            cl=np.random.rand(20, 2),
            cd=np.random.rand(20, 2) * 0.1,
            cm=np.random.rand(20, 2) * 0.1 - 0.05,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = airfoil.generate_c81_file(mbdynformat=True, pathout=tmpdir)

            with open(output_path) as f:
                lines = f.readlines()

            # Find first data matrix
            matrix_start = 1  # Skip header line

            # Mach header should be wrapped (20 values / 9 per line = 3 lines)
            # Each continuation line should start with 7 spaces
            mach_line_2 = lines[matrix_start + 1]
            mach_line_3 = lines[matrix_start + 2]

            assert mach_line_2.startswith(" " * 7)
            assert mach_line_3.startswith(" " * 7)
