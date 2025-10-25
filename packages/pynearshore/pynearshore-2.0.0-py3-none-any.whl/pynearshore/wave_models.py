"""
Wave transformation models for nearshore zone

Implements multiple empirical and theoretical models for wave height transformation
including breaking wave height estimation and energy dissipation formulations.

Models Implemented:
-------------------
1. Depth-limited breaking (various gamma formulations)
2. Goda (1970, 1985) breaking wave height model
3. Battjes-Janssen (1978) energy dissipation
4. Thornton-Guza (1983) probabilistic breaking
5. Dally et al. (1985) decay model

References:
-----------
- Goda, Y. (1970). A synthesis of breaker indices. Trans. JSCE, 2(2), 227-230.
- Goda, Y. (1985). Random Seas and Design of Maritime Structures. 
  University of Tokyo Press.
- Battjes, J.A. and Janssen, J.P.F.M. (1978). Energy loss and set-up due to 
  breaking of random waves. Proc. 16th Coastal Eng. Conf., ASCE, 569-587.
- Thornton, E.B. and Guza, R.T. (1983). Transformation of wave height distribution.
  J. Geophys. Res., 88(C10), 5925-5938.
"""
import numpy as np
from typing import Tuple, Optional
from .physical_constants import (
    GRAVITATIONAL_ACCELERATION,
    PI,
    BREAKING_PARAMETER_DEFAULT,
    DissipationModel
)


def calculate_breaking_height_depth_limited(
    water_depth: float,
    gamma: float = BREAKING_PARAMETER_DEFAULT
) -> float:
    """
    Calculate breaking wave height using simple depth-limited criterion.
    
    The depth-limited breaking criterion states:
    H_b = γ·h
    
    where H_b is breaking wave height, h is water depth, and γ is the
    breaking parameter (typically 0.78 for beaches, range 0.4-1.2).
    
    This is the simplest breaking criterion, assuming breaking occurs when
    wave height reaches a fixed fraction of water depth.
    
    Parameters:
    -----------
    water_depth : float
        Local water depth h (m)
    gamma : float, optional
        Breaking parameter γ (dimensionless, typically 0.78)
        
    Returns:
    --------
    breaking_height : float
        Maximum wave height before breaking H_b (m)
        
    Notes:
    ------
    - γ ≈ 0.78: typical for natural beaches (Miche, 1944)
    - γ ≈ 0.40-0.50: very flat slopes
    - γ ≈ 1.0-1.2: steep slopes or structures
    - Does not account for slope, period, or nonlinearity effects
    
    References:
    -----------
    - Miche, R. (1944). Mouvements ondulatoires de la mer en profondeur 
      constante ou décroissante. Annales des Ponts et Chaussées, 114, 25-78.
    """
    return gamma * water_depth


