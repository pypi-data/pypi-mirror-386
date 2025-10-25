"""
Unit tests for data_io module

Tests data loading, bathymetry discretization, and output formatting.

Author: Pavlishenku
Email: pavlishenku@gmail.com
"""
import pytest
import numpy as np
import tempfile
import json
import os
from pynearshore.data_io import DataInput, DataOutput


class TestDataInput:
    """Test suite for DataInput class"""
    
    def test_load_from_dict_basic(self):
        """Test basic data loading from dictionary"""
        data = {
            'wave': {'H13': 2.0, 'PERIOD': 10.0, 'TETAH': 15.0},
            'water': {'NIVMAR': 0.0},
            'wind': {'W': 5.0, 'TETAW': 0.0},
            'sediment': {'ROS': 2650, 'WC': 0.04, 'PHI': 32, 'EPSB': 0.1, 'EPSS': 0.02},
            'numerical': {'CF': 0.01, 'PAS': 10.0, 'GAMMA': 0.78, 'LAMBDA': 43.0},
            'bathymetry': {
                'XZ': [1000, 500, 0],
                'Z': [10, 5, 0],
            },
        }
        
        data_input = DataInput()
        params = data_input.load_from_dict(data)
        
        assert params['significant_height_m'] == 2.0
        assert params['peak_period_s'] == 10.0
        assert params['spatial_step_m'] == 10.0
        assert len(params['bathymetry_x_m']) == 3
    
    def test_load_from_dict_conversions(self):
        """Test unit conversions during loading"""
        data = {
            'wave': {'H13': 1.0, 'PERIOD': 8.0, 'TETAH': 30.0},
            'water': {'NIVMAR': 0.5},
            'wind': {'W': 10.0, 'TETAW': 45.0},
            'sediment': {'ROS': 2650, 'WC': 0.04, 'PHI': 32, 'EPSB': 0.1, 'EPSS': 0.02},
            'numerical': {'CF': 0.01, 'PAS': 5.0, 'GAMMA': 0.78, 'LAMBDA': 43.0},
            'bathymetry': {'XZ': [500, 0], 'Z': [5, 0]},
        }
        
        data_input = DataInput()
        params = data_input.load_from_dict(data)
        
        # Test angle conversions to radians
        assert np.isclose(params['incident_angle_rad'], 30 * np.pi / 180)
        assert np.isclose(params['wind_direction_rad'], 45 * np.pi / 180)
        
        # Test amplitude calculation
        assert np.isclose(params['wave_amplitude_m'], 0.706 * 1.0)
    
    def test_discretize_bathymetry_uniform(self):
        """Test bathymetry discretization on uniform slope"""
        data_input = DataInput()
        
        # Uniform 1/100 slope
        x = np.array([1000, 500, 0])
        z = np.array([10, 5, 0])
        
        grid_x, grid_z, n = data_input.discretize_bathymetry(
            x, z,
            spatial_step_m=10.0,
            mean_sea_level_m=0.0,
            peak_period_s=10.0
        )
        
        assert n > 0
        assert len(grid_x) == n
        assert len(grid_z) == n
        assert grid_x[0] == 1000  # Offshore boundary
        assert grid_x[-1] < grid_x[0]  # Decreasing
    
    def test_discretize_bathymetry_even_points(self):
        """Test that grid has even number of points (Simpson's rule)"""
        data_input = DataInput()
        
        x = np.array([2000, 1000, 500, 0])
        z = np.array([20, 10, 5, 0])
        
        _, _, n = data_input.discretize_bathymetry(
            x, z,
            spatial_step_m=20.0,
            mean_sea_level_m=0.0,
            peak_period_s=10.0
        )
        
        assert n % 2 == 0, "Number of grid points should be even"
    
    def test_discretize_bathymetry_interpolation(self):
        """Test linear interpolation of bathymetry"""
        data_input = DataInput()
        
        # Simple linear profile
        x = np.array([100, 50, 0])
        z = np.array([10, 5, 0])
        
        grid_x, grid_z, n = data_input.discretize_bathymetry(
            x, z,
            spatial_step_m=10.0,
            mean_sea_level_m=0.0,
            peak_period_s=8.0
        )
        
        # Check interpolation at midpoint
        mid_idx = np.argmin(np.abs(grid_x - 50))
        assert np.isclose(grid_z[mid_idx], 5.0, atol=0.1)
    
    def test_discretize_bathymetry_min_depth(self):
        """Test minimum depth criterion"""
        data_input = DataInput()
        
        # Profile that goes very shallow
        x = np.array([1000, 100, 10, 0])
        z = np.array([20, 2, 0.1, 0])
        
        grid_x, grid_z, n = data_input.discretize_bathymetry(
            x, z,
            spatial_step_m=5.0,
            mean_sea_level_m=0.0,
            peak_period_s=10.0
        )
        
        # Should stop before reaching zero depth
        assert grid_x[-1] > 0
    
    def test_load_from_json(self, tmp_path):
        """Test loading from JSON file"""
        data = {
            'wave': {'H13': 1.5, 'PERIOD': 9.0, 'TETAH': 10.0},
            'water': {'NIVMAR': 0.0},
            'wind': {'W': 3.0, 'TETAW': 0.0},
            'sediment': {'ROS': 2650, 'WC': 0.04, 'PHI': 32, 'EPSB': 0.1, 'EPSS': 0.02},
            'numerical': {'CF': 0.01, 'PAS': 10.0, 'GAMMA': 0.78, 'LAMBDA': 43.0},
            'bathymetry': {'XZ': [500, 0], 'Z': [10, 0]},
        }
        
        # Write to temp JSON file
        json_file = tmp_path / "test_data.json"
        with open(json_file, 'w') as f:
            json.dump(data, f)
        
        # Load from JSON
        data_input = DataInput()
        params = data_input.load_from_json(str(json_file))
        
        assert params['significant_height_m'] == 1.5
        assert params['peak_period_s'] == 9.0


