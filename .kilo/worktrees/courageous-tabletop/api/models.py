"""
API Data Models
===============
Pydantic v2 models for request/response validation
"""

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import uuid


# ============================================================================
# Enums
# ============================================================================
class UserRole(str, Enum):
    """User roles"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class DocumentType(str, Enum):
    """Document types"""
    LAW = "law"
    CASE = "case"
    CONTRACT = "contract"
    REGULATION = "regulation"
    OTHER = "other"


# ============================================================================
# Authentication Models
# ============================================================================
class UserLogin(BaseModel):
    """User login request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserRegister(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

    @field_validator('password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class User(BaseModel):
    """User model"""
    id: uuid.UUID
    username: str
    email: EmailStr
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = ConfigDict(use_enum_values=True)


# ============================================================================
# Document Ingestion Models
# ============================================================================
class DocumentIngest(BaseModel):
    """Document ingestion request"""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10)
    doc_type: DocumentType
    law_id: Optional[str] = None
    case_id: Optional[str] = None
    date_published: Optional[datetime] = None
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

    model_config = ConfigDict(use_enum_values=True)


class DocumentIngestResponse(BaseModel):
    """Document ingestion response"""
    doc_id: str
    status: str
    message: str
    chunks_created: int
    embeddings_created: int
    graph_nodes_created: int


# ============================================================================
# Job Management Models (Phase 6 - Async)
# ============================================================================
class JobStatus(str, Enum):
    """Job status enum"""
    QUEUED = "queued"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobProgressInfo(BaseModel):
    """Job progress information"""
    current_step: str = Field(..., description="Current processing step")
    percent: int = Field(..., ge=0, le=100, description="Progress percentage")
    sub_steps: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Sub-step completion status (vector, graph, sync)"
    )


class JobSubmissionResponse(BaseModel):
    """Response when submitting a new ingestion job"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(default=JobStatus.QUEUED)
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    message: str = Field(default="Job submitted successfully")


class JobStatusResponse(BaseModel):
    """Response for job status query"""
    job_id: str
    status: JobStatus
    progress: Optional[JobProgressInfo] = None
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Result object when completed"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobListResponse(BaseModel):
    """Response for listing jobs"""
    jobs: List[JobStatusResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# Dead Letter Queue (DLQ) Models
# ============================================================================
class DLQErrorType(str, Enum):
    """DLQ error types"""
    OOM = "OOM"
    CORRUPTED_FILE = "CorruptedFile"
    PARSE_ERROR = "ParseError"
    TIMEOUT = "Timeout"
    UNKNOWN = "Unknown"


class DLQItem(BaseModel):
    """Dead Letter Queue item"""
    job_id: str
    file_name: str
    failed_at: datetime
    error_type: DLQErrorType
    error_message: str
    retry_count: int = 0
    can_retry: bool = True
    original_metadata: Optional[Dict[str, Any]] = None


class DLQListResponse(BaseModel):
    """Response for listing DLQ items"""
    items: List[DLQItem]
    total: int


class DLQRetryResponse(BaseModel):
    """Response for DLQ retry operation"""
    success: bool
    new_job_id: Optional[str] = None
    message: str


# ============================================================================
# Analysis Models
# ============================================================================
class AnalysisRequest(BaseModel):
    """Legal analysis request"""
    query: str = Field(..., min_length=5, max_length=1000)
    top_k: int = Field(default=10, ge=1, le=50)
    use_gat_reranking: bool = True
    use_guardrails: bool = True
    return_explanations: bool = False
    return_uncertainty: bool = True


class CitationInfo(BaseModel):
    """Citation information"""
    text: str
    source_id: str
    confidence: float
    is_verified: bool


class UncertaintyInfo(BaseModel):
    """Uncertainty information"""
    epistemic: float
    aleatoric: float
    total: float


class GuardrailsResult(BaseModel):
    """Guardrails verification result"""
    nli_supported: bool
    nli_confidence: float
    citation_accuracy: float
    hallucination_detected: bool
    hallucination_score: float
    warnings: List[str] = []


class RetrievedDocument(BaseModel):
    """Retrieved document"""
    doc_id: str
    text: str
    score: float
    law_id: Optional[str]
    case_id: Optional[str]
    source: Optional[str]
    uncertainty: Optional[UncertaintyInfo]


class AnalysisResponse(BaseModel):
    """Legal analysis response"""
    request_id: uuid.UUID
    query: str
    answer: str
    confidence: float
    retrieved_documents: List[RetrievedDocument]
    citations: List[CitationInfo]
    guardrails: Optional[GuardrailsResult]
    uncertainty: Optional[UncertaintyInfo]
    reasoning_steps: Optional[List[str]]
    latency_ms: int
    timestamp: datetime


# ============================================================================
# Audit Models
# ============================================================================
class AuditLogEntry(BaseModel):
    """Audit log entry"""
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    request_id: uuid.UUID
    endpoint: str
    method: str
    query_text: Optional[str]
    answer_generated: Optional[str]
    nli_verification: Optional[Dict]
    hallucination_check: Optional[Dict]
    uncertainty_score: Optional[float]
    latency_ms: int
    status_code: int
    ip_address: str
    created_at: datetime


class AuditLogQuery(BaseModel):
    """Audit log query parameters"""
    user_id: Optional[uuid.UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    endpoint: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ============================================================================
# Explainability Models
# ============================================================================
class ExplainabilityRequest(BaseModel):
    """Explainability request"""
    request_id: uuid.UUID


class ReasoningStep(BaseModel):
    """Reasoning step"""
    step_number: int
    description: str
    evidence: List[str]
    confidence: float


class GraphPath(BaseModel):
    """Graph reasoning path"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    path_score: float


class ExplainabilityResponse(BaseModel):
    """Explainability response"""
    request_id: uuid.UUID
    query: str
    answer: str
    reasoning_steps: List[ReasoningStep]
    graph_path: Optional[GraphPath]
    evidence_documents: List[RetrievedDocument]
    confidence_breakdown: Dict[str, float]


# ============================================================================
# Admin Models
# ============================================================================
class SystemStats(BaseModel):
    """System statistics"""
    total_users: int
    total_documents: int
    total_queries: int
    avg_latency_ms: float
    nli_pass_rate: float
    hallucination_rate: float
    uptime_seconds: int


class HealthStatus(BaseModel):
    """Health status"""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, bool]
    metrics: Dict[str, Any]


# ============================================================================
# Error Models
# ============================================================================
class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[uuid.UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
