"""
Quality Analyzer - Re-export from data_prep_advanced
====================================================

This module re-exports the QualityAnalyzer implementation from
pipelines.data_prep_advanced.quality_analyzer for backward compatibility.

For new code, prefer importing directly from:
    from pipelines.data_prep_advanced.quality_analyzer import QualityAnalyzer
"""

# Re-export all public APIs from the actual implementation
from pipelines.data_prep_advanced.quality_analyzer import (
    QualityAnalyzer,
)

__all__ = [
    'QualityAnalyzer',
]
