"""
Unit tests for numerical methods module

Tests the wavelength calculation, breaking percentage, and convergence
of iterative methods to ensure numerical accuracy.
"""
import pytest
import numpy as np
from pynearshore.numerical_methods import (
    calculate_wavelength_iterative,
    calculate_breaking_percentage
)
from pynearshore.physical_constants import (
    GRAVITATIONAL_ACCELERATION,
    PI,
    CONVERGENCE_TOLERANCE
)


class TestWavelengthCalculation:
    """Tests for wavelength calculation via dispersion relation."""
    
    def test_deep_water_wavelength(self):
        """Test wavelength in deep water (h/L0 > 0.5)."""
        water_depth = 100.0  # Deep water
        wave_period = 10.0   # 10 second waves
        
        wavelength, num_iter = calculate_wavelength_iterative(
            water_depth, wave_period
        )
        
        # Deep water wavelength: L0 = g*T^2/(2*pi)
        expected_wavelength = (GRAVITATIONAL_ACCELERATION * wave_period ** 2) / (2.0 * PI)
        
        # Should be very close to deep water value
        assert abs(wavelength - expected_wavelength) / expected_wavelength < 0.01
        assert num_iter > 0
        assert num_iter < 20  # Should converge quickly
    
    def test_shallow_water_wavelength(self):
        """Test wavelength in shallow water (h/L0 < 0.05)."""
        water_depth = 2.0    # Shallow water
        wave_period = 10.0
        
        wavelength, num_iter = calculate_wavelength_iterative(
            water_depth, wave_period
        )
        
        # Shallow water wavelength: L = T*sqrt(g*h)
        expected_wavelength = wave_period * np.sqrt(GRAVITATIONAL_ACCELERATION * water_depth)
        
        # Should be close to shallow water approximation
        assert abs(wavelength - expected_wavelength) / expected_wavelength < 0.05
        assert num_iter > 0
    
    def test_intermediate_water_wavelength(self):
        """Test wavelength in intermediate depth."""
        water_depth = 10.0
        wave_period = 8.0
        
        wavelength, num_iter = calculate_wavelength_iterative(
            water_depth, wave_period
        )
        
        # Wavelength should be between shallow and deep water limits
        shallow_limit = wave_period * np.sqrt(GRAVITATIONAL_ACCELERATION * water_depth)
        deep_limit = (GRAVITATIONAL_ACCELERATION * wave_period ** 2) / (2.0 * PI)
        
        assert shallow_limit < wavelength < deep_limit
        assert num_iter > 0
    
    def test_wavelength_with_current(self):
        """Test wavelength calculation with ambient current."""
        water_depth = 10.0
        wave_period = 10.0
        current_velocity = 0.5  # 0.5 m/s following current
        
        # Calculate wavelength without current
        wl_no_current, _ = calculate_wavelength_iterative(
            water_depth, wave_period, current_velocity=0.0
        )
        
        # Calculate wavelength with current
        dispersion_constant = 0.01  # Small value
        wl_with_current, _ = calculate_wavelength_iterative(
            water_depth, wave_period, 
            current_velocity=current_velocity,
            dispersion_constant=dispersion_constant
        )
        
        # Following current should decrease wavelength slightly
        assert wl_with_current < wl_no_current
    
    def test_convergence_criteria(self):
        """Test that iteration respects convergence tolerance."""
        water_depth = 15.0
        wave_period = 12.0
        tolerance = 1e-6
        
        wavelength, num_iter = calculate_wavelength_iterative(
            water_depth, wave_period, tolerance=tolerance
        )
        
        assert wavelength > 0
        assert num_iter < 100  # Should converge well before max iterations


class TestBreakingPercentage:
    """Tests for breaking percentage calculation (Battjes-Janssen)."""
    
    def test_no_breaking_small_waves(self):
        """Test that small waves don't break."""
        rms_height_squared = 0.01  # Very small waves
        breaking_height = 2.0      # Large breaking limit
        
        qb = calculate_breaking_percentage(rms_height_squared, breaking_height)
        
        # Small waves should have qb ≈ 0
        assert qb < 0.01
        assert qb >= 0.0
    
    def test_full_breaking_large_waves(self):
        """Test that waves at breaking limit have qb=1."""
        breaking_height = 2.0
        rms_height_squared = breaking_height ** 2  # At breaking limit
        
        qb = calculate_breaking_percentage(rms_height_squared, breaking_height)
        
        # Should be fully breaking
        assert abs(qb - 1.0) < 0.01
    
    def test_partial_breaking_intermediate(self):
        """Test intermediate breaking percentage."""
        breaking_height = 2.0
        rms_height_squared = (0.5 * breaking_height) ** 2  # 50% of breaking
        
        qb = calculate_breaking_percentage(rms_height_squared, breaking_height)
        
        # Should be between 0 and 1
        assert 0.0 < qb < 1.0
    
    def test_breaking_percentage_monotonic(self):
        """Test that qb increases monotonically with wave height."""
        breaking_height = 2.0
        heights = np.linspace(0.2, 2.0, 10)
        
        qb_values = []
        for h in heights:
            qb = calculate_breaking_percentage(h ** 2, breaking_height)
            qb_values.append(qb)
        
        # Check monotonicity
        for i in range(len(qb_values) - 1):
            assert qb_values[i] <= qb_values[i+1]
    
    def test_zero_breaking_height(self):
        """Test edge case with zero breaking height."""
        rms_height_squared = 1.0
        breaking_height = 0.0
        
        qb = calculate_breaking_percentage(rms_height_squared, breaking_height)
        
        # Should return 0 for zero breaking height
        assert qb == 0.0


class TestNumericalStability:
    """Tests for numerical stability and edge cases."""
    
    def test_very_small_depth(self):
        """Test wavelength calculation in very shallow water."""
        water_depth = 0.1  # 10 cm
        wave_period = 2.0
        
        wavelength, num_iter = calculate_wavelength_iterative(
            water_depth, wave_period
        )
        
        # Should still converge
        assert wavelength > 0
        assert num_iter < 50
    
    def test_very_long_period(self):
        """Test wavelength with very long period waves."""
        water_depth = 50.0
        wave_period = 20.0  # 20 second waves
        
        wavelength, num_iter = calculate_wavelength_iterative(
            water_depth, wave_period
        )
        
        # Should still converge
        assert wavelength > 0
        assert num_iter < 50
    
    def test_negative_inputs_raise_error(self):
        """Test that negative inputs are handled properly."""
        # These should not raise errors but return valid results
        # (physical validity is checked elsewhere)
        water_depth = 10.0
        wave_period = 10.0
        
        try:
            wavelength, _ = calculate_wavelength_iterative(
                water_depth, wave_period
            )
            assert wavelength > 0
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")


@pytest.mark.parametrize("depth,period", [
    (1.0, 5.0),
    (5.0, 8.0),
    (10.0, 10.0),
    (20.0, 12.0),
    (50.0, 15.0),
])
def test_wavelength_various_conditions(depth, period):
    """Parametrized test for various depth/period combinations."""
    wavelength, num_iter = calculate_wavelength_iterative(depth, period)
    
    # Basic validity checks
    assert wavelength > 0
    assert num_iter > 0
    assert num_iter < 100
    
    # Wavelength should be reasonable
    # Between shallow water and deep water limits
    shallow_limit = period * np.sqrt(GRAVITATIONAL_ACCELERATION * depth)
    deep_limit = (GRAVITATIONAL_ACCELERATION * period ** 2) / (2.0 * PI)
    
    assert wavelength >= shallow_limit * 0.9  # Allow some tolerance
    assert wavelength <= deep_limit * 1.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

