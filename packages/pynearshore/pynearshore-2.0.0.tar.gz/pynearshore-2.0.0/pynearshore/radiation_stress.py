"""
Radiation stress and water level elevation module

Calculates wave setup/setdown from radiation stress gradients,
wind stress, and Coriolis effects.

Based on Longuet-Higgins and Stewart (1964) radiation stress theory.
"""
import numpy as np
from typing import Dict, Tuple
from .physical_constants import (
    PI,
    GRAVITATIONAL_ACCELERATION
)


def calculate_water_level_elevation(
    current_velocity_m_per_s: np.ndarray,
    cos_wave_angle: np.ndarray,
    wavelength_m: np.ndarray,
    rms_wave_height_squared_m2: np.ndarray,
    total_water_depth_m: np.ndarray,
    bottom_depth_m: np.ndarray,
    wind_stress_x: float,
    params: Dict
) -> np.ndarray:
    """
    Calculate water level elevation from radiation stress balance.
    
    Solves the momentum equation:
    dη/dx = (1/ρgh) · (dS_xx/dx + τ_wind_x + F_Coriolis)
    
    where:
    - η: water surface elevation
    - S_xx: radiation stress component
    - τ_wind_x: wind stress in cross-shore direction
    - F_Coriolis: Coriolis force
    
    Parameters:
    -----------
    current_velocity_m_per_s : np.ndarray
        Longshore current velocity (m/s)
    cos_wave_angle : np.ndarray
        Cosine of wave angle
    wavelength_m : np.ndarray
        Local wavelength (m)
    rms_wave_height_squared_m2 : np.ndarray
        Square of RMS wave height (m²)
    total_water_depth_m : np.ndarray
        Total water depth h = d + η (m)
    bottom_depth_m : np.ndarray
        Bottom depth d relative to datum (m)
    wind_stress_x : float
        Wind stress in cross-shore direction (N/m²)
    params : Dict
        Parameter dictionary containing spatial_step_m, water_density,
        earth_rotation, latitude, etc.
        
    Returns:
    --------
    water_elevation_m : np.ndarray
        Water surface elevation η relative to datum (m)
    """
    num_grid_points = params['num_grid_points']
    spatial_step_m = params['spatial_step_m']
    water_density = params['water_density_kg_per_m3']
    earth_rotation_rad_per_s = params['earth_rotation_rad_per_s']
    latitude_rad = params['latitude_rad']
    gravity = params['gravity_m_per_s2']
    
    # Initialize elevation array
    water_elevation_m = np.zeros(num_grid_points)
    
    # Set initial elevation at offshore boundary
    water_elevation_m[0] = params['mean_sea_level_m']
    
    # Coriolis parameter
    coriolis_parameter = 2.0 * earth_rotation_rad_per_s * np.sin(latitude_rad)
    
    # Calculate elevation at each grid point
    for i in range(num_grid_points - 1):
        # Coriolis force
        coriolis_force = water_density * coriolis_parameter * current_velocity_m_per_s[i] * total_water_depth_m[i]
        
        # Radiation stress at current point
        depth_wavelength_ratio_i = 4.0 * PI * total_water_depth_m[i] / wavelength_m[i]
        c1 = depth_wavelength_ratio_i / np.sinh(depth_wavelength_ratio_i)
        
        # Radiation stress at next point
        depth_wavelength_ratio_ip1 = 4.0 * PI * total_water_depth_m[i+1] / wavelength_m[i+1]
        c2 = depth_wavelength_ratio_ip1 / np.sinh(depth_wavelength_ratio_ip1)
        
        # Radiation stress S_xx components
        # S_xx = (ρg/16) · H_rms² · [(1+C)(1+cos²θ) - 1]
        sxx_i = (water_density * gravity / 16.0 * rms_wave_height_squared_m2[i] *
                ((1.0 + c1) * (1.0 + (cos_wave_angle[i] ** 2)) - 1.0))
        
        sxx_ip1 = (water_density * gravity / 16.0 * rms_wave_height_squared_m2[i+1] *
                  ((1.0 + c2) * (1.0 + (cos_wave_angle[i+1] ** 2)) - 1.0))
        
        # Radiation stress gradient
        radiation_stress_gradient = (sxx_i - sxx_ip1) / spatial_step_m
        
        # Water level elevation at next point
        water_elevation_m[i+1] = (water_elevation_m[i] +
                                  spatial_step_m / water_density / gravity / total_water_depth_m[i] *
                                  (radiation_stress_gradient + wind_stress_x + coriolis_force))
    
    return water_elevation_m


def update_water_depth(
    bottom_depth_m: np.ndarray,
    water_elevation_m: np.ndarray
) -> np.ndarray:
    """
    Update total water depth from bottom depth and elevation.
    
    Parameters:
    -----------
    bottom_depth_m : np.ndarray
        Bottom depth relative to datum (m, positive downward)
    water_elevation_m : np.ndarray
        Water surface elevation relative to datum (m)
        
    Returns:
    --------
    total_water_depth_m : np.ndarray
        Total water depth h = d + η (m)
    """
    # Calculate total depth: h = d + η
    total_water_depth_m = bottom_depth_m + water_elevation_m
    
    return total_water_depth_m


class RadiationStressCalculator:
    """
    Complete radiation stress and water elevation calculator.
    
    Provides unified interface for wave setup/setdown calculations
    including all forcing terms and depth updates.
    """
    
    def __init__(self, params: Dict):
        """
        Initialize radiation stress calculator.
        
        Parameters:
        -----------
        params : Dict
            Complete parameter dictionary
        """
        self.params = params
        
    def calculate_elevation_and_update_depth(
        self,
        current_velocity_m_per_s: np.ndarray,
        cos_wave_angle: np.ndarray,
        wavelength_m: np.ndarray,
        rms_wave_height_squared_m2: np.ndarray,
        total_water_depth_m: np.ndarray,
        bottom_depth_m: np.ndarray,
        wind_stress_x: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate water elevation and update total depth.
        
        Parameters:
        -----------
        current_velocity_m_per_s : np.ndarray
            Longshore current velocity (m/s)
        cos_wave_angle : np.ndarray
            Cosine of wave angle
        wavelength_m : np.ndarray
            Local wavelength (m)
        rms_wave_height_squared_m2 : np.ndarray
            Square of RMS wave height (m²)
        total_water_depth_m : np.ndarray
            Current total water depth (m)
        bottom_depth_m : np.ndarray
            Bottom depth (m)
        wind_stress_x : float
            Wind stress in x-direction (N/m²)
            
        Returns:
        --------
        water_elevation_m : np.ndarray
            Updated water surface elevation (m)
        updated_total_depth_m : np.ndarray
            Updated total water depth (m)
        """
        # Calculate elevation
        water_elevation_m = calculate_water_level_elevation(
            current_velocity_m_per_s,
            cos_wave_angle,
            wavelength_m,
            rms_wave_height_squared_m2,
            total_water_depth_m,
            bottom_depth_m,
            wind_stress_x,
            self.params
        )
        
        # Update total depth
        updated_total_depth_m = update_water_depth(
            bottom_depth_m,
            water_elevation_m
        )
        
        return water_elevation_m, updated_total_depth_m

