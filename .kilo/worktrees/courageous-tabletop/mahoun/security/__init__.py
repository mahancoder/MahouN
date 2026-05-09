"""
Security Hardening Module
==========================

Enterprise-grade security features for production deployment.

Features:
- Rate limiting with sliding window
- OAuth2/JWT authentication
- Prompt injection defense
- API key management
- Security audit logging
- AES-256-GCM encryption (data at rest/in transit)
- Ed25519 digital signatures (ledger integrity)
- Model reliability monitoring
- PII scrubbing
- Adversarial detection
- Alerting & anomaly detection
"""

from mahoun.security.rate_limiter import RateLimiter, RateLimitExceeded
from mahoun.security.auth import JWTAuthenticator, OAuth2Handler
from mahoun.security.prompt_defense import PromptInjectionDefender
from mahoun.security.api_keys import APIKeyManager
from mahoun.security.encryption import (
    AESEncryption,
    EnvelopeEncryption,
    EncryptionKey,
    EncryptedData,
    get_aes_encryption,
    get_envelope_encryption,
)
from mahoun.security.signing import (
    Ed25519Signing,
    LedgerSigning,
    SigningKeyPair,
    Signature,
    get_ed25519_signing,
    get_ledger_signing,
)

# New modules from New Folder
from mahoun.security.adversarial_detector import AdversarialDetector
from mahoun.security.alerting import AlertManager
from mahoun.security.anomaly_detector import AnomalyDetector
from mahoun.security.diagnostic_reports import DiagnosticReportGenerator
from mahoun.security.metrics_endpoint import MetricsEndpoint
from mahoun.security.metrics_tracker import MetricsTracker
from mahoun.security.model_fallback import ModelFallbackManager
from mahoun.security.model_manager import ModelManager
from mahoun.security.model_reliability import ModelReliabilityMonitor
from mahoun.security.pii_scrubber import PIIScrubber
from mahoun.security.rbac import RBAC, PermissionEvaluator
from mahoun.security.retention import DataRetentionManager
from mahoun.security.rolling_stats import RollingStats
from mahoun.security.shadow_deployment import ShadowDeployment
from mahoun.security.wandb_logger import WandbLogger

__all__ = [
    # Rate limiting & auth
    "RateLimiter",
    "RateLimitExceeded",
    "JWTAuthenticator",
    "OAuth2Handler",
    "PromptInjectionDefender",
    "APIKeyManager",
    # Encryption
    "AESEncryption",
    "EnvelopeEncryption",
    "EncryptionKey",
    "EncryptedData",
    "get_aes_encryption",
    "get_envelope_encryption",
    # Signing
    "Ed25519Signing",
    "LedgerSigning",
    "SigningKeyPair",
    "Signature",
    "get_ed25519_signing",
    "get_ledger_signing",
    # New modules from New Folder
    "AdversarialDetector",
    "AlertManager",
    "AnomalyDetector",
    "DiagnosticReportGenerator",
    "MetricsEndpoint",
    "MetricsTracker",
    "ModelFallbackManager",
    "ModelManager",
    "ModelReliabilityMonitor",
    "PIIScrubber",
    "RBAC",
    "PermissionEvaluator",
    "DataRetentionManager",
    "RollingStats",
    "ShadowDeployment",
    "WandbLogger",
]