def calculate_breaking_height_with_slope(
    water_depth: float,
    wavelength: float,
    bed_slope: float,
    gamma_max: float = 0.88,
    use_goda_formula: bool = True
) -> float:
    """
    Calculate breaking wave height accounting for bed slope effects.
    
    Implements Goda's (1970, 1985) formulation for breaking wave height:
    
    H_b = (γ_max / (2π)) · L · tanh((2πh)/(L·γ_max))
    
    where γ_max depends on bed slope and wave steepness. For small slopes:
    γ_max ≈ 0.88  (Goda's recommendation)
    
    This formulation smoothly transitions from deep water (H_b ∝ L) to
    shallow water (H_b ∝ h) breaking limits.
    
    Parameters:
    -----------
    water_depth : float
        Local water depth h (m)
    wavelength : float
        Local wavelength L (m)
    bed_slope : float
        Bottom slope s = dh/dx (dimensionless, positive for upslope)
    gamma_max : float, optional
        Maximum breaker height parameter (typically 0.88)
    use_goda_formula : bool, optional
        If True, uses Goda's hyperbolic tangent formulation
        If False, uses simple depth-limited with slope-dependent gamma
        
    Returns:
    --------
    breaking_height : float
        Breaking wave height H_b (m) accounting for slope effects
        
    Notes:
    ------
    Goda's original study analyzed 524 laboratory and field measurements
    to derive his formulation. The model accounts for:
    - Wave steepness effects (via wavelength)
    - Depth limitation (via depth)
    - Bed slope effects (via gamma_max adjustment)
    
    For detailed slope dependence, γ_max can be calculated from:
    γ_max = A · (s·L/H₀)^(1/3)
    where A ≈ 0.17-0.18 for spilling breakers, s is bed slope,
    H₀ is deep water wave height.
    
    References:
    -----------
    - Goda, Y. (1970). A synthesis of breaker indices. Transactions of JSCE, 
      2(2), 227-230.
    - Goda, Y. (2010). Random Seas and Design of Maritime Structures, 3rd ed.
      World Scientific.
    - Kaminsky, G.M. and Kraus, N.C. (1993). Evaluation of depth-limited wave 
      breaking criteria. Proc. Ocean Wave Measurement and Analysis, ASCE, 180-193.
    """
    if use_goda_formula:
        # Goda's hyperbolic tangent formulation
        # H_b = (γ_max/(2π)) · L · tanh((2π·γ_max·h)/L)
        depth_wavelength_ratio = (2.0 * PI * gamma_max * water_depth) / wavelength
        breaking_height = (gamma_max / (2.0 * PI)) * wavelength * np.tanh(depth_wavelength_ratio)
    else:
        # Simple depth-limited with slope-adjusted gamma
        # Adjust gamma based on slope (empirical)
        # γ increases with bed slope: γ ≈ γ₀(1 + α·s)
        slope_factor = 1.0 + 5.0 * bed_slope  # α ≈ 5 from laboratory studies
        gamma_effective = min(gamma_max, 0.4 + slope_factor * 0.38)
        breaking_height = gamma_effective * water_depth
    
    return breaking_height


def calculate_energy_dissipation_battjes_janssen(
    rms_wave_height_squared: float,
    breaking_wave_height: float,
    breaking_fraction: float,
    wave_period: float,
    water_density: float,
    alpha: float = 1.0,
    gravity: float = GRAVITATIONAL_ACCELERATION
) -> float:
    """
    Calculate energy dissipation rate using Battjes-Janssen (1978) model.
    
    The Battjes-Janssen model estimates wave energy dissipation as:
    
    ε_d = (α/4) · (ρg/T) · H_m² · Q_b
    
    where:
    - ε_d is energy dissipation per unit surface area (W/m²)
    - α is empirical coefficient (≈ 1.0)
    - ρ is water density (kg/m³)
    - g is gravitational acceleration (m/s²)
    - T is wave period (s)
    - H_m is maximum wave height (breaking limit) (m)
    - Q_b is fraction of breaking waves (dimensionless, 0-1)
    
    Physical interpretation: Energy loss occurs through turbulent bore
    dissipation after breaking. The model assumes a sawtooth distribution
    of individual wave heights.
    
    Parameters:
    -----------
    rms_wave_height_squared : float
        Square of root-mean-square wave height H_rms² (m²)
    breaking_wave_height : float
        Maximum wave height H_m = γh (m)
    breaking_fraction : float
        Fraction of breaking waves Q_b ∈ [0,1]
    wave_period : float
        Wave period T (s)
    water_density : float
        Water density ρ (kg/m³)
    alpha : float, optional
        Empirical coefficient α (typically 0.8-1.2, default 1.0)
    gravity : float, optional
        Gravitational acceleration g (m/s²)
        
    Returns:
    --------
    dissipation : float
        Energy dissipation rate ε_d (W/m² or J/(s·m²))
        
    Notes:
    ------
    - α = 1.0 is most commonly used
    - Model validated extensively for random wave breaking
    - Works well in surf zone but may underpredict in transition zone
    - Assumes stationary, homogeneous wave field
    
    References:
    -----------
    - Battjes, J.A. and Janssen, J.P.F.M. (1978). Energy loss and set-up due 
      to breaking of random waves. Proc. 16th Int. Conf. Coastal Eng., ASCE, 
      569-587.
    - Baldock, T.E., et al. (1998). Cross-shore hydrodynamics within an 
      unsaturated surf zone. Coastal Engineering, 34(3-4), 173-196.
    """
    dissipation = (
        (alpha / 4.0) / wave_period * 
        water_density * gravity * 
        (breaking_wave_height ** 2) * 
        breaking_fraction
    )
    
    return max(0.0, dissipation)  # Ensure non-negative


