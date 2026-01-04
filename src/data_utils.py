"""
Data Loading and Error Handling Utilities
Robust data loading with comprehensive error handling and validation
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
import os
import warnings
from functools import wraps
import traceback

warnings.filterwarnings('ignore')


class DataLoadError(Exception):
    """Custom exception for data loading errors."""
    pass


class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


class DataLoader:
    """
    Robust data loader with error handling and validation.
    """
    
    def __init__(self, config=None):
        """
        Initialize data loader.
        
        Args:
            config: Configuration object (optional)
        """
        self.config = config
        self._cache = {}
        print("✅ DataLoader initialized")
    
    def load_dataset(self, paths: List[str], encodings: List[str] = None) -> pd.DataFrame:
        """
        Load dataset from multiple possible paths with fallback.
        
        Args:
            paths: List of possible file paths
            encodings: List of encodings to try
            
        Returns:
            Loaded DataFrame
            
        Raises:
            DataLoadError: If dataset cannot be loaded
        """
        if encodings is None:
            encodings = ['utf-8', 'latin1', 'iso-8859-1']
        
        errors = []
        
        for path in paths:
            if not os.path.exists(path):
                errors.append(f"Path not found: {path}")
                continue
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(path, encoding=encoding)
                    print(f"✅ Successfully loaded data from: {path} (encoding: {encoding})")
                    print(f"📊 Dataset shape: {df.shape}")
                    return df
                    
                except UnicodeDecodeError:
                    errors.append(f"Encoding failed: {path} with {encoding}")
                    continue
                    
                except pd.errors.EmptyDataError:
                    errors.append(f"Empty file: {path}")
                    break
                    
                except pd.errors.ParserError as e:
                    errors.append(f"Parse error in {path}: {str(e)}")
                    break
                    
                except Exception as e:
                    errors.append(f"Unexpected error loading {path}: {str(e)}")
                    continue
        
        # If we get here, all attempts failed
        error_msg = "Failed to load dataset from any path:\n" + "\n".join(errors)
        raise DataLoadError(error_msg)
    
    def validate_dataset(self, df: pd.DataFrame, required_columns: List[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate dataset structure and content.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        # Check if DataFrame is empty
        if df.empty:
            errors.append("Dataset is empty")
            return False, errors
        
        # Check required columns
        if required_columns:
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Check for all-null columns
        null_columns = df.columns[df.isnull().all()].tolist()
        if null_columns:
            errors.append(f"Columns with all null values: {', '.join(null_columns)}")
        
        # Check data types
        if 'Date' in df.columns:
            try:
                pd.to_datetime(df['Date'], errors='coerce')
            except Exception as e:
                errors.append(f"Invalid date format in 'Date' column: {str(e)}")
        
        # Check for numeric columns
        numeric_cols = ['Fatalities', 'Aboard', 'Ground']
        for col in numeric_cols:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        pd.to_numeric(df[col], errors='coerce')
                    except Exception as e:
                        errors.append(f"Column '{col}' cannot be converted to numeric: {str(e)}")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            print("✅ Dataset validation passed")
        else:
            print("⚠️ Dataset validation issues found:")
            for error in errors:
                print(f"  - {error}")
        
        return is_valid, errors
    
    def clean_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess dataset.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        print("🧹 Cleaning dataset...")
        
        df_clean = df.copy()
        
        # Remove duplicate rows
        initial_rows = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        removed_duplicates = initial_rows - len(df_clean)
        if removed_duplicates > 0:
            print(f"  Removed {removed_duplicates} duplicate rows")
        
        # Convert date column
        if 'Date' in df_clean.columns:
            df_clean['Date'] = pd.to_datetime(df_clean['Date'], errors='coerce')
            invalid_dates = df_clean['Date'].isnull().sum()
            if invalid_dates > 0:
                print(f"  Found {invalid_dates} invalid dates (set to NaT)")
        
        # Convert numeric columns
        numeric_cols = ['Fatalities', 'Aboard', 'Ground']
        for col in numeric_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                df_clean[col] = df_clean[col].fillna(0).astype(int)
        
        # Clean string columns
        string_cols = ['Location', 'Operator', 'Type', 'Registration']
        for col in string_cols:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.strip()
                df_clean[col] = df_clean[col].replace(['nan', 'None', ''], np.nan)
        
        # Add derived columns
        if 'Date' in df_clean.columns:
            df_clean['Year'] = df_clean['Date'].dt.year
            df_clean['Month'] = df_clean['Date'].dt.month
            df_clean['Day'] = df_clean['Date'].dt.day
            df_clean['DayOfWeek'] = df_clean['Date'].dt.dayofweek
            df_clean['Quarter'] = df_clean['Date'].dt.quarter
        
        # Calculate survival rate
        if 'Fatalities' in df_clean.columns and 'Aboard' in df_clean.columns:
            df_clean['Survivors'] = df_clean['Aboard'] - df_clean['Fatalities']
            df_clean['SurvivalRate'] = np.where(
                df_clean['Aboard'] > 0,
                (df_clean['Survivors'] / df_clean['Aboard']) * 100,
                0
            )
        
        print(f"✅ Dataset cleaned: {len(df_clean)} rows, {len(df_clean.columns)} columns")
        
        return df_clean
    
    def optimize_memory(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize DataFrame memory usage.
        
        Args:
            df: DataFrame to optimize
            
        Returns:
            Optimized DataFrame
        """
        print("⚡ Optimizing memory usage...")
        
        initial_memory = df.memory_usage(deep=True).sum() / 1024**2
        
        df_opt = df.copy()
        
        # Optimize integer columns
        int_cols = df_opt.select_dtypes(include=['int64']).columns
        for col in int_cols:
            col_min = df_opt[col].min()
            col_max = df_opt[col].max()
            
            if col_min >= 0:
                if col_max < 255:
                    df_opt[col] = df_opt[col].astype(np.uint8)
                elif col_max < 65535:
                    df_opt[col] = df_opt[col].astype(np.uint16)
                elif col_max < 4294967295:
                    df_opt[col] = df_opt[col].astype(np.uint32)
            else:
                if col_min > np.iinfo(np.int8).min and col_max < np.iinfo(np.int8).max:
                    df_opt[col] = df_opt[col].astype(np.int8)
                elif col_min > np.iinfo(np.int16).min and col_max < np.iinfo(np.int16).max:
                    df_opt[col] = df_opt[col].astype(np.int16)
                elif col_min > np.iinfo(np.int32).min and col_max < np.iinfo(np.int32).max:
                    df_opt[col] = df_opt[col].astype(np.int32)
        
        # Optimize float columns
        float_cols = df_opt.select_dtypes(include=['float64']).columns
        for col in float_cols:
            df_opt[col] = df_opt[col].astype(np.float32)
        
        # Convert object columns to category if beneficial
        for col in df_opt.select_dtypes(include=['object']).columns:
            num_unique = df_opt[col].nunique()
            num_total = len(df_opt[col])
            
            if num_unique / num_total < 0.5:  # Less than 50% unique values
                df_opt[col] = df_opt[col].astype('category')
        
        final_memory = df_opt.memory_usage(deep=True).sum() / 1024**2
        reduction = (1 - final_memory / initial_memory) * 100
        
        print(f"  Memory reduced from {initial_memory:.2f}MB to {final_memory:.2f}MB ({reduction:.1f}% reduction)")
        
        return df_opt
    
    def get_dataset_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get comprehensive dataset information.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with dataset info
        """
        info = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024**2,
            'null_counts': df.isnull().sum().to_dict(),
            'null_percentages': (df.isnull().sum() / len(df) * 100).to_dict()
        }
        
        # Date range
        if 'Date' in df.columns:
            info['date_range'] = {
                'min': df['Date'].min(),
                'max': df['Date'].max(),
                'span_years': (df['Date'].max() - df['Date'].min()).days / 365.25
            }
        
        # Numeric statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            info['numeric_stats'] = df[numeric_cols].describe().to_dict()
        
        return info


def handle_errors(default_return=None):
    """
    Decorator for error handling in functions.
    
    Args:
        default_return: Value to return on error
        
    Example:
        @handle_errors(default_return=pd.DataFrame())
        def load_data():
            # Your code here
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"❌ Error in {func.__name__}: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                return default_return
        return wrapper
    return decorator


