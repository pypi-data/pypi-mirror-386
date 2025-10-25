"""
DUST input file generator using dataclasses.

This module provides a structured way to generate DUST input files using
Python dataclasses for better type safety and organization.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TimingConfig:
    """Time integration and output parameters."""

    tstart: float = 0.0  # Starting time
    tend: float = 0.0  # Ending time
    dt: float = 0.0  # Time step
    timesteps: Optional[int] = None  # Number of timesteps
    dt_out: Optional[float] = None  # Output time interval (defaults to dt)
    dt_debug_out: Optional[float] = None  # Debug output time interval (defaults to dt)
    ndt_update_wake: int = 1  # Number of dt between two wake updates

    def __post_init__(self) -> None:
        """Set default values for output intervals."""
        if self.dt_out is None:
            self.dt_out = self.dt
        if self.dt_debug_out is None:
            self.dt_debug_out = self.dt

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for timing parameters."""
        print("! ----- Time and timestep options -----", file=file)
        print(f"tstart = {self.tstart}  ! Starting time", file=file)
        print(f"tend = {self.tend}  ! Ending time", file=file)
        print(f"dt = {self.dt}  ! Time step", file=file)
        print(f"timesteps = {self.timesteps}  ! Number of timesteps", file=file)
        print(f"dt_out = {self.dt_out}  ! Output time interval", file=file)
        print(
            f"dt_debug_out = {self.dt_debug_out}  ! Debug output time interval",
            file=file,
        )
        print(
            f"ndt_update_wake = {self.ndt_update_wake}  ! Number of dt between two wake updates",
            file=file,
        )
        print("", file=file)


@dataclass
class IntegrationConfig:
    """Integration method and reformulation parameters."""

    integrator: str = "euler"  # Integrator solver: Euler or low storage
    reformulated: str = "T"  # Employ rVPM by Alvarez
    f: float = 0.0  # rVPM coefficient f
    g: float = 0.2  # rVPM coefficient g
    suppress_initial_wake: str = "F"  # Suppress the initial wake
    suppress_initial_wake_nsteps: int = 100  # Suppress initial wake after n timesteps

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for integration parameters."""
        print("! ----- Reformulated formulation options -----", file=file)
        print(
            f"reformulated = {self.reformulated}  ! Employ rVPM by Alvarez", file=file
        )
        print(f"f = {self.f}  ! rVPM coefficient f", file=file)
        print(f"g = {self.g}  ! rVPM coefficient g", file=file)
        print("", file=file)
        print("! ----- Treatment of the initial wake -----", file=file)
        print(
            f"suppress_initial_wake = {self.suppress_initial_wake}  ! Suppress the initial wake",
            file=file,
        )
        print(
            f"suppress_initial_wake_nsteps = {self.suppress_initial_wake_nsteps}  ! Suppress initial wake after n timesteps",
            file=file,
        )
        print("", file=file)
        print("! ----- Integration options -----", file=file)
        print(
            f"integrator = {self.integrator}  ! Integrator solver: Euler or low-storage RK",
            file=file,
        )
        print("", file=file)


@dataclass
class IOConfig:
    """Input/output file configuration."""

    geometry_file: str = "geo_input.h5"  # Main geometry definition file
    reference_file: str = "References.in"  # Reference frames file
    basename: str = "./"  # Output basename
    basename_debug: Optional[str] = (
        None  # Output basename for debug (defaults to basename)
    )
    output_start: str = "F"  # Output values at starting iteration
    output_detailed_geo: str = "F"  # Output detailed geometry at each timestep
    debug_level: int = 1  # Level of debug verbosity/output

    def __post_init__(self) -> None:
        """Set default values for debug basename."""
        if self.basename_debug is None:
            self.basename_debug = self.basename

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for I/O parameters."""
        print("! ----- Input options -----", file=file)
        print(
            f"geometry_file = {self.geometry_file}  ! Main geometry definition file",
            file=file,
        )
        print(
            f"reference_file = {self.reference_file}  ! Reference frames file",
            file=file,
        )
        print("", file=file)
        print("! ----- Output options -----", file=file)
        print(f"basename = {self.basename}  ! Output basename", file=file)
        print(
            f"basename_debug = {self.basename_debug}  ! Output basename for debug",
            file=file,
        )
        print(
            f"output_start = {self.output_start}  ! Output values at starting iteration",
            file=file,
        )
        print(
            f"output_detailed_geo = {self.output_detailed_geo}  ! Output detailed geometry in results file",
            file=file,
        )
        print(
            f"debug_level = {self.debug_level}  ! Level of debug verbosity/output",
            file=file,
        )
        print("", file=file)


