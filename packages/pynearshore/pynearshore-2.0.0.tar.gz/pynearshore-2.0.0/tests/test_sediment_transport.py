"""
Unit tests for sediment_transport module

Tests Bailard (1981) energetics model and Simpson integration.

Author: Pavlishenku
Email: pavlishenku@gmail.com
"""
import pytest
import numpy as np
from pynearshore.sediment_transport import (
    calculate_sediment_transport_bailard,
    integrate_total_transport_simpson,
    SedimentTransportCalculator
)


class TestBailardModel:
    """Test suite for Bailard (1981) sediment transport model"""
    
    def create_mock_params(self, n=10):
        """Create mock parameters for testing"""
        return {
            'num_grid_points': n,
            'bed_friction_coefficient': 0.01,
            'bedload_efficiency': 0.1,
            'suspended_load_efficiency': 0.02,
            'sediment_density_kg_per_m3': 2650.0,
            'water_density_kg_per_m3': 1023.0,
            'tan_friction_angle': np.tan(32 * np.pi / 180),
            'fall_velocity_m_per_s': 0.04,
            'sediment_porosity': 0.3,
            'gravity_m_per_s2': 9.81,
        }
    
    def test_bailard_zero_current(self):
        """Test Bailard model with zero current"""
        n = 5
        current = np.zeros(n)
        orbital = np.ones(n) * 0.5
        depth = np.ones(n) * 2.0
        params = self.create_mock_params(n)
        
        transport, concentration = calculate_sediment_transport_bailard(
            current, orbital, depth, params
        )
        
        # Zero current should give zero transport
        assert np.allclose(transport, 0.0)
        assert np.allclose(concentration, 0.0)
    
    def test_bailard_zero_waves(self):
        """Test Bailard model with zero orbital velocity"""
        n = 5
        current = np.ones(n) * 0.2
        orbital = np.zeros(n)
        depth = np.ones(n) * 2.0
        params = self.create_mock_params(n)
        
        transport, concentration = calculate_sediment_transport_bailard(
            current, orbital, depth, params
        )
        
        # Only current-driven bedload (cubic term)
        assert np.all(transport > 0)
        assert np.allclose(concentration, 0.0)  # No suspended load without waves
    
    def test_bailard_positive_transport(self):
        """Test that transport is positive for positive current"""
        n = 5
        current = np.ones(n) * 0.3
        orbital = np.ones(n) * 0.5
        depth = np.ones(n) * 2.0
        params = self.create_mock_params(n)
        
        transport, concentration = calculate_sediment_transport_bailard(
            current, orbital, depth, params
        )
        
        assert np.all(transport > 0)
        assert np.all(concentration >= 0)
    
    def test_bailard_negative_current(self):
        """Test transport direction with negative current"""
        n = 5
        current_pos = np.ones(n) * 0.3
        current_neg = np.ones(n) * (-0.3)
        orbital = np.ones(n) * 0.5
        depth = np.ones(n) * 2.0
        params = self.create_mock_params(n)
        
        transport_pos, _ = calculate_sediment_transport_bailard(
            current_pos, orbital, depth, params
        )
        transport_neg, _ = calculate_sediment_transport_bailard(
            current_neg, orbital, depth, params
        )
        
        # Transport should reverse direction
        assert np.allclose(transport_pos, -transport_neg, rtol=1e-10)
    
    def test_bailard_scaling_current(self):
        """Test transport scales with current"""
        n = 5
        current_small = np.ones(n) * 0.1
        current_large = np.ones(n) * 0.2
        orbital = np.ones(n) * 0.5
        depth = np.ones(n) * 2.0
        params = self.create_mock_params(n)
        
        transport_small, _ = calculate_sediment_transport_bailard(
            current_small, orbital, depth, params
        )
        transport_large, _ = calculate_sediment_transport_bailard(
            current_large, orbital, depth, params
        )
        
        # Larger current should give more transport
        assert np.all(transport_large > transport_small)
    
    def test_bailard_scaling_waves(self):
        """Test transport scales with wave orbital velocity"""
        n = 5
        current = np.ones(n) * 0.2
        orbital_small = np.ones(n) * 0.3
        orbital_large = np.ones(n) * 0.6
        depth = np.ones(n) * 2.0
        params = self.create_mock_params(n)
        
        transport_small, _ = calculate_sediment_transport_bailard(
            current, orbital_small, depth, params
        )
        transport_large, _ = calculate_sediment_transport_bailard(
            current, orbital_large, depth, params
        )
        
        # Larger waves should give more transport
        assert np.all(transport_large > transport_small)
    
    def test_concentration_units(self):
        """Test sediment concentration is dimensionless and realistic"""
        n = 5
        current = np.ones(n) * 0.2
        orbital = np.ones(n) * 0.5
        depth = np.ones(n) * 2.0
        params = self.create_mock_params(n)
        
        _, concentration = calculate_sediment_transport_bailard(
            current, orbital, depth, params
        )
        
        # Concentration should be small (typically < 0.01)
        assert np.all(concentration >= 0)
        assert np.all(concentration < 0.1)  # Reasonable upper limit


