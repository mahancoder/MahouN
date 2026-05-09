"""
Sequence Modeling Module for MAHOUN
====================================

Advanced BART and CRF implementations for:
- Text Generation (BART)
- Sequence Labeling (CRF)
"""

from .advanced_bart import (
    AdvancedBARTModel,
    BARTTask,
    GenerationConstraints,
    LegalTermsLogitsProcessor,
    ForbiddenWordsLogitsProcessor,
    LengthControlLogitsProcessor,
)

from .advanced_crf import (
    AdvancedCRF,
    BiLSTMCRF,
    BERTCRF,
    HierarchicalCRF,
    CRFTrainer,
    CRFTask,
    BIO_LABELS,
    BIOES_LABELS,
)

__all__ = [
    # BART
    "AdvancedBARTModel",
    "BARTTask",
    "GenerationConstraints",
    "LegalTermsLogitsProcessor",
    "ForbiddenWordsLogitsProcessor",
    "LengthControlLogitsProcessor",
    
    # CRF
    "AdvancedCRF",
    "BiLSTMCRF",
    "BERTCRF",
    "HierarchicalCRF",
    "CRFTrainer",
    "CRFTask",
    "BIO_LABELS",
    "BIOES_LABELS",
]

__version__ = "2.0.0"