class TestDataOutput:
    """Test suite for DataOutput class"""
    
    def create_mock_results(self):
        """Create mock results for testing"""
        n = 10
        return {
            'grid_positions_m': np.linspace(1000, 0, n),
            'bottom_depth_m': np.linspace(10, 0, n),
            'total_water_depth_m': np.linspace(10, 0.5, n),
            'water_elevation_m': np.zeros(n),
            'wave_angle_rad': np.linspace(0.26, 0.1, n),  # ~15 to 6 deg
            'rms_wave_height_m': np.linspace(1.5, 0.5, n),
            'breaking_wave_height_m': np.linspace(7.8, 0.4, n),
            'breaking_fraction': np.linspace(0, 0.5, n),
            'energy_dissipation_w_per_m2': np.linspace(0, 50, n),
            'current_velocity_m_per_s': np.linspace(0, 0.3, n),
            'local_transport_m3_per_m_per_s': np.linspace(0, 0.0001, n),
            'sediment_concentration': np.linspace(0, 0.001, n),
            'total_transport_m3_per_s': 0.05,
        }
    
    def create_mock_params(self):
        """Create mock parameters for testing"""
        return {
            'num_grid_points': 10,
            'significant_height_m': 2.0,
            'peak_period_s': 10.0,
            'incident_angle_rad': 0.26,
            'wind_speed_m_per_s': 5.0,
            'wind_direction_rad': 0.0,
            'sediment_density_kg_per_m3': 2650,
            'fall_velocity_m_per_s': 0.04,
            'friction_angle_deg': 32,
            'bedload_efficiency': 0.1,
            'suspended_load_efficiency': 0.02,
            'spatial_step_m': 10.0,
            'breaking_parameter_gamma': 0.78,
            'mean_sea_level_m': 0.0,
        }
    
    def test_format_results(self):
        """Test results formatting"""
        data_output = DataOutput()
        results = self.create_mock_results()
        params = self.create_mock_params()
        
        formatted = data_output.format_results(results, params)
        
        assert 'input_parameters' in formatted
        assert 'wave_results' in formatted
        assert 'current_results' in formatted
        assert 'sediment_results' in formatted
    
    def test_save_to_json(self, tmp_path):
        """Test saving results to JSON"""
        data_output = DataOutput()
        results = self.create_mock_results()
        params = self.create_mock_params()
        
        json_file = tmp_path / "results.json"
        data_output.save_to_json(results, params, str(json_file))
        
        assert json_file.exists()
        
        # Verify contents
        with open(json_file, 'r') as f:
            loaded = json.load(f)
        
        assert 'input_parameters' in loaded
        assert 'wave_results' in loaded
    
    def test_save_to_csv(self, tmp_path):
        """Test saving results to CSV"""
        data_output = DataOutput()
        results = self.create_mock_results()
        params = self.create_mock_params()
        
        csv_file = tmp_path / "results.csv"
        data_output.save_to_csv(results, params, str(csv_file))
        
        assert csv_file.exists()
        
        # Verify CSV has header and data
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) > 10  # Header + data rows
        assert 'X (m)' in lines[0]  # Check header
        assert 'QTOTAL' in ''.join(lines)  # Check summary


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

