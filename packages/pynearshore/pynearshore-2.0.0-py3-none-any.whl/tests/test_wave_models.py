"""
Unit tests for wave breaking and dissipation models

Tests Goda breaking model, Battjes-Janssen dissipation, and other
wave transformation models to verify correct implementation.
"""
import pytest
import numpy as np
from pynearshore.wave_models import (
    calculate_breaking_height_depth_limited,
    calculate_breaking_height_with_slope,
    calculate_energy_dissipation_battjes_janssen,
    calculate_energy_dissipation_thornton_guza,
    WaveBreakingModel
)
from coastal_wave_transport.physical_constants import (
    GRAVITATIONAL_ACCELERATION,
    PI,
    BREAKING_PARAMETER_DEFAULT,
    WATER_DENSITY
)


class TestDepthLimitedBreaking:
    """Tests for simple depth-limited breaking criterion."""
    
    def test_default_gamma(self):
        """Test breaking height with default gamma=0.78."""
        water_depth = 2.0
        
        breaking_height = calculate_breaking_height_depth_limited(water_depth)
        
        expected = 0.78 * water_depth
        assert abs(breaking_height - expected) < 1e-10
    
    def test_custom_gamma(self):
        """Test breaking height with custom gamma."""
        water_depth = 3.0
        gamma = 0.90
        
        breaking_height = calculate_breaking_height_depth_limited(
            water_depth, gamma=gamma
        )
        
        expected = gamma * water_depth
        assert abs(breaking_height - expected) < 1e-10
    
    def test_shallow_water(self):
        """Test breaking in shallow water."""
        water_depth = 0.5
        
        breaking_height = calculate_breaking_height_depth_limited(water_depth)
        
        assert breaking_height > 0
        assert breaking_height < water_depth * 1.0  # Must be less than depth
    
    def test_proportionality(self):
        """Test that breaking height scales linearly with depth."""
        gamma = 0.78
        depths = np.array([1.0, 2.0, 4.0, 8.0])
        
        breaking_heights = [
            calculate_breaking_height_depth_limited(d, gamma) 
            for d in depths
        ]
        
        # Should scale linearly
        ratios = np.array(breaking_heights) / depths
        assert np.allclose(ratios, gamma)


class TestGodaBreakingModel:
    """Tests for Goda's breaking wave height formulation."""
    
    def test_goda_vs_depth_limited(self):
        """Compare Goda model with simple depth-limited."""
        water_depth = 3.0
        wavelength = 50.0
        bed_slope = 0.01
        gamma_max = 0.88
        
        # Goda formulation
        goda_height = calculate_breaking_height_with_slope(
            water_depth, wavelength, bed_slope, gamma_max, use_goda_formula=True
        )
        
        # Simple depth-limited
        simple_height = gamma_max * water_depth
        
        # Goda should give slightly different result
        assert goda_height > 0
        # In moderate depths, should be somewhat close
        assert abs(goda_height - simple_height) / simple_height < 0.3
    
    def test_goda_shallow_water_limit(self):
        """Test that Goda model approaches depth-limited in shallow water."""
        water_depth = 1.0
        wavelength = 100.0  # Very long wavelength relative to depth
        bed_slope = 0.01
        gamma_max = 0.88
        
        goda_height = calculate_breaking_height_with_slope(
            water_depth, wavelength, bed_slope, gamma_max, use_goda_formula=True
        )
        
        depth_limited = gamma_max * water_depth
        
        # Should be close to depth-limited in shallow water
        assert abs(goda_height - depth_limited) / depth_limited < 0.10
    
    def test_goda_deep_water_characteristics(self):
        """Test Goda model behavior in deeper water."""
        water_depth = 20.0
        wavelength = 78.0  # Typical for T=7s
        bed_slope = 0.02
        gamma_max = 0.88
        
        goda_height = calculate_breaking_height_with_slope(
            water_depth, wavelength, bed_slope, gamma_max, use_goda_formula=True
        )
        
        # Should scale with wavelength in deep water
        assert goda_height > wavelength * 0.05  # At least 5% of wavelength
        assert goda_height < wavelength * 0.20  # But less than 20%
    
    def test_goda_wavelength_dependence(self):
        """Test that Goda height depends on wavelength."""
        water_depth = 5.0
        bed_slope = 0.01
        gamma_max = 0.88
        
        wavelengths = [30.0, 60.0, 90.0]
        heights = []
        
        for wl in wavelengths:
            h = calculate_breaking_height_with_slope(
                water_depth, wl, bed_slope, gamma_max, use_goda_formula=True
            )
            heights.append(h)
        
        # Height should increase with wavelength (to a point)
        assert heights[0] < heights[1]
    
    def test_goda_slope_effect(self):
        """Test effect of bed slope on breaking height."""
        water_depth = 5.0
        wavelength = 50.0
        gamma_max = 0.88
        
        # Flat slope
        h_flat = calculate_breaking_height_with_slope(
            water_depth, wavelength, 0.001, gamma_max, use_goda_formula=False
        )
        
        # Steep slope
        h_steep = calculate_breaking_height_with_slope(
            water_depth, wavelength, 0.05, gamma_max, use_goda_formula=False
        )
        
        # Steeper slopes should allow higher breaking
        assert h_steep > h_flat


