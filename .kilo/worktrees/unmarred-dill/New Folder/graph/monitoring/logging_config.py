"""
Advanced Logging Configuration for Knowledge Graph
==================================================

Structured logging with slow query detection and error tracking.
"""

import logging
import logging.handlers
import json
import time
import traceback
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from functools import wraps


# ============================================================================
# Custom Formatters
# ============================================================================

class StructuredFormatter(logging.Formatter):
    """JSON structured logging formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, 'query_duration'):
            log_data['query_duration_ms'] = record.query_duration
        
        if hasattr(record, 'query'):
            log_data['query'] = record.query
        
        if hasattr(record, 'operation'):
            log_data['operation'] = record.operation
        
        if hasattr(record, 'error_type'):
            log_data['error_type'] = record.error_type
        
        # Add exception info
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False)


class GraphFormatter(logging.Formatter):
    """Custom formatter for graph operations"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with graph-specific information"""
        # Base format
        base_msg = super().format(record)
        
        # Add graph-specific info
        extras = []
        
        if hasattr(record, 'query_duration'):
            extras.append(f"duration={record.query_duration:.2f}ms")
        
        if hasattr(record, 'node_count'):
            extras.append(f"nodes={record.node_count}")
        
        if hasattr(record, 'edge_count'):
            extras.append(f"edges={record.edge_count}")
        
        if extras:
            base_msg += f" [{', '.join(extras)}]"
        
        return base_msg


# ============================================================================
# Logging Setup
# ============================================================================

def setup_graph_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    enable_structured: bool = True,
    enable_slow_query_log: bool = True,
    enable_error_log: bool = True,
) -> Dict[str, logging.Logger]:
    """
    Setup comprehensive logging for knowledge graph
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_structured: Enable JSON structured logging
        enable_slow_query_log: Enable slow query logging
        enable_error_log: Enable separate error log
    
    Returns:
        Dictionary of configured loggers
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = GraphFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Main log file (rotating)
    main_handler = logging.handlers.RotatingFileHandler(
        log_path / "graph.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    main_handler.setLevel(logging.DEBUG)
    main_handler.setFormatter(GraphFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    root_logger.addHandler(main_handler)
    
    # Structured JSON log
    if enable_structured:
        json_handler = logging.handlers.RotatingFileHandler(
            log_path / "graph_structured.json",
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(json_handler)
    
    # Slow query log
    slow_query_logger = None
    if enable_slow_query_log:
        slow_query_logger = logging.getLogger('graph.slow_queries')
        slow_query_logger.setLevel(logging.WARNING)
        slow_query_logger.propagate = False
        
        slow_query_handler = logging.handlers.RotatingFileHandler(
            log_path / "slow_queries.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        slow_query_handler.setFormatter(GraphFormatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        slow_query_logger.addHandler(slow_query_handler)
    
    # Error log
    error_logger = None
    if enable_error_log:
        error_logger = logging.getLogger('graph.errors')
        error_logger.setLevel(logging.ERROR)
        error_logger.propagate = False
        
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / "errors.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=10
        )
        error_handler.setFormatter(StructuredFormatter())
        error_logger.addHandler(error_handler)
    
    logging.info(f"Graph logging initialized (level={log_level}, dir={log_dir})")
    
    return {
        'root': root_logger,
        'slow_queries': slow_query_logger,
        'errors': error_logger,
    }


# ============================================================================
# Logging Decorators
# ============================================================================

def log_query(slow_threshold_ms: float = 5000):
    """
    Decorator to log query execution
    
    Args:
        slow_threshold_ms: Threshold for slow query logging (milliseconds)
    
    Usage:
        @log_query(slow_threshold_ms=5000)
        def execute_query(self, query):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            slow_logger = logging.getLogger('graph.slow_queries')
            
            start_time = time.time()
            query = kwargs.get('query', args[1] if len(args) > 1 else 'unknown')
            
            try:
                result = func(*args, **kwargs)
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Log query
                logger.debug(
                    f"Query executed: {func.__name__}",
                    extra={
                        'query_duration': duration_ms,
                        'query': query[:200] if isinstance(query, str) else str(query)[:200],
                        'operation': func.__name__
                    }
                )
                
                # Log slow query
                if duration_ms > slow_threshold_ms:
                    slow_logger.warning(
                        f"Slow query detected in {func.__name__}: {duration_ms:.2f}ms",
                        extra={
                            'query_duration': duration_ms,
                            'query': query[:500] if isinstance(query, str) else str(query)[:500],
                            'operation': func.__name__,
                            'threshold_ms': slow_threshold_ms
                        }
                    )
                
                return result
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Log error
                error_logger = logging.getLogger('graph.errors')
                error_logger.error(
                    f"Query failed in {func.__name__}: {str(e)}",
                    exc_info=True,
                    extra={
                        'query_duration': duration_ms,
                        'query': query[:500] if isinstance(query, str) else str(query)[:500],
                        'operation': func.__name__,
                        'error_type': type(e).__name__
                    }
                )
                
                raise
        
        return wrapper
    return decorator