def safe_divide(numerator, denominator, default=0):
    """
    Safely divide two numbers, handling division by zero.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if division fails
        
    Returns:
        Result of division or default value
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except Exception:
        return default


def safe_percentage(part, total, decimals=2):
    """
    Safely calculate percentage.
    
    Args:
        part: Part value
        total: Total value
        decimals: Number of decimal places
        
    Returns:
        Percentage value
    """
    result = safe_divide(part, total, 0) * 100
    return round(result, decimals)


def validate_dataframe(df: pd.DataFrame, min_rows: int = 1) -> bool:
    """
    Validate DataFrame is not empty and has minimum rows.
    
    Args:
        df: DataFrame to validate
        min_rows: Minimum number of rows required
        
    Returns:
        True if valid, False otherwise
    """
    if df is None:
        print("❌ DataFrame is None")
        return False
    
    if df.empty:
        print("❌ DataFrame is empty")
        return False
    
    if len(df) < min_rows:
        print(f"❌ DataFrame has only {len(df)} rows (minimum {min_rows} required)")
        return False
    
    return True


def create_sample_dataset() -> pd.DataFrame:
    """
    Create a sample dataset for demo purposes.
    
    Returns:
        Sample DataFrame
    """
    print("📝 Creating sample dataset for demo...")
    
    sample_data = {
        'Date': pd.date_range(start='1990-01-01', periods=100, freq='M'),
        'Location': ['Location ' + str(i % 10) for i in range(100)],
        'Operator': ['Operator ' + str(i % 5) for i in range(100)],
        'Type': ['Aircraft Type ' + str(i % 3) for i in range(100)],
        'Fatalities': np.random.randint(0, 200, 100),
        'Aboard': np.random.randint(50, 300, 100),
        'Ground': np.random.randint(0, 50, 100)
    }
    
    df = pd.DataFrame(sample_data)
    
    print(f"✅ Sample dataset created: {df.shape}")
    
    return df