@dataclass
class RestartConfig:
    """Restart configuration parameters."""

    restart_from_file: str = "F"  # Restarting from file?
    restart_file: Optional[str] = None  # Restart file name
    reset_time: str = "F"  # Reset the time from previous execution?

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for restart parameters."""
        print("! ----- Restart options -----", file=file)
        print(
            f"restart_from_file = {self.restart_from_file}  ! Restarting from file?",
            file=file,
        )
        print(f"restart_file = {self.restart_file}  ! Restart file name", file=file)
        print(
            f"reset_time = {self.reset_time}  ! Reset the time from previous execution?",
            file=file,
        )
        print("", file=file)


@dataclass
class ReferenceConditions:
    """Reference atmospheric and flow conditions."""

    altitude: float = 0.0  # Altitude in meters
    units: str = "SI"  # Units of the input data
    u_inf: list[float] = field(
        default_factory=lambda: [1.0, 0.0, 0.0]
    )  # Free stream velocity
    u_ref: float = 1.0  # Reference velocity
    P_inf: float = 101325.0  # Free stream pressure (Pa)
    rho_inf: float = 1.225  # Free stream density (kg/m³)
    a_inf: float = 340.0  # Speed of sound (m/s)
    mu_inf: float = 0.000018  # Dynamic viscosity (Pa·s)

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for reference conditions."""
        print("! ----- Reference conditions parameters -----", file=file)
        print(f"altitude = {self.altitude}  ! Altitude in meters", file=file)
        print(f"units = {self.units}  ! Units of the input data", file=file)
        print(
            f"u_inf = (/{self.u_inf[0]} , {self.u_inf[1]} , {self.u_inf[2]}/)",
            file=file,
        )
        print(f"u_ref = {self.u_ref}  ! Reference velocity", file=file)
        print(f"P_inf = {self.P_inf}  ! Free stream pressure", file=file)
        print(f"rho_inf = {self.rho_inf}  ! Free stream density", file=file)
        print(f"a_inf = {self.a_inf}  ! Speed of sound", file=file)
        print(f"mu_inf = {self.mu_inf}  ! Dynamic viscosity", file=file)
        print("", file=file)


@dataclass
class GPUConfig:
    """GPU acceleration options."""

    gpu: str = "F"  # Employ GPU

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for GPU options."""
        print("! ----- GPU options -----", file=file)
        print(f"gpu = {self.gpu}  ! Employ GPU", file=file)
        print("", file=file)


@dataclass
class WakeConfig:
    """Wake model parameters."""

    n_wake_panels: int = 1  # Number of wake panels
    n_wake_particles: int = 10000  # Number of wake particles
    particles_box_min: list[float] = field(
        default_factory=lambda: [-10.0, -10.0, -10.0]
    )  # Min coordinates of the particles bounding box
    particles_box_max: list[float] = field(
        default_factory=lambda: [10.0, 10.0, 10.0]
    )  # Max coordinates of the particles bounding box
    mag_threshold: float = 1.0e-9  # Minimum particle magnitude allowed

    # Implicit panel settings
    implicit_panel_scale: float = 0.3  # Scaling of the first implicit wake panel
    implicit_panel_min_vel: float = 1.0e-8  # Minimum velocity at the trailing edge

    # Rigid wake options
    join_te: str = "F"  # Join trailing edge
    join_te_factor: float = 1.0  # Join trailing edges factor

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for wake parameters."""
        print("! ----- Wake options -----", file=file)
        print(
            f"n_wake_panels = {self.n_wake_panels}  ! Number of wake panels", file=file
        )
        print(
            f"n_wake_particles = {self.n_wake_particles}  ! Number of wake particles",
            file=file,
        )
        print(
            f"particles_box_min = (/{self.particles_box_min[0]} , {self.particles_box_min[1]} , {self.particles_box_min[2]}/) ! Min coordinates of the particles bounding box",
            file=file,
        )
        print(
            f"particles_box_max = (/{self.particles_box_max[0]} , {self.particles_box_max[1]} , {self.particles_box_max[2]}/)  ! Max coordinates of the particles bounding box",
            file=file,
        )
        print(
            f"mag_threshold = {self.mag_threshold}  ! Minimum particle magnitude allowed",
            file=file,
        )
        print(
            f"implicit_panel_scale = {self.implicit_panel_scale}  ! Scaling of the first implicit wake panel",
            file=file,
        )
        print(
            f"implicit_panel_min_vel = {self.implicit_panel_min_vel}  ! Minimum velocity at the trailing edge",
            file=file,
        )
        print(f"join_te = {self.join_te}  ! Join trailing edge", file=file)
        print(
            f"join_te_factor = {self.join_te_factor}  ! Factor for joining trailing edges",
            file=file,
        )
        print("", file=file)


