"""
MAHOUN Proof-Carrying Response Models
======================================

Classification: CRITICAL GOVERNANCE ENFORCEMENT
Purpose: Base models with mandatory proof-carrying contract fields

All API response models that involve reasoning MUST inherit from
ProofCarryingResponse to ensure governance metadata is present.

Author: MahouN AEO Governance Council
Version: 1.0.0
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProofCarryingResponse(BaseModel):
    """
    Base response model with proof-carrying contract enforcement.
    
    All reasoning-related API responses MUST inherit from this class
    to ensure governance metadata is included.
    
    MANDATORY FIELDS:
    - fortress_validated: Validation status
    - audit_hash: Forensic hash for tamper detection
    - validation_timestamp: When validation occurred
    - correlation_id: Distributed tracing ID
    
    Example:
        class MyReasoningResponse(ProofCarryingResponse):
            result: str
            confidence: float
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fortress_validated": True,
                "audit_hash": "a1b2c3d4e5f6g7h8",
                "validation_timestamp": "2026-05-14T04:30:00Z",
                "correlation_id": "req-12345-abcde"
            }
        }
    )
    
    # Proof-carrying contract fields
    fortress_validated: bool = Field(
        ...,
        description="Whether this response has been validated by FortressValidator"
    )
    
    audit_hash: str = Field(
        ...,
        description="Forensic audit hash (SHA256) for tamper detection",
        min_length=16,
        max_length=64
    )
    
    validation_timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp when validation occurred"
    )
    
    correlation_id: str = Field(
        ...,
        description="Unique correlation ID for distributed tracing"
    )
    
    @field_validator('fortress_validated')
    def validate_fortress_status(cls, v):
        """Ensure fortress_validated is True for successful responses"""
        if not v:
            raise ValueError(
                "fortress_validated must be True. "
                "All responses must pass FortressValidator before being returned."
            )
        return v

    @field_validator('validation_timestamp')
    def validate_timestamp_format(cls, v):
        """Ensure timestamp is valid ISO 8601 format"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"validation_timestamp must be ISO 8601 format, got: {v}")
        return v


class OptionalProofCarryingResponse(BaseModel):
    """
    Response model with OPTIONAL proof-carrying fields.
    
    Use this for responses that MAY contain reasoning but don't always.
    For example, health checks, metrics, or status endpoints.
    
    If fortress_validated is True, all other fields become mandatory.
    """
    
    model_config = ConfigDict()
    
    fortress_validated: Optional[bool] = Field(
        default=None,
        description="Whether this response has been validated (None if not applicable)"
    )
    
    audit_hash: Optional[str] = Field(
        default=None,
        description="Forensic audit hash (if validated)"
    )
    
    validation_timestamp: Optional[str] = Field(
        default=None,
        description="Validation timestamp (if validated)"
    )
    
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID (if applicable)"
    )
    
    @model_validator(mode='after')
    def validate_proof_fields_if_validated(self):
        """If fortress_validated is True, all proof fields must be present"""
        if self.fortress_validated is True:
            if self.audit_hash is None or self.validation_timestamp is None or self.correlation_id is None:
                raise ValueError(
                    "If fortress_validated is True, all proof-carrying fields must be present"
                )
        return self


# ============================================================================
# SERIALIZATION HELPERS
# ============================================================================

def inject_proof_carrying_metadata(
    response_dict: dict,
    fortress_validated: bool,
    audit_hash: str,
    validation_timestamp: str,
    correlation_id: str
) -> dict:
    """
    Inject proof-carrying metadata into response dictionary.
    
    Use this helper when constructing API responses manually.
    
    Args:
        response_dict: Original response dictionary
        fortress_validated: Validation status
        audit_hash: Forensic hash
        validation_timestamp: ISO 8601 timestamp
        correlation_id: Tracing ID
        
    Returns:
        Response dictionary with proof-carrying metadata
        
    Example:
        response = {"result": "Tax exemption applies", "confidence": 0.92}
        response = inject_proof_carrying_metadata(
            response,
            fortress_validated=True,
            audit_hash="abc123",
            validation_timestamp="2026-05-14T04:30:00Z",
            correlation_id="req-001"
        )
    """
    response_dict.update({
        "fortress_validated": fortress_validated,
        "audit_hash": audit_hash,
        "validation_timestamp": validation_timestamp,
        "correlation_id": correlation_id
    })
    return response_dict


def validate_proof_carrying_metadata(response_dict: dict) -> bool:
    """
    Validate that response dictionary contains all proof-carrying fields.
    
    Args:
        response_dict: Response dictionary to validate
        
    Returns:
        True if all fields present and valid, False otherwise
        
    Example:
        if not validate_proof_carrying_metadata(response):
            raise ValueError("Missing proof-carrying metadata")
    """
    required_fields = [
        'fortress_validated',
        'audit_hash',
        'validation_timestamp',
        'correlation_id'
    ]
    
    for field in required_fields:
        if field not in response_dict:
            return False
        if response_dict[field] is None:
            return False
    
    # Validate fortress_validated is True
    if not response_dict['fortress_validated']:
        return False
    
    return True
