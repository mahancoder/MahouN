"""
Graph Services Module
====================

This module contains service classes for querying and analyzing the graph.
"""

# Using ultra systems for enhanced query service
from ultra_systems.graph import UltraGraphQueryService

# Map UltraGraphQueryService to GraphQueryService for compatibility
GraphQueryService = UltraGraphQueryService
from .analytics_service import GraphAnalytics

__all__ = ['GraphQueryService', 'GraphAnalytics']