class TestBattjesJanssenDissipation:
    """Tests for Battjes-Janssen energy dissipation model."""
    
    def test_zero_dissipation_no_breaking(self):
        """Test that no breaking gives zero dissipation."""
        rms_height_squared = 0.1
        breaking_height = 5.0  # Much larger than wave
        breaking_fraction = 0.0  # No breaking
        wave_period = 10.0
        
        dissipation = calculate_energy_dissipation_battjes_janssen(
            rms_height_squared, breaking_height, breaking_fraction,
            wave_period, WATER_DENSITY
        )
        
        assert dissipation == 0.0
    
    def test_positive_dissipation_with_breaking(self):
        """Test that breaking waves dissipate energy."""
        rms_height_squared = 2.0
        breaking_height = 1.5
        breaking_fraction = 0.5  # 50% breaking
        wave_period = 10.0
        
        dissipation = calculate_energy_dissipation_battjes_janssen(
            rms_height_squared, breaking_height, breaking_fraction,
            wave_period, WATER_DENSITY
        )
        
        assert dissipation > 0
    
    def test_dissipation_scales_with_qb(self):
        """Test that dissipation increases with breaking fraction."""
        rms_height_squared = 2.0
        breaking_height = 1.5
        wave_period = 10.0
        
        qb_values = [0.2, 0.5, 0.8]
        dissipations = []
        
        for qb in qb_values:
            d = calculate_energy_dissipation_battjes_janssen(
                rms_height_squared, breaking_height, qb,
                wave_period, WATER_DENSITY
            )
            dissipations.append(d)
        
        # Should increase monotonically
        assert dissipations[0] < dissipations[1] < dissipations[2]
    
    def test_dissipation_scales_with_height(self):
        """Test that dissipation scales with breaking height squared."""
        breaking_fraction = 0.5
        wave_period = 10.0
        
        heights = [1.0, 2.0, 3.0]
        dissipations = []
        
        for h in heights:
            d = calculate_energy_dissipation_battjes_janssen(
                h ** 2, h, breaking_fraction,
                wave_period, WATER_DENSITY
            )
            dissipations.append(d)
        
        # Should scale approximately as h^2
        ratio_1_to_2 = dissipations[1] / dissipations[0]
        ratio_2_to_3 = dissipations[2] / dissipations[1]
        
        # Both ratios should be similar (quadratic scaling)
        assert abs(ratio_1_to_2 / ratio_2_to_3 - 1.0) < 0.5
    
    def test_alpha_coefficient_effect(self):
        """Test effect of alpha calibration coefficient."""
        rms_height_squared = 2.0
        breaking_height = 1.5
        breaking_fraction = 0.5
        wave_period = 10.0
        
        d1 = calculate_energy_dissipation_battjes_janssen(
            rms_height_squared, breaking_height, breaking_fraction,
            wave_period, WATER_DENSITY, alpha=0.8
        )
        
        d2 = calculate_energy_dissipation_battjes_janssen(
            rms_height_squared, breaking_height, breaking_fraction,
            wave_period, WATER_DENSITY, alpha=1.2
        )
        
        # Dissipation should scale linearly with alpha
        assert d2 / d1 == pytest.approx(1.2 / 0.8, rel=1e-10)


