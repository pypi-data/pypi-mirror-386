"""
Data input/output module for coastal wave transport modeling

Handles loading of wave conditions, bathymetric profiles, and sediment properties,
as well as saving simulation results in various formats (JSON, CSV).
"""
import numpy as np
import json
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from .physical_constants import (
    PI,
    MAX_GRID_POINTS,
    GRAVITATIONAL_ACCELERATION
)


class DataInput:
    """
    Input data handler for coastal wave transport model.
    
    Loads wave conditions, bathymetric profiles, sediment properties,
    and numerical parameters. Discretizes bathymetric profile onto
    regular computational grid.
    """
    
    def __init__(self):
        """Initialize data input handler."""
        self.wave_conditions = None
        self.bathymetry_profile = None
        self.sediment_properties = None
        self.numerical_params = None
        
    def load_from_dict(self, data: Dict) -> Dict:
        """
        Load all input data from dictionary.
        
        Parameters:
        -----------
        data : Dict
            Complete input dictionary with keys:
            - 'wave': wave parameters
            - 'water': water level
            - 'wind': wind forcing
            - 'sediment': sediment properties
            - 'numerical': discretization parameters
            - 'bathymetry': profile definition
            
        Returns:
        --------
        params : Dict
            Complete parameter dictionary for solver
        """
        # Extract wave parameters
        wave = data.get('wave', {})
        significant_height_m = wave.get('H13', wave.get('significant_height_m', 1.0))
        peak_period_s = wave.get('PERIOD', wave.get('peak_period_s', 10.0))
        incident_angle_deg = wave.get('TETAH', wave.get('incident_angle_deg', 0.0))
        
        # Extract water level
        water = data.get('water', {})
        mean_sea_level_m = water.get('NIVMAR', water.get('mean_sea_level_m', 0.0))
        
        # Extract wind parameters
        wind = data.get('wind', {})
        wind_speed_m_per_s = wind.get('W', wind.get('wind_speed_m_per_s', 0.0))
        wind_direction_deg = wind.get('TETAW', wind.get('wind_direction_deg', 0.0))
        
        # Extract sediment properties
        sediment = data.get('sediment', {})
        sediment_density_kg_per_m3 = sediment.get('ROS', sediment.get('sediment_density_kg_per_m3', 2650.0))
        fall_velocity_m_per_s = sediment.get('WC', sediment.get('fall_velocity_m_per_s', 0.04))
        friction_angle_deg = sediment.get('PHI', sediment.get('friction_angle_deg', 32.0))
        bedload_efficiency = sediment.get('EPSB', sediment.get('bedload_efficiency', 0.1))
        suspended_load_efficiency = sediment.get('EPSS', sediment.get('suspended_load_efficiency', 0.02))
        
        # Extract numerical parameters
        numerical = data.get('numerical', {})
        bed_friction_coefficient = numerical.get('CF', numerical.get('bed_friction_coefficient', 0.01))
        spatial_step_m = numerical.get('PAS', numerical.get('spatial_step_m', 10.0))
        output_step = numerical.get('IED', numerical.get('output_step', 1))
        max_output_distance_m = numerical.get('XDEB', numerical.get('max_output_distance_m', 10000.0))
        breaking_parameter_gamma = numerical.get('GAMMA', numerical.get('breaking_parameter_gamma', 0.78))
        latitude_deg = numerical.get('LAMBDA', numerical.get('latitude_deg', 43.0))
        
        # Extract bathymetry
        bathymetry = data.get('bathymetry', data.get('profile', {}))
        cross_shore_positions_m = np.array(bathymetry.get('XZ', bathymetry.get('cross_shore_distance_m', [])))
        depths_m = np.array(bathymetry.get('Z', bathymetry.get('depth_m', [])))
        
        # Ensure positive depths (invert if necessary)
        if np.mean(depths_m) < 0:
            depths_m = -depths_m
        
        # Convert angles to radians
        incident_angle_rad = incident_angle_deg * PI / 180.0
        wind_direction_rad = wind_direction_deg * PI / 180.0
        latitude_rad = latitude_deg * PI / 180.0
        
        # Calculate derived parameters
        # Convert H1/3 to amplitude using RMS relationship
        amplitude_m = 0.706 * significant_height_m  # AMPLI = 0.706 * H13
        
        # Tangent of friction angle for sediment transport
        tan_friction_angle = np.tan(friction_angle_deg * PI / 180.0)
        
        # Assemble complete parameter dictionary
        self.params = {
            # Wave parameters
            'significant_height_m': significant_height_m,
            'peak_period_s': peak_period_s,
            'incident_angle_rad': incident_angle_rad,
            'incident_angle_deg': incident_angle_deg,
            'wave_amplitude_m': amplitude_m,
            
            # Water parameters
            'mean_sea_level_m': mean_sea_level_m,
            
            # Wind parameters
            'wind_speed_m_per_s': wind_speed_m_per_s,
            'wind_direction_rad': wind_direction_rad,
            'wind_direction_deg': wind_direction_deg,
            
            # Sediment parameters
            'sediment_density_kg_per_m3': sediment_density_kg_per_m3,
            'fall_velocity_m_per_s': fall_velocity_m_per_s,
            'friction_angle_deg': friction_angle_deg,
            'friction_angle_rad': friction_angle_deg * PI / 180.0,
            'tan_friction_angle': tan_friction_angle,
            'bedload_efficiency': bedload_efficiency,
            'suspended_load_efficiency': suspended_load_efficiency,
            'sediment_porosity': 0.3,  # Typical sand porosity
            
            # Numerical parameters
            'bed_friction_coefficient': bed_friction_coefficient,
            'spatial_step_m': spatial_step_m,
            'output_step': output_step,
            'max_output_distance_m': max_output_distance_m,
            'breaking_parameter_gamma': breaking_parameter_gamma,
            'latitude_rad': latitude_rad,
            
            # Physical constants
            'water_density_kg_per_m3': 1023.0,  # Seawater density
            'gravity_m_per_s2': 9.81,  # Gravitational acceleration
            'earth_rotation_rad_per_s': 0.000072722,  # Earth rotation rate
            'convergence_tolerance': 0.0001,  # Wave-current iteration tolerance
            
            # Model selection parameters
            'use_goda_breaking': True,  # Use Goda breaking formulation
            'dissipation_model_id': 1,  # 1=Battjes-Janssen, 2=Barailler, 3=Thornton-Guza
            'battjes_alpha_coefficient': 1.0,  # Battjes-Janssen alpha coefficient
            
            # Temperature for air density calculation
            'air_temperature_celsius': 20.0,  # Ambient air temperature
            
            # Bathymetry (to be discretized)
            'bathymetry_x_m': cross_shore_positions_m,
            'bathymetry_depth_m': depths_m,
        }
        
        return self.params
    
    def discretize_bathymetry(
        self,
        cross_shore_positions_m: np.ndarray,
        depths_m: np.ndarray,
        spatial_step_m: float,
        mean_sea_level_m: float,
        peak_period_s: float
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        """
        Discretize bathymetric profile onto regular computational grid.
        
        Uses linear interpolation to map irregular profile points onto
        a regular grid with specified spatial resolution.
        
        Parameters:
        -----------
        cross_shore_positions_m : np.ndarray
            Cross-shore distances of profile points (m)
        depths_m : np.ndarray
            Water depths at profile points (m, positive downward)
        spatial_step_m : float
            Computational grid spacing (m)
        mean_sea_level_m : float
            Mean water level (m)
        peak_period_s : float
            Wave period for minimum depth criterion (s)
            
        Returns:
        --------
        grid_positions_m : np.ndarray
            Cross-shore positions of grid points (m)
        grid_depths_m : np.ndarray
            Water depths at grid points (m)
        num_grid_points : int
            Number of computational grid points (even number)
        """
        num_profile_points = len(cross_shore_positions_m)
        
        # Calculate number of grid points needed
        num_requested_points = int(cross_shore_positions_m[0] / spatial_step_m)
        
        # Check maximum array size limit
        if num_requested_points > MAX_GRID_POINTS:
            raise ValueError(
                f"Requested {num_requested_points} grid points exceeds "
                f"maximum {MAX_GRID_POINTS}. Increase spatial_step_m."
            )
        
        # Initialize grid arrays
        grid_positions_m = np.zeros(num_requested_points)
        grid_depths_m = np.zeros(num_requested_points)
        
        # Set offshore boundary position
        grid_positions_m[0] = cross_shore_positions_m[0]
        
        # Minimum water depth criterion (avoid very shallow water)
        # Based on wave period: h_min = 0.0002 * 1.56 * T²
        min_water_depth_m = 0.0002 * 1.56 * (peak_period_s ** 2)
        
        last_valid_index = 0
        
        # Discretize profile using linear interpolation
        for grid_idx in range(1, num_requested_points):
            # Calculate grid position from offshore
            grid_positions_m[grid_idx] = grid_positions_m[0] - grid_idx * spatial_step_m
            
            if grid_positions_m[grid_idx] < 0:
                grid_positions_m[grid_idx] = 0
            
            # Find profile points bracketing current grid point
            profile_idx_upper = 0
            for profile_idx in range(1, num_profile_points):
                if cross_shore_positions_m[profile_idx] <= grid_positions_m[grid_idx]:
                    profile_idx_upper = profile_idx
                    break
            
            if profile_idx_upper == 0:
                profile_idx_upper = num_profile_points - 1
            
            # Linear interpolation between bracketing points
            x_lower = cross_shore_positions_m[profile_idx_upper]
            x_upper = cross_shore_positions_m[profile_idx_upper - 1]
            depth_lower = depths_m[profile_idx_upper]
            depth_upper = depths_m[profile_idx_upper - 1]
            
            interpolation_factor = (grid_positions_m[grid_idx] - x_lower) / (x_upper - x_lower)
            grid_depths_m[grid_idx] = depth_lower + interpolation_factor * (depth_upper - depth_lower)
            
            # Check for minimum water depth to stop grid
            if last_valid_index == 0:
                if (grid_depths_m[grid_idx] + mean_sea_level_m) <= min_water_depth_m:
                    last_valid_index = grid_idx - 1
        
        # Determine final number of grid points
        if last_valid_index == 0:
            last_valid_index = grid_idx
        
        # Ensure even number of points for Simpson's rule integration
        if (last_valid_index % 2) == 1:
            last_valid_index = last_valid_index - 1
        
        num_grid_points = last_valid_index
        
        # Set offshore boundary conditions (constant depth for first 2 points)
        grid_depths_m[0] = depths_m[0]
        grid_depths_m[1] = grid_depths_m[0]
        
        # Trim arrays to actual size
        grid_positions_m = grid_positions_m[:num_grid_points]
        grid_depths_m = grid_depths_m[:num_grid_points]
        
        return grid_positions_m, grid_depths_m, num_grid_points
    
    def load_from_json(self, filepath: str) -> Dict:
        """
        Load input data from JSON file.
        
        Parameters:
        -----------
        filepath : str
            Path to JSON input file
            
        Returns:
        --------
        params : Dict
            Complete parameter dictionary
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return self.load_from_dict(data)


class DataOutput:
    """
    Output data handler for coastal wave transport model.
    
    Formats and saves simulation results to various file formats
    (CSV, JSON) with proper units and documentation.
    """
    
    def __init__(self):
        """Initialize data output handler."""
        pass
    
    def format_results(
        self,
        results: Dict,
        params: Dict
    ) -> Dict:
        """
        Format simulation results for output.
        
        Parameters:
        -----------
        results : Dict
            Raw simulation results from solver
        params : Dict
            Simulation parameters
            
        Returns:
        --------
        formatted : Dict
            Formatted results with proper units and naming
        """
        num_grid_points = params['num_grid_points']
        
        # Convert angles to degrees for output
        incident_angle_deg = params['incident_angle_rad'] * 180.0 / PI
        wind_direction_deg = params['wind_direction_rad'] * 180.0 / PI
        wave_angles_deg = results['wave_angle_rad'] * 180.0 / PI
        
        # Convert RMS height to H1/3 (significant height)
        significant_heights_m = results['rms_wave_height_m'] / 0.706
        
        # Convert transport rates to m3/day
        total_transport_m3_per_day = results['total_transport_m3_per_s'] * 3600.0 * 24.0
        local_transport_m3_per_m_per_day = results['local_transport_m3_per_m_per_s'] * 3600.0 * 24.0
        
        formatted = {
            'input_parameters': {
                'wave': {
                    'significant_height_m': params['significant_height_m'],
                    'peak_period_s': params['peak_period_s'],
                    'incident_angle_deg': incident_angle_deg,
                },
                'wind': {
                    'speed_m_per_s': params['wind_speed_m_per_s'],
                    'direction_deg': wind_direction_deg,
                },
                'sediment': {
                    'density_kg_per_m3': params['sediment_density_kg_per_m3'],
                    'fall_velocity_m_per_s': params['fall_velocity_m_per_s'],
                    'friction_angle_deg': params['friction_angle_deg'],
                    'bedload_efficiency': params['bedload_efficiency'],
                    'suspended_load_efficiency': params['suspended_load_efficiency'],
                },
                'numerical': {
                    'spatial_step_m': params['spatial_step_m'],
                    'num_grid_points': num_grid_points,
                    'breaking_parameter': params['breaking_parameter_gamma'],
                },
            },
            'profile': {
                'cross_shore_distance_m': results['grid_positions_m'].tolist(),
                'bottom_depth_m': (-results['bottom_depth_m']).tolist(),  # Negative for elevation
                'water_elevation_m': results['water_elevation_m'].tolist(),
                'total_water_depth_m': results['total_water_depth_m'].tolist(),
            },
            'wave_results': {
                'angle_deg': wave_angles_deg.tolist(),
                'significant_height_m': significant_heights_m.tolist(),
                'breaking_height_m': results['breaking_wave_height_m'].tolist(),
                'breaking_fraction': results['breaking_fraction'].tolist(),
                'energy_dissipation_w_per_m2': results['energy_dissipation_w_per_m2'].tolist(),
            },
            'current_results': {
                'velocity_m_per_s': results['current_velocity_m_per_s'].tolist(),
            },
            'sediment_results': {
                'local_transport_m3_per_m_per_day': local_transport_m3_per_m_per_day.tolist(),
                'concentration': results['sediment_concentration'].tolist(),
                'total_transport_m3_per_day': total_transport_m3_per_day,
            },
        }
        
        return formatted
    
    def save_to_json(
        self,
        results: Dict,
        params: Dict,
        filepath: str
    ):
        """
        Save results to JSON file.
        
        Parameters:
        -----------
        results : Dict
            Simulation results
        params : Dict
            Simulation parameters
        filepath : str
            Output file path
        """
        formatted = self.format_results(results, params)
        
        with open(filepath, 'w') as f:
            json.dump(formatted, f, indent=2)
    
    def save_to_csv(
        self,
        results: Dict,
        params: Dict,
        filepath: str
    ):
        """
        Save results to CSV file.
        
        Parameters:
        -----------
        results : Dict
            Simulation results
        params : Dict
            Simulation parameters
        filepath : str
            Output file path
        """
        import csv
        
        num_grid_points = params['num_grid_points']
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header row with all variables
            writer.writerow([
                'X (m)',
                'Depth (m)',
                'Elevation (m)',
                'Setup (m)',
                'Angle (deg)',
                'H1/3 (m)',
                'HM (m)',
                'QB',
                'U (m/s)',
                'Q (m3/ml/day)',
                'Qss/Qtot (%)',
                'Conc',
                'ED (J/s/m3)'
            ])
            
            # Convert units
            angles_deg = results['wave_angle_rad'] * 180.0 / PI
            h13 = results['rms_wave_height_m'] / 0.706
            q_day = results['local_transport_m3_per_m_per_s'] * 3600.0 * 24.0
            
            # Write data rows
            for i in range(num_grid_points):
                # Calculate setup relative to mean sea level
                setup_m = results['water_elevation_m'][i] - params['mean_sea_level_m']
                
                # Calculate suspended load fraction as percentage of total
                if results['local_transport_m3_per_m_per_s'][i] != 0:
                    qss_fraction = (
                        results['sediment_concentration'][i] *
                        results['total_water_depth_m'][i] *
                        abs(results['current_velocity_m_per_s'][i]) /
                        results['local_transport_m3_per_m_per_s'][i] * 100.0
                    )
                else:
                    qss_fraction = 0.0
                
                writer.writerow([
                    f"{results['grid_positions_m'][i]:.2f}",
                    f"{-results['bottom_depth_m'][i]:.2f}",
                    f"{results['water_elevation_m'][i]:.4f}",
                    f"{setup_m:.4f}",
                    f"{angles_deg[i]:.2f}",
                    f"{h13[i]:.3f}",
                    f"{results['breaking_wave_height_m'][i]:.3f}",
                    f"{results['breaking_fraction'][i]:.4f}",
                    f"{results['current_velocity_m_per_s'][i]:.4f}",
                    f"{q_day[i]:.6f}",
                    f"{qss_fraction:.2f}",
                    f"{results['sediment_concentration'][i]:.6f}",
                    f"{results['energy_dissipation_w_per_m2'][i]:.6f}",
                ])
            
            # Add total transport summary
            writer.writerow([])
            writer.writerow([
                'QTOTAL (m3/day)',
                f"{results['total_transport_m3_per_s'] * 3600.0 * 24.0:.2f}"
            ])
            writer.writerow([
                'Note: Volumes are in-place (with porosity 0.3)'
            ])

