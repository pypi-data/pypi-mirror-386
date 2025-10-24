"""Visualization utilities for flow field post-processing.

This module provides tools for 3D visualization of computational fluid dynamics
results using PyVista and Matplotlib. It includes colormap management and
various flow field visualization methods including vorticity, Q-criterion,
and Lambda2-criterion.

Classes
-------
ColorMapManager
    Manages color maps for PyVista and Matplotlib visualizations.
FlowPostProcessor
    Provides methods for visualizing flow field quantities and derived criteria.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from matplotlib.colors import LinearSegmentedColormap, ListedColormap


# ==============================================================================
# Constants
# ==============================================================================

# Default glyph scaling factor for visualization
DEFAULT_GLYPH_SCALE_FACTOR = 850.0

# Default text label position (x, y) in pixel coordinates
DEFAULT_TEXT_POSITION = (910, 120)

# Default colorbar properties
DEFAULT_COLORBAR_WIDTH = 0.03
DEFAULT_COLORBAR_POSITION_X = 0.90
DEFAULT_COLORBAR_N_LABELS = 5
DEFAULT_COLORBAR_TITLE_FONT_SIZE = 20
DEFAULT_COLORBAR_LABEL_FONT_SIZE = 14


# ==============================================================================
# ColorMapManager
# ==============================================================================


class ColorMapManager:
    """Manages color maps for PyVista and Matplotlib visualizations.

    This class handles loading, storing, and converting colormaps between
    PyVista lookup tables and Matplotlib colormap formats.

    Attributes
    ----------
    colormaps : dict[str, dict]
        Dictionary mapping colormap names to their definitions.
    """

    def __init__(self, json_path: Path | str | None = None) -> None:
        """
        Initialize colormap manager

        Parameters
        ----------
        json_path : Path | str | None, optional
            Path to JSON file with colormap definitions. If None, loads defaults.
        """
        self.colormaps: dict[str, dict] = {}

        if json_path is None:
            self._load_defaults()
        else:
            self.load_from_json(json_path)

    def _load_defaults(self):
        """Load default colormaps."""
        defaults = [
            {
                "Name": "Viridis",
                "ColorSpace": "Lab",
                "NanColor": [0.5, 0.0, 0.0],
                "RGBPoints": [
                    -1.0,
                    0.267004,
                    0.004874,
                    0.329415,
                    0.0,
                    0.282623,
                    0.140926,
                    0.457517,
                    1.0,
                    0.253935,
                    0.265254,
                    0.529983,
                ],
            },
            {
                "Name": "Coolwarm",
                "ColorSpace": "Diverging",
                "NanColor": [1.0, 1.0, 0.0],
                "RGBPoints": [
                    -1.0,
                    0.231373,
                    0.298039,
                    0.752941,
                    0.0,
                    0.865003,
                    0.865003,
                    0.865003,
                    1.0,
                    0.705882,
                    0.0156863,
                    0.14902,
                ],
            },
        ]
        self.add_colormaps(defaults)

    def load_from_json(self, json_path: Path | str) -> None:
        """
        Load colormaps from JSON file

        Parameters
        ----------
        json_path : Path | str
            Path to JSON file with colormap definitions
        """
        json_path = Path(json_path)
        try:
            with open(json_path) as f:
                colormaps = json.load(f)
            self.add_colormaps(colormaps)
        except Exception as e:
            print(f"Error loading colormaps from {json_path}: {e}")
            raise e

    def add_colormap(self, colormap: dict) -> None:
        """Add a single colormap definition

        Parameters
        ----------
        colormap : dict
            Colormap definition with 'Name' and 'RGBPoints' keys
        """
        required_keys = ["Name", "RGBPoints"]
        if not all(k in colormap for k in required_keys):
            raise ValueError("Colormap missing required keys")

        self.colormaps[colormap["Name"]] = colormap

    def add_colormaps(self, colormaps: list[dict]) -> None:
        """Add multiple colormap definitions

        Parameters
        ----------
        colormaps : list[dict]
            List of colormap definitions
        """
        for cmap in colormaps:
            self.add_colormap(cmap)

    def get_colormap(self, name: str) -> dict:
        """Get colormap definition by name

        Parameters
        ----------
        name : str
            Name of the colormap

        Returns
        -------
        dict
            Colormap definition dictionary
        """
        if name not in self.colormaps:
            raise KeyError(
                f"Colormap '{name}' not found. Available maps: {list(self.colormaps.keys())}"
            )
        return self.colormaps[name]

    def get_pv_lookup_table(
        self,
        name: str,
        clim: tuple[float, float],
        nan_color: list[float] | None = None,
        n_points: int = 256,
    ) -> pv.LookupTable:
        """
        Convert colormap definition to PyVista LookupTable

        Args:
            name (str): Name of registered colormap
            nan_color (list): Override NaN color [R, G, B] (0-1)
            n_points (int): Number of interpolation points
        """
        cmap = self.get_colormap(name)

        # Extract RGB points and NaN color
        rgb_points = cmap["RGBPoints"]
        nan_color = nan_color or cmap.get("NanColor", [1, 1, 0])  # Default yellow

        # Parse RGB points
        positions, red, green, blue = [], [], [], []
        for i in range(0, len(rgb_points), 4):
            positions.append(rgb_points[i])
            red.append(rgb_points[i + 1])
            green.append(rgb_points[i + 2])
            blue.append(rgb_points[i + 3])

        # Create interpolated colormap
        x_new = np.linspace(0, 1, n_points)
        r_interp = np.interp(x_new, positions, red)
        g_interp = np.interp(x_new, positions, green)
        b_interp = np.interp(x_new, positions, blue)

        # Convert to 0-255 integers with alpha
        rgba = (np.c_[r_interp, g_interp, b_interp, np.ones(n_points)] * 255).astype(
            np.uint8
        )

        # Convert NaN color to 0-255
        nan_rgba = [int(c * 255) for c in nan_color] + [255]

        # Create lookup table
        lut = pv.LookupTable()
        lut.values = rgba
        lut.nan_color = nan_rgba
        lut.scalar_range = clim or [0, 1]

        return lut

    def get_mpl_colormap(
        self,
        name: str,
        as_linear: bool = False,
        nan_color: list[float] | None = None,
    ) -> tuple[ListedColormap | LinearSegmentedColormap, list[float]]:
        """
        Get Matplotlib colormap (ListedColormap or LinearSegmentedColormap).

        Parameters
        ----------
        name : str
            Colormap name
        as_linear : bool, optional
            Return LinearSegmentedColormap instead of ListedColormap
        nan_color : list[float] | None, optional
            Override NaN color [R, G, B] in 0-1 range

        Returns
        -------
        tuple[ListedColormap | LinearSegmentedColormap, list[float]]
            Matplotlib colormap and NaN color
        """
        cmap_def = self.get_colormap(name)
        rgb_points = cmap_def["RGBPoints"]
        nan_color = nan_color or cmap_def.get("NanColor", [1, 1, 0])

        # Parse RGB points
        positions, red, green, blue = [], [], [], []
        for i in range(0, len(rgb_points), 4):
            positions.append(rgb_points[i])
            red.append(rgb_points[i + 1])
            green.append(rgb_points[i + 2])
            blue.append(rgb_points[i + 3])

        if as_linear:
            # Create LinearSegmentedColormap (supports non-uniform positions)
            cdict: dict[str, Sequence[tuple[float, ...]]] = {
                "red": [
                    (float(pos), float(r), float(r)) for pos, r in zip(positions, red)
                ],
                "green": [
                    (float(pos), float(g), float(g)) for pos, g in zip(positions, green)
                ],
                "blue": [
                    (float(pos), float(b), float(b)) for pos, b in zip(positions, blue)
                ],
            }
            # Type ignore: cdict keys are correct but mypy wants Literal types
            result_cmap: ListedColormap | LinearSegmentedColormap = (
                LinearSegmentedColormap(
                    name,
                    cdict,  # type: ignore[arg-type]
                )
            )
        else:
            # Interpolate to 256 points for ListedColormap
            x_new = np.linspace(0, 1, 256)
            r = np.interp(x_new, positions, red)
            g = np.interp(x_new, positions, green)
            b = np.interp(x_new, positions, blue)
            rgba = np.vstack([r, g, b, np.ones(256)]).T
            result_cmap = ListedColormap(rgba, name=name)

        return result_cmap, nan_color

    def register_mpl_colormap(self, name, **kwargs):
        """Universal colormap registration for Matplotlib"""
        mpl_cmap, nan_color = self.get_mpl_colormap(name, **kwargs)

        # Register (legacy) colormap
        if hasattr(mpl, "colormaps"):
            mpl.colormaps.register(name=name, cmap=mpl_cmap)
            mpl.colormaps.get_cmap(name).set_bad(color=nan_color)
        else:
            plt.register_cmap(name=name, cmap=mpl_cmap)
            plt.get_cmap(name).set_bad(color=nan_color)

        # Retrieve the registered colormap
        return plt.get_cmap(name)


class FlowPostProcessor:
    """Visualizes flow field quantities and derived criteria.

    This class provides methods for visualizing vorticity, sectional loads,
    Q-criterion, and Lambda2-criterion using PyVista for 3D rendering.

    Attributes
    ----------
    colormap_manager : ColorMapManager | None
        Optional colormap manager for custom color handling
    glyph_geom : pv.Arrow
        Arrow geometry for glyph visualizations
    """

    def __init__(self, colormap_manager: ColorMapManager | None = None) -> None:
        """
        Initialize post-processor with optional colormap manager

        Parameters
        ----------
        colormap_manager : ColorMapManager | None, optional
            Optional colormap manager for custom colormap handling
        """
        self.colormap_manager = colormap_manager
        self.glyph_geom = pv.Arrow()

    def _visualize_vector_field_glyphs(
        self,
        mesh: pv.DataSet,
        field_name: str,
        label_text: str,
        plotter: pv.Plotter | None = None,
        scale_factor: float = DEFAULT_GLYPH_SCALE_FACTOR,
        clim_range: tuple[float, float] | None = None,
        cmap_name: str = "",
    ) -> pv.Plotter:
        """
        Generic method to visualize vector fields using arrow glyphs.

        Parameters
        ----------
        mesh : pv.DataSet
            Input dataset with vector field
        field_name : str
            Name of the vector field to visualize
        label_text : str
            Text label for the scalar bar (e.g., "Vorticity [1/s]")
        plotter : pv.Plotter | None, optional
            Existing plotter or create new
        scale_factor : float, optional
            Scaling factor for glyph size
        clim_range : tuple[float, float] | None, optional
            (min, max) for color mapping. Defaults to (0, 1e-4)
        cmap_name : str, optional
            Name of registered colormap

        Returns
        -------
        pv.Plotter
            Configured plotter
        """
        if clim_range is None:
            clim_range = (0, 1e-4)

        # Create plotter if none provided
        if plotter is None:
            plotter = pv.Plotter(notebook=True)

        # Validate input fields
        if field_name not in mesh.array_names:
            available_fields = ", ".join(mesh.array_names)
            raise ValueError(
                f"Dataset missing '{field_name}' field. "
                f"Available fields: {available_fields}"
            )

        # Create glyphs
        glyphs = mesh.glyph(
            orient=field_name,
            scale=field_name,
            factor=scale_factor,
            geom=self.glyph_geom,
        )

        # Get colormap
        cmap: pv.LookupTable | str
        if self.colormap_manager:
            cmap = self.colormap_manager.get_pv_lookup_table(cmap_name, clim=clim_range)
        else:
            cmap = cmap_name

        # Add mesh to plotter
        plotter.add_mesh(
            glyphs,
            show_scalar_bar=False,
            cmap=cmap,  # type: ignore[arg-type]
            clim=clim_range,
            render_points_as_spheres=True,
            point_size=4,
        )

        # Add scalar bar and title
        self._add_scalar_bar_with_label(plotter, label_text, clim_range)

        return plotter

    def visualize_vorticity_glyphs(
        self,
        mesh: pv.DataSet,
        plotter: pv.Plotter | None = None,
        scale_factor: float = DEFAULT_GLYPH_SCALE_FACTOR,
        clim_range: tuple[float, float] | None = None,
        cmap_name: str = "",
    ) -> pv.Plotter:
        """
        Visualize vorticity using arrow glyphs

        Parameters
        ----------
        mesh : pv.DataSet
            Input dataset with vorticity field
        plotter : pv.Plotter | None, optional
            Existing plotter or create new
        scale_factor : float, optional
            Scaling factor for glyph size
        clim_range : tuple[float, float] | None, optional
            (min, max) for color mapping. Defaults to (0, 1e-4)
        cmap_name : str, optional
            Name of registered colormap

        Returns
        -------
        pv.Plotter
            Configured plotter
        """
        return self._visualize_vector_field_glyphs(
            mesh=mesh,
            field_name="Vorticity",
            label_text=r"Vorticity [1/s]",
            plotter=plotter,
            scale_factor=scale_factor,
            clim_range=clim_range,
            cmap_name=cmap_name,
        )

    def visualize_sectional_glyphs(
        self,
        mesh: pv.DataSet,
        plotter: pv.Plotter | None = None,
        scale_factor: float = DEFAULT_GLYPH_SCALE_FACTOR,
        clim_range: tuple[float, float] | None = None,
        cmap_name: str = "",
    ) -> pv.Plotter:
        """
        Visualize sectional forces using arrow glyphs

        Parameters
        ----------
        mesh : pv.DataSet
            Input dataset with sectional field
        plotter : pv.Plotter | None, optional
            Existing plotter or create new
        scale_factor : float, optional
            Scaling factor for glyph size
        clim_range : tuple[float, float] | None, optional
            (min, max) for color mapping. Defaults to (0, 1e-4)
        cmap_name : str, optional
            Name of registered colormap

        Returns
        -------
        pv.Plotter
            Configured plotter
        """
        return self._visualize_vector_field_glyphs(
            mesh=mesh,
            field_name="Sectional",
            label_text=r"Sectional Loads [N/m]",
            plotter=plotter,
            scale_factor=scale_factor,
            clim_range=clim_range,
            cmap_name=cmap_name,
        )

    def _add_scalar_bar_with_label(
        self, plotter: pv.Plotter, label_text: str, clim_range: tuple[float, float]
    ) -> None:
        """
        Add scalar bar with vertical text label.

        Parameters
        ----------
        plotter : pv.Plotter
            The plotter to add the scalar bar to
        label_text : str
            Text label to display (e.g., "Vorticity [1/s]")
        clim_range : tuple[float, float]
            Color limits for the scalar bar
        """
        plotter.add_scalar_bar(  # type: ignore[call-arg]
            title="",  # Empty string instead of None for PyVista compatibility
            n_labels=DEFAULT_COLORBAR_N_LABELS,
            width=DEFAULT_COLORBAR_WIDTH,
            position_x=DEFAULT_COLORBAR_POSITION_X,
            fmt="%.1f",
            title_font_size=DEFAULT_COLORBAR_TITLE_FONT_SIZE,
            label_font_size=DEFAULT_COLORBAR_LABEL_FONT_SIZE,
            font_family="Times",
            vertical=True,
        )

        plotter.add_text(
            text=label_text,
            orientation=90,
            font_size=10,
            position=DEFAULT_TEXT_POSITION,
            font="times",
            shadow=False,
        )

    def visualize_q_criterion(
        self,
        flowfield: pv.DataSet,
        plotter: pv.Plotter | None = None,
        q_threshold: float = 1.0,
        velocity_range: tuple[float, float] | None = None,
        cmap_name: str = "",
    ) -> pv.Plotter:
        """
        Compute and visualize Q-criterion with velocity magnitude coloring

        Parameters
        ----------
        flowfield : pv.DataSet
            Input flow field data
        plotter : pv.Plotter | None, optional
            Existing plotter or create new
        q_threshold : float, optional
            Threshold for Q-criterion isosurface
        velocity_range : tuple[float, float] | None, optional
            (min, max) for color mapping. Defaults to (0, 1)
        cmap_name : str, optional
            Name of registered colormap

        Returns
        -------
        pv.Plotter
            Configured plotter
        """
        if velocity_range is None:
            velocity_range = (0, 1)

        # Input validation
        if velocity_range[0] < 0:
            raise ValueError("velocity_range minimum must be non-negative")
        if velocity_range[1] <= velocity_range[0]:
            raise ValueError("velocity_range maximum must be greater than minimum")

        # Create plotter if none provided
        if plotter is None:
            plotter = pv.Plotter(notebook=True)

        # Convert grid type if needed
        if isinstance(flowfield, pv.RectilinearGrid):
            flowfield = flowfield.cast_to_structured_grid()

        try:
            # Compute derivatives and Q-criterion
            flowfield = flowfield.compute_derivative(
                scalars="velocity", gradient=True, qcriterion=True
            )
        except KeyError as e:
            raise ValueError("Dataset missing required 'velocity' field") from e

        # Extract Q-criterion isosurface
        q_contour = flowfield.contour(scalars="qcriterion", isosurfaces=[q_threshold])

        # Compute velocity magnitude on the isosurface
        if "velocity" in q_contour.array_names:
            q_contour["velocity_magnitude"] = np.linalg.norm(
                q_contour["velocity"], axis=1
            )

        # Get colormap from manager or use default
        cmap: pv.LookupTable | str
        if self.colormap_manager:
            cmap = self.colormap_manager.get_pv_lookup_table(cmap_name, velocity_range)
        else:
            cmap = cmap_name

        # Add visualization elements
        self._add_q_visualization(
            plotter, q_contour, cmap=cmap, velocity_range=velocity_range
        )

        return plotter

    def _add_q_visualization(self, plotter, q_contour, cmap, velocity_range):
        """Add visualization elements to plotter"""
        # Add main mesh
        plotter.add_mesh(
            q_contour,
            scalars="velocity_magnitude",
            cmap=cmap,
            opacity=1.0,
            clim=velocity_range,
            show_scalar_bar=False,
        )

        # Add scalar bar
        self._add_custom_scalar_bar(plotter, velocity_range)

    def _add_custom_scalar_bar(
        self, plotter: pv.Plotter, velocity_range: tuple[float, float]
    ) -> None:
        """Add custom scalar bar with vertical title workaround (alias for velocity fields)"""
        self._add_scalar_bar_with_label(plotter, r"Velocity [m/s]", velocity_range)

    def compute_lambda2_criterion(self, flowfield: pv.DataSet) -> pv.DataSet:
        """
        Compute Lambda2-criterion for vortex identification.

        Parameters
        ----------
        flowfield : pv.DataSet
            Flow field data containing gradient field

        Returns
        -------
        pv.DataSet
            Flow field with added lambda2 scalar field
        """
        gradients = flowfield["gradient"]

        # Reshape into 3x3 matrix (n_points, 3, 3)
        gradient_tensors = gradients.reshape(-1, 3, 3)

        # Compute symmetric (strain rate) and antisymmetric (rotation rate) tensors
        s = 0.5 * (
            gradient_tensors + np.transpose(gradient_tensors, (0, 2, 1))
        )  # Strain rate
        omega = 0.5 * (
            gradient_tensors - np.transpose(gradient_tensors, (0, 2, 1))
        )  # Rotation rate

        # Compute M = S² + Ω²
        s_squared = np.einsum("...ij,...jk->...ik", s, s)
        omega_squared = np.einsum("...ij,...jk->...ik", omega, omega)
        m = s_squared + omega_squared

        # Compute eigenvalues of M (vectorized)
        eigvals = np.linalg.eigh(m)[0]

        # Add λ2 as a scalar field to dataset
        flowfield["lambda2"] = eigvals[:, 1]  # Second eigenvalue (λ2)

        return flowfield

    def visualize_lambda2_criterion(
        self,
        flowfield: pv.DataSet,
        plotter: pv.Plotter | None = None,
        lambda2_threshold: float = -0.5,
        velocity_range: tuple[float, float] | None = None,
        cmap_name: str = "",
    ) -> pv.Plotter:
        """
        Compute and visualize Lambda2-criterion with velocity magnitude coloring

        Parameters
        ----------
        flowfield : pv.DataSet
            Input flow field data
        plotter : pv.Plotter | None, optional
            Existing plotter or create new
        lambda2_threshold : float, optional
            Threshold for Lambda2-criterion isosurface
        velocity_range : tuple[float, float] | None, optional
            (min, max) for color mapping. Defaults to (0, 1)
        cmap_name : str, optional
            Name of registered colormap

        Returns
        -------
        pv.Plotter
            Configured plotter
        """
        if velocity_range is None:
            velocity_range = (0, 1)

        # Input validation
        if velocity_range[0] < 0:
            raise ValueError("velocity_range minimum must be non-negative")
        if velocity_range[1] <= velocity_range[0]:
            raise ValueError("velocity_range maximum must be greater than minimum")

        # Create plotter if none provided
        if plotter is None:
            plotter = pv.Plotter(notebook=True)

        # Convert grid type if needed
        if isinstance(flowfield, pv.RectilinearGrid):
            flowfield = flowfield.cast_to_structured_grid()

        try:
            flowfield = flowfield.compute_derivative(
                scalars="velocity",  # Process each velocity component as a scalar
                gradient=True,
            )

        except KeyError as e:
            raise ValueError("Dataset missing required 'velocity' field") from e

        flowfield = self.compute_lambda2_criterion(flowfield)

        lambda2_contour = flowfield.contour(
            scalars="lambda2", isosurfaces=[lambda2_threshold]
        )

        # Compute velocity magnitude on the isosurface
        if "velocity" in lambda2_contour.array_names:
            lambda2_contour["velocity_magnitude"] = np.linalg.norm(
                lambda2_contour["velocity"], axis=1
            )

        # Get colormap from manager or use default
        cmap: pv.LookupTable | str
        if self.colormap_manager:
            cmap = self.colormap_manager.get_pv_lookup_table(cmap_name, velocity_range)
        else:
            cmap = cmap_name

        # Add visualization elements
        self._add_q_visualization(
            plotter, lambda2_contour, cmap=cmap, velocity_range=velocity_range
        )

        return plotter


def plot_dustpre_pv(
    rr: np.ndarray,
    ee: np.ndarray,
    view_angle: float = 30.0,
    show_wireframe: bool = True,
    title: str = "",
    background: str = "#1e1e1e",
    show_axes: bool = True,
    rendering_backend: str = "trame",
) -> pv.Plotter:
    """
    3D interactive visualization of DUST pre-processor mesh using PyVista.

    This function creates an interactive 3D visualization of mesh geometry
    produced by the DUST pre-processor (dust_pre). It renders quadrilateral
    elements with optional wireframe edges.

    Parameters
    ----------
    rr : np.ndarray
        Vertex coordinates array with shape (n_vertices, 3).
        Each row contains [x, y, z] coordinates of a vertex.
    ee : np.ndarray
        Element connectivity array with shape (n_elements, 4+).
        Each row contains vertex indices (1-based) for a quadrilateral element.
        First 4 columns define the quad connectivity.
    view_angle : float, optional
        Camera field of view angle in degrees, by default 30.0.
        Smaller values create a more "zoomed in" perspective.
    show_wireframe : bool, optional
        Whether to display wireframe edges on the mesh, by default True.
    title : str, optional
        Plot title text displayed at the lower edge, by default "".
    background : str, optional
        Background color as hex string or color name, by default "#1e1e1e" (dark gray).
    show_axes : bool, optional
        Whether to display coordinate system axes, by default True.
    rendering_backend : str, optional
        PyVista Jupyter backend: 'trame' for interactive or 'static' for static images,
        by default 'trame'.

    Returns
    -------
    pv.Plotter
        PyVista plotter object. Call .show() to display if not in Jupyter.

    Examples
    --------
    >>> import h5py
    >>> import numpy as np
    >>> # Load mesh from DUST pre-processor HDF5 output
    >>> with h5py.File('geo_input.h5', 'r') as f:
    ...     rr = f['Components/Comp001/Geometry/rr'][:]
    ...     ee = f['Components/Comp001/Geometry/ee'][:]
    >>> # Visualize the mesh
    >>> plotter = plot_dustpre_pv(rr, ee, title="Blade Mesh")

    Notes
    -----
    - The function converts 1-based indices (DUST convention) to 0-based (PyVista)
    - Designed for quadrilateral elements (4-node quads)
    - Works in Jupyter notebooks with interactive backends
    - For static plots, use rendering_backend='static'
    """
    pv.set_jupyter_backend(rendering_backend)

    # Create PyVista mesh from vertex coordinates and element connectivity
    # Convert 1-based indices (DUST) to 0-based indices (PyVista)
    faces = np.hstack([[4, *quad] for quad in (ee[:, :4] - 1)])
    mesh = pv.PolyData(rr, faces)

    plotter = pv.Plotter(notebook=True)

    # Set background color
    plotter.set_background(background)
    plotter.background_color = background

    # Add the mesh with styling
    plotter.add_mesh(
        mesh,
        color="#3b87bd",
        show_edges=show_wireframe,
        edge_color="#464646" if show_wireframe else None,
    )

    # Set isometric view and camera angle
    plotter.view_isometric()
    plotter.camera.view_angle = view_angle

    # Add axes if requested
    if show_axes:
        plotter.show_axes()
        plotter.add_axes()

    # Add title text overlay
    if title:
        plotter.add_text(
            title,
            font="times",
            font_size=DEFAULT_COLORBAR_LABEL_FONT_SIZE,
            position="lower_edge",
            shadow=False,
        )

    # Show with specified backend
    plotter.show(jupyter_backend=rendering_backend)

    return plotter