@dataclass
class RegularizationConfig:
    """Regularization and vortex core parameters."""

    particles_file: Optional[str] = None  # File with particles initial condition
    far_field_ratio_doublet: float = (
        10.0  # Multiplier for far field threshold (doublet)
    )
    far_field_ratio_source: float = 10.0  # Multiplier for far field threshold (source)
    doublet_threshold: float = 1.0e-6  # Threshold for point in plane in doublets
    rankine_rad: float = 0.1  # Radius of Rankine correction
    octree_vortex_rad: float = 0.1  # Vortex particle core size for octree
    vortex_rad: float = 0.1  # Radius of vortex core for particles
    k_vortex_rad: float = 1.0  # Radius coefficient of vortex core
    k_volume: float = 1.0  # Radius coefficient of volume
    cutoff_rad: float = 0.001  # Radius of complete cutoff

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for regularization parameters."""
        print("! ----- Regularization -----", file=file)
        print(
            f"particles_file = {self.particles_file}  ! File with particles initial condition",
            file=file,
        )
        print(
            f"far_field_ratio_doublet = {self.far_field_ratio_doublet}  ! Multiplier for far field threshold computation on doublet",
            file=file,
        )
        print(
            f"far_field_ratio_source = {self.far_field_ratio_source}  ! Multiplier for far field threshold computation on sources",
            file=file,
        )
        print(
            f"doublet_threshold = {self.doublet_threshold}  ! Threshold for considering the point in plane in doublets",
            file=file,
        )
        print(
            f"rankine_rad = {self.rankine_rad}  ! Radius of Rankine correction for vortex induction near core",
            file=file,
        )
        print(
            f"octree_vortex_rad = {self.octree_vortex_rad}  ! Vortex particle core size for octree initialization",
            file=file,
        )
        print(
            f"vortex_rad = {self.vortex_rad}  ! Radius of vortex core for particles",
            file=file,
        )
        print(
            f"k_vortex_rad = {self.k_vortex_rad}  ! Radius coefficient of vortex core for particles (default is ON)",
            file=file,
        )
        print(
            f"k_volume = {self.k_volume}  ! Radius coefficient of volume for particles",
            file=file,
        )
        print(
            f"cutoff_rad = {self.cutoff_rad}  ! Radius of complete cutoff for vortex induction near core",
            file=file,
        )
        print("", file=file)


@dataclass
class LiftingLineConfig:
    """Lifting line element parameters."""

    ll_maxiter: int = 100  # Maximum number of iterations in LL algorithm
    ll_tol: float = 1.0e-6  # Tolerance for relative error in fixed point iteration
    ll_relax: float = 25.0  # Damping parameter in fixed point iteration

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for lifting line parameters."""
        print("! ----- Lifting line elements -----", file=file)
        print(
            f"ll_maxiter = {self.ll_maxiter}  ! Maximum number of iterations in LL algorithm",
            file=file,
        )
        print(
            f"ll_tol = {self.ll_tol}  ! Tolerance for the relative error in fixed point iteration for LL",
            file=file,
        )
        print(
            f"ll_relax= {self.ll_relax}  ! Damping parameter in fixed point iteration for LL to avoid oscillations",
            file=file,
        )
        print("", file=file)


