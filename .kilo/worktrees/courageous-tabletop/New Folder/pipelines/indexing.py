"""
Indexing Service - Re-export from data_prep_advanced
====================================================

This module re-exports the IndexingService implementation from
pipelines.data_prep_advanced.indexing for backward compatibility.

For new code, prefer importing directly from:
    from pipelines.data_prep_advanced.indexing import IndexingService
"""

# Re-export all public APIs from the actual implementation
from pipelines.data_prep_advanced.indexing import (
    IndexItem,
    IndexingService,
    build_indexing_service_from_config,
)

__all__ = [
    'IndexItem',
    'IndexingService',
    'build_indexing_service_from_config',
]