class TestThorntonGuzaDissipation:
    """Tests for Thornton-Guza energy dissipation model."""
    
    def test_positive_dissipation(self):
        """Test that Thornton-Guza gives positive dissipation."""
        rms_height = 1.5
        water_depth = 2.0
        wave_period = 10.0
        
        dissipation = calculate_energy_dissipation_thornton_guza(
            rms_height, water_depth, wave_period, WATER_DENSITY
        )
        
        assert dissipation > 0
    
    def test_zero_dissipation_zero_height(self):
        """Test zero dissipation with zero wave height."""
        rms_height = 0.0
        water_depth = 2.0
        wave_period = 10.0
        
        dissipation = calculate_energy_dissipation_thornton_guza(
            rms_height, water_depth, wave_period, WATER_DENSITY
        )
        
        assert dissipation == 0.0
    
    def test_dissipation_very_shallow(self):
        """Test handling of very shallow water."""
        rms_height = 0.5
        water_depth = 0.001  # Very shallow
        wave_period = 5.0
        
        dissipation = calculate_energy_dissipation_thornton_guza(
            rms_height, water_depth, wave_period, WATER_DENSITY
        )
        
        # Should handle without overflow
        assert dissipation >= 0
        assert not np.isinf(dissipation)
    
    def test_dissipation_increases_with_height(self):
        """Test that dissipation increases with wave height."""
        water_depth = 3.0
        wave_period = 10.0
        
        heights = [0.5, 1.0, 1.5]
        dissipations = []
        
        for h in heights:
            d = calculate_energy_dissipation_thornton_guza(
                h, water_depth, wave_period, WATER_DENSITY
            )
            dissipations.append(d)
        
        # Should increase monotonically
        assert dissipations[0] < dissipations[1] < dissipations[2]


class TestWaveBreakingModelClass:
    """Tests for WaveBreakingModel unified interface."""
    
    def test_model_initialization_depth_limited(self):
        """Test initialization with depth-limited model."""
        model = WaveBreakingModel(
            breaking_model='depth_limited',
            dissipation_model=1,
            gamma=0.78
        )
        
        assert model.breaking_model == 'depth_limited'
        assert model.dissipation_model == 1
    
    def test_model_initialization_goda(self):
        """Test initialization with Goda model."""
        model = WaveBreakingModel(
            breaking_model='goda',
            dissipation_model=1,
            gamma_max=0.88
        )
        
        assert model.breaking_model == 'goda'
    
    def test_calculate_breaking_height_interface(self):
        """Test breaking height calculation through unified interface."""
        model = WaveBreakingModel(breaking_model='depth_limited', gamma=0.80)
        
        water_depth = 2.5
        wavelength = 40.0
        bed_slope = 0.01
        
        h_break = model.calculate_breaking_height(
            water_depth, wavelength, bed_slope
        )
        
        expected = 0.80 * water_depth
        assert abs(h_break - expected) < 1e-10
    
    def test_calculate_dissipation_interface(self):
        """Test dissipation calculation through unified interface."""
        model = WaveBreakingModel(
            breaking_model='depth_limited',
            dissipation_model=1,  # Battjes-Janssen
            alpha=1.0
        )
        
        dissipation = model.calculate_dissipation(
            rms_wave_height=1.5,
            water_depth=2.0,
            wave_period=10.0,
            breaking_height=1.6,
            breaking_fraction=0.5,
            water_density=WATER_DENSITY
        )
        
        assert dissipation > 0
    
    def test_invalid_breaking_model_raises_error(self):
        """Test that invalid model name raises error."""
        model = WaveBreakingModel(breaking_model='invalid_model')
        
        with pytest.raises(ValueError):
            model.calculate_breaking_height(2.0, 40.0, 0.01)
    
    def test_invalid_dissipation_model_raises_error(self):
        """Test that invalid dissipation model raises error."""
        model = WaveBreakingModel(
            breaking_model='depth_limited',
            dissipation_model=999  # Invalid
        )
        
        with pytest.raises(ValueError):
            model.calculate_dissipation(
                rms_wave_height=1.5,
                water_depth=2.0,
                wave_period=10.0,
                breaking_height=1.6,
                breaking_fraction=0.5
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

