"""Tests for launcher module."""

import tempfile
from pathlib import Path

import pytest

from pydust_utils.launcher import (
    DUSTConfig,
    FMMConfig,
    GPUConfig,
    HCASConfig,
    IOConfig,
    IntegrationConfig,
    KuttaConfig,
    LiftingLineConfig,
    ModelsConfig,
    ReferenceConditions,
    RegularizationConfig,
    RestartConfig,
    TimingConfig,
    VLCorrectionConfig,
    VariableWindConfig,
    WakeConfig,
    launch_dust,
)


# Fixtures for common test configurations
@pytest.fixture
def basic_timing():
    """Basic timing configuration for testing."""
    return TimingConfig(
        tstart=0.0,
        tend=1.0,
        dt=0.01,
        dt_out=0.1,
    )


@pytest.fixture
def basic_integration():
    """Basic integration configuration for testing."""
    return IntegrationConfig(
        integrator="RK",
        reformulated="T",
        f=2.0,
        g=1.0,
    )


@pytest.fixture
def basic_io():
    """Basic I/O configuration for testing."""
    return IOConfig(
        geometry_file="test.geo",
        reference_file="refs.dat",
        basename="results",
    )


@pytest.fixture
def basic_reference():
    """Basic reference conditions for testing."""
    return ReferenceConditions(
        altitude=0.0,
        u_inf=[10.0, 0.0, 0.0],
        u_ref=10.0,
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# Tests for TimingConfig
class TestTimingConfig:
    """Tests for TimingConfig dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        config = TimingConfig(tstart=0.0, tend=1.0, dt=0.01)
        assert config.tstart == 0.0
        assert config.tend == 1.0
        assert config.dt == 0.01
        assert config.dt_out == 0.01  # Should default to dt
        assert config.dt_debug_out == 0.01  # Should default to dt
        assert config.ndt_update_wake == 1

    def test_custom_values(self):
        """Test custom values override defaults."""
        config = TimingConfig(
            tstart=0.0,
            tend=10.0,
            dt=0.01,
            dt_out=0.5,
            dt_debug_out=1.0,
            ndt_update_wake=5,
        )
        assert config.dt_out == 0.5
        assert config.dt_debug_out == 1.0
        assert config.ndt_update_wake == 5

    def test_timesteps_optional(self):
        """Test that timesteps can be None."""
        config = TimingConfig(tstart=0.0, tend=1.0, dt=0.01)
        assert config.timesteps is None

    def test_to_dust_format(self):
        """Test output format generation."""
        from io import StringIO

        config = TimingConfig(tstart=0.0, tend=1.0, dt=0.01, timesteps=100)
        buffer = StringIO()
        config.to_dust_format(buffer)
        output = buffer.getvalue()

        assert "! ----- Time and timestep options -----" in output
        assert "tstart = 0.0" in output
        assert "tend = 1.0" in output
        assert "dt = 0.01" in output
        assert "timesteps = 100" in output


# Tests for IntegrationConfig
class TestIntegrationConfig:
    """Tests for IntegrationConfig dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        config = IntegrationConfig()
        assert config.integrator == "euler"
        assert config.reformulated == "T"
        assert config.f == 0.0
        assert config.g == 0.2
        assert config.suppress_initial_wake == "F"
        assert config.suppress_initial_wake_nsteps == 100

    def test_to_dust_format(self):
        """Test output format generation."""
        from io import StringIO

        config = IntegrationConfig(integrator="RK", reformulated="T")
        buffer = StringIO()
        config.to_dust_format(buffer)
        output = buffer.getvalue()

        assert "! ----- Reformulated formulation options -----" in output
        assert "integrator = RK" in output
        assert "reformulated = T" in output


# Tests for IOConfig
class TestIOConfig:
    """Tests for IOConfig dataclass."""

    def test_default_basename_debug(self):
        """Test basename_debug defaults to basename."""
        config = IOConfig(
            geometry_file="test.geo",
            reference_file="refs.dat",
            basename="results",
        )
        assert config.basename_debug == "results"

    def test_custom_basename_debug(self):
        """Test custom basename_debug."""
        config = IOConfig(
            geometry_file="test.geo",
            reference_file="refs.dat",
            basename="results",
            basename_debug="debug_results",
        )
        assert config.basename_debug == "debug_results"

    def test_to_dust_format(self):
        """Test output format generation."""
        from io import StringIO

        config = IOConfig(
            geometry_file="wing.geo",
            reference_file="refs.dat",
            basename="output",
        )
        buffer = StringIO()
        config.to_dust_format(buffer)
        output = buffer.getvalue()

        assert "! ----- Input options -----" in output
        assert "geometry_file = wing.geo" in output
        assert "reference_file = refs.dat" in output
        assert "basename = output" in output


# Tests for ReferenceConditions
class TestReferenceConditions:
    """Tests for ReferenceConditions dataclass."""

    def test_default_values(self):
        """Test default atmospheric values."""
        config = ReferenceConditions()
        assert config.altitude == 0.0
        assert config.units == "SI"
        assert config.u_inf == [1.0, 0.0, 0.0]  # Default is [1.0, 0.0, 0.0]
        assert config.u_ref == 1.0
        assert config.P_inf == 101325.0
        assert config.rho_inf == 1.225
        assert config.a_inf == 340.0
        assert config.mu_inf == 1.8e-5

    def test_vector_formatting(self):
        """Test vector is formatted correctly in output."""
        from io import StringIO

        config = ReferenceConditions(u_inf=[10.0, 0.0, 0.0])
        buffer = StringIO()
        config.to_dust_format(buffer)
        output = buffer.getvalue()

        assert "u_inf = (/10.0 , 0.0 , 0.0/)" in output


# Tests for WakeConfig
class TestWakeConfig:
    """Tests for WakeConfig dataclass."""

    def test_default_values(self):
        """Test default wake parameters."""
        config = WakeConfig()
        assert config.n_wake_panels == 1
        assert config.n_wake_particles == 10000
        assert config.particles_box_min == [-10.0, -10.0, -10.0]
        assert config.particles_box_max == [10.0, 10.0, 10.0]

    def test_vector_formatting(self):
        """Test vector formatting in output."""
        from io import StringIO

        config = WakeConfig(
            particles_box_min=[-20.0, -10.0, -10.0],
            particles_box_max=[50.0, 10.0, 10.0],
        )
        buffer = StringIO()
        config.to_dust_format(buffer)
        output = buffer.getvalue()

        assert "(/-20.0 , -10.0 , -10.0/)" in output
        assert "(/50.0 , 10.0 , 10.0/)" in output


# Tests for FMMConfig
class TestFMMConfig:
    """Tests for FMMConfig dataclass."""

    def test_default_values(self):
        """Test default FMM parameters."""
        config = FMMConfig()
        assert config.fmm == "T"
        assert config.fmm_panels == "F"
        assert config.dyn_layers is False

    def test_optional_vector_formatting(self):
        """Test optional vector parameters are handled correctly."""
        from io import StringIO

        config = FMMConfig(n_box=[10, 10, 10])
        buffer = StringIO()
        config.to_dust_format(buffer)
        output = buffer.getvalue()

        assert "(/10 , 10 , 10/)" in output

    def test_none_vector_formatting(self):
        """Test None vectors output 'None'."""
        from io import StringIO

        config = FMMConfig(n_box=None)
        buffer = StringIO()
        config.to_dust_format(buffer)
        output = buffer.getvalue()

        assert "n_box = None" in output

    def test_boolean_conversion(self):
        """Test boolean values are converted to T/F."""
        from io import StringIO

        config = FMMConfig(dyn_layers=True)
        buffer = StringIO()
        config.to_dust_format(buffer)
        output = buffer.getvalue()

        assert "dyn_layers = T" in output


# Tests for LiftingLineConfig
class TestLiftingLineConfig:
    """Tests for LiftingLineConfig dataclass."""

    def test_default_values(self):
        """Test default lifting line parameters."""
        config = LiftingLineConfig()
        # Simplified config only has these three parameters now
        assert config.ll_maxiter == 100
        assert config.ll_tol == 1.0e-6
        assert config.ll_relax == 25.0


# Tests for VariableWindConfig
class TestVariableWindConfig:
    """Tests for VariableWindConfig dataclass."""

    def test_default_values(self):
        """Test default variable wind parameters."""
        config = VariableWindConfig()
        assert config.time_varying_u_inf == "F"
        assert config.non_uniform_u_inf == "F"
        assert config.gust == "F"
        assert config.gust_perturbation_direction == [0.0, 0.0, 1.0]

    def test_optional_gust_vectors(self):
        """Test optional gust vector parameters."""
        from io import StringIO

        config = VariableWindConfig(
            gust="T",
            gust_origin=[0.0, 0.0, 0.0],
            gust_front_direction=[1.0, 0.0, 0.0],
        )
        buffer = StringIO()
        config.to_dust_format(buffer)
        output = buffer.getvalue()

        assert "gust_origin = (/0.0 , 0.0 , 0.0/)" in output
        assert "gust_front_direction = (/1.0 , 0.0 , 0.0/)" in output


# Tests for DUSTConfig
class TestDUSTConfig:
    """Tests for main DUSTConfig dataclass."""

    def test_initialization_with_defaults(self, temp_dir):
        """Test DUSTConfig initializes with default subconfigs."""
        config_file = temp_dir / "test.in"
        config = DUSTConfig(name=str(config_file))

        assert isinstance(config.timing, TimingConfig)
        assert isinstance(config.integration, IntegrationConfig)
        assert isinstance(config.io, IOConfig)
        assert isinstance(config.restart, RestartConfig)
        assert isinstance(config.reference, ReferenceConditions)
        assert isinstance(config.wake, WakeConfig)
        assert isinstance(config.regularization, RegularizationConfig)
        assert isinstance(config.lifting_line, LiftingLineConfig)
        assert isinstance(config.vl_correction, VLCorrectionConfig)
        assert isinstance(config.kutta, KuttaConfig)
        assert isinstance(config.fmm, FMMConfig)
        assert isinstance(config.models, ModelsConfig)
        assert isinstance(config.hcas, HCASConfig)
        assert isinstance(config.variable_wind, VariableWindConfig)
        assert isinstance(config.gpu, GPUConfig)

    def test_initialization_with_custom_configs(
        self, temp_dir, basic_timing, basic_integration
    ):
        """Test DUSTConfig initializes with custom subconfigs."""
        config_file = temp_dir / "test.in"
        config = DUSTConfig(
            name=str(config_file),
            timing=basic_timing,
            integration=basic_integration,
        )

        assert config.timing.dt == 0.01
        assert config.integration.integrator == "RK"

    def test_file_creation(self, temp_dir):
        """Test that __post_init__ creates an empty file."""
        config_file = temp_dir / "test.in"
        _ = DUSTConfig(name=str(config_file))  # Create config to trigger file creation

        assert config_file.exists()
        assert config_file.stat().st_size == 0

    def test_generate_input_file(
        self, temp_dir, basic_timing, basic_integration, basic_io, basic_reference
    ):
        """Test generate_input_file creates content."""
        config_file = temp_dir / "test.in"
        config = DUSTConfig(
            name=str(config_file),
            timing=basic_timing,
            integration=basic_integration,
            io=basic_io,
            reference=basic_reference,
        )

        config.generate_input_file()

        assert config._content != ""
        assert "! ----- Time and timestep options -----" in config._content
        assert "! ----- Integration options -----" in config._content
        assert "! ----- Input options -----" in config._content

    def test_save_to_file(
        self, temp_dir, basic_timing, basic_integration, basic_io, basic_reference
    ):
        """Test save_to_file writes content correctly."""
        config_file = temp_dir / "test.in"
        config = DUSTConfig(
            name=str(config_file),
            timing=basic_timing,
            integration=basic_integration,
            io=basic_io,
            reference=basic_reference,
        )

        config.generate_input_file()
        config.save_to_file()

        # Check file was written
        assert config_file.exists()
        content = config_file.read_text()

        # Check key sections are present
        assert "tstart = 0.0" in content
        assert "tend = 1.0" in content
        assert "dt = 0.01" in content
        assert "integrator = RK" in content
        assert "geometry_file = test.geo" in content

    def test_save_to_custom_path(
        self, temp_dir, basic_timing, basic_integration, basic_io, basic_reference
    ):
        """Test save_to_file with custom path."""
        config_file = temp_dir / "test.in"
        custom_file = temp_dir / "custom.in"

        config = DUSTConfig(
            name=str(config_file),
            timing=basic_timing,
            integration=basic_integration,
            io=basic_io,
            reference=basic_reference,
        )

        config.generate_input_file()
        config.save_to_file(str(custom_file))

        assert custom_file.exists()
        content = custom_file.read_text()
        assert "tstart = 0.0" in content

    def test_none_filtering(self, temp_dir):
        """Test that lines with 'None' are filtered out."""
        config_file = temp_dir / "test.in"
        config = DUSTConfig(name=str(config_file))

        # Generate file with some None values (e.g., optional FMM parameters)
        config.generate_input_file()
        config.save_to_file()

        content = config_file.read_text()

        # Check that lines with None are not in the output
        # (timesteps should be None by default and filtered)
        lines_with_none = [line for line in content.split("\n") if "None" in line]
        assert len(lines_with_none) == 0


# Tests for complete workflow
class TestCompleteWorkflow:
    """Test complete DUST input file generation workflow."""

    def test_minimal_configuration(self, temp_dir):
        """Test creating a minimal DUST input file."""
        config_file = temp_dir / "minimal.in"

        config = DUSTConfig(
            name=str(config_file),
            timing=TimingConfig(tstart=0.0, tend=1.0, dt=0.01),
            reference=ReferenceConditions(u_inf=[10.0, 0.0, 0.0], u_ref=10.0),
        )

        config.generate_input_file()
        config.save_to_file()

        assert config_file.exists()
        content = config_file.read_text()

        # Verify essential sections are present
        assert "! ----- Time and timestep options -----" in content
        assert "! ----- Reference conditions parameters -----" in content
        assert "u_inf = (/10.0 , 0.0 , 0.0/)" in content

    def test_complex_configuration(self, temp_dir):
        """Test creating a complex DUST input file with multiple features."""
        config_file = temp_dir / "complex.in"

        config = DUSTConfig(
            name=str(config_file),
            timing=TimingConfig(tstart=0.0, tend=10.0, dt=0.01, dt_out=0.1),
            integration=IntegrationConfig(integrator="RK", reformulated="T"),
            io=IOConfig(
                geometry_file="wing.geo",
                reference_file="refs.dat",
                basename="results",
                output_start="T",
            ),
            reference=ReferenceConditions(
                altitude=1000.0, u_inf=[20.0, 0.0, 0.0], u_ref=20.0
            ),
            wake=WakeConfig(
                n_wake_panels=100,
                n_wake_particles=50000,
                particles_box_min=[-50.0, -20.0, -20.0],
                particles_box_max=[100.0, 20.0, 20.0],
            ),
            fmm=FMMConfig(
                fmm="T",
                fmm_panels="T",
                n_box=[20, 20, 20],
                dyn_layers=True,
            ),
            lifting_line=LiftingLineConfig(
                ll_maxiter=200,
            ),
            variable_wind=VariableWindConfig(
                gust="T",
                gust_type="AMC",
                gust_origin=[0.0, 0.0, 0.0],
                gust_front_direction=[1.0, 0.0, 0.0],
            ),
        )

        config.generate_input_file()
        config.save_to_file()

        assert config_file.exists()
        content = config_file.read_text()

        # Verify all configured sections are present
        assert "tend = 10.0" in content
        assert "integrator = RK" in content
        assert "geometry_file = wing.geo" in content
        assert "altitude = 1000.0" in content
        assert "n_wake_panels = 100" in content
        assert "fmm_panels = T" in content
        assert "ll_maxiter = 200" in content
        assert "gust = T" in content


# Tests for edge cases
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_vectors_not_allowed(self):
        """Test that empty vectors use defaults."""
        config = ReferenceConditions()
        assert len(config.u_inf) == 3

    def test_negative_timestep_allowed(self):
        """Test that negative timestep is allowed (though physically invalid)."""
        config = TimingConfig(tstart=0.0, tend=1.0, dt=-0.01)
        assert config.dt == -0.01

    def test_very_large_particle_count(self):
        """Test handling of very large particle counts."""
        config = WakeConfig(n_wake_particles=10000000)
        assert config.n_wake_particles == 10000000

    def test_special_characters_in_filenames(self, temp_dir):
        """Test handling of special characters in filenames."""
        config = IOConfig(
            geometry_file="test_file-v2.geo",
            reference_file="refs_2024.dat",
            basename="results_final",
        )

        from io import StringIO

        buffer = StringIO()
        config.to_dust_format(buffer)
        output = buffer.getvalue()

        assert "test_file-v2.geo" in output
        assert "refs_2024.dat" in output


# Tests for launch_dust function
class TestLaunchDust:
    """Tests for launch_dust function."""

    def test_launch_dust_signature(self):
        """Test that launch_dust has the correct signature."""
        import inspect

        sig = inspect.signature(launch_dust)
        assert "dust_executable" in sig.parameters
        assert "input_file" in sig.parameters

    def test_launch_dust_command_format(self, capsys, monkeypatch):
        """Test that launch_dust formats command correctly."""
        # Mock os.system to prevent actual execution
        commands_run = []

        def mock_system(cmd):
            commands_run.append(cmd)
            return 0

        monkeypatch.setattr("os.system", mock_system)

        launch_dust("/path/to/dust", "simulation.in")

        # Check the command was formatted correctly
        assert len(commands_run) == 1
        assert "/path/to/dust simulation.in" in commands_run[0]

        # Check that it printed the command
        captured = capsys.readouterr()
        assert "/path/to/dust simulation.in" in captured.out


# Integration tests
class TestIntegration:
    """Integration tests combining multiple components."""

    def test_modify_and_regenerate(self, temp_dir):
        """Test modifying configuration and regenerating file."""
        config_file = temp_dir / "test.in"

        # Create initial configuration
        config = DUSTConfig(
            name=str(config_file),
            timing=TimingConfig(tstart=0.0, tend=1.0, dt=0.01),
        )
        config.generate_input_file()
        config.save_to_file()

        # Modify configuration
        config.timing.tend = 5.0
        config.timing.dt = 0.05

        # Regenerate
        config.generate_input_file()
        config.save_to_file()

        # Check modifications are reflected
        content = config_file.read_text()
        assert "tend = 5.0" in content
        assert "dt = 0.05" in content

    def test_multiple_configs_same_directory(self, temp_dir):
        """Test creating multiple configurations in same directory."""
        config1 = DUSTConfig(
            name=str(temp_dir / "sim1.in"),
            timing=TimingConfig(tstart=0.0, tend=1.0, dt=0.01),
        )
        config2 = DUSTConfig(
            name=str(temp_dir / "sim2.in"),
            timing=TimingConfig(tstart=0.0, tend=2.0, dt=0.02),
        )

        config1.generate_input_file()
        config1.save_to_file()

        config2.generate_input_file()
        config2.save_to_file()

        # Check both files exist and are different
        file1 = (temp_dir / "sim1.in").read_text()
        file2 = (temp_dir / "sim2.in").read_text()

        assert "tend = 1.0" in file1
        assert "tend = 2.0" in file2
        assert "dt = 0.01" in file1
        assert "dt = 0.02" in file2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
