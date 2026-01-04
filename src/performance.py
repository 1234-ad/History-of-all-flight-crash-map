"""
Performance Monitoring and Optimization Utilities
Track and optimize application performance
"""

import time
import functools
from typing import Callable, Any, Dict
import psutil
import os
from datetime import datetime


class PerformanceMonitor:
    """
    Monitor application performance metrics.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = {
            'function_calls': {},
            'execution_times': {},
            'memory_usage': [],
            'cache_hits': 0,
            'cache_misses': 0
        }
        self.start_time = time.time()
        print("✅ PerformanceMonitor initialized")
    
    def record_function_call(self, func_name: str, duration: float) -> None:
        """
        Record function call metrics.
        
        Args:
            func_name: Name of the function
            duration: Execution duration in seconds
        """
        if func_name not in self.metrics['function_calls']:
            self.metrics['function_calls'][func_name] = 0
            self.metrics['execution_times'][func_name] = []
        
        self.metrics['function_calls'][func_name] += 1
        self.metrics['execution_times'][func_name].append(duration)
    
    def record_memory_usage(self) -> None:
        """Record current memory usage."""
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        self.metrics['memory_usage'].append({
            'timestamp': datetime.now().isoformat(),
            'memory_mb': memory_mb
        })
    
    def record_cache_hit(self) -> None:
        """Record cache hit."""
        self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self) -> None:
        """Record cache miss."""
        self.metrics['cache_misses'] += 1
    
    def get_function_stats(self, func_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific function.
        
        Args:
            func_name: Name of the function
            
        Returns:
            Dictionary with function statistics
        """
        if func_name not in self.metrics['function_calls']:
            return {}
        
        times = self.metrics['execution_times'][func_name]
        
        return {
            'calls': self.metrics['function_calls'][func_name],
            'total_time': sum(times),
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times)
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.metrics['cache_hits'] + self.metrics['cache_misses']
        hit_rate = (self.metrics['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.metrics['cache_hits'],
            'misses': self.metrics['cache_misses'],
            'total_requests': total_requests,
            'hit_rate': f"{hit_rate:.2f}%"
        }
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        if not self.metrics['memory_usage']:
            return {}
        
        memory_values = [m['memory_mb'] for m in self.metrics['memory_usage']]
        
        return {
            'current_mb': memory_values[-1],
            'peak_mb': max(memory_values),
            'avg_mb': sum(memory_values) / len(memory_values),
            'samples': len(memory_values)
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with all performance metrics
        """
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': self._format_duration(uptime),
            'function_stats': {
                name: self.get_function_stats(name)
                for name in self.metrics['function_calls'].keys()
            },
            'cache_stats': self.get_cache_stats(),
            'memory_stats': self.get_memory_stats()
        }
    
    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds / 60:.1f}m"
        else:
            return f"{seconds / 3600:.1f}h"
    
    def print_summary(self) -> None:
        """Print performance summary."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE SUMMARY")
        print("="*60)
        
        print(f"\n⏱️  Uptime: {summary['uptime_formatted']}")
        
        # Function stats
        if summary['function_stats']:
            print("\n📈 Function Statistics:")
            for func_name, stats in summary['function_stats'].items():
                print(f"  {func_name}:")
                print(f"    Calls: {stats['calls']}")
                print(f"    Avg Time: {stats['avg_time']:.3f}s")
                print(f"    Total Time: {stats['total_time']:.3f}s")
        
        # Cache stats
        cache_stats = summary['cache_stats']
        if cache_stats.get('total_requests', 0) > 0:
            print("\n💾 Cache Statistics:")
            print(f"  Hits: {cache_stats['hits']}")
            print(f"  Misses: {cache_stats['misses']}")
            print(f"  Hit Rate: {cache_stats['hit_rate']}")
        
        # Memory stats
        memory_stats = summary['memory_stats']
        if memory_stats:
            print("\n🧠 Memory Usage:")
            print(f"  Current: {memory_stats['current_mb']:.2f} MB")
            print(f"  Peak: {memory_stats['peak_mb']:.2f} MB")
            print(f"  Average: {memory_stats['avg_mb']:.2f} MB")
        
        print("\n" + "="*60 + "\n")


def monitor_performance(monitor: PerformanceMonitor = None):
    """
    Decorator to monitor function performance.
    
    Args:
        monitor: PerformanceMonitor instance
        
    Example:
        @monitor_performance(monitor)
        def my_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                
                if monitor:
                    monitor.record_function_call(func.__name__, duration)
                
                # Log slow functions
                if duration > 1.0:
                    print(f"⚠️ Slow function: {func.__name__} took {duration:.2f}s")
        
        return wrapper
    return decorator


def measure_time(func: Callable) -> Callable:
    """
    Simple decorator to measure function execution time.
    
    Example:
        @measure_time
        def my_function():
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        print(f"⏱️  {func.__name__} executed in {duration:.3f}s")
        
        return result
    
    return wrapper


def optimize_dataframe_operations(func: Callable) -> Callable:
    """
    Decorator to optimize DataFrame operations.
    
    Example:
        @optimize_dataframe_operations
        def process_data(df):
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import pandas as pd
        
        # Disable chained assignment warning
        pd.options.mode.chained_assignment = None
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Re-enable warning
            pd.options.mode.chained_assignment = 'warn'
    
    return wrapper


class Timer:
    """
    Context manager for timing code blocks.
    
    Example:
        with Timer("Data loading"):
            df = load_data()
    """
    
    def __init__(self, name: str = "Operation"):
        """
        Initialize timer.
        
        Args:
            name: Name of the operation being timed
        """
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        print(f"⏱️  Starting: {self.name}")
        return self
    
    def __exit__(self, *args):
        """Stop timer and print duration."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        print(f"✅ Completed: {self.name} in {duration:.3f}s")
    
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0


def get_system_info() -> Dict[str, Any]:
    """
    Get system information.
    
    Returns:
        Dictionary with system info
    """
    import platform
    
    return {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'python_version': platform.python_version(),
        'processor': platform.processor(),
        'cpu_count': psutil.cpu_count(),
        'memory_total_gb': psutil.virtual_memory().total / (1024**3),
        'memory_available_gb': psutil.virtual_memory().available / (1024**3),
        'memory_percent': psutil.virtual_memory().percent
    }


def print_system_info() -> None:
    """Print system information."""
    info = get_system_info()
    
    print("\n" + "="*60)
    print("💻 SYSTEM INFORMATION")
    print("="*60)
    print(f"Platform: {info['platform']} {info['platform_version']}")
    print(f"Python: {info['python_version']}")
    print(f"Processor: {info['processor']}")
    print(f"CPU Cores: {info['cpu_count']}")
    print(f"Total Memory: {info['memory_total_gb']:.2f} GB")
    print(f"Available Memory: {info['memory_available_gb']:.2f} GB")
    print(f"Memory Usage: {info['memory_percent']:.1f}%")
    print("="*60 + "\n")


# Global performance monitor instance
_global_monitor: PerformanceMonitor = None


def get_monitor() -> PerformanceMonitor:
    """
    Get or create global performance monitor.
    
    Returns:
        PerformanceMonitor instance
    """
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    
    return _global_monitor
