# PyNearshore

Python package for nearshore wave propagation, currents, and sediment transport modeling.

## Features

- Wave propagation with refraction, shoaling, and breaking
- Wave-induced nearshore currents
- Sediment transport (Bailard 1981 energetics model)
- Multiple breaking models (Goda, depth-limited)
- Energy dissipation (Battjes-Janssen, Thornton-Guza)
- Adaptive numerical solvers (RK4, RK45, DOP853)

## Installation

```bash
pip install pynearshore
```

Or from source:
```bash
git clone https://github.com/pavlishenku/pynearshore.git
cd pynearshore
pip install -e .
```

## Quick Start

```python
from pynearshore import CoastalWaveModel

# Create model
model = CoastalWaveModel()

# Define conditions
data = {
    'wave': {'H13': 2.0, 'PERIOD': 10.0, 'TETAH': 15.0},
    'water': {'NIVMAR': 0.0},
    'wind': {'W': 5.0, 'TETAW': 0.0},
    'sediment': {'ROS': 2650, 'WC': 0.04, 'PHI': 32, 'EPSB': 0.1, 'EPSS': 0.02},
    'numerical': {'CF': 0.01, 'PAS': 10.0, 'GAMMA': 0.78, 'LAMBDA': 43.0},
    'bathymetry': {
        'XZ': [2000, 1000, 500, 0],
        'Z': [20, 10, 5, 0],
    },
}

# Run simulation
params = model.load_data(data)
results = model.solve()

# Save results
model.save_results('results.csv')

# Print transport
print(f"Sediment transport: {results['total_transport_m3_per_s'] * 86400:.1f} m³/day")
```

## Physical Models

### Wave Transformation
- Linear wave theory with currents
- Snell's law refraction
- Shoaling on variable bathymetry
- Breaking: Goda (1970, 1985) or depth-limited

### Energy Dissipation
- Battjes & Janssen (1978) - Wave breaking
- Thornton & Guza (1983) - Probabilistic breaking
- Barailler - Gradual slopes

### Currents
- Orbital velocities (linear theory)
- Longshore currents (radiation stress)
- Wind stress (Wu 1982)
- Bottom friction
- Coriolis force

### Sediment Transport
- Bailard (1981) energetics model
- Bedload and suspended load
- Integration via Simpson's rule

## Requirements

- Python >= 3.7
- numpy >= 1.19.0
- scipy >= 1.5.0

## Testing

```bash
pytest tests/ -v
```

## Examples

See `examples/` directory:
- `example_basic_usage.py` - Simple simulation
- `example_solver_comparison.py` - Compare numerical solvers
- `test_complete_implementation.py` - Full validation

## Documentation

### Input Parameters

**Wave**:
- `H13`: Significant wave height (m)
- `PERIOD`: Peak wave period (s)
- `TETAH`: Incident angle (degrees)

**Bathymetry**:
- `XZ`: Cross-shore distances (m, decreasing)
- `Z`: Water depths (m, positive)

**Sediment**:
- `ROS`: Sediment density (kg/m³, ~2650 for sand)
- `WC`: Fall velocity (m/s, ~0.04 for fine sand)
- `PHI`: Friction angle (degrees, ~32 for sand)
- `EPSB`: Bedload efficiency (0.05-0.15)
- `EPSS`: Suspended load efficiency (0.01-0.03)

**Numerical**:
- `PAS`: Spatial step (m, 5-20)
- `GAMMA`: Breaking parameter (0.78 default)
- `CF`: Bottom friction (0.005-0.02)

### Output

Results dictionary contains:
- `rms_wave_height_m`: Wave heights
- `wave_angle_deg`: Wave angles
- `current_velocity_m_per_s`: Currents
- `water_elevation_m`: Setup/setdown
- `local_transport_m3_per_m_per_s`: Local sediment transport
- `total_transport_m3_per_s`: Total transport

## Citation

If you use this software, please cite:

```
Pavlishenku (2025). PyNearshore: A Python package for nearshore 
wave propagation and sediment transport modeling.
GitHub: https://github.com/pavlishenku/pynearshore
```

## Scientific References

- Battjes, J.A., & Janssen, J.P.F.M. (1978). Energy loss and set-up due to breaking of random waves.
- Goda, Y. (1970). A synthesis of breaker indices.
- Thornton, E.B., & Guza, R.T. (1983). Transformation of wave height distribution.
- Bailard, J.A. (1981). An energetics total load sediment transport model.
- Longuet-Higgins, M.S., & Stewart, R.W. (1964). Radiation stresses in water waves.
- Wu, J. (1982). Wind-stress coefficients over sea surface.

## License

MIT License - see LICENSE file

## Author

**Pavlishenku**  
Email: pavlishenku@gmail.com

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Support

- Issues: GitHub issue tracker
- Email: pavlishenku@gmail.com
