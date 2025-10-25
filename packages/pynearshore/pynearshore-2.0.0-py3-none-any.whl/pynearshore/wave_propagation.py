"""
Wave propagation module for coastal environments

Implements complete wave transformation including refraction, shoaling,
and breaking dissipation using energy flux balance equations.

Solves the energy conservation equation using Runge-Kutta 4th order method.
"""
import numpy as np
from typing import Dict, Tuple
from .physical_constants import (
    PI,
    GRAVITATIONAL_ACCELERATION
)
from .numerical_methods import (
    calculate_wavelength_iterative,
    calculate_breaking_percentage
)
from .wave_models import (
    calculate_breaking_height_with_slope,
    calculate_energy_dissipation_battjes_janssen,
    calculate_energy_dissipation_thornton_guza
)


class WavePropagation:
    """
    Complete wave propagation calculator for nearshore zone.
    
    Calculates wave transformation from offshore to shore including:
    - Wavelength via dispersion relation
    - Wave refraction (Snell's law)
    - Wave shoaling
    - Energy dissipation from breaking
    - RMS wave height evolution
    """
    
    def __init__(self, params: Dict):
        """
        Initialize wave propagation calculator.
        
        Parameters:
        -----------
        params : Dict
            Complete parameter dictionary with wave conditions,
            grid information, and model settings
        """
        self.params = params
        
        # Extract key parameters
        self.num_grid_points = params['num_grid_points']
        self.peak_period_s = params['peak_period_s']
        self.incident_angle_rad = params['incident_angle_rad']
        self.wave_amplitude_m = params['wave_amplitude_m']
        self.breaking_parameter_gamma = params['breaking_parameter_gamma']
        self.use_goda_breaking = params['use_goda_breaking']
        self.dissipation_model_id = params['dissipation_model_id']
        self.battjes_alpha = params['battjes_alpha_coefficient']
        self.spatial_step_m = params['spatial_step_m']
        self.water_density = params['water_density_kg_per_m3']
        self.gravity = params['gravity_m_per_s2']
        
    def calculate_wave_parameters(
        self,
        total_water_depth_m: np.ndarray,
        current_velocity_m_per_s: np.ndarray,
        iteration_number: int
    ) -> Dict[str, np.ndarray]:
        """
        Calculate all wave parameters at each grid point.
        
        Implements complete wave transformation calculation including
        wavelength, refraction angle, group velocity, and breaking height.
        
        Parameters:
        -----------
        total_water_depth_m : np.ndarray
            Total water depth h = d + eta at each point (m)
        current_velocity_m_per_s : np.ndarray
            Current velocity at each point (m/s)
        iteration_number : int
            Current wave-current iteration number
            
        Returns:
        --------
        wave_params : Dict[str, np.ndarray]
            Dictionary containing:
            - wavelength_m: Local wavelength (m)
            - wave_angle_rad: Local wave angle (rad)
            - relative_period_s: Period in moving frame (s)
            - angular_frequency_rad_per_s: Wave frequency (rad/s)
            - group_velocity_m_per_s: Group velocity (m/s)
            - cos_wave_angle: Cosine of wave angle
            - breaking_wave_height_m: Breaking wave height limit (m)
        """
        n = self.num_grid_points
        
        # Initialize arrays
        wavelength_m = np.zeros(n)
        wave_angle_rad = np.zeros(n)
        relative_period_s = np.zeros(n)
        angular_frequency_rad_per_s = np.zeros(n)
        group_velocity_m_per_s = np.zeros(n)
        cos_wave_angle = np.zeros(n)
        breaking_wave_height_m = np.zeros(n)
        
        # Calculate wavelength and dispersion constant at first point 
        wavelength_m[0], _ = calculate_wavelength_iterative(
            total_water_depth_m[0],
            self.peak_period_s,
            current_velocity=0.0,
            dispersion_constant=0.0
        )
        
        # Dispersion constant from Snell's law  / AL(1))
        dispersion_constant = np.sin(self.incident_angle_rad) / wavelength_m[0]
        
        # If current present at first point, iterate for wavelength 
        if abs(current_velocity_m_per_s[0]) > 0.001:
            wavelength_m[0], _ = calculate_wavelength_iterative(
                total_water_depth_m[0],
                self.peak_period_s,
                current_velocity=current_velocity_m_per_s[0],
                dispersion_constant=dispersion_constant
            )
            # Update dispersion constant
            dispersion_constant = np.sin(self.incident_angle_rad) / wavelength_m[0]
        
        # Calculate wave parameters at first point 
        wave_angle_rad[0] = np.arcsin(dispersion_constant * wavelength_m[0])
        relative_period_s[0] = 1.0 / (1.0 / self.peak_period_s - 
                                      dispersion_constant * current_velocity_m_per_s[0])
        angular_frequency_rad_per_s[0] = 2.0 * PI / relative_period_s[0]
        
        # Group velocity 
        depth_wavelength_ratio = 4.0 * PI * total_water_depth_m[0] / wavelength_m[0]
        group_velocity_m_per_s[0] = (wavelength_m[0] / (2.0 * relative_period_s[0]) *
                                     (1.0 + depth_wavelength_ratio / np.sinh(depth_wavelength_ratio)))
        cos_wave_angle[0] = np.cos(wave_angle_rad[0])
        
        # Breaking wave height at first point 
        deep_water_wavelength_m = self.gravity * (self.peak_period_s ** 2) / (2.0 * PI)
        
        if self.use_goda_breaking:
            # Goda formulation 
            breaking_wave_height_m[0] = calculate_breaking_height_with_slope(
                total_water_depth_m[0],
                wavelength_m[0],
                bed_slope=0.01,  # Approximate slope
                gamma_max=0.88,
                use_goda_formula=True
            )
        else:
            # Simple depth-limited 
            breaking_wave_height_m[0] = self.breaking_parameter_gamma * total_water_depth_m[0]
        
        # Calculate parameters at all other points 
        for k in range(1, n):
            # Wavelength with current and dispersion 
            wavelength_m[k], _ = calculate_wavelength_iterative(
                total_water_depth_m[k],
                self.peak_period_s,
                current_velocity=current_velocity_m_per_s[k],
                dispersion_constant=dispersion_constant
            )
            
            # Wave angle from Snell's law 
            wave_angle_rad[k] = np.arcsin(dispersion_constant * wavelength_m[k])
            
            # Relative period accounting for Doppler shift 
            relative_period_s[k] = 1.0 / (1.0 / self.peak_period_s -
                                         dispersion_constant * current_velocity_m_per_s[k])
            
            # Angular frequency 
            angular_frequency_rad_per_s[k] = 2.0 * PI / relative_period_s[k]
            
            # Group velocity 
            depth_wavelength_ratio = 4.0 * PI * total_water_depth_m[k] / wavelength_m[k]
            group_velocity_m_per_s[k] = (wavelength_m[k] / (2.0 * relative_period_s[k]) *
                                        (1.0 + depth_wavelength_ratio / np.sinh(depth_wavelength_ratio)))
            
            # Cosine of wave angle 
            cos_wave_angle[k] = np.cos(wave_angle_rad[k])
            
            # Breaking wave height 
            if self.use_goda_breaking:
                breaking_wave_height_m[k] = calculate_breaking_height_with_slope(
                    total_water_depth_m[k],
                    wavelength_m[k],
                    bed_slope=0.01,
                    gamma_max=0.88,
                    use_goda_formula=True
                )
            else:
                breaking_wave_height_m[k] = self.breaking_parameter_gamma * total_water_depth_m[k]
        
        return {
            'wavelength_m': wavelength_m,
            'wave_angle_rad': wave_angle_rad,
            'relative_period_s': relative_period_s,
            'angular_frequency_rad_per_s': angular_frequency_rad_per_s,
            'group_velocity_m_per_s': group_velocity_m_per_s,
            'cos_wave_angle': cos_wave_angle,
            'breaking_wave_height_m': breaking_wave_height_m,
        }
    
    def calculate_wave_height_evolution(
        self,
        wave_params: Dict[str, np.ndarray],
        iteration_number: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate RMS wave height evolution using Runge-Kutta 4th order.
        
        Solves the wave energy flux equation:
        d(E·C_g·cos(θ))/dx = -ε_d
        
        where E = ρg·H_rms²/8 and ε_d is energy dissipation.
        
        Parameters:
        -----------
        wave_params : Dict[str, np.ndarray]
            Wave parameters from calculate_wave_parameters()
        iteration_number : int
            Current iteration number
            
        Returns:
        --------
        rms_height_squared_m2 : np.ndarray
            Square of RMS wave height H_rms² (m²)
        rms_height_m : np.ndarray
            RMS wave height H_rms (m)
        breaking_fraction : np.ndarray
            Fraction of breaking waves Q_b
        energy_dissipation_w_per_m2 : np.ndarray
            Energy dissipation rate (W/m²)
        """
        n = self.num_grid_points
        
        # Initialize at first two points 
        rms_height_squared_m2 = np.zeros(n)
        if iteration_number == 0:
            rms_height_squared_m2[0] = self.wave_amplitude_m ** 2
            rms_height_squared_m2[1] = self.wave_amplitude_m ** 2
        else:
            # Keep previous values for subsequent iterations
            rms_height_squared_m2[0] = self.wave_amplitude_m ** 2
            rms_height_squared_m2[1] = self.wave_amplitude_m ** 2
        
        breaking_fraction = np.zeros(n)
        
        # Runge-Kutta 4th order integration 
        for k in range(n - 2):
            # RK4 stage 1
            fonc_k1 = self._compute_rhs_energy_equation(
                k, rms_height_squared_m2[k],
                wave_params, breaking_fraction
            )
            ak1 = -self.spatial_step_m * fonc_k1 * 2.0
            
            # RK4 stage 2
            fonc_k2 = self._compute_rhs_energy_equation(
                k + 1, rms_height_squared_m2[k] + ak1 / 2.0,
                wave_params, breaking_fraction
            )
            ak2 = -self.spatial_step_m * fonc_k2 * 2.0
            
            # RK4 stage 3
            fonc_k3 = self._compute_rhs_energy_equation(
                k + 1, rms_height_squared_m2[k] + ak2 / 2.0,
                wave_params, breaking_fraction
            )
            ak3 = -self.spatial_step_m * fonc_k3 * 2.0
            
            # RK4 stage 4
            fonc_k4 = self._compute_rhs_energy_equation(
                k + 2, rms_height_squared_m2[k] + ak3,
                wave_params, breaking_fraction
            )
            ak4 = -self.spatial_step_m * fonc_k4 * 2.0
            
            # RK4 update 
            rms_height_squared_m2[k + 2] = rms_height_squared_m2[k] + (ak1 + 2.0 * (ak2 + ak3) + ak4) / 6.0
            
            # Check for numerical instability 
            if rms_height_squared_m2[k + 2] < 0:
                raise RuntimeError(
                    f"Wave height calculation gave negative result at point {k+2}. "
                    f"Numerical instability detected. REDUCE SPATIAL STEP. "
                    f"Current step: {self.spatial_step_m} m. Try {self.spatial_step_m/2} m."
                )
        
        # Calculate final RMS height, breaking fraction, and dissipation 
        rms_height_m = np.zeros(n)
        energy_dissipation_w_per_m2 = np.zeros(n)
        
        for i in range(n):
            # RMS wave height 
            rms_height_m[i] = np.sqrt(rms_height_squared_m2[i])
            
            # Limit to breaking height 
            if rms_height_m[i] > wave_params['breaking_wave_height_m'][i]:
                rms_height_m[i] = wave_params['breaking_wave_height_m'][i]
            
            # Update squared value 
            rms_height_squared_m2[i] = rms_height_m[i] * rms_height_m[i]
            
            # Breaking percentage 
            breaking_fraction[i] = calculate_breaking_percentage(
                rms_height_squared_m2[i],
                wave_params['breaking_wave_height_m'][i]
            )
            
            # Energy dissipation based on model selection 
            if self.dissipation_model_id == 1:
                # Battjes-Janssen model 
                energy_dissipation_w_per_m2[i] = calculate_energy_dissipation_battjes_janssen(
                    rms_height_squared_m2[i],
                    wave_params['breaking_wave_height_m'][i],
                    breaking_fraction[i],
                    wave_params['relative_period_s'][i],
                    self.water_density,
                    alpha=self.battjes_alpha,
                    gravity=self.gravity
                )
            
            elif self.dissipation_model_id == 2:
                # Barailler model 
                if i != 0:
                    dsxx_dx = ((wave_params['breaking_wave_height_m'][i-1] ** 2) * 
                              wave_params['group_velocity_m_per_s'][i-1] * 
                              wave_params['cos_wave_angle'][i-1] -
                              (wave_params['breaking_wave_height_m'][i] ** 2) * 
                              wave_params['group_velocity_m_per_s'][i] * 
                              wave_params['cos_wave_angle'][i])
                else:
                    dsxx_dx = ((wave_params['breaking_wave_height_m'][0] ** 2) * 
                              wave_params['group_velocity_m_per_s'][0] * 
                              wave_params['cos_wave_angle'][0] -
                              (wave_params['breaking_wave_height_m'][1] ** 2) * 
                              wave_params['group_velocity_m_per_s'][1] * 
                              wave_params['cos_wave_angle'][1])
                
                energy_dissipation_w_per_m2[i] = (dsxx_dx / self.spatial_step_m * 
                                                 self.water_density * self.gravity / 8.0 * 
                                                 breaking_fraction[i])
            
            elif self.dissipation_model_id == 3:
                # Thornton-Guza model 
                energy_dissipation_w_per_m2[i] = calculate_energy_dissipation_thornton_guza(
                    rms_height_m[i],
                    wave_params['breaking_wave_height_m'][i] / self.breaking_parameter_gamma,  # Depth
                    wave_params['relative_period_s'][i],
                    self.water_density,
                    beta=1.0,
                    gamma=self.breaking_parameter_gamma,
                    gravity=self.gravity
                )
                breaking_fraction[i] = 0.0  # #
            
            # Ensure non-negative dissipation 
            if energy_dissipation_w_per_m2[i] < 0:
                energy_dissipation_w_per_m2[i] = 0.0
        
        return rms_height_squared_m2, rms_height_m, breaking_fraction, energy_dissipation_w_per_m2
    
    def _compute_rhs_energy_equation(
        self,
        position_index: int,
        rms_height_squared_m2: float,
        wave_params: Dict[str, np.ndarray],
        breaking_fraction: np.ndarray
    ) -> float:
        """
        Compute right-hand side of energy flux equation for Runge-Kutta.
        
        Implements the function for d(H_rms²)/dx calculation.
        
        Parameters:
        -----------
        position_index : int
            Current grid point index
        rms_height_squared_m2 : float
            Current value of H_rms² (m²)
        wave_params : Dict[str, np.ndarray]
            Wave parameters at all grid points
        breaking_fraction : np.ndarray
            Array to store breaking fractions
            
        Returns:
        --------
        rhs : float
            Spatial derivative d(H_rms²)/dx
        """
        j = position_index
        
        # Ensure non-negative wave height 
        if rms_height_squared_m2 < 0:
            rms_height_squared_m2 = 0.0
        
        # Calculate energy dissipation 
        if self.dissipation_model_id == 1:
            # Battjes-Janssen 
            qb_j = calculate_breaking_percentage(
                rms_height_squared_m2,
                wave_params['breaking_wave_height_m'][j]
            )
            breaking_fraction[j] = qb_j
            
            dissipation = (self.battjes_alpha / 4.0 / wave_params['relative_period_s'][j] *
                          self.water_density * self.gravity *
                          (wave_params['breaking_wave_height_m'][j] ** 2) * qb_j)
        
        elif self.dissipation_model_id == 2:
            # Barailler 
            qb_j = calculate_breaking_percentage(
                rms_height_squared_m2,
                wave_params['breaking_wave_height_m'][j]
            )
            breaking_fraction[j] = qb_j
            
            if j == 0:
                gradient = ((wave_params['breaking_wave_height_m'][0] ** 2) *
                           wave_params['group_velocity_m_per_s'][0] *
                           wave_params['cos_wave_angle'][0] -
                           (wave_params['breaking_wave_height_m'][1] ** 2) *
                           wave_params['group_velocity_m_per_s'][1] *
                           wave_params['cos_wave_angle'][1])
            else:
                gradient = ((wave_params['breaking_wave_height_m'][j-1] ** 2) *
                           wave_params['group_velocity_m_per_s'][j-1] *
                           wave_params['cos_wave_angle'][j-1] -
                           (wave_params['breaking_wave_height_m'][j] ** 2) *
                           wave_params['group_velocity_m_per_s'][j] *
                           wave_params['cos_wave_angle'][j])
            
            dissipation = gradient / self.spatial_step_m * self.water_density * self.gravity / 8.0 * qb_j
            if dissipation < 0.0:
                dissipation = 0.0
        
        elif self.dissipation_model_id == 3:
            # Thornton-Guza 
            dissipation = (3.0 / 16.0 * np.sqrt(PI * rms_height_squared_m2) * 
                          self.water_density * self.gravity * 
                          (1.0 ** 3))  # COB=1.0
            depth_estimate = wave_params['breaking_wave_height_m'][j] / self.breaking_parameter_gamma
            dissipation = dissipation / ((self.breaking_parameter_gamma ** 4) * 
                                        (depth_estimate ** 5)) / wave_params['relative_period_s'][j]
            breaking_fraction[j] = 0.0
        
        # Calculate derivative of energy flux 
        if j == 0:
            flux_derivative = (wave_params['group_velocity_m_per_s'][0] *
                              wave_params['cos_wave_angle'][0] *
                              wave_params['relative_period_s'][0] -
                              wave_params['group_velocity_m_per_s'][1] *
                              wave_params['cos_wave_angle'][1] *
                              wave_params['relative_period_s'][1])
        else:
            flux_derivative = (wave_params['group_velocity_m_per_s'][j-1] *
                              wave_params['cos_wave_angle'][j-1] *
                              wave_params['relative_period_s'][j-1] -
                              wave_params['group_velocity_m_per_s'][j] *
                              wave_params['cos_wave_angle'][j] *
                              wave_params['relative_period_s'][j])
        
        flux_derivative = (flux_derivative * wave_params['angular_frequency_rad_per_s'][j] /
                          self.spatial_step_m / 2.0 / PI)
        
        # Final RHS 
        rhs = -(rms_height_squared_m2 * flux_derivative - dissipation * 8.0 / self.water_density / self.gravity) / (
            wave_params['group_velocity_m_per_s'][j] * wave_params['cos_wave_angle'][j]
        )
        
        return rhs

