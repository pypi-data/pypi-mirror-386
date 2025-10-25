"""
Current dynamics module for wave-induced and wind-induced currents

Calculates nearshore current velocities including:
- Orbital velocities from waves
- Wave-induced longshore currents
- Wind stress effects
- Bottom friction
"""
import numpy as np
from typing import Dict, Tuple
from .physical_constants import (
    PI,
    GRAVITATIONAL_ACCELERATION
)


class CurrentCalculator:
    """
    Calculator for wave-induced and wind-induced nearshore currents.
    
    Computes current velocities from balance of:
    - Radiation stress gradients (wave forcing)
    - Wind stress (surface forcing)
    - Bottom friction (dissipation)
    """
    
    def __init__(self, params: Dict):
        """
        Initialize current calculator.
        
        Parameters:
        -----------
        params : Dict
            Complete parameter dictionary
        """
        self.params = params
        self.water_density = params['water_density_kg_per_m3']
        self.air_temperature_celsius = params['air_temperature_celsius']
        self.wind_speed_m_per_s = params['wind_speed_m_per_s']
        self.wind_direction_rad = params['wind_direction_rad']
        self.bed_friction_coefficient = params['bed_friction_coefficient']
        self.num_grid_points = params['num_grid_points']
        
    def calculate_wind_stress(self) -> Tuple[float, float]:
        """
        Calculate wind stress components using Wu (1982) formulation.
        
        The wind drag coefficient varies with wind speed:
        C_D = (10.4 + 15/(1 + exp((12.5-W)/1.56))) × 10^-4
        
        Returns:
        --------
        wind_stress_x : float
            Wind stress in x-direction (N/m²)
        wind_stress_y : float
            Wind stress in y-direction (N/m²)
        """
        # Air density as function of temperature
        air_density_kg_per_m3 = 1.276 * 273.0 / (273.0 + self.air_temperature_celsius)
        
        # Wind drag coefficient - Wu (1982) formula
        c10 = (10.4 + 15.0 / (1.0 + np.exp((12.5 - self.wind_speed_m_per_s) / 1.56))) * 0.0001
        
        # Wind stress components
        wind_stress_x = c10 * air_density_kg_per_m3 * (self.wind_speed_m_per_s ** 2) * np.cos(self.wind_direction_rad)
        wind_stress_y = c10 * air_density_kg_per_m3 * (self.wind_speed_m_per_s ** 2) * np.sin(self.wind_direction_rad)
        
        return wind_stress_x, wind_stress_y
    
    def calculate_orbital_velocities(
        self,
        rms_wave_height_squared_m2: np.ndarray,
        relative_period_s: np.ndarray,
        wavelength_m: np.ndarray,
        total_water_depth_m: np.ndarray
    ) -> np.ndarray:
        """
        Calculate orbital velocity amplitudes from wave motion.
        
        Uses linear wave theory:
        u_m = π·H_rms / (T·sinh(2πh/L))
        
        Parameters:
        -----------
        rms_wave_height_squared_m2 : np.ndarray
            Square of RMS wave height (m²)
        relative_period_s : np.ndarray
            Relative wave period (s)
        wavelength_m : np.ndarray
            Local wavelength (m)
        total_water_depth_m : np.ndarray
            Total water depth (m)
            
        Returns:
        --------
        orbital_velocity_m_per_s : np.ndarray
            Orbital velocity amplitude (m/s)
        """
        n = self.num_grid_points
        orbital_velocity_m_per_s = np.zeros(n)
        
        for i in range(n):
            # Calculate orbital velocity from wave amplitude
            depth_wavelength_ratio = 2.0 * PI * total_water_depth_m[i] / wavelength_m[i]
            orbital_velocity_m_per_s[i] = (PI * np.sqrt(rms_wave_height_squared_m2[i]) /
                                          relative_period_s[i] /
                                          np.sinh(depth_wavelength_ratio))
        
        return orbital_velocity_m_per_s
    
    def calculate_longshore_currents(
        self,
        rms_wave_height_squared_m2: np.ndarray,
        wave_angle_rad: np.ndarray,
        angular_frequency_rad_per_s: np.ndarray,
        orbital_velocity_m_per_s: np.ndarray,
        energy_dissipation_w_per_m2: np.ndarray,
        wavelength_m: np.ndarray,
        wind_stress_y: float
    ) -> np.ndarray:
        """
        Calculate longshore current velocities.
        
        Solves momentum balance:
        τ_wind + τ_wave - τ_bottom = 0
        
        where:
        - τ_wind: wind stress
        - τ_wave: radiation stress gradient (wave forcing)
        - τ_bottom: bottom friction
        
        Parameters:
        -----------
        rms_wave_height_squared_m2 : np.ndarray
            Square of RMS wave height (m²)
        wave_angle_rad : np.ndarray
            Local wave angle (rad)
        angular_frequency_rad_per_s : np.ndarray
            Angular frequency (rad/s)
        orbital_velocity_m_per_s : np.ndarray
            Orbital velocity amplitude (m/s)
        energy_dissipation_w_per_m2 : np.ndarray
            Energy dissipation rate (W/m²)
        wavelength_m : np.ndarray
            Local wavelength (m)
        wind_stress_y : float
            Wind stress in longshore direction (N/m²)
            
        Returns:
        --------
        current_velocity_m_per_s : np.ndarray
            Longshore current velocity (m/s)
        """
        n = self.num_grid_points
        current_velocity_m_per_s = np.zeros(n)
        
        # Dispersion constant from Snell's law
        dispersion_constant = np.sin(wave_angle_rad[0]) / wavelength_m[0]
        
        for i in range(n):
            # Radiation stress gradient
            radiation_stress_gradient = (2.0 * PI * dispersion_constant *
                                        energy_dissipation_w_per_m2[i] /
                                        angular_frequency_rad_per_s[i])
            
            # Calculate current velocity
            if orbital_velocity_m_per_s[i] == 0.0:
                # No waves - wind-driven only
                current_velocity_m_per_s[i] = (np.sqrt(abs(wind_stress_y)) /
                                              self.water_density /
                                              self.bed_friction_coefficient)
                if np.sin(self.wind_direction_rad) < 0.0:
                    current_velocity_m_per_s[i] = -current_velocity_m_per_s[i]
            else:
                # Wave and wind forcing
                # Bottom friction: τ_b = sqrt(π)·ρ·c_f·u_m·u·(1 + sin²(θ))
                bottom_friction_coefficient = (np.sqrt(PI) * self.water_density *
                                              orbital_velocity_m_per_s[i] *
                                              self.bed_friction_coefficient / PI *
                                              (1.0 + (np.sin(wave_angle_rad[i]) ** 2)))
                
                # Solve for current: (radiation stress + wind stress) / bottom friction
                current_velocity_m_per_s[i] = ((radiation_stress_gradient + wind_stress_y) /
                                              bottom_friction_coefficient)
        
        return current_velocity_m_per_s
    
    def calculate_currents(
        self,
        rms_wave_height_squared_m2: np.ndarray,
        wave_angle_rad: np.ndarray,
        angular_frequency_rad_per_s: np.ndarray,
        relative_period_s: np.ndarray,
        total_water_depth_m: np.ndarray,
        wavelength_m: np.ndarray,
        energy_dissipation_w_per_m2: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Complete current calculation procedure.
        
        Parameters:
        -----------
        rms_wave_height_squared_m2 : np.ndarray
            Square of RMS wave height (m²)
        wave_angle_rad : np.ndarray
            Local wave angle (rad)
        angular_frequency_rad_per_s : np.ndarray
            Angular frequency (rad/s)
        relative_period_s : np.ndarray
            Relative period (s)
        total_water_depth_m : np.ndarray
            Total water depth (m)
        wavelength_m : np.ndarray
            Local wavelength (m)
        energy_dissipation_w_per_m2 : np.ndarray
            Energy dissipation rate (W/m²)
            
        Returns:
        --------
        current_velocity_m_per_s : np.ndarray
            Longshore current velocity (m/s)
        orbital_velocity_m_per_s : np.ndarray
            Orbital velocity amplitude (m/s)
        """
        # Calculate wind stress
        wind_stress_x, wind_stress_y = self.calculate_wind_stress()
        
        # Calculate orbital velocities
        orbital_velocity_m_per_s = self.calculate_orbital_velocities(
            rms_wave_height_squared_m2,
            relative_period_s,
            wavelength_m,
            total_water_depth_m
        )
        
        # Calculate longshore currents
        current_velocity_m_per_s = self.calculate_longshore_currents(
            rms_wave_height_squared_m2,
            wave_angle_rad,
            angular_frequency_rad_per_s,
            orbital_velocity_m_per_s,
            energy_dissipation_w_per_m2,
            wavelength_m,
            wind_stress_y
        )
        
        return current_velocity_m_per_s, orbital_velocity_m_per_s, wind_stress_x

