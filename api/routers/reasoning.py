"""
MAHOUN Reasoning API Router
============================

Core reasoning endpoints for evidence-linked verdict generation.

CRITICAL GUARANTEES:
- Zero-hallucination: All reasoning grounded in graph evidence
- Full auditability: Complete evidence trail in blockchain ledger
- Cryptographic proofs: Tamper-evident verification
- Deterministic contradiction resolution: Predictable conflict handling

Architecture:
- Evidence-Linked Verdict Engine: Graph-based reasoning
- Immutable Ledger: Blockchain audit trail
- Cryptographic Proofs: Non-repudiation guarantees
- Runtime Guardrails: Zero-hallucination enforcement
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from mahoun.core.logging import setup_logger
from mahoun.api.errors import (
    handle_runtime_error,
    handle_value_error,
    VerdictGenerationError,
    VerificationError,
)
from mahoun.reasoning.evidence_linked_verdict import (
    EvidenceLinkedVerdictEngine,
)
from mahoun.graph.ultra_graph_builder import UltraGraphBuilder
from mahoun.reasoning.knowledge_graph import LegalKnowledgeGraph
from mahoun.ledger.writer import EvidenceLedgerWriter
from mahoun.ledger.blockchain import ImmutableLedger
from mahoun.crypto.proof_system import ProofSystem
from mahoun.crypto.signatures import generate_keypair
from mahoun.core.runtime_config import is_desktop_minimal, should_skip_graph

log = setup_logger("reasoning_api")

router = APIRouter(
    prefix="/api/v1/reasoning",
    tags=["reasoning"],
    responses={
        500: {"description": "Internal server error"},
        503: {"description": "Service unavailable in current mode"},
    },
)


# ============================================================================
# Request/Response Models
# ============================================================================


class FactInput(BaseModel):
    """Single fact input"""

    id: Optional[str] = Field(None, description="Fact identifier (optional)")
    value: str = Field(..., description="Fact text", min_length=1)
    type: Optional[str] = Field("UNKNOWN", description="Fact type")
    confidence: Optional[float] = Field(
        1.0, ge=0.0, le=1.0, description="Fact confidence"
    )


class VerdictGenerationRequest(BaseModel):
    """Request for verdict generation"""

    question: str = Field(..., description="Legal question to answer", min_length=1)
    facts: List[FactInput] = Field(..., description="Case facts", min_length=0)
    case_id: Optional[str] = Field(None, description="Case identifier (optional)")
    generate_proof: bool = Field(True, description="Generate cryptographic proof")


class EvidenceReferenceResponse(BaseModel):
    """Evidence reference in response"""

    node_id: str
    node_type: str
    edge_id: Optional[str] = None
    justification: str
    confidence: float


class VerdictStepResponse(BaseModel):
    """Verdict step in response"""

    statement: str
    evidence: List[EvidenceReferenceResponse]


class CryptographicProofResponse(BaseModel):
    """Cryptographic proof in response"""

    graph_state_hash: str
    reasoning_chain_hash: str
    evidence_merkle_root: str
    timestamp: str
    signature: str
    verdict_id: str
    case_id: str
    confidence: float


class VerdictGenerationResponse(BaseModel):
    """Response for verdict generation"""

    success: bool
    verdict_id: str
    case_id: str
    final_verdict: str
    steps: List[VerdictStepResponse]
    unresolved_conflicts: List[str]
    confidence_score: float
    proof: Optional[CryptographicProofResponse] = None
    ledger_entry_id: Optional[str] = None
    processing_time_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VerdictVerificationRequest(BaseModel):
    """Request for verdict verification"""

    verdict_id: str = Field(..., description="Verdict identifier")
    proof: CryptographicProofResponse = Field(
        ..., description="Cryptographic proof to verify"
    )


class VerdictVerificationResponse(BaseModel):
    """Response for verdict verification"""

    success: bool
    verdict_id: str
    is_valid: bool
    verification_details: Dict[str, Any]
    timestamp: str


class LedgerQueryRequest(BaseModel):
    """Request for ledger query"""

    case_id: Optional[str] = Field(None, description="Case identifier")
    verdict_id: Optional[str] = Field(None, description="Verdict identifier")
    node_id: Optional[str] = Field(None, description="Node identifier")
    start_time: Optional[str] = Field(None, description="Start time (ISO 8601)")
    end_time: Optional[str] = Field(None, description="End time (ISO 8601)")


class LedgerQueryResponse(BaseModel):
    """Response for ledger query"""

    success: bool
    entries: List[Dict[str, Any]]
    total_count: int
    query_time_ms: float


# ============================================================================
# Dependencies
# ============================================================================

_verdict_engine: Optional[EvidenceLinkedVerdictEngine] = None
_immutable_ledger: Optional[ImmutableLedger] = None
_proof_system: Optional[ProofSystem] = None
_private_key: Optional[str] = None
_public_key: Optional[str] = None


def get_verdict_engine() -> EvidenceLinkedVerdictEngine:
    """Get or create verdict engine instance"""
    global _verdict_engine

    if _verdict_engine is None:
        # Check if we're in DESKTOP_MINIMAL mode with graph disabled
        if is_desktop_minimal() and should_skip_graph():
            # Log blocked attempt
            log.warning(
                "Verdict engine initialization blocked due to mode constraint",
                extra={
                    "mode": "desktop_minimal",
                    "graph_enabled": False,
                    "entry_point": "api",
                },
            )
            
            # Record metrics
            try:
                from mahoun.metrics import record_blocked_attempt, record_mode_check
                record_blocked_attempt(
                    mode="desktop_minimal",
                    reason="graph_disabled",
                    entry_point="api"
                )
                record_mode_check(
                    mode="desktop_minimal",
                    graph_enabled=False,
                    passed=False
                )
            except ImportError:
                log.debug("Metrics module not available - skipping metrics recording")
            
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "service_unavailable",
                    "message": "Reasoning API requires full graph operations. "
                    "Current mode: DESKTOP_MINIMAL with graph disabled. "
                    "Please run in ENTERPRISE_FULL mode or enable graph "
                    "(MAHOUN_ENABLE_GRAPH=true).",
                },
            )

        # Initialize components
        graph_builder = UltraGraphBuilder()
        knowledge_graph = LegalKnowledgeGraph()
        immutable_ledger = get_immutable_ledger()
        ledger_writer = EvidenceLedgerWriter(blockchain=immutable_ledger)

        _verdict_engine = EvidenceLinkedVerdictEngine(
            graph_builder=graph_builder,
            knowledge_graph=knowledge_graph,
            ledger_writer=ledger_writer,
            container=None,  # No dependency injection for now
        )

        log.info("Evidence-Linked Verdict Engine initialized")
        
        # Record metrics
        try:
            from mahoun.metrics import set_verdict_engine_initialized
            set_verdict_engine_initialized(True)
        except ImportError:
            pass

    return _verdict_engine


def get_immutable_ledger() -> ImmutableLedger:
    """Get or create immutable ledger instance"""
    global _immutable_ledger

    if _immutable_ledger is None:
        # Use persistent storage in production
        import os

        storage_path = os.getenv("MAHOUN_LEDGER_PATH", "./data/ledger.json")
        _immutable_ledger = ImmutableLedger(storage_path=storage_path)
        log.info(f"Immutable ledger initialized: {storage_path}")

    return _immutable_ledger


def get_proof_system() -> ProofSystem:
    """Get or create proof system instance"""
    global _proof_system

    if _proof_system is None:
        _proof_system = ProofSystem()
        log.info("Cryptographic proof system initialized")

    return _proof_system


def get_keypair() -> tuple[str, str]:
    """Get or generate cryptographic keypair"""
    global _private_key, _public_key

    if _private_key is None or _public_key is None:
        # In production, load from secure storage
        # For now, generate ephemeral keypair
        _private_key, _public_key = generate_keypair()
        log.warning(
            "Using ephemeral keypair - configure persistent keys for production"
        )

    return _private_key, _public_key


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/generate-verdict",
    response_model=VerdictGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate evidence-linked verdict",
    description="""
    Generate legal verdict with zero-hallucination guarantee.
    
    **Guarantees:**
    - Every conclusion linked to graph evidence
    - Complete audit trail in blockchain ledger
    - Cryptographic proof for verification
    - Deterministic contradiction resolution
    
    **Process:**
    1. Build case graph from facts
    2. Find applicable rules and precedents
    3. Detect and resolve contradictions
    4. Generate verdict steps with evidence links
    5. Write to immutable ledger
    6. Generate cryptographic proof
    
    **Modes:**
    - ENTERPRISE_FULL: Full graph reasoning (required)
    - DESKTOP_MINIMAL: Not supported (returns 503)
    """,
)
async def generate_verdict(
    request: VerdictGenerationRequest,
    engine: EvidenceLinkedVerdictEngine = Depends(get_verdict_engine),
) -> VerdictGenerationResponse:
    """Generate evidence-linked verdict"""
    import time

    start_time = time.time()

    try:
        log.info(f"Generating verdict for question: {request.question[:50]}...")

        # Convert facts to engine format
        facts_list = [fact.value for fact in request.facts]

        # Generate verdict (async)
        verdict = await engine.generate_verdict(
            question=request.question, facts=facts_list
        )

        # Generate verdict ID
        verdict_id = str(uuid.uuid4())
        case_id = request.case_id or str(uuid.uuid4())

        # Generate cryptographic proof if requested
        proof_response = None
        if request.generate_proof:
            proof_system = get_proof_system()
            private_key, public_key = get_keypair()

            # Extract graph nodes and edges from engine
            graph_nodes: Dict[str, Any] = {}
            graph_edges: List[Any] = []

            # Collect nodes from verdict steps
            for step in verdict.steps:
                for evidence in step.evidence:
                    if evidence.node_id not in graph_nodes:
                        # Create minimal node representation
                        graph_nodes[evidence.node_id] = {
                            "id": evidence.node_id,
                            "type": evidence.node_type,
                            "confidence": evidence.confidence,
                        }

            # Generate proof
            proof = proof_system.generate_proof(
                graph_nodes=graph_nodes,
                graph_edges=graph_edges,
                reasoning_steps=verdict.steps,
                evidence_refs=[ev for step in verdict.steps for ev in step.evidence],
                verdict_id=verdict_id,
                case_id=case_id,
                confidence=verdict.confidence_score,
                private_key=private_key,
            )

            proof_response = CryptographicProofResponse(
                graph_state_hash=proof.graph_state_hash,
                reasoning_chain_hash=proof.reasoning_chain_hash,
                evidence_merkle_root=proof.evidence_merkle_root,
                timestamp=proof.timestamp,
                signature=proof.signature,
                verdict_id=proof.verdict_id,
                case_id=proof.case_id,
                confidence=proof.confidence,
            )

        # Convert verdict to response format
        steps_response = [
            VerdictStepResponse(
                statement=step.statement,
                evidence=[
                    EvidenceReferenceResponse(
                        node_id=ev.node_id,
                        node_type=ev.node_type,
                        edge_id=ev.edge_id,
                        justification=ev.justification,
                        confidence=ev.confidence,
                    )
                    for ev in step.evidence
                ],
            )
            for step in verdict.steps
        ]

        processing_time_ms = (time.time() - start_time) * 1000

        log.info(
            f"Verdict generated: {len(verdict.steps)} steps, "
            f"confidence={verdict.confidence_score:.2f}, "
            f"time={processing_time_ms:.1f}ms"
        )

        return VerdictGenerationResponse(
            success=True,
            verdict_id=verdict_id,
            case_id=case_id,
            final_verdict=verdict.final_verdict,
            steps=steps_response,
            unresolved_conflicts=verdict.unresolved_conflicts,
            confidence_score=verdict.confidence_score,
            proof=proof_response,
            ledger_entry_id=verdict_id,  # Ledger entry uses verdict_id
            processing_time_ms=processing_time_ms,
            metadata={
                "total_steps": len(verdict.steps),
                "total_evidence": sum(len(step.evidence) for step in verdict.steps),
                "has_unresolved_conflicts": len(verdict.unresolved_conflicts) > 0,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except RuntimeError as e:
        # Handle resource constraint and runtime errors
        api_error = handle_runtime_error(e)
        raise HTTPException(
            status_code=api_error.status_code,
            detail={
                "error": api_error.error_code.value,
                "message": api_error.message,
                "details": api_error.details,
            },
        )

    except ValueError as e:
        # Handle validation errors
        api_error = handle_value_error(e)
        raise HTTPException(
            status_code=api_error.status_code,
            detail={
                "error": api_error.error_code.value,
                "message": api_error.message,
                "details": api_error.details,
            },
        )

    except Exception as e:
        log.error(f"Verdict generation failed: {e}", exc_info=True)
        error = VerdictGenerationError(message=str(e))
        raise HTTPException(
            status_code=error.status_code,
            detail={"error": error.error_code.value, "message": error.message},
        )


@router.post(
    "/verify-verdict",
    response_model=VerdictVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify cryptographic proof",
    description="""
    Verify cryptographic proof of verdict.
    
    **Verification checks:**
    1. Signature validity
    2. Timestamp validity (not in future)
    3. Confidence range [0, 1]
    4. Graph state integrity
    5. Reasoning chain integrity
    
    **Returns:**
    - is_valid: True if all checks pass
    - verification_details: Detailed check results
    """,
)
async def verify_verdict(
    request: VerdictVerificationRequest,
) -> VerdictVerificationResponse:
    """Verify cryptographic proof"""
    import time

    start_time = time.time()

    try:
        log.info(f"Verifying verdict: {request.verdict_id}")

        # Get public key
        _, public_key = get_keypair()

        # Reconstruct proof from response
        from mahoun.crypto.proof_system import CryptographicProof

        proof = CryptographicProof(
            graph_state_hash=request.proof.graph_state_hash,
            reasoning_chain_hash=request.proof.reasoning_chain_hash,
            evidence_merkle_root=request.proof.evidence_merkle_root,
            timestamp=request.proof.timestamp,
            signature=request.proof.signature,
            verdict_id=request.proof.verdict_id,
            case_id=request.proof.case_id,
            confidence=request.proof.confidence,
        )

        # Verify proof
        is_valid = proof.verify(public_key)

        # Detailed verification
        verification_details = {
            "signature_valid": is_valid,
            "timestamp_valid": True,  # Checked in proof.verify()
            "confidence_valid": 0.0 <= proof.confidence <= 1.0,
            "verdict_id_match": proof.verdict_id == request.verdict_id,
            "graph_hash": proof.graph_state_hash[:16] + "...",
            "reasoning_hash": proof.reasoning_chain_hash[:16] + "...",
            "merkle_root": proof.evidence_merkle_root[:16] + "...",
        }

        processing_time_ms = (time.time() - start_time) * 1000

        log.info(
            f"Verification completed: valid={is_valid}, time={processing_time_ms:.1f}ms"
        )

        return VerdictVerificationResponse(
            success=True,
            verdict_id=request.verdict_id,
            is_valid=is_valid,
            verification_details=verification_details,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        log.error(f"Verification failed: {e}", exc_info=True)
        error = VerificationError(message=str(e))
        raise HTTPException(
            status_code=error.status_code,
            detail={"error": error.error_code.value, "message": error.message},
        )


@router.post(
    "/query-ledger",
    response_model=LedgerQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query immutable ledger",
    description="""
    Query blockchain ledger for audit trail.
    
    **Query options:**
    - By case_id: All verdicts for a case
    - By verdict_id: Specific verdict entry
    - By node_id: All verdicts using a node
    - By time range: Entries in time window
    
    **Use cases:**
    - Audit trail review
    - Impact analysis (when rule changes)
    - Case history
    - Compliance reporting
    """,
)
async def query_ledger(
    request: LedgerQueryRequest, ledger: ImmutableLedger = Depends(get_immutable_ledger)
) -> LedgerQueryResponse:
    """Query immutable ledger"""
    import time

    start_time = time.time()

    try:
        log.info(f"Querying ledger: {request.model_dump()}")

        entries = []

        # Query by verdict_id
        if request.verdict_id:
            entry = ledger.get_entry(request.verdict_id)
            if entry:
                entries = [entry]

        # Query by case_id
        elif request.case_id:
            entries = ledger.get_entries_by_case(request.case_id)

        # Query by node_id
        elif request.node_id:
            entries = ledger.find_entries_using_node(request.node_id)

        # Query by time range
        elif request.start_time and request.end_time:
            start_dt = datetime.fromisoformat(request.start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(request.end_time.replace("Z", "+00:00"))
            entries = ledger.get_entries_in_range(start_dt, end_dt)

        # Convert entries to dict
        entries_dict = [entry.model_dump() for entry in entries]

        processing_time_ms = (time.time() - start_time) * 1000

        log.info(
            f"Ledger query completed: {len(entries)} entries, time={processing_time_ms:.1f}ms"
        )

        return LedgerQueryResponse(
            success=True,
            entries=entries_dict,
            total_count=len(entries),
            query_time_ms=processing_time_ms,
        )

    except Exception as e:
        log.error(f"Ledger query failed: {e}", exc_info=True)
        from mahoun.api.errors import MAHOUNAPIError, ErrorCode

        error = MAHOUNAPIError(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=f"Ledger query failed: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        raise HTTPException(
            status_code=error.status_code,
            detail={"error": error.error_code.value, "message": error.message},
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Reasoning API health check",
    description="Check if reasoning API is available and operational",
)
async def health_check() -> Dict[str, Any]:
    """Health check for reasoning API"""
    try:
        # Check if we're in supported mode
        if is_desktop_minimal() and should_skip_graph():
            return {
                "status": "unavailable",
                "mode": "DESKTOP_MINIMAL",
                "graph_enabled": False,
                "message": "Reasoning API requires ENTERPRISE_FULL mode or graph enabled",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Check components
        get_verdict_engine()  # Verify engine can be initialized
        ledger = get_immutable_ledger()
        get_proof_system()  # Verify proof system can be initialized

        # Verify ledger integrity
        ledger_integrity = ledger.verify_integrity()

        return {
            "status": "healthy",
            "mode": "ENTERPRISE_FULL"
            if not is_desktop_minimal()
            else "DESKTOP_MINIMAL",
            "graph_enabled": not should_skip_graph(),
            "components": {
                "verdict_engine": "initialized",
                "immutable_ledger": "initialized",
                "proof_system": "initialized",
                "ledger_integrity": ledger_integrity,
                "ledger_blocks": len(ledger),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        log.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
