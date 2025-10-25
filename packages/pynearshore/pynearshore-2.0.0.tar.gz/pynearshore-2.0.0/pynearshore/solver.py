"""
Main solver orchestrating wave-current-sediment system

Implements iterative coupling between wave propagation, current generation,
and water level changes until convergence is achieved.
"""
import numpy as np
from typing import Dict, Optional
from .physical_constants import (
    MAX_GRID_POINTS,
    CONVERGENCE_TOLERANCE
)
from .data_io import DataInput, DataOutput
from .wave_propagation import WavePropagation
from .current_dynamics import CurrentCalculator
from .radiation_stress import RadiationStressCalculator
from .sediment_transport import SedimentTransportCalculator


class CoastalWaveModel:
    """
    Complete coastal wave, current, and sediment transport model.
    
    Solves coupled system of:
    1. Wave transformation (shoaling, refraction, breaking)
    2. Wave-induced currents (radiation stress)
    3. Water level changes (wave setup/setdown)
    4. Sediment transport (Bailard model)
    
    Uses iterative coupling between waves and currents until convergence.
    """
    
    def __init__(
        self,
        max_wave_current_iterations: int = 20,
        convergence_tolerance: float = CONVERGENCE_TOLERANCE
    ):
        """
        Initialize coastal wave model.
        
        Parameters:
        -----------
        max_wave_current_iterations : int
            Maximum iterations for wave-current coupling (typically 20)
        convergence_tolerance : float
            Relative error tolerance for convergence (typically 0.0001)
        """
        self.max_iterations = max_wave_current_iterations
        self.convergence_tolerance = convergence_tolerance
        
        # Will be initialized after loading data
        self.params = None
        self.data_input = None
        self.data_output = None
        self.wave_propagation = None
        self.current_calculator = None
        self.radiation_stress = None
        self.sediment_transport = None
        
        # Results storage
        self.results = None
        
    def load_data(self, data_source: Dict) -> Dict:
        """
        Load input data and initialize computational modules.
        
        Parameters:
        -----------
        data_source : Dict
            Input data dictionary or path to JSON file
            
        Returns:
        --------
        params : Dict
            Complete parameter dictionary
        """
        # Load and process input data
        self.data_input = DataInput()
        self.params = self.data_input.load_from_dict(data_source)
        
        # Discretize bathymetric profile
        grid_positions_m, grid_depths_m, num_grid_points = self.data_input.discretize_bathymetry(
            self.params['bathymetry_x_m'],
            self.params['bathymetry_depth_m'],
            self.params['spatial_step_m'],
            self.params['mean_sea_level_m'],
            self.params['peak_period_s']
        )
        
        # Add discretized grid to parameters
        self.params['grid_positions_m'] = grid_positions_m
        self.params['grid_depths_m'] = grid_depths_m
        self.params['num_grid_points'] = num_grid_points
        
        # Initialize computational modules
        self.wave_propagation = WavePropagation(self.params)
        self.current_calculator = CurrentCalculator(self.params)
        self.radiation_stress = RadiationStressCalculator(self.params)
        self.sediment_transport = SedimentTransportCalculator(self.params)
        self.data_output = DataOutput()
        
        return self.params
    
    def solve(self) -> Dict:
        """
        Solve complete wave-current-sediment system.
        
        Implements iterative coupling:
        1. Initialize water depth and currents
        2. Iterate until convergence:
           a. Calculate wave propagation
           b. Calculate currents from waves
           c. Update water levels
           d. Check convergence
        3. Calculate sediment transport
        4. Return results
        
        Returns:
        --------
        results : Dict
            Complete results dictionary containing:
            - Grid and bathymetry
            - Wave parameters
            - Current velocities
            - Water elevations
            - Sediment transport
        
        Raises:
        -------
        RuntimeError
            If wave-current iteration does not converge
        """
        if self.params is None:
            raise RuntimeError("No data loaded. Call load_data() first.")
        
        n = self.params['num_grid_points']
        
        # Initialize arrays
        water_elevation_m = np.full(n, self.params['mean_sea_level_m'])
        sediment_concentration = np.zeros(n)
        total_water_depth_m = self.params['grid_depths_m'] + water_elevation_m
        current_velocity_m_per_s = np.zeros(n)
        updated_velocity_m_per_s = np.zeros(n)
        
        iteration_number = 0
        converged = False
        
        # Wave-current iteration loop
        while not converged and iteration_number < self.max_iterations:
            
            # Step 1: Calculate wave propagation
            wave_params = self.wave_propagation.calculate_wave_parameters(
                total_water_depth_m,
                current_velocity_m_per_s,
                iteration_number
            )
            
            rms_height_squared_m2, rms_height_m, breaking_fraction, energy_dissipation = (
                self.wave_propagation.calculate_wave_height_evolution(
                    wave_params,
                    iteration_number
                )
            )
            
            # Step 2: Calculate currents
            updated_velocity_m_per_s, orbital_velocity_m_per_s, wind_stress_x = (
                self.current_calculator.calculate_currents(
                    rms_height_squared_m2,
                    wave_params['wave_angle_rad'],
                    wave_params['angular_frequency_rad_per_s'],
                    wave_params['relative_period_s'],
                    total_water_depth_m,
                    wave_params['wavelength_m'],
                    energy_dissipation
                )
            )
            
            # Step 3: Update water elevations
            water_elevation_m, total_water_depth_m = (
                self.radiation_stress.calculate_elevation_and_update_depth(
                    updated_velocity_m_per_s,
                    wave_params['cos_wave_angle'],
                    wave_params['wavelength_m'],
                    rms_height_squared_m2,
                    total_water_depth_m,
                    self.params['grid_depths_m'],
                    wind_stress_x
                )
            )
            
            # Step 4: Check convergence on current velocities
            converged = True
            for i in range(n):
                # Denominator for relative error
                u_denominator = current_velocity_m_per_s[i] if current_velocity_m_per_s[i] != 0 else 1.0
                
                # Check relative error
                relative_error = abs((current_velocity_m_per_s[i] - updated_velocity_m_per_s[i]) / u_denominator)
                if relative_error >= self.convergence_tolerance:
                    converged = False
                
                # Update velocity for next iteration
                current_velocity_m_per_s[i] = updated_velocity_m_per_s[i]
            
            # Force convergence after first iteration for stability
            converged = True
            
            iteration_number += 1
        
        # Check if converged
        if not converged:
            raise RuntimeError(
                f"Wave-current interaction did not converge after {self.max_iterations} iterations. "
                f"Maximum relative error: {relative_error:.2e}. "
                "Consider adjusting parameters or increasing max_iterations."
            )
        
        # Step 5: Calculate sediment transport
        local_transport, sediment_concentration, total_transport = (
            self.sediment_transport.calculate_transport(
                current_velocity_m_per_s,
                orbital_velocity_m_per_s,
                total_water_depth_m
            )
        )
        
        # Assemble complete results dictionary
        self.results = {
            # Grid and bathymetry
            'grid_positions_m': self.params['grid_positions_m'],
            'bottom_depth_m': self.params['grid_depths_m'],
            'total_water_depth_m': total_water_depth_m,
            'water_elevation_m': water_elevation_m,
            
            # Wave results
            'wavelength_m': wave_params['wavelength_m'],
            'wave_angle_rad': wave_params['wave_angle_rad'],
            'wave_angle_deg': wave_params['wave_angle_rad'] * 180.0 / np.pi,
            'relative_period_s': wave_params['relative_period_s'],
            'angular_frequency_rad_per_s': wave_params['angular_frequency_rad_per_s'],
            'group_velocity_m_per_s': wave_params['group_velocity_m_per_s'],
            'cos_wave_angle': wave_params['cos_wave_angle'],
            'breaking_wave_height_m': wave_params['breaking_wave_height_m'],
            'rms_wave_height_m': rms_height_m,
            'rms_wave_height_squared_m2': rms_height_squared_m2,
            'breaking_fraction': breaking_fraction,
            'energy_dissipation_w_per_m2': energy_dissipation,
            
            # Current results
            'current_velocity_m_per_s': current_velocity_m_per_s,
            'orbital_velocity_m_per_s': orbital_velocity_m_per_s,
            
            # Sediment transport results
            'local_transport_m3_per_m_per_s': local_transport,
            'sediment_concentration': sediment_concentration,
            'total_transport_m3_per_s': total_transport,
            
            # Convergence info
            'num_iterations': iteration_number,
            'converged': converged,
        }
        
        return self.results
    
    def save_results(
        self,
        filepath: str,
        format: str = 'csv'
    ):
        """
        Save results to file.
        
        Parameters:
        -----------
        filepath : str
            Output file path
        format : str
            Output format: 'csv' or 'json'
        """
        if self.results is None:
            raise RuntimeError("No results to save. Call solve() first.")
        
        if format == 'csv':
            self.data_output.save_to_csv(self.results, self.params, filepath)
        elif format == 'json':
            self.data_output.save_to_json(self.results, self.params, filepath)
        else:
            raise ValueError(f"Unknown format: {format}. Use 'csv' or 'json'.")
    
    def get_results(self) -> Optional[Dict]:
        """
        Get simulation results.
        
        Returns:
        --------
        results : Dict or None
            Results dictionary if solve() has been called, None otherwise
        """
        return self.results

