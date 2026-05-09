"""
Validation - Re-export from data_prep_advanced
===============================================

This module re-exports validation functionality from
pipelines.data_prep_advanced.validation for backward compatibility.

For new code, prefer importing directly from:
    from pipelines.data_prep_advanced.validation import DataValidator
"""

# Re-export all public APIs from the actual implementation
from pipelines.data_prep_advanced.validation import (
    DataValidator,
)

__all__ = [
    'DataValidator',
]
