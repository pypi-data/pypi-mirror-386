"""Generate C81 aerodynamic tables from airfoil profiles.

This module provides functionality to generate C81 aerodynamic coefficient tables
for use with DUST and MBDyn simulations. Tables include lift, drag, and moment
coefficients as functions of angle of attack and Mach number.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

try:
    import aerosandbox as asb  # type: ignore[import-untyped]
except ImportError as e:
    raise ImportError(
        "aerosandbox is required for c81generator. "
        "Install with: pip install aerosandbox"
    ) from e

__all__ = ["Airfoil", "generate_airfoil_data"]

# Constants for file formats
DUST_HEADER_LINE1 = "1 0 0"
DUST_HEADER_LINE2 = "0 1"
CHORD_REFERENCE = "0.158 0.158"
DEFAULT_CHORD_LOCATION = 0.200

# Format specifications
MACH_FORMAT = "{:7.2f}"
COEF_FORMAT = "{:7.3f}"
AOA_FORMAT = "{:7.1f}"
MBDYN_LINE_LENGTH = 9  # Columns per line in MBDyn format


@dataclass
class Airfoil:
    """Airfoil aerodynamic data for C81 table generation.

    Attributes:
        name: Airfoil name identifier
        mach: Array of Mach numbers
        aoa: Array of angles of attack (degrees)
        re: Reynolds number(s). Can be a single float or array of floats.
            For DUST format with multiple Re, use array: [Re1, Re2, ...]
        cl: Lift coefficient matrix. Shape depends on re:
            - Single Re: [mach x aoa]
            - Multiple Re: [n_re x mach x aoa]
        cd: Drag coefficient matrix (same shape as cl)
        cm: Moment coefficient matrix (same shape as cl)
        filename: Generated output filename (set during write)
    """

    name: str
    mach: NDArray[np.float64]
    aoa: NDArray[np.float64]
    re: float | NDArray[np.float64]
    cl: NDArray[np.float64]
    cd: NDArray[np.float64]
    cm: NDArray[np.float64]
    filename: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate airfoil data consistency."""
        n_mach = len(self.mach)
        n_aoa = len(self.aoa)

        # Determine if we have single or multiple Reynolds numbers
        is_multi_re = isinstance(self.re, np.ndarray)

        if is_multi_re:
            # Type narrowing for mypy
            assert isinstance(self.re, np.ndarray)
            n_re = len(self.re)
            expected_shape: tuple[int, int] | tuple[int, int, int] = (
                n_re,
                n_mach,
                n_aoa,
            )

            # Validate all Re are positive
            if np.any(self.re <= 0):
                raise ValueError(
                    f"All Reynolds numbers must be positive, got {self.re}"
                )
        else:
            expected_shape = (n_mach, n_aoa)

            # Validate single Re is positive
            assert isinstance(self.re, float)
            if self.re <= 0:
                raise ValueError(f"Reynolds number must be positive, got {self.re}")

        # Validate coefficient matrix shapes
        for coef_name, coef_data in [("cl", self.cl), ("cd", self.cd), ("cm", self.cm)]:
            if coef_data.shape != expected_shape:
                raise ValueError(
                    f"{coef_name} matrix shape {coef_data.shape} does not match "
                    f"expected {expected_shape} from mach, aoa, and re arrays"
                )

    def generate_c81_file(
        self,
        mbdynformat: bool = False,
        pathout: Path | str = "c81tables",
    ) -> Path:
        """Generate C81 aerodynamic table file.

        Args:
            mbdynformat: If True, generate MBDyn-compatible format.
                        If False (default), generate DUST format.
                        Note: MBDyn format only supports single Reynolds number.
            pathout: Output directory path for generated files.

        Returns:
            Path to the generated C81 file.

        Raises:
            OSError: If unable to create output directory or write file.
            ValueError: If data validation fails or if trying to use
                       multiple Re with MBDyn format.
        """
        output_folder = Path(pathout)
        output_folder.mkdir(exist_ok=True, parents=True)

        # Check if multiple Reynolds numbers
        is_multi_re = isinstance(self.re, np.ndarray)

        if mbdynformat and is_multi_re:
            raise ValueError(
                "MBDyn format does not support multiple Reynolds numbers. "
                "Use DUST format or provide a single Reynolds number."
            )

        postfix = "mbdyn" if mbdynformat else "dust"

        # Generate filename
        if is_multi_re:
            # Type narrowing for mypy
            assert isinstance(self.re, np.ndarray)
            re_str = f"Re_{int(self.re[0])}_to_{int(self.re[-1])}"
        else:
            assert isinstance(self.re, float)
            re_str = f"Re_{int(self.re)}"

        self.filename = f"{self.name}_{postfix}_{re_str}"
        output_file = output_folder / f"{self.filename}.c81"

        if mbdynformat:
            content = self._format_mbdyn()
        else:
            content = self._format_dust()

        with open(output_file, "w") as f:
            f.write(content)

        return output_file

    def _format_mbdyn(self) -> str:
        """Format data in MBDyn-compatible C81 format.

        Returns:
            Formatted C81 file content as string.
        """
        header = f"{self.name:30}"  # Name (30 chars)
        header += f"{self.cl.shape[0]:02}{self.cl.shape[1]:02}"  # Mach, AoA for CL
        header += f"{self.cd.shape[0]:02}{self.cd.shape[1]:02}"  # Mach, AoA for CD
        header += f"{self.cm.shape[0]:02}{self.cm.shape[1]:02}"  # Mach, AoA for CM
        header += "\n"

        content = header
        content += self._format_matrix_mbdyn(self.cl, self.mach, self.aoa)
        content += self._format_matrix_mbdyn(self.cd, self.mach, self.aoa)
        content += self._format_matrix_mbdyn(self.cm, self.mach, self.aoa)

        return content

    def _format_dust(self) -> str:
        """Format data in DUST C81 format.

        Supports both single and multiple Reynolds numbers.
        For multiple Re: data shape is [n_re x mach x aoa]
        For single Re: data shape is [mach x aoa]

        Returns:
            Formatted C81 file content as string.
        """
        is_multi_re = isinstance(self.re, np.ndarray)

        # First line: number of Re tables
        if is_multi_re:
            # Type narrowing for mypy
            assert isinstance(self.re, np.ndarray)
            n_re = len(self.re)
            header = f"{n_re} 0 0\n"
        else:
            header = f"{DUST_HEADER_LINE1}\n"

        header += f"{DUST_HEADER_LINE2}\n"
        header += f"{CHORD_REFERENCE}\n"
        header += "COMMENT#1\n"

        content = header

        # Handle multiple Reynolds numbers
        if is_multi_re:
            # Type narrowing for mypy
            assert isinstance(self.re, np.ndarray)
            for i_re, re_val in enumerate(self.re):
                # Reynolds number header for this table
                re_header = f"{re_val}    {DEFAULT_CHORD_LOCATION:.3f}\n"
                re_header += " "
                re_header += (
                    f"{self.cl.shape[1]:02}{self.cl.shape[2]:02}"  # Mach, AoA for CL
                )
                re_header += (
                    f"{self.cd.shape[1]:02}{self.cd.shape[2]:02}"  # Mach, AoA for CD
                )
                re_header += (
                    f"{self.cm.shape[1]:02}{self.cm.shape[2]:02}"  # Mach, AoA for CM
                )
                re_header += "\n"

                content += re_header

                # Data tables for this Reynolds number
                content += self._format_matrix_dust(
                    self.cl[i_re, :, :], self.mach, self.aoa
                )
                content += self._format_matrix_dust(
                    self.cd[i_re, :, :], self.mach, self.aoa
                )
                content += self._format_matrix_dust(
                    self.cm[i_re, :, :], self.mach, self.aoa
                )
        else:
            # Single Reynolds number (original format)
            assert isinstance(self.re, float)
            re_header = f"{self.re}    {DEFAULT_CHORD_LOCATION:.3f}\n"
            re_header += " "
            re_header += (
                f"{self.cl.shape[0]:02}{self.cl.shape[1]:02}"  # Mach, AoA for CL
            )
            re_header += (
                f"{self.cd.shape[0]:02}{self.cd.shape[1]:02}"  # Mach, AoA for CD
            )
            re_header += (
                f"{self.cm.shape[0]:02}{self.cm.shape[1]:02}"  # Mach, AoA for CM
            )
            re_header += "\n"

            content += re_header
            content += self._format_matrix_dust(self.cl, self.mach, self.aoa)
            content += self._format_matrix_dust(self.cd, self.mach, self.aoa)
            content += self._format_matrix_dust(self.cm, self.mach, self.aoa)

        return content

    def _format_matrix_mbdyn(
        self,
        matrix: NDArray[np.float64],
        mach: NDArray[np.float64],
        aoa: NDArray[np.float64],
    ) -> str:
        """Format coefficient matrix in MBDyn format with line wrapping.

        Args:
            matrix: Coefficient matrix [mach x aoa]
            mach: Mach number array
            aoa: Angle of attack array

        Returns:
            Formatted matrix string.
        """
        lines = []

        # Mach header line (with wrapping every 9 values)
        mach_line = " " * 7  # Initial indent
        for j, m in enumerate(mach):
            if j > 0 and j % MBDYN_LINE_LENGTH == 0:
                lines.append(mach_line)
                mach_line = " " * 7  # Indent for continuation
            mach_line += MACH_FORMAT.format(m)
        lines.append(mach_line)

        # Data rows (one per AoA)
        for k, alpha in enumerate(aoa):
            row = AOA_FORMAT.format(alpha)
            for j in range(matrix.shape[0]):
                if j > 0 and j % MBDYN_LINE_LENGTH == 0:
                    lines.append(row)
                    row = " " * 7  # Indent for continuation
                row += COEF_FORMAT.format(matrix[j, k])
            lines.append(row)

        return "\n".join(lines) + "\n"

    def _format_matrix_dust(
        self,
        matrix: NDArray[np.float64],
        mach: NDArray[np.float64],
        aoa: NDArray[np.float64],
    ) -> str:
        """Format coefficient matrix in DUST format (no line wrapping).

        Args:
            matrix: Coefficient matrix [mach x aoa]
            mach: Mach number array
            aoa: Angle of attack array

        Returns:
            Formatted matrix string.
        """
        lines = []

        # Mach header line
        mach_line = " " * 7
        for m in mach:
            mach_line += MACH_FORMAT.format(m)
        lines.append(mach_line)

        # Data rows (one per AoA)
        for k, alpha in enumerate(aoa):
            row = AOA_FORMAT.format(alpha)
            for j in range(matrix.shape[0]):
                row += COEF_FORMAT.format(matrix[j, k])
            lines.append(row)

        return "\n".join(lines) + "\n"

    def plot_c81_table(
        self,
        aoa_limits: tuple[float, float] = (-30, 30),
        pathout: Path | str = "c81plots",
        save_fig: bool = True,
        re_index: Optional[int] = None,
    ) -> Optional[plt.Figure]:
        """Generate visualization plots of aerodynamic coefficients.

        Args:
            aoa_limits: Tuple of (min, max) angle of attack for plot limits.
            pathout: Output directory path for plot images.
            save_fig: If True, save figure to file. If False, return figure object.
            re_index: For multiple Re, specify which index to plot (0-based).
                     If None and multiple Re exist, plots all Re on same figure.

        Returns:
            matplotlib Figure object if save_fig=False, otherwise None.

        Raises:
            OSError: If unable to create output directory or save figure.
            IndexError: If re_index is out of bounds.
        """
        is_multi_re = isinstance(self.re, np.ndarray)

        # Determine title
        if is_multi_re:
            # Type narrowing for mypy
            assert isinstance(self.re, np.ndarray)
            if re_index is not None:
                if re_index < 0 or re_index >= len(self.re):
                    raise IndexError(
                        f"re_index {re_index} out of bounds for {len(self.re)} Reynolds numbers"
                    )
                title = f"C81 Table for {self.name} at Re={int(self.re[re_index])}"
            else:
                title = f"C81 Table for {self.name} (Multiple Re)"
        else:
            assert isinstance(self.re, float)
            title = f"C81 Table for {self.name} at Re={int(self.re)}"

        fig, axes = plt.subplots(1, 3, figsize=(21, 7))
        fig.suptitle(title)

        coef_names = ["cl", "cd", "cm"]
        coef_labels = ["CL", "CD", "CM"]

        for ax, name, label in zip(axes, coef_names, coef_labels):
            ax.set_title(label)
            ax.set_xlabel("AoA [deg]")
            ax.set_xlim(aoa_limits)
            ax.grid(True)

            coef_data = getattr(self, name)

            if is_multi_re:
                # Type narrowing for mypy
                assert isinstance(self.re, np.ndarray)
                if re_index is not None:
                    # Plot only specified Re
                    for j, m in enumerate(self.mach):
                        ax.plot(
                            self.aoa, coef_data[re_index, j, :], label=f"Mach {m:.2f}"
                        )
                else:
                    # Plot all Re (different colors/styles per Re)
                    for i_re, re_val in enumerate(self.re):
                        for j, m in enumerate(self.mach):
                            label_str = f"Re={int(re_val)}, Mach {m:.2f}"
                            ax.plot(
                                self.aoa,
                                coef_data[i_re, j, :],
                                label=label_str,
                                alpha=0.7,
                            )
            else:
                # Single Re
                for j, m in enumerate(self.mach):
                    ax.plot(self.aoa, coef_data[j, :], label=f"Mach {m:.2f}")

        # Add legend to last subplot
        axes[-1].legend(fontsize=8 if is_multi_re and re_index is None else 10)

        if save_fig:
            output_folder = Path(pathout)
            output_folder.mkdir(exist_ok=True, parents=True)

            if is_multi_re:
                # Type narrowing for mypy
                assert isinstance(self.re, np.ndarray)
                if re_index is not None:
                    filename = f"{self.name}_Re_{int(self.re[re_index])}.png"
                else:
                    filename = f"{self.name}_Re_all.png"
            else:
                assert isinstance(self.re, float)
                filename = f"{self.name}_Re_{int(self.re)}.png"

            output_file = output_folder / filename
            plt.savefig(output_file, dpi=150, bbox_inches="tight")
            plt.close(fig)
            return None
        else:
            return fig


