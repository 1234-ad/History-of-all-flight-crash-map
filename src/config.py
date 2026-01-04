"""
Configuration Management System
Centralized configuration for the Aviation Crash Analytics Dashboard
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json


@dataclass
class DataConfig:
    """Data-related configuration."""
    
    # Dataset paths (in order of priority)
    dataset_paths: list = field(default_factory=lambda: [
        'data/dataset.csv.csv',
        'data/dataset.csv',
        'dataset.csv.csv',
        'dataset.csv',
        './data/dataset.csv.csv',
        './data/dataset.csv'
    ])
    
    # Encoding options
    encodings: list = field(default_factory=lambda: ['utf-8', 'latin1', 'iso-8859-1'])
    
    # Cache settings
    cache_ttl: int = 3600  # 1 hour in seconds
    enable_caching: bool = True
    
    # Data validation
    required_columns: list = field(default_factory=lambda: [
        'Date', 'Location', 'Operator', 'Fatalities'
    ])
    
    # Performance
    chunk_size: int = 10000
    max_rows: Optional[int] = None  # None = load all


@dataclass
class AppConfig:
    """Application-level configuration."""
    
    # App metadata
    app_title: str = "✈️ Aviation Crash Analytics Dashboard"
    page_icon: str = "✈️"
    layout: str = "wide"
    
    # Server settings
    port: int = 8501
    host: str = "0.0.0.0"
    
    # UI settings
    theme: str = "light"
    show_warnings: bool = False
    
    # Feature flags
    enable_predictions: bool = True
    enable_advanced_analytics: bool = True
    enable_export: bool = True


@dataclass
class VisualizationConfig:
    """Visualization-related configuration."""
    
    # Color scheme
    colors: Dict[str, str] = field(default_factory=lambda: {
        "primary": "#2E86AB",
        "secondary": "#A23B72",
        "accent": "#F18F01",
        "success": "#4CAF50",
        "danger": "#F44336",
        "warning": "#FF9800",
        "light_bg": "#F8F9FE",
        "card_bg": "#FFFFFF",
        "text": "#2C3E50"
    })
    
    # Chart settings
    default_height: int = 500
    default_width: Optional[int] = None  # None = auto
    
    # Map settings
    default_zoom: int = 2
    default_center: tuple = (20.0, 0.0)  # lat, lon
    
    # Animation
    enable_animations: bool = True
    animation_duration: int = 500  # milliseconds


@dataclass
class PerformanceConfig:
    """Performance optimization configuration."""
    
    # Memory management
    max_memory_mb: int = 1024
    enable_garbage_collection: bool = True
    
    # Processing
    use_multiprocessing: bool = False
    num_workers: int = 4
    
    # Optimization
    optimize_dtypes: bool = True
    drop_duplicates: bool = True
    
    # Limits
    max_chart_points: int = 10000
    max_map_markers: int = 5000


@dataclass
class LoggingConfig:
    """Logging configuration."""
    
    # Log levels
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # Log files
    log_dir: str = "logs"
    app_log_file: str = "app.log"
    error_log_file: str = "error.log"
    
    # Log format
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # Rotation
    max_log_size_mb: int = 10
    backup_count: int = 5


class Config:
    """
    Main configuration class that combines all config sections.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Optional path to JSON config file
        """
        self.data = DataConfig()
        self.app = AppConfig()
        self.visualization = VisualizationConfig()
        self.performance = PerformanceConfig()
        self.logging = LoggingConfig()
        
        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        
        # Override with environment variables
        self.load_from_env()
    
    def load_from_file(self, config_file: str) -> None:
        """
        Load configuration from JSON file.
        
        Args:
            config_file: Path to JSON config file
        """
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Update each config section
            if 'data' in config_data:
                self._update_dataclass(self.data, config_data['data'])
            
            if 'app' in config_data:
                self._update_dataclass(self.app, config_data['app'])
            
            if 'visualization' in config_data:
                self._update_dataclass(self.visualization, config_data['visualization'])
            
            if 'performance' in config_data:
                self._update_dataclass(self.performance, config_data['performance'])
            
            if 'logging' in config_data:
                self._update_dataclass(self.logging, config_data['logging'])
            
            print(f"✅ Configuration loaded from {config_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to load config from {config_file}: {str(e)}")
    
    def load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # App settings
        if os.getenv('APP_PORT'):
            self.app.port = int(os.getenv('APP_PORT'))
        
        if os.getenv('APP_HOST'):
            self.app.host = os.getenv('APP_HOST')
        
        # Data settings
        if os.getenv('DATASET_PATH'):
            self.data.dataset_paths.insert(0, os.getenv('DATASET_PATH'))
        
        if os.getenv('CACHE_TTL'):
            self.data.cache_ttl = int(os.getenv('CACHE_TTL'))
        
        if os.getenv('ENABLE_CACHING'):
            self.data.enable_caching = os.getenv('ENABLE_CACHING').lower() == 'true'
        
        # Logging
        if os.getenv('LOG_LEVEL'):
            self.logging.log_level = os.getenv('LOG_LEVEL')
        
        # Performance
        if os.getenv('MAX_MEMORY_MB'):
            self.performance.max_memory_mb = int(os.getenv('MAX_MEMORY_MB'))
    
    def _update_dataclass(self, obj: Any, data: Dict[str, Any]) -> None:
        """
        Update dataclass fields from dictionary.
        
        Args:
            obj: Dataclass instance
            data: Dictionary with new values
        """
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of config
        """
        return {
            'data': self.data.__dict__,
            'app': self.app.__dict__,
            'visualization': self.visualization.__dict__,
            'performance': self.performance.__dict__,
            'logging': self.logging.__dict__
        }
    
    def save_to_file(self, config_file: str) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            config_file: Path to save config file
        """
        try:
            with open(config_file, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            print(f"✅ Configuration saved to {config_file}")
        except Exception as e:
            print(f"❌ Failed to save config to {config_file}: {str(e)}")
    
    def validate(self) -> bool:
        """
        Validate configuration values.
        
        Returns:
            True if configuration is valid
        """
        errors = []
        
        # Validate port
        if not (1024 <= self.app.port <= 65535):
            errors.append(f"Invalid port: {self.app.port} (must be 1024-65535)")
        
        # Validate log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.logging.log_level not in valid_levels:
            errors.append(f"Invalid log level: {self.logging.log_level}")
        
        # Validate memory limit
        if self.performance.max_memory_mb < 128:
            errors.append(f"Memory limit too low: {self.performance.max_memory_mb}MB")
        
        # Validate cache TTL
        if self.data.cache_ttl < 0:
            errors.append(f"Invalid cache TTL: {self.data.cache_ttl}")
        
        if errors:
            print("❌ Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("✅ Configuration validation passed")
        return True
    
    def get_dataset_path(self) -> Optional[str]:
        """
        Get the first existing dataset path.
        
        Returns:
            Path to dataset file or None if not found
        """
        for path in self.data.dataset_paths:
            if os.path.exists(path):
                return path
        return None


# Global configuration instance
_config: Optional[Config] = None


def get_config(config_file: Optional[str] = None) -> Config:
    """
    Get or create global configuration instance.
    
    Args:
        config_file: Optional path to config file
        
    Returns:
        Config instance
    """
    global _config
    
    if _config is None:
        _config = Config(config_file)
    
    return _config


def reload_config(config_file: Optional[str] = None) -> Config:
    """
    Reload configuration from file.
    
    Args:
        config_file: Optional path to config file
        
    Returns:
        New Config instance
    """
    global _config
    _config = Config(config_file)
    return _config