def log_operation(operation_name: Optional[str] = None):
    """
    Decorator to log general operations
    
    Usage:
        @log_operation('import_laws')
        def import_laws(self, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            op_name = operation_name or func.__name__
            
            start_time = time.time()
            
            logger.info(f"Starting operation: {op_name}")
            
            try:
                result = func(*args, **kwargs)
                
                duration_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"Operation completed: {op_name}",
                    extra={
                        'query_duration': duration_ms,
                        'operation': op_name
                    }
                )
                
                return result
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                error_logger = logging.getLogger('graph.errors')
                error_logger.error(
                    f"Operation failed: {op_name} - {str(e)}",
                    exc_info=True,
                    extra={
                        'query_duration': duration_ms,
                        'operation': op_name,
                        'error_type': type(e).__name__
                    }
                )
                
                raise
        
        return wrapper
    return decorator


# ============================================================================
# Logging Utilities
# ============================================================================

def log_graph_statistics(stats: Dict[str, Any]):
    """
    Log graph statistics
    
    Args:
        stats: Dictionary with graph statistics
    """
    logger = logging.getLogger('graph.statistics')
    
    logger.info(
        "Graph statistics",
        extra={
            'node_count': stats.get('total_nodes', 0),
            'edge_count': stats.get('total_edges', 0),
            **stats
        }
    )


def log_slow_query(query: str, duration_ms: float, operation: str = 'unknown'):
    """
    Log a slow query
    
    Args:
        query: Query string
        duration_ms: Query duration in milliseconds
        operation: Operation name
    """
    logger = logging.getLogger('graph.slow_queries')
    
    logger.warning(
        f"Slow query: {operation} took {duration_ms:.2f}ms",
        extra={
            'query': query[:500],
            'query_duration': duration_ms,
            'operation': operation
        }
    )


def log_error(error: Exception, context: Optional[Dict] = None, operation: str = 'unknown'):
    """
    Log an error with full context
    
    Args:
        error: Exception object
        context: Additional context dictionary
        operation: Operation name
    """
    logger = logging.getLogger('graph.errors')
    
    extra = {
        'error_type': type(error).__name__,
        'operation': operation
    }
    
    if context:
        extra.update(context)
    
    logger.error(
        f"Error in {operation}: {str(error)}",
        exc_info=True,
        extra=extra
    )


def log_import_progress(
    item_type: str,
    processed: int,
    total: int,
    duration_ms: float
):
    """
    Log import progress
    
    Args:
        item_type: Type of items being imported
        processed: Number of items processed
        total: Total number of items
        duration_ms: Duration so far
    """
    logger = logging.getLogger('graph.import')
    
    progress_pct = (processed / total * 100) if total > 0 else 0
    rate = (processed / (duration_ms / 1000)) if duration_ms > 0 else 0
    
    logger.info(
        f"Import progress: {item_type} - {processed}/{total} ({progress_pct:.1f}%) - {rate:.1f} items/sec",
        extra={
            'item_type': item_type,
            'processed': processed,
            'total': total,
            'progress_percent': progress_pct,
            'rate_per_sec': rate,
            'duration_ms': duration_ms
        }
    )


# ============================================================================
# Context Manager for Operation Logging
# ============================================================================

class LogOperation:
    """
    Context manager for logging operations
    
    Usage:
        with LogOperation('import_laws') as log_ctx:
            # do import
            log_ctx.add_info('items_processed', 100)
    """
    
    def __init__(self, operation: str, logger_name: str = 'graph'):
        self.operation = operation
        self.logger = logging.getLogger(logger_name)
        self.start_time = None
        self.info = {}
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        if exc_type is None:
            # Success
            self.logger.info(
                f"Completed: {self.operation}",
                extra={
                    'operation': self.operation,
                    'query_duration': duration_ms,
                    **self.info
                }
            )
        else:
            # Error
            error_logger = logging.getLogger('graph.errors')
            error_logger.error(
                f"Failed: {self.operation} - {str(exc_val)}",
                exc_info=(exc_type, exc_val, exc_tb),
                extra={
                    'operation': self.operation,
                    'query_duration': duration_ms,
                    'error_type': exc_type.__name__,
                    **self.info
                }
            )
        
        return False  # Don't suppress exceptions
    
    def add_info(self, key: str, value: Any):
        """Add additional information to log"""
        self.info[key] = value


# ============================================================================
# Initialize Default Logging
# ============================================================================

# Setup default logging on module import
_default_loggers = setup_graph_logging()
