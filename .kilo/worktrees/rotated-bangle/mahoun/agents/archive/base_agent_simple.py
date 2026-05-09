"""
Base Agent Class (HAJIX Refactored)
====================================

Foundation class for all MAHOUN agents with automatic metrics tracking.

Features:
    - Automatic metrics collection
    - Standardized error handling
    - Status reporting
    - Async processing interface

Usage:
    class MyAgent(BaseAgent):
        async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
            # Implementation
            return {"result": "..."}
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
import time

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all MAHOUN agents.
    
    Every agent must:
        1. Have a unique name
        2. Implement the process() method
        3. Handle errors gracefully
    
    Attributes:
        name: Unique agent identifier
        config: Agent configuration dictionary
        logger: Agent-specific logger instance
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize agent.
        
        Args:
            name: Unique agent identifier
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Initialize metrics collector
        self._metrics_enabled = False
        self.metrics_collector = None
        try:
            from mahoun.metrics import get_metrics_collector
            self.metrics_collector = get_metrics_collector()
            self._metrics_enabled = True
        except ImportError:
            self.logger.debug(f"Metrics collector not available for {name}")
        
        self.logger.info(f"Agent initialized: {name} (metrics: {self._metrics_enabled})")
    
    async def process_with_metrics(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input with automatic metrics tracking.
        
        Wrapper method that collects timing and success/failure metrics.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Processing result dictionary
        """
        if not self._metrics_enabled:
            return await self.process(input_data)
        
        self.metrics_collector.record_counter(f"agent.{self.name}.calls")
        start_time = time.time()
        
        try:
            result = await self.process(input_data)
            duration_ms = (time.time() - start_time) * 1000
            
            self.metrics_collector.record_counter(f"agent.{self.name}.success")
            self.metrics_collector.record_timing(f"agent.{self.name}", duration_ms)
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.metrics_collector.record_counter(
                f"agent.{self.name}.errors",
                tags={"error_type": type(e).__name__}
            )
            self.metrics_collector.record_timing(
                f"agent.{self.name}",
                duration_ms,
                tags={"status": "error"}
            )
            raise
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and produce output.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Processing result dictionary
        """
        pass
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if input is valid
        """
        return True
    
    async def handle_error(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle processing error.
        
        Args:
            error: Exception that occurred
            context: Additional context information
            
        Returns:
            Error response dictionary
        """
        self.logger.error(f"Error in {self.name}: {error}", exc_info=True)
        
        if self._metrics_enabled:
            self.metrics_collector.record_counter(
                f"agent.{self.name}.handled_errors",
                tags={"error_type": type(error).__name__}
            )
        
        return {
            "success": False,
            "error": str(error),
            "agent": self.name,
            "context": context
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status information.
        
        Returns:
            Status dictionary with name, config, and metrics state
        """
        status = {
            "name": self.name,
            "status": "ready",
            "config": self.config,
            "metrics_enabled": self._metrics_enabled
        }
        
        if self._metrics_enabled:
            status["metrics"] = self.get_metrics()
        
        return status
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get agent performance metrics.
        
        Returns:
            Metrics dictionary with call counts, timing, and success rate
        """
        if not self._metrics_enabled:
            return {"enabled": False}
        
        calls = self.metrics_collector.get_metrics(f"agent.{self.name}.calls")
        success = self.metrics_collector.get_metrics(f"agent.{self.name}.success")
        errors = self.metrics_collector.get_metrics(f"agent.{self.name}.errors")
        timing = self.metrics_collector.get_metrics(f"agent.{self.name}.duration_ms")
        
        total_calls = calls.get("counter", 0)
        successful_calls = success.get("counter", 0)
        
        return {
            "enabled": True,
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": errors.get("counter", 0),
            "average_duration_ms": timing.get("gauge", 0.0),
            "success_rate": (
                successful_calls / total_calls * 100 if total_calls > 0 else 0.0
            )
        }
