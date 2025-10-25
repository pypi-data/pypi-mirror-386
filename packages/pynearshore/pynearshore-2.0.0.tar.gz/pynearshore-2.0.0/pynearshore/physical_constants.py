"""
Physical constants and default parameters for coastal wave transport modeling

All constants follow PEP 8 naming conventions (UPPER_CASE_WITH_UNDERSCORES)
with clear physical meanings and proper units specified.
"""
import numpy as np

# ============================================================================
# PHYSICAL CONSTANTS
# ============================================================================

# Water properties
WATER_DENSITY = 1023.0  # Seawater density (kg/m³)
AIR_DENSITY_REF = 1.276  # Reference air density at 0°C (kg/m³)
TEMPERATURE_REF = 273.0  # Reference temperature (K)

# Universal constants
GRAVITATIONAL_ACCELERATION = 9.81  # Gravitational acceleration (m/s²)
EARTH_ROTATION_RATE = 0.000072722  # Earth's angular velocity (rad/s)
PI = np.pi  # Pi constant

# Sediment properties (defaults)
SEDIMENT_POROSITY = 0.3  # Porosity of sediment bed (dimensionless, 0-1)
SEDIMENT_DENSITY_DEFAULT = 2650.0  # Quartz sand density (kg/m³)

# ============================================================================
# NUMERICAL PARAMETERS
# ============================================================================

# Convergence criteria
CONVERGENCE_TOLERANCE = 1e-4  # Relative error for iterative convergence
MAX_WAVELENGTH_ITERATIONS = 100  # Maximum iterations for wavelength calculation
MAX_WAVE_CURRENT_ITERATIONS = 20  # Maximum iterations for wave-current coupling

# Wave theory thresholds
SHALLOW_WATER_THRESHOLD = 0.1  # h/L < 0.1 defines shallow water (COL parameter)

# Array sizes
MAX_GRID_POINTS = 10000  # Maximum number of spatial grid points

# ============================================================================
# WAVE BREAKING PARAMETERS
# ============================================================================

# Breaking wave height to depth ratio (gamma)
BREAKING_PARAMETER_DEFAULT = 0.78  # Default gamma for depth-limited breaking

# Battjes-Janssen model coefficient
BATTJES_ALPHA_DEFAULT = 1.0  # Proportionality coefficient for energy dissipation

# Thornton-Guza model coefficient  
THORNTON_BETA_DEFAULT = 1.0  # Weighting coefficient for bore dissipation

# Minimum relative wave height for breaking detection
MIN_BREAKING_RATIO = 0.11  # Below Hrms/Hm < 0.11, no breaking occurs

# ============================================================================
# SEDIMENT TRANSPORT PARAMETERS
# ============================================================================

# Bailard model efficiency factors (dimensionless)
BEDLOAD_EFFICIENCY_DEFAULT = 0.1  # Epsilon_b: bedload transport efficiency
SUSPENDED_LOAD_EFFICIENCY_DEFAULT = 0.02  # Epsilon_s: suspended load efficiency

# Friction coefficients
BED_FRICTION_COEFFICIENT_DEFAULT = 0.01  # cf: bed friction coefficient

# Sediment fall velocity (depends on grain size)
FALL_VELOCITY_DEFAULT = 0.04  # ws: typical for fine sand (m/s)

# Internal friction angle
FRICTION_ANGLE_DEFAULT = 32.0  # phi: angle of repose for sand (degrees)

# ============================================================================
# WIND STRESS PARAMETERIZATION
# ============================================================================

# Wu (1982) wind drag coefficient parameters
WIND_DRAG_C1 = 10.4  # First coefficient in drag formula
WIND_DRAG_C2 = 15.0  # Second coefficient in drag formula  
WIND_DRAG_C3 = 12.5  # Transition wind speed (m/s)
WIND_DRAG_C4 = 1.56  # Transition width parameter
WIND_DRAG_SCALE = 1e-4  # Scaling factor for drag coefficient

# ============================================================================
# WAVE DISSIPATION MODEL IDENTIFIERS
# ============================================================================

class DissipationModel:
    """Enumeration of available wave breaking dissipation models"""
    BATTJES_JANSSEN = 1  # Battjes and Janssen (1978) - most widely used
    BARAILLER = 2  # Barailler variant
    THORNTON_GUZA = 3  # Thornton and Guza (1983) - probabilistic approach

# ============================================================================
# DEFAULT SIMULATION PARAMETERS
# ============================================================================

DEFAULT_SIMULATION_PARAMS = {
    # Physical constants
    'water_density': WATER_DENSITY,
    'gravity': GRAVITATIONAL_ACCELERATION,
    'earth_rotation': EARTH_ROTATION_RATE,
    'sediment_porosity': SEDIMENT_POROSITY,
    
    # Numerical parameters
    'convergence_tolerance': CONVERGENCE_TOLERANCE,
    'max_wave_current_iterations': MAX_WAVE_CURRENT_ITERATIONS,
    
    # Wave breaking
    'breaking_parameter': BREAKING_PARAMETER_DEFAULT,
    'battjes_alpha': BATTJES_ALPHA_DEFAULT,
    'dissipation_model': DissipationModel.BATTJES_JANSSEN,
    
    # Sediment transport
    'bedload_efficiency': BEDLOAD_EFFICIENCY_DEFAULT,
    'suspended_load_efficiency': SUSPENDED_LOAD_EFFICIENCY_DEFAULT,
    'bed_friction_coefficient': BED_FRICTION_COEFFICIENT_DEFAULT,
    'sediment_density': SEDIMENT_DENSITY_DEFAULT,
    'fall_velocity': FALL_VELOCITY_DEFAULT,
    'friction_angle_degrees': FRICTION_ANGLE_DEFAULT,
}

