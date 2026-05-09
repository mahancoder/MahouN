"""
Metrics Decorators
==================
Decorators for automatic metrics collection.

استفاده:
    @track_timing("api.search")
    async def search_verdicts(query: str):
        # Implementation
    
    @track_calls("agent.process")
    async def process(self, data: dict):
        # Implementation
"""

import time
import asyncio
from functools import wraps
from typing import Any, Callable
import logging

from .collector import get_metrics_collector

logger = logging.getLogger(__name__)


def track_timing(metric_name: str):
    """
    Decorator to track function execution time
    
    Args:
        metric_name: Name of the metric to record
    
    Usage:
        @track_timing("my_function")
        async def my_function():
            # Implementation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start = time.time()
            collector = get_metrics_collector()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                collector.record_timing(
                    metric_name,
                    duration_ms,
                    tags={"status": "success"}
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                collector.record_timing(
                    metric_name,
                    duration_ms,
                    tags={"status": "error", "error_type": type(e).__name__}
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start = time.time()
            collector = get_metrics_collector()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                collector.record_timing(
                    metric_name,
                    duration_ms,
                    tags={"status": "success"}
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                collector.record_timing(
                    metric_name,
                    duration_ms,
                    tags={"status": "error", "error_type": type(e).__name__}
                )
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_calls(metric_name: str):
    """
    Decorator to track function calls and success/error rates
    
    Args:
        metric_name: Name of the metric to record
    
    Usage:
        @track_calls("my_function")
        async def my_function():
            # Implementation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            collector = get_metrics_collector()
            collector.record_counter(f"{metric_name}.calls")
            
            try:
                result = await func(*args, **kwargs)
                collector.record_counter(f"{metric_name}.success")
                return result
            except Exception as e:
                collector.record_counter(
                    f"{metric_name}.errors",
                    tags={"error_type": type(e).__name__}
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            collector = get_metrics_collector()
            collector.record_counter(f"{metric_name}.calls")
            
            try:
                result = func(*args, **kwargs)
                collector.record_counter(f"{metric_name}.success")
                return result
            except Exception as e:
                collector.record_counter(
                    f"{metric_name}.errors",
                    tags={"error_type": type(e).__name__}
                )
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_all(metric_name: str):
    """
    Decorator to track both timing and calls
    
    Combines @track_timing and @track_calls
    
    Args:
        metric_name: Name of the metric to record
    
    Usage:
        @track_all("my_function")
        async def my_function():
            # Implementation
    """
    def decorator(func: Callable) -> Callable:
        # Apply both decorators
        func = track_calls(metric_name)(func)
        func = track_timing(metric_name)(func)
        return func
    
    return decorator