def calculate_energy_dissipation_thornton_guza(
    rms_wave_height: float,
    water_depth: float,
    wave_period: float,
    water_density: float,
    beta: float = 1.0,
    gamma: float = 0.78,
    gravity: float = GRAVITATIONAL_ACCELERATION
) -> float:
    """
    Calculate energy dissipation using Thornton-Guza (1983) model.
    
    The Thornton-Guza model is based on probabilistic wave breaking:
    
    ε_d = (3√π/16) · (ρgβ³/T) · (H_rms⁷/(γ⁴h⁵))
    
    where β is an empirical weighting coefficient (≈ 1.0).
    
    This formulation assumes waves break probabilistically based on local
    wave height distribution, with higher dissipation for larger H_rms/h ratios.
    
    Parameters:
    -----------
    rms_wave_height : float
        Root-mean-square wave height H_rms (m)
    water_depth : float
        Water depth h (m)
    wave_period : float
        Wave period T (s)
    water_density : float
        Water density ρ (kg/m³)
    beta : float, optional
        Weighting coefficient β (typically 0.8-1.2)
    gamma : float, optional
        Breaking parameter γ
    gravity : float, optional
        Gravitational acceleration g (m/s²)
        
    Returns:
    --------
    dissipation : float
        Energy dissipation rate ε_d (W/m²)
        
    Notes:
    ------
    - β typically calibrated to match measured data (0.8-1.2)
    - Model gives continuous dissipation (no abrupt breaking threshold)
    - Better for gradual bottom slopes
    - May overestimate dissipation in deep water
    
    References:
    -----------
    - Thornton, E.B. and Guza, R.T. (1983). Transformation of wave height 
      distribution. J. Geophys. Res., 88(C10), 5925-5938.
    """
    # Avoid division by zero
    if water_depth < 1e-6:
        return 0.0
    
    dissipation = (
        (3.0 * np.sqrt(PI) / 16.0) *
        water_density * gravity * (beta ** 3) / wave_period *
        (rms_wave_height ** 7) /
        ((gamma ** 4) * (water_depth ** 5))
    )
    
    return max(0.0, dissipation)


def calculate_energy_dissipation_dally(
    rms_wave_height: float,
    stable_wave_height: float,
    wave_group_velocity: float,
    decay_coefficient: float = 0.15
) -> float:
    """
    Calculate energy dissipation using Dally et al. (1985) decay model.
    
    The Dally model represents energy dissipation as exponential decay
    toward a stable wave height:
    
    dE/dx = -(Γ/h) · C_g · (E - E_stable)
    
    where Γ is a decay coefficient and E_stable corresponds to the
    equilibrium energy level in saturated surf zone.
    
    Parameters:
    -----------
    rms_wave_height : float
        Current root-mean-square wave height H_rms (m)
    stable_wave_height : float
        Stable (equilibrium) wave height H_stable = κ·h (m)
    wave_group_velocity : float
        Wave group velocity C_g (m/s)
    decay_coefficient : float, optional
        Decay coefficient Γ (typically 0.10-0.20)
        
    Returns:
    --------
    dissipation : float
        Energy dissipation rate ε_d (W/m²)
        
    References:
    -----------
    - Dally, W.R., Dean, R.G., and Dalrymple, R.A. (1985). Wave height 
      variation across beaches of arbitrary profile. J. Geophys. Res., 
      90(C6), 11917-11927.
    """
    # Wave energy per unit area
    current_energy = (1.0/8.0) * 1025.0 * 9.81 * (rms_wave_height ** 2)
    stable_energy = (1.0/8.0) * 1025.0 * 9.81 * (stable_wave_height ** 2)
    
    # Energy dissipation (only if current > stable)
    if current_energy > stable_energy:
        dissipation = decay_coefficient * wave_group_velocity * (current_energy - stable_energy)
    else:
        dissipation = 0.0
    
    return dissipation


