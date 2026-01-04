"""
Unit Tests for Aviation Crash Analytics Dashboard
Tests for data loading, processing, and utility functions
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_utils import (
    DataLoader,
    DataLoadError,
    DataValidationError,
    safe_divide,
    safe_percentage,
    validate_dataframe,
    create_sample_dataset
)


class TestDataLoader:
    """Tests for DataLoader class."""
    
    def test_initialization(self):
        """Test DataLoader initialization."""
        loader = DataLoader()
        assert loader is not None
        assert loader._cache == {}
    
    def test_validate_dataset_empty(self):
        """Test validation of empty dataset."""
        loader = DataLoader()
        df = pd.DataFrame()
        
        is_valid, errors = loader.validate_dataset(df)
        
        assert not is_valid
        assert "Dataset is empty" in errors
    
    def test_validate_dataset_missing_columns(self):
        """Test validation with missing required columns."""
        loader = DataLoader()
        df = pd.DataFrame({'A': [1, 2, 3]})
        required_columns = ['A', 'B', 'C']
        
        is_valid, errors = loader.validate_dataset(df, required_columns)
        
        assert not is_valid
        assert any('Missing required columns' in error for error in errors)
    
    def test_validate_dataset_valid(self):
        """Test validation of valid dataset."""
        loader = DataLoader()
        df = pd.DataFrame({
            'Date': ['2020-01-01', '2020-01-02'],
            'Location': ['Location A', 'Location B'],
            'Fatalities': [10, 20]
        })
        required_columns = ['Date', 'Location', 'Fatalities']
        
        is_valid, errors = loader.validate_dataset(df, required_columns)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_clean_dataset(self):
        """Test dataset cleaning."""
        loader = DataLoader()
        df = pd.DataFrame({
            'Date': ['2020-01-01', '2020-01-02', '2020-01-01'],  # Duplicate
            'Fatalities': ['10', '20', '10'],  # String numbers
            'Aboard': ['100', '200', '100']
        })
        
        df_clean = loader.clean_dataset(df)
        
        # Check duplicates removed
        assert len(df_clean) == 2
        
        # Check numeric conversion
        assert pd.api.types.is_numeric_dtype(df_clean['Fatalities'])
        assert pd.api.types.is_numeric_dtype(df_clean['Aboard'])
        
        # Check derived columns
        assert 'Year' in df_clean.columns
        assert 'Month' in df_clean.columns
        assert 'Survivors' in df_clean.columns
        assert 'SurvivalRate' in df_clean.columns
    
    def test_optimize_memory(self):
        """Test memory optimization."""
        loader = DataLoader()
        df = pd.DataFrame({
            'SmallInt': np.arange(100, dtype=np.int64),
            'LargeFloat': np.random.random(100).astype(np.float64)
        })
        
        initial_memory = df.memory_usage(deep=True).sum()
        df_opt = loader.optimize_memory(df)
        final_memory = df_opt.memory_usage(deep=True).sum()
        
        # Memory should be reduced
        assert final_memory < initial_memory
        
        # Data should be preserved
        assert df['SmallInt'].equals(df_opt['SmallInt'])
    
    def test_get_dataset_info(self):
        """Test dataset info extraction."""
        loader = DataLoader()
        df = pd.DataFrame({
            'Date': pd.date_range('2020-01-01', periods=10),
            'Value': np.arange(10),
            'Category': ['A'] * 5 + ['B'] * 5
        })
        
        info = loader.get_dataset_info(df)
        
        assert 'shape' in info
        assert info['shape'] == (10, 3)
        assert 'columns' in info
        assert 'date_range' in info
        assert 'numeric_stats' in info


class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_safe_divide_normal(self):
        """Test safe division with normal values."""
        result = safe_divide(10, 2)
        assert result == 5.0
    
    def test_safe_divide_by_zero(self):
        """Test safe division by zero."""
        result = safe_divide(10, 0, default=0)
        assert result == 0
    
    def test_safe_divide_custom_default(self):
        """Test safe division with custom default."""
        result = safe_divide(10, 0, default=-1)
        assert result == -1
    
    def test_safe_percentage_normal(self):
        """Test safe percentage calculation."""
        result = safe_percentage(25, 100)
        assert result == 25.0
    
    def test_safe_percentage_zero_total(self):
        """Test safe percentage with zero total."""
        result = safe_percentage(10, 0)
        assert result == 0.0
    
    def test_safe_percentage_decimals(self):
        """Test safe percentage with decimal places."""
        result = safe_percentage(1, 3, decimals=2)
        assert result == 33.33
    
    def test_validate_dataframe_valid(self):
        """Test DataFrame validation with valid data."""
        df = pd.DataFrame({'A': [1, 2, 3]})
        assert validate_dataframe(df) is True
    
    def test_validate_dataframe_none(self):
        """Test DataFrame validation with None."""
        assert validate_dataframe(None) is False
    
    def test_validate_dataframe_empty(self):
        """Test DataFrame validation with empty DataFrame."""
        df = pd.DataFrame()
        assert validate_dataframe(df) is False
    
    def test_validate_dataframe_min_rows(self):
        """Test DataFrame validation with minimum rows."""
        df = pd.DataFrame({'A': [1, 2]})
        assert validate_dataframe(df, min_rows=5) is False
        assert validate_dataframe(df, min_rows=2) is True
    
    def test_create_sample_dataset(self):
        """Test sample dataset creation."""
        df = create_sample_dataset()
        
        assert not df.empty
        assert 'Date' in df.columns
        assert 'Location' in df.columns
        assert 'Fatalities' in df.columns
        assert len(df) == 100


class TestDataProcessing:
    """Tests for data processing functions."""
    
    def test_survival_rate_calculation(self):
        """Test survival rate calculation."""
        loader = DataLoader()
        df = pd.DataFrame({
            'Date': ['2020-01-01'],
            'Fatalities': [50],
            'Aboard': [100]
        })
        
        df_clean = loader.clean_dataset(df)
        
        assert 'SurvivalRate' in df_clean.columns
        assert df_clean['SurvivalRate'].iloc[0] == 50.0
    
    def test_survival_rate_zero_aboard(self):
        """Test survival rate with zero aboard."""
        loader = DataLoader()
        df = pd.DataFrame({
            'Date': ['2020-01-01'],
            'Fatalities': [0],
            'Aboard': [0]
        })
        
        df_clean = loader.clean_dataset(df)
        
        assert df_clean['SurvivalRate'].iloc[0] == 0.0
    
    def test_date_derived_columns(self):
        """Test date-derived column generation."""
        loader = DataLoader()
        df = pd.DataFrame({
            'Date': ['2020-03-15']
        })
        
        df_clean = loader.clean_dataset(df)
        
        assert df_clean['Year'].iloc[0] == 2020
        assert df_clean['Month'].iloc[0] == 3
        assert df_clean['Day'].iloc[0] == 15
        assert 'DayOfWeek' in df_clean.columns
        assert 'Quarter' in df_clean.columns


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_data_load_error(self):
        """Test DataLoadError exception."""
        loader = DataLoader()
        
        with pytest.raises(DataLoadError):
            loader.load_dataset(['nonexistent_file.csv'])
    
    def test_invalid_encoding(self):
        """Test handling of invalid encoding."""
        loader = DataLoader()
        
        # This should raise DataLoadError after trying all encodings
        with pytest.raises(DataLoadError):
            loader.load_dataset(['nonexistent.csv'], encodings=['utf-8'])


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_string_cleaning(self):
        """Test cleaning of empty strings."""
        loader = DataLoader()
        df = pd.DataFrame({
            'Location': ['', 'Location A', 'None', 'nan']
        })
        
        df_clean = loader.clean_dataset(df)
        
        # Empty strings should be converted to NaN
        assert df_clean['Location'].isnull().sum() > 0
    
    def test_large_numbers(self):
        """Test handling of large numbers."""
        loader = DataLoader()
        df = pd.DataFrame({
            'Fatalities': [1000000],
            'Aboard': [2000000]
        })
        
        df_clean = loader.clean_dataset(df)
        
        assert df_clean['Fatalities'].iloc[0] == 1000000
        assert df_clean['Aboard'].iloc[0] == 2000000
    
    def test_negative_numbers(self):
        """Test handling of negative numbers."""
        loader = DataLoader()
        df = pd.DataFrame({
            'Fatalities': [-10],
            'Aboard': [100]
        })
        
        df_clean = loader.clean_dataset(df)
        
        # Negative fatalities should be converted to 0
        assert df_clean['Fatalities'].iloc[0] == 0


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