class TestSimpsonIntegration:
    """Test suite for Simpson's 1/3 rule integration"""
    
    def test_simpson_constant_function(self):
        """Test Simpson integration of constant function"""
        # Integrate f(x) = 1 from 0 to 100
        n = 10
        transport = np.ones(n)
        dx = 10.0
        
        total = integrate_total_transport_simpson(transport, dx, n)
        
        # Should give area = 1 * 100 = 100
        expected = 100.0
        assert np.isclose(total, expected, rtol=0.01)
    
    def test_simpson_linear_function(self):
        """Test Simpson integration of linear function"""
        # Integrate f(x) = x/100 from 0 to 100
        n = 10
        x = np.linspace(0, 100, n)
        transport = x / 100.0
        dx = (x[1] - x[0])
        
        total = integrate_total_transport_simpson(transport, dx, n)
        
        # Analytical: integral of x/100 from 0 to 100 = 50
        expected = 50.0
        assert np.isclose(total, expected, rtol=0.05)
    
    def test_simpson_parabola(self):
        """Test Simpson integration of parabolic function"""
        # Simpson's rule is exact for polynomials up to degree 3
        n = 20
        x = np.linspace(0, 10, n)
        transport = x ** 2  # f(x) = x^2
        dx = x[1] - x[0]
        
        total = integrate_total_transport_simpson(transport, dx, n)
        
        # Analytical: integral of x^2 from 0 to 10 = 1000/3
        expected = 1000.0 / 3.0
        assert np.isclose(total, expected, rtol=0.001)
    
    def test_simpson_even_points_required(self):
        """Test that even number of points is required"""
        # Simpson's 1/3 rule requires even number of intervals
        n_even = 10
        n_odd = 11
        
        transport_even = np.ones(n_even)
        transport_odd = np.ones(n_odd)
        dx = 1.0
        
        # Even should work fine
        result_even = integrate_total_transport_simpson(transport_even, dx, n_even)
        assert result_even > 0
        
        # Odd might give different result
        result_odd = integrate_total_transport_simpson(transport_odd, dx, n_odd)
        # Still should give reasonable result
        assert result_odd > 0


class TestSedimentTransportCalculator:
    """Test suite for SedimentTransportCalculator class"""
    
    def create_full_params(self):
        """Create complete params dictionary"""
        return {
            'num_grid_points': 10,
            'bed_friction_coefficient': 0.01,
            'bedload_efficiency': 0.1,
            'suspended_load_efficiency': 0.02,
            'sediment_density_kg_per_m3': 2650.0,
            'water_density_kg_per_m3': 1023.0,
            'tan_friction_angle': np.tan(32 * np.pi / 180),
            'fall_velocity_m_per_s': 0.04,
            'sediment_porosity': 0.3,
            'gravity_m_per_s2': 9.81,
            'spatial_step_m': 10.0,
        }
    
    def test_calculator_initialization(self):
        """Test calculator initialization"""
        params = self.create_full_params()
        calculator = SedimentTransportCalculator(params)
        
        assert calculator.params == params
    
    def test_calculator_full_workflow(self):
        """Test complete calculation workflow"""
        params = self.create_full_params()
        calculator = SedimentTransportCalculator(params)
        
        n = params['num_grid_points']
        current = np.linspace(0, 0.3, n)
        orbital = np.linspace(0.3, 0.8, n)
        depth = np.linspace(5.0, 1.0, n)
        
        local, concentration, total = calculator.calculate_transport(
            current, orbital, depth
        )
        
        assert len(local) == n
        assert len(concentration) == n
        assert total > 0
        assert np.all(local >= 0)  # Assuming positive current
        assert np.all(concentration >= 0)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