class WaveBreakingModel:
    """
    Comprehensive wave breaking model with multiple formulations.
    
    Provides unified interface for different breaking height and
    dissipation models, allowing easy comparison and model selection.
    """
    
    def __init__(
        self,
        breaking_model: str = 'goda',
        dissipation_model: int = DissipationModel.BATTJES_JANSSEN,
        **kwargs
    ):
        """
        Initialize wave breaking model.
        
        Parameters:
        -----------
        breaking_model : str
            Breaking height model: 'depth_limited', 'goda', 'dally'
        dissipation_model : int
            Dissipation model identifier (from DissipationModel class)
        **kwargs : dict
            Model-specific parameters (gamma, alpha, beta, etc.)
        """
        self.breaking_model = breaking_model.lower()
        self.dissipation_model = dissipation_model
        self.params = kwargs
        
    def calculate_breaking_height(
        self,
        water_depth: float,
        wavelength: float,
        bed_slope: float = 0.01
    ) -> float:
        """
        Calculate breaking wave height using selected model.
        
        Parameters:
        -----------
        water_depth : float
            Water depth (m)
        wavelength : float
            Wavelength (m)
        bed_slope : float
            Bottom slope (dimensionless)
            
        Returns:
        --------
        breaking_height : float
            Breaking wave height (m)
        """
        if self.breaking_model == 'depth_limited':
            gamma = self.params.get('gamma', BREAKING_PARAMETER_DEFAULT)
            return calculate_breaking_height_depth_limited(water_depth, gamma)
        
        elif self.breaking_model == 'goda':
            gamma_max = self.params.get('gamma_max', 0.88)
            return calculate_breaking_height_with_slope(
                water_depth, wavelength, bed_slope, gamma_max, use_goda_formula=True
            )
        
        else:
            raise ValueError(f"Unknown breaking model: {self.breaking_model}")
    
    def calculate_dissipation(
        self,
        rms_wave_height: float,
        water_depth: float,
        wave_period: float,
        breaking_height: float,
        breaking_fraction: float,
        **kwargs
    ) -> float:
        """
        Calculate energy dissipation using selected model.
        
        Parameters:
        -----------
        rms_wave_height : float
            RMS wave height (m)
        water_depth : float
            Water depth (m)
        wave_period : float
            Wave period (s)
        breaking_height : float
            Breaking wave height (m)
        breaking_fraction : float
            Fraction of breaking waves
        **kwargs : dict
            Additional parameters
            
        Returns:
        --------
        dissipation : float
            Energy dissipation (W/m²)
        """
        water_density = kwargs.get('water_density', 1023.0)
        
        if self.dissipation_model == DissipationModel.BATTJES_JANSSEN:
            alpha = self.params.get('alpha', 1.0)
            return calculate_energy_dissipation_battjes_janssen(
                rms_wave_height ** 2, breaking_height, breaking_fraction,
                wave_period, water_density, alpha
            )
        
        elif self.dissipation_model == DissipationModel.THORNTON_GUZA:
            beta = self.params.get('beta', 1.0)
            gamma = self.params.get('gamma', 0.78)
            return calculate_energy_dissipation_thornton_guza(
                rms_wave_height, water_depth, wave_period,
                water_density, beta, gamma
            )
        
        else:
            raise ValueError(f"Unknown dissipation model: {self.dissipation_model}")