def generate_airfoil_data(
    file_name: str,
    pathprofile: Path | str,
    reynolds: float | list[float] | NDArray[np.float64],
    mach_range: tuple[float, float] = (0.0, 0.90),
    n_mach: int = 10,
    aoa_range: tuple[float, float] = (-180.0, 180.0),
    model_size: Literal[
        "small", "medium", "large", "xlarge", "xxlarge", "xxxlarge"
    ] = "xxxlarge",
    mbdynformat: bool = False,
    pathout: Path | str = "c81tables",
) -> Airfoil:
    """Generate airfoil aerodynamic data using NeuralFoil.

    Supports both single and multiple Reynolds numbers. For multiple Reynolds
    numbers, creates a C81 table compatible with DUST's multi-Re format.

    Args:
        file_name: Airfoil name (corresponding to .dat file without extension).
        pathprofile: Directory path containing airfoil coordinate files.
        reynolds: Reynolds number(s) for aerodynamic calculations.
                 Can be a single float, list of floats, or numpy array.
        mach_range: Tuple of (min, max) Mach numbers.
        n_mach: Number of Mach numbers to evaluate.
        aoa_range: Tuple of (min, max) angles of attack (degrees).
        model_size: NeuralFoil model size (larger = more accurate but slower).
        mbdynformat: If True, generate MBDyn-compatible format automatically.
                    If False (default), generate DUST format.
                    Note: MBDyn format only supports single Reynolds number.
        pathout: Output directory path for generated C81 file.

    Returns:
        Airfoil object with computed aerodynamic coefficients and generated C81 file.
        - Single Re: coefficient arrays have shape [n_mach x n_aoa]
        - Multiple Re: coefficient arrays have shape [n_re x n_mach x n_aoa]

    Raises:
        FileNotFoundError: If airfoil coordinate file not found.
        ValueError: If input parameters are invalid or if trying to use
                   multiple Re with MBDyn format.
        ImportError: If required dependencies are not installed.

    Examples:
        >>> # Single Reynolds number with DUST format
        >>> airfoil = generate_airfoil_data(
        ...     "naca0012",
        ...     "airfoils/",
        ...     reynolds=1e6
        ... )

        >>> # Multiple Reynolds numbers with DUST format
        >>> airfoil = generate_airfoil_data(
        ...     "naca0012",
        ...     "airfoils/",
        ...     reynolds=[1e5, 5e5, 1e6],
        ...     n_mach=5
        ... )

        >>> # Single Reynolds number with MBDyn format
        >>> airfoil = generate_airfoil_data(
        ...     "naca0012",
        ...     "airfoils/",
        ...     reynolds=1e6,
        ...     mbdynformat=True
        ... )
    """
    # Convert reynolds to numpy array for uniform handling
    if isinstance(reynolds, (list, np.ndarray)):
        reynolds_array: NDArray[np.float64] = np.asarray(reynolds, dtype=np.float64)
    else:
        # Single Reynolds number - convert to array of length 1
        reynolds_array = np.array([reynolds], dtype=np.float64)

    # Validate Reynolds numbers
    if len(reynolds_array) == 0:
        raise ValueError("Reynolds number array cannot be empty")
    if np.any(reynolds_array <= 0):
        raise ValueError(f"All Reynolds numbers must be positive, got {reynolds_array}")

    # Check MBDyn format compatibility
    if mbdynformat and len(reynolds_array) > 1:
        raise ValueError(
            "MBDyn format does not support multiple Reynolds numbers. "
            f"Got {len(reynolds_array)} Reynolds numbers."
        )

    # Validate Mach range
    if not (0.0 <= mach_range[0] < mach_range[1] <= 1.0):
        raise ValueError(f"Invalid Mach range {mach_range}, must be in [0, 1)")

    # Load airfoil geometry
    airfoil_file = Path(pathprofile) / f"{file_name}.dat"
    if not airfoil_file.exists():
        raise FileNotFoundError(f"Airfoil file not found: {airfoil_file}")

    af = asb.Airfoil(name=file_name, coordinates=airfoil_file).to_kulfan_airfoil()

    # Define angle of attack array (fine near zero, coarse at extremes)
    alphas_nf = np.concatenate(
        (
            np.arange(aoa_range[0], -23, 6),
            np.arange(-22, 23, 1),
            np.arange(24, aoa_range[1] + 1, 6),
        )
    )

    # Define Mach number array
    mach = np.linspace(mach_range[0], mach_range[1], n_mach)

    # Compute aerodynamics for all Reynolds numbers
    # Always use shape [n_re, n_mach, n_aoa] for consistency
    aero_data: dict[str, list[list[NDArray[np.float64]]]] = {
        "cl": [],
        "cd": [],
        "cm": [],
    }

    for re in reynolds_array:
        re_data: dict[str, list[NDArray[np.float64]]] = {
            "cl": [],
            "cd": [],
            "cm": [],
        }
        for m in mach:
            aero = af.get_aero_from_neuralfoil(
                alpha=alphas_nf, Re=re, mach=m, model_size=model_size
            )
            re_data["cl"].append(aero["CL"])
            re_data["cd"].append(aero["CD"])
            re_data["cm"].append(aero["CM"])

        # Append this Re's data
        aero_data["cl"].append(re_data["cl"])
        aero_data["cd"].append(re_data["cd"])
        aero_data["cm"].append(re_data["cm"])

    # Convert to numpy arrays with shape [n_re, n_mach, n_aoa]
    aero_data_np = {k: np.array(v) for k, v in aero_data.items()}

    # For single Re, store as float; for multiple Re, store as array
    re_to_store: float | NDArray[np.float64] = (
        reynolds_array[0] if len(reynolds_array) == 1 else reynolds_array
    )

    # For single Re, squeeze out the first dimension to get [n_mach, n_aoa]
    if len(reynolds_array) == 1:
        cl_data = aero_data_np["cl"][0]
        cd_data = aero_data_np["cd"][0]
        cm_data = aero_data_np["cm"][0]
    else:
        cl_data = aero_data_np["cl"]
        cd_data = aero_data_np["cd"]
        cm_data = aero_data_np["cm"]

    airfoil = Airfoil(
        name=file_name,
        aoa=alphas_nf,
        mach=mach,
        re=re_to_store,
        cl=cl_data,
        cd=cd_data,
        cm=cm_data,
    )

    # Generate C81 file
    airfoil.generate_c81_file(mbdynformat=mbdynformat, pathout=pathout)

    return airfoil
