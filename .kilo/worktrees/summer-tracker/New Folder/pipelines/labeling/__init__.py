"""
MAHOUN Advanced Labeling Module
================================

Ultra-advanced labeling system with uncertainty quantification,
active learning, and multi-model ensemble.

Components:
- UltraAdvancedLabeler: Main labeling service with ensemble
- Weight Management: Dynamic model weight adjustment
- Active Learning: Intelligent sample selection
- Uncertainty: Confidence scoring and calibration

Features:
- Multi-model ensemble (BERT, Legal-BERT, RoBERTa)
- Bayesian uncertainty quantification
- Active learning strategies
- Hierarchical label taxonomy
- Real-time weight adaptation
"""

# Import only the classes that actually exist
from pipelines.labeling.ultra_advanced_labeler import (
    MultiPassNER as UltraAdvancedLabeler,
    ConfidenceCalibrator,
    ContextAnalyzer,
    HierarchicalClassifier,
)

# Import weight management classes
from pipelines.labeling.weight import (
    LABEL_PRIORITY,
    CATEGORY_RULES,
)

__all__ = [
    "UltraAdvancedLabeler",
    "ConfidenceCalibrator",
    "ContextAnalyzer",
    "HierarchicalClassifier",
    "LABEL_PRIORITY",
    "CATEGORY_RULES",
]