@dataclass
class VLCorrectionConfig:
    """Vortex lattice correction parameters."""

    vl_relax: float = 0.3  # Relaxation factor for RHS update
    vl_maxiter: int = 100  # Maximum number of iterations in VL algorithm
    vl_tol: float = 1.0e-2  # Tolerance for absolute error on lift coefficient
    vl_start_step: int = 0  # Step in which the VL correction starts
    vl_dynstall: str = "F"  # Dynamic stall on corrected VL
    aitken_relaxation: str = "T"  # Employ Aitken acceleration method
    vl_average: str = "F"  # Average panel intensity between last iterations
    vl_average_iter: int = 10  # Number of iterations to average

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for VL correction parameters."""
        print("! ----- VL correction parameters -----", file=file)
        print(
            f"vl_relax = {self.vl_relax}  ! Relaxation factor for rhs update", file=file
        )
        print(
            f"vl_maxiter = {self.vl_maxiter}  ! Maximum number of iterations in VL algorithm",
            file=file,
        )
        print(
            f"vl_tol = {self.vl_tol}  ! Tolerance for the absolute error on lift coefficient in fixed point iteration for VL",
            file=file,
        )
        print(
            f"vl_start_step = {self.vl_start_step}  ! Step in which the VL correction starts",
            file=file,
        )
        print(
            f"vl_dynstall = {self.vl_dynstall}  ! Dynamic stall on corrected VL",
            file=file,
        )
        print(
            f"aitken_relaxation = {self.aitken_relaxation}  ! Employ Aitken acceleration method during fixed point iteration",
            file=file,
        )
        print(
            f"vl_average = {self.vl_average}  ! Average panel intensity between the last iterations",
            file=file,
        )
        print(
            f"vl_average_iter = {self.vl_average_iter}  ! Number of iterations to average",
            file=file,
        )
        print("", file=file)


@dataclass
class KuttaConfig:
    """Kutta condition correction parameters."""

    kutta_correction: str = "F"  # Employ Kutta condition
    kutta_beta: float = 0.01  # Perturbation factor for Kutta condition
    kutta_tol: float = 1.0e-4  # Tolerance for Kutta condition
    kutta_maxiter: int = 100  # Maximum number of iterations for Kutta condition
    kutta_start_step: int = 1  # Step in which the Kutta condition starts
    kutta_update_jacobian: int = 1  # Step frequency for updating the Jacobian

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for Kutta correction parameters."""
        print("! ----- Kutta correction parameters -----", file=file)
        print(
            f"kutta_correction = {self.kutta_correction}  ! Employ Kutta condition",
            file=file,
        )
        print(
            f"kutta_beta = {self.kutta_beta}  ! Perturbation factor for Kutta condition",
            file=file,
        )
        print(
            f"kutta_tol = {self.kutta_tol}  ! Tolerance for Kutta condition", file=file
        )
        print(
            f"kutta_maxiter = {self.kutta_maxiter}  ! Maximum number of iterations for Kutta condition",
            file=file,
        )
        print(
            f"kutta_start_step = {self.kutta_start_step}  ! Step in which the Kutta condition starts",
            file=file,
        )
        print(
            f"kutta_update_jacobian = {self.kutta_update_jacobian}  ! Step frequency where the Jacobian is updated",
            file=file,
        )
        print("", file=file)


