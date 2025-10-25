"""
Coastal Wave Transport Model - Nearshore Wave Propagation and Sediment Transport

This package implements a comprehensive model for coastal engineering applications:
- Wave transformation in the nearshore zone (shoaling, refraction, breaking)
- Wave-current interaction with iterative coupling
- Energy dissipation from wave breaking (Battjes-Janssen, Thornton-Guza models)
- Longshore current generation
- Sediment transport (bedload and suspended load, Bailard formulation)

Physical Models:
---------------
- Linear wave theory for wave propagation
- Battjes-Janssen (1978) or Thornton-Guza (1983) for wave breaking
- Longuet-Higgins (1970) radiation stress formulation
- Bailard (1981) energetics-based sediment transport

Numerical Methods:
------------------
- 4th-order Runge-Kutta (classical) or adaptive methods (RK45, DOP853)
- Iterative wave-current coupling
- Simpson's rule for transport integration

References:
-----------
- Battjes, J.A. and Janssen, J.P.F.M. (1978). Energy loss and set-up due to 
  breaking of random waves. Proc. 16th Int. Conf. Coastal Eng., ASCE, 569-587.
- Bailard, J.A. (1981). An energetics total load sediment transport model for 
  a plane sloping beach. Journal of Geophysical Research, 86(C11), 10938-10954.
- Thornton, E.B. and Guza, R.T. (1983). Transformation of wave height distribution. 
  Journal of Geophysical Research, 88(C10), 5925-5938.
"""

__version__ = "2.0.0"
__author__ = "Pavlishenku"

from .solver import CoastalWaveModel
from .data_io import DataInput, DataOutput

__all__ = ['CoastalWaveModel', 'DataInput', 'DataOutput']

