"""
Sediment transport module using Bailard (1981) energetics model

Calculates bedload and suspended load transport rates from
wave orbital velocities and mean currents.

Reference:
Bailard, J.A. (1981). An energetics total load sediment transport model 
for a plane sloping beach. Journal of Geophysical Research, 86(C11), 
10938-10954.
"""
import numpy as np
from typing import Dict, Tuple
from .physical_constants import (
    GRAVITATIONAL_ACCELERATION,
    SEDIMENT_POROSITY
)


def calculate_sediment_transport_bailard(
    current_velocity_m_per_s: np.ndarray,
    orbital_velocity_m_per_s: np.ndarray,
    total_water_depth_m: np.ndarray,
    params: Dict
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate sediment transport using Bailard (1981) energetics model.
    
    The Bailard model separates transport into bedload and suspended load:
    
    Bedload:
    q_b = ε_b · (ū·u_m² + ū³) / [(ρ_s - ρ)·g·(1-n)·tan(φ)]
    
    Suspended load:
    q_s = ε_s · (ū·u_m³) / [(ρ_s - ρ)·(1-n)·w_s]
    
    where:
    - ε_b, ε_s: bedload and suspended load efficiencies
    - ū: mean current velocity
    - u_m: orbital velocity amplitude
    - ρ_s, ρ: sediment and water densities
    - n: porosity
    - tan(φ): tangent of friction angle
    - w_s: sediment fall velocity
    - g: gravitational acceleration
    
    Parameters:
    -----------
    current_velocity_m_per_s : np.ndarray
        Mean longshore current velocity ū (m/s)
    orbital_velocity_m_per_s : np.ndarray
        Orbital velocity amplitude u_m (m/s)
    total_water_depth_m : np.ndarray
        Total water depth h (m)
    params : Dict
        Parameter dictionary containing:
        - bed_friction_coefficient
        - bedload_efficiency
        - suspended_load_efficiency
        - sediment_density_kg_per_m3
        - water_density_kg_per_m3
        - tan_friction_angle
        - fall_velocity_m_per_s
        - sediment_porosity
        - gravity_m_per_s2
        
    Returns:
    --------
    local_transport_m3_per_m_per_s : np.ndarray
        Local sediment transport rate q (m³/m/s, in-place volume)
    sediment_concentration : np.ndarray
        Volumetric sediment concentration C (dimensionless)
    """
    num_grid_points = params['num_grid_points']
    
    # Extract parameters
    bed_friction_coef = params['bed_friction_coefficient']
    bedload_efficiency = params['bedload_efficiency']
    suspended_load_efficiency = params['suspended_load_efficiency']
    sediment_density = params['sediment_density_kg_per_m3']
    water_density = params['water_density_kg_per_m3']
    tan_friction_angle = params['tan_friction_angle']
    fall_velocity = params['fall_velocity_m_per_s']
    porosity = params.get('sediment_porosity', SEDIMENT_POROSITY)
    gravity = params['gravity_m_per_s2']
    
    # Calculate transport coefficients
    # Bedload coefficient
    coef1_bedload = water_density * bed_friction_coef * bedload_efficiency
    
    # Suspended load coefficient
    coef4_suspended = water_density * bed_friction_coef * suspended_load_efficiency
    
    # Suspended denominator
    coef5_suspended_denom = (sediment_density - water_density) * (1.0 - porosity) * fall_velocity
    
    # Bedload denominator
    coef2_bedload_denom = (sediment_density - water_density) * gravity * (1.0 - porosity) * tan_friction_angle
    
    # Initialize output arrays
    local_transport_m3_per_m_per_s = np.zeros(num_grid_points)
    sediment_concentration = np.zeros(num_grid_points)
    
    # Calculate transport at each grid point
    for i in range(num_grid_points):
        u_current = current_velocity_m_per_s[i]
        u_orbital = orbital_velocity_m_per_s[i]
        h_total = total_water_depth_m[i]
        
        # Bedload term
        coef3_bedload_numerator = u_current * (u_orbital ** 2) + (u_current ** 3)
        
        # Suspended load term (factor 0.6 for wave asymmetry)
        coef6_suspended_numerator = u_current * (u_orbital ** 3) * 0.6
        
        # Total transport
        bedload_transport = (coef1_bedload / coef2_bedload_denom) * coef3_bedload_numerator
        suspended_load_transport = (coef4_suspended / coef5_suspended_denom) * coef6_suspended_numerator
        
        local_transport_m3_per_m_per_s[i] = bedload_transport + suspended_load_transport
        
        # Sediment concentration
        if u_current * h_total != 0.0:
            sediment_concentration[i] = (coef4_suspended / coef5_suspended_denom * 
                                        coef6_suspended_numerator / 
                                        u_current / h_total)
        else:
            sediment_concentration[i] = 0.0
    
    return local_transport_m3_per_m_per_s, sediment_concentration


def integrate_total_transport_simpson(
    local_transport_m3_per_m_per_s: np.ndarray,
    spatial_step_m: float,
    num_grid_points: int
) -> float:
    """
    Integrate local transport using Simpson's 1/3 rule.
    
    Simpson's rule for even number of intervals:
    ∫f(x)dx ≈ (Δx/3) · [f₀ + 4·Σf_odd + 2·Σf_even + f_n]
    
    Parameters:
    -----------
    local_transport_m3_per_m_per_s : np.ndarray
        Local transport rate at each grid point (m³/m/s)
    spatial_step_m : float
        Spatial step Δx (m)
    num_grid_points : int
        Number of grid points (must be even for Simpson's rule)
        
    Returns:
    --------
    total_transport_m3_per_s : float
        Integrated total transport rate Q_total (m³/s)
    """
    # Initialize sums for Simpson's rule
    sum_even_indices = 0.0
    sum_odd_indices = 0.0
    
    # Simpson's rule integration
    for i in range(2, num_grid_points, 2):
        sum_even_indices += local_transport_m3_per_m_per_s[i]
        sum_odd_indices += local_transport_m3_per_m_per_s[i - 1]
    
    # Simpson's 1/3 rule
    total_transport_m3_per_s = (
        local_transport_m3_per_m_per_s[0] +
        local_transport_m3_per_m_per_s[num_grid_points - 1] +
        4.0 * sum_odd_indices +
        2.0 * sum_even_indices
    ) * spatial_step_m / 3.0
    
    return total_transport_m3_per_s


class SedimentTransportCalculator:
    """
    Complete sediment transport calculator.
    
    Provides unified interface for calculating local and total
    sediment transport using Bailard (1981) energetics model.
    """
    
    def __init__(self, params: Dict):
        """
        Initialize sediment transport calculator.
        
        Parameters:
        -----------
        params : Dict
            Complete parameter dictionary
        """
        self.params = params
        
    def calculate_transport(
        self,
        current_velocity_m_per_s: np.ndarray,
        orbital_velocity_m_per_s: np.ndarray,
        total_water_depth_m: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Calculate local and total sediment transport.
        
        Parameters:
        -----------
        current_velocity_m_per_s : np.ndarray
            Mean current velocity (m/s)
        orbital_velocity_m_per_s : np.ndarray
            Orbital velocity amplitude (m/s)
        total_water_depth_m : np.ndarray
            Total water depth (m)
            
        Returns:
        --------
        local_transport_m3_per_m_per_s : np.ndarray
            Local transport rate (m³/m/s)
        sediment_concentration : np.ndarray
            Volumetric concentration
        total_transport_m3_per_s : float
            Total integrated transport (m³/s)
        """
        # Calculate local transport
        local_transport, concentration = calculate_sediment_transport_bailard(
            current_velocity_m_per_s,
            orbital_velocity_m_per_s,
            total_water_depth_m,
            self.params
        )
        
        # Integrate total transport
        total_transport = integrate_total_transport_simpson(
            local_transport,
            self.params['spatial_step_m'],
            self.params['num_grid_points']
        )
        
        return local_transport, concentration, total_transport