@dataclass
class FMMConfig:
    """Fast Multipole Method (FMM) and octree parameters."""

    fmm: str = "T"  # Employ fast multipole method
    fmm_panels: str = "F"  # Employ FMM for panels
    box_length: Optional[float] = None  # Length of the octree box
    n_box: Optional[list[int]] = None  # Number of boxes in each direction
    octree_origin: Optional[list[float]] = None  # Octree origin
    n_octree_levels: Optional[int] = None  # Number of octree levels
    min_octree_part: int = 1  # Minimum number of octree particles
    multipole_degree: Optional[int] = None  # Multipole expansion degree
    dyn_layers: bool = False  # Use dynamic layers
    nmax_octree_levels: Optional[int] = None  # Maximum number of octree levels
    leaves_time_ratio: Optional[float] = None  # Ratio triggering increase of levels

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for FMM parameters."""
        n_box_str = (
            f"(/{self.n_box[0]} , {self.n_box[1]} , {self.n_box[2]}/)"
            if self.n_box
            else "None"
        )
        octree_origin_str = (
            f"(/{self.octree_origin[0]}, {self.octree_origin[1]}, {self.octree_origin[2]}/)"
            if self.octree_origin
            else "None"
        )
        dyn_layers_str = "T" if self.dyn_layers else "F"

        print("! ----- Octree and multipole data -----", file=file)
        print(f"fmm = {self.fmm}  ! Employ fast multipole method?", file=file)
        print(
            f"fmm_panels = {self.fmm_panels}  ! Employ fast multipole method also for panels?",
            file=file,
        )
        print(f"box_length = {self.box_length}  ! Length of the octree box", file=file)
        print(f"n_box = {n_box_str} ! Number of boxes in each direction", file=file)
        print(f"octree_origin = {octree_origin_str}", file=file)
        print(
            f"n_octree_levels = {self.n_octree_levels}  ! Number of octree levels",
            file=file,
        )
        print(
            f"min_octree_part = {self.min_octree_part}  ! Minimum number of octree particles",
            file=file,
        )
        print(
            f"multipole_degree = {self.multipole_degree}  ! Multipole expansion degree",
            file=file,
        )
        print(f"dyn_layers = {dyn_layers_str}  ! Use dynamic layers?", file=file)
        print(
            f"nmax_octree_levels = {self.nmax_octree_levels}  ! Maximum number of octree levels",
            file=file,
        )
        print(
            f"leaves_time_ratio = {self.leaves_time_ratio}  ! Ratio that triggers the increase of the number of levels",
            file=file,
        )
        print("", file=file)


@dataclass
class ModelsConfig:
    """Physical models and numerical methods."""

    vortstretch: str = "T"  # Employ vortex stretching
    vortstretch_from_elems: str = "F"  # Vortex stretching from geometry elements
    divergence_filtering: str = "T"  # Employ divergence filtering
    alpha_divergence_filter: float = 0.3  # Pedrizzetti relaxation coefficient
    diffusion: str = "T"  # Employ vorticity diffusion
    turbulent_viscosity: str = "F"  # Employ turbulent viscosity
    penetration_avoidance: str = "F"  # Employ penetration avoidance
    penetration_avoidance_check_radius: float = 5.0  # Check radius
    penetration_avoidance_element_radius: float = 1.5  # Element impact radius
    viscosity_effects: str = "F"  # Simulate viscosity effects

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for models parameters."""
        print("! ----- Models options -----", file=file)
        print(
            f"vortstretch = {self.vortstretch}  ! Employ vortex stretching", file=file
        )
        print(
            f"vortstretch_from_elems = {self.vortstretch_from_elems}  ! Employ vortex stretching from geometry elements",
            file=file,
        )
        print(
            f"divergence_filtering = {self.divergence_filtering}  ! Employ divergence filtering",
            file=file,
        )
        print(
            f"alpha_divergence_filter = {self.alpha_divergence_filter}  ! Pedrizzetti relaxation coefficient",
            file=file,
        )
        print(f"diffusion = {self.diffusion}  ! Employ vorticity diffusion", file=file)
        print(
            f"turbulent_viscosity = {self.turbulent_viscosity}  ! Employ turbulent viscosity",
            file=file,
        )
        print(
            f"penetration_avoidance = {self.penetration_avoidance}  ! Employ penetration avoidance",
            file=file,
        )
        print(
            f"penetration_avoidance_check_radius = {self.penetration_avoidance_check_radius}  ! Check radius for penetration avoidance",
            file=file,
        )
        print(
            f"penetration_avoidance_element_radius = {self.penetration_avoidance_element_radius}  ! Element impact radius for penetration avoidance",
            file=file,
        )
        print(
            f"viscosity_effects = {self.viscosity_effects}  ! Simulate viscosity effects",
            file=file,
        )
        print("", file=file)


@dataclass
class HCASConfig:
    """Hover Convergence Augmentation System parameters."""

    HCAS: str = "F"  # Hover Convergence Augmentation System
    HCAS_time: Optional[float] = None  # HCAS deployment time
    HCAS_velocity: Optional[float] = None  # HCAS velocity

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for HCAS parameters."""
        print("! ----- HCAS -----", file=file)
        print(f"HCAS = {self.HCAS}  ! Hover Convergence Augmentation System", file=file)
        print(f"HCAS_time = {self.HCAS_time}  ! HCAS deployment time", file=file)
        print(f"HCAS_velocity = {self.HCAS_velocity}  ! HCAS velocity", file=file)
        print("", file=file)


@dataclass
class VariableWindConfig:
    """Variable wind and gust parameters."""

    time_varying_u_inf: str = "F"  # Use time-varying free stream velocity
    non_uniform_u_inf: str = "F"  # Use non-uniform free stream velocity
    non_uniform_u_inf_dir: Optional[str] = None  # Direction of variation
    u_inf_file: Optional[str] = None  # File with time/coordinates + variable Ux, Uy, Uz
    gust: str = "F"  # Gust perturbation
    gust_type: str = "AMC"  # Gust model
    gust_origin: Optional[list[float]] = None  # Gust origin point
    gust_front_direction: Optional[list[float]] = None  # Gust front direction vector
    gust_front_speed: Optional[float] = None  # Gust front speed
    gust_u_des: Optional[float] = None  # Design gust velocity
    gust_perturbation_direction: list[float] = field(
        default_factory=lambda: [0.0, 0.0, 1.0]
    )  # Gust perturbation direction
    gust_gradient: Optional[float] = None  # Gust gradient
    gust_start_time: float = 0.0  # Gust starting time

    def to_dust_format(self, file) -> None:
        """Generate DUST input format for variable wind parameters."""
        gust_origin_str = (
            f"(/{self.gust_origin[0]} , {self.gust_origin[1]} , {self.gust_origin[2]}/)"
            if self.gust_origin
            else "None"
        )
        gust_front_dir_str = (
            f"(/{self.gust_front_direction[0]} , {self.gust_front_direction[1]} , {self.gust_front_direction[2]}/)"
            if self.gust_front_direction
            else "None"
        )

        print("! ----- Variable wind -----", file=file)
        print(
            f"time_varying_u_inf = {self.time_varying_u_inf}  ! Use time-varying free stream velocity",
            file=file,
        )
        print(
            f"non_uniform_u_inf = {self.non_uniform_u_inf}  ! Use non-uniform free stream velocity",
            file=file,
        )
        print(
            f"non_uniform_u_inf_dir = {self.non_uniform_u_inf_dir}  ! Direction of variation of non-uniform u_inf",
            file=file,
        )
        print(
            f"u_inf_file = {self.u_inf_file}  ! File containing time/coordinates + variable Ux, Uy, Uz",
            file=file,
        )
        print(f"gust = {self.gust}  ! Gust perturbation", file=file)
        print(f"gust_type = {self.gust_type}  ! Gust model", file=file)
        print(f"gust_origin = {gust_origin_str}  ! Gust origin point", file=file)
        print(
            f"gust_front_direction = {gust_front_dir_str}  ! Gust front direction vector",
            file=file,
        )
        print(
            f"gust_front_speed = {self.gust_front_speed}  ! Gust front speed", file=file
        )
        print(f"gust_u_des = {self.gust_u_des}", file=file)
        print(
            f"gust_perturbation_direction = (/{self.gust_perturbation_direction[0]} , {self.gust_perturbation_direction[1]} , {self.gust_perturbation_direction[2]}/)",
            file=file,
        )
        print(f"gust_gradient = {self.gust_gradient}", file=file)
        print(f"gust_start_time = {self.gust_start_time}", file=file)
        print("", file=file)


@dataclass
class DUSTConfig:
    """
    Main DUST simulation configuration.

    This dataclass contains all the configuration parameters for a DUST simulation,
    organized into logical subgroups for better maintainability.

    Attributes
    ----------
    name : str
        Name of the input file to generate
    timing : TimingConfig
        Time integration and output parameters
    integration : IntegrationConfig
        Integration method and reformulation parameters
    io : IOConfig
        Input/output file configuration
    restart : RestartConfig
        Restart configuration parameters
    reference : ReferenceConditions
        Reference atmospheric and flow conditions
    wake : WakeConfig
        Wake model parameters
    regularization : RegularizationConfig
        Regularization and vortex core parameters
    lifting_line : LiftingLineConfig
        Lifting line element parameters
    vl_correction : VLCorrectionConfig
        Vortex lattice correction parameters
    kutta : KuttaConfig
        Kutta condition correction parameters
    fmm : FMMConfig
        Fast Multipole Method and octree parameters
    models : ModelsConfig
        Physical models and numerical methods
    hcas : HCASConfig
        Hover Convergence Augmentation System parameters
    variable_wind : VariableWindConfig
        Variable wind and gust parameters
    gpu : GPUConfig
        GPU acceleration options

    Examples
    --------
    >>> config = DUSTConfig(name="simulation.in")
    >>> config.timing.tstart = 0.0
    >>> config.timing.tend = 10.0
    >>> config.timing.dt = 0.01
    >>> config.reference.u_inf = [10.0, 0.0, 0.0]
    >>> config.generate_input_file()
    >>> config.save_to_file("simulation.in")
    """

    name: str
    timing: TimingConfig = field(default_factory=TimingConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    io: IOConfig = field(default_factory=IOConfig)
    restart: RestartConfig = field(default_factory=RestartConfig)
    reference: ReferenceConditions = field(default_factory=ReferenceConditions)
    wake: WakeConfig = field(default_factory=WakeConfig)
    regularization: RegularizationConfig = field(default_factory=RegularizationConfig)
    lifting_line: LiftingLineConfig = field(default_factory=LiftingLineConfig)
    vl_correction: VLCorrectionConfig = field(default_factory=VLCorrectionConfig)
    kutta: KuttaConfig = field(default_factory=KuttaConfig)
    fmm: FMMConfig = field(default_factory=FMMConfig)
    models: ModelsConfig = field(default_factory=ModelsConfig)
    hcas: HCASConfig = field(default_factory=HCASConfig)
    variable_wind: VariableWindConfig = field(default_factory=VariableWindConfig)
    gpu: GPUConfig = field(default_factory=GPUConfig)

    _content: str = field(default="", init=False, repr=False)

    def __post_init__(self) -> None:
        """Create empty file if it doesn't exist."""
        self.create_empty_file()

    def create_empty_file(self) -> None:
        """Create an empty file with the specified name."""
        try:
            with open(self.name, "w"):
                pass  # Just create the file
            print(f"Created an empty file: {self.name}")
        except Exception as e:
            print(f"Error creating file {self.name}: {e}")

    def generate_input_file(self) -> None:
        """
        Generate the DUST input file content.

        This method creates the formatted input file content based on all
        configuration parameters stored in the dataclass attributes by calling
        the to_dust_format() method of each subclass.
        """
        # Use StringIO to collect output from print statements
        from io import StringIO

        buffer = StringIO()
        self.timing.to_dust_format(buffer)
        self.integration.to_dust_format(buffer)
        self.io.to_dust_format(buffer)
        self.restart.to_dust_format(buffer)
        self.reference.to_dust_format(buffer)
        self.gpu.to_dust_format(buffer)
        self.wake.to_dust_format(buffer)
        self.regularization.to_dust_format(buffer)
        self.lifting_line.to_dust_format(buffer)
        self.vl_correction.to_dust_format(buffer)
        self.kutta.to_dust_format(buffer)
        self.fmm.to_dust_format(buffer)
        self.models.to_dust_format(buffer)
        self.hcas.to_dust_format(buffer)
        self.variable_wind.to_dust_format(buffer)
        self._content = buffer.getvalue()

    def save_to_file(self, file_path: Optional[str] = None) -> None:
        """
        Save the generated DUST input file.

        Parameters
        ----------
        file_path : str, optional
            Path where to save the file. If None, uses self.name

        Notes
        -----
        This method filters out lines containing "None" to avoid writing
        undefined optional parameters to the input file.
        """
        if file_path is None:
            file_path = self.name

        with open(file_path, "w") as file:
            for line in self._content.splitlines():
                # Check if the line is not empty or does not contain "None"
                if "None" not in line:
                    file.write(line + "\n")
        print(f"File '{file_path}' has been created.")


def launch_dust(dust_executable: str, input_file: str) -> None:
    """
    Launch DUST simulation.

    Parameters
    ----------
    dust_executable : str
        Path to the DUST executable
    input_file : str
        Path to the DUST input file

    Examples
    --------
    >>> launch_dust("/path/to/dust", "simulation.in")
    """
    command = f"{dust_executable} {input_file}"
    print(command)
    os.system(command)
