"""
Document Ingestion Router
==========================
Upload and process legal documents
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import uuid
import logging

from api.models import (
    DocumentIngest,
    DocumentIngestResponse,
    User,
    JobSubmissionResponse,
    JobStatusResponse,
    JobListResponse,
    JobStatus,
    DLQItem,
    DLQListResponse,
    DLQRetryResponse,
    DLQErrorType,
)
from api.auth.dependencies import require_analyst, get_optional_user
from api.database import get_postgres
from typing import Any, Optional

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# Lazy initialization of ingestion pipeline & unified loader
# ============================================================================

_ingestion_pipeline: Optional[Any] = None
_unified_loader: Optional[Any] = None


async def get_unified_loader():
    """
    Lazy init UnifiedLoader for async job-based ingestion.

    This is the Phase 6 async orchestrator that handles:
    - Job queue management
    - Atomic transactions
    - Retry logic with exponential backoff
    - Dead Letter Queue (DLQ)
    """
    global _unified_loader

    if _unified_loader is None:
        try:
            from mahoun.orchestrator.unified_loader import UnifiedLoader

            _unified_loader = UnifiedLoader(worker_count=2)
            await _unified_loader.initialize()

            logger.info("Initialized UnifiedLoader for async job-based ingestion")
        except ImportError as e:
            logger.error(f"Could not import UnifiedLoader: {e}")
            _unified_loader = None
        except Exception as e:
            logger.error(f"Could not initialize UnifiedLoader: {e}")
            _unified_loader = None

    return _unified_loader


async def get_ingestion_pipeline():
    """
    Lazy init ingestion pipeline.

    This creates a single shared pipeline instance for the API router.
    The pipeline coordinates chunking, embedding, and vector storage.

    Can use EnhancedIngestionPipeline if USE_ENHANCED_INGESTION env var is set.
    """
    global _ingestion_pipeline
    import os

    if _ingestion_pipeline is None:
        try:
            # Check if enhanced pipeline should be used
            use_enhanced = (
                os.getenv("USE_ENHANCED_INGESTION", "false").lower() == "true"
            )

            if use_enhanced:
                try:
                    from mahoun.pipelines.ingestion.enhanced_pipeline import (
                        EnhancedIngestionPipeline,
                    )

                    _ingestion_pipeline = EnhancedIngestionPipeline(
                        enable_llm_refinement=True,
                        enable_cross_validation=True,
                        enable_validation=True,
                    )
                    await _ingestion_pipeline.initialize()

                    logger.info("Initialized EnhancedIngestionPipeline for ingest API")
                except ImportError as e:
                    logger.warning(
                        f"Enhanced pipeline not available: {e}. Falling back to standard pipeline."
                    )
                    use_enhanced = False

            if not use_enhanced:
                from mahoun.pipelines.ingestion.pipeline import IngestionPipeline

                _ingestion_pipeline = IngestionPipeline()
                await _ingestion_pipeline.initialize()

                logger.info("Initialized IngestionPipeline for ingest API")

        except ImportError as e:
            logger.error(f"Could not import IngestionPipeline: {e}")
            _ingestion_pipeline = None
        except Exception as e:
            logger.error(f"Could not initialize IngestionPipeline: {e}")
            _ingestion_pipeline = None
    return _ingestion_pipeline


def _build_upload_response(
    file_path: str,
    filename: str,
    mime: str,
    include_text: bool,
) -> dict:
    import hashlib
    from pathlib import Path
    from mahoun.pipelines.ingestion.document_handlers import extract_document_text

    extracted = extract_document_text(file_path)
    text = extracted.text or ""
    file_bytes = Path(file_path).read_bytes()
    file_sha256 = hashlib.sha256(file_bytes).hexdigest()

    response = {
        "doc_id": str(uuid.uuid4()),
        "filename": filename,
        "mime": mime,
        "sha256": file_sha256,
        "text_length": len(text),
        "text_preview": text[:2000],
        "extraction_method": extracted.metadata.get("extraction_method"),
    }

    if include_text:
        response["text"] = text

    if not extracted.success:
        response["extraction_error"] = (
            extracted.metadata.get("error") or extracted.error
        )

    return response


# ============================================================================
# Routes
# ============================================================================


@router.post("/", response_model=DocumentIngestResponse)
async def ingest_document(
    document: DocumentIngest,
    current_user: User = Depends(require_analyst),
    db=Depends(get_postgres),
):
    """
    Ingest legal document into MAHOUN system

    Requires: analyst or admin role

    Pipeline:
    1. Store metadata in PostgreSQL
    2. Chunk document text
    3. Generate embeddings
    4. (Future) Store in vector DB
    5. (Future) Build graph relationships
    """
    # Generate UUIDs consistently as strings for database compatibility
    record_id = str(uuid.uuid4())  # Primary key for the database record
    doc_id = str(uuid.uuid4())  # Document identifier
    chunks_created = 0
    embeddings_created = 0
    indexed = False
    graph_nodes_created = 0

    try:
        # Store metadata in PostgreSQL
        await db.execute(
            """
            INSERT INTO documents_metadata 
            (id, doc_id, title, law_type, law_id, case_id, date_published, source)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            record_id,
            doc_id,
            document.title,
            document.doc_type.value,
            document.law_id,
            document.case_id,
            document.date_published,
            document.source,
        )

        # Get ingestion pipeline
        pipeline = await get_ingestion_pipeline()

        if pipeline and document.content:
            # Run full ingestion: chunking + embedding + vector storage
            metadata = {
                "title": document.title,
                "doc_type": document.doc_type.value,
                "law_id": document.law_id,
                "case_id": document.case_id,
                "date_published": str(document.date_published)
                if document.date_published
                else None,
                "source": document.source,
            }

            result = await pipeline.ingest_document(
                doc_id=doc_id, text=document.content, metadata=metadata
            )

            chunks_created = result.chunks_created
            embeddings_created = result.embeddings_created
            indexed = result.indexed

            logger.info(
                f"Ingested document {doc_id}: "
                f"{chunks_created} chunks, {embeddings_created} embeddings, indexed={indexed}"
            )
        else:
            if not pipeline:
                logger.warning(
                    "Ingestion pipeline not available, document not fully processed"
                )
            if not document.content:
                logger.warning(f"No content provided for document {doc_id}")

        import os

        graph_build_enabled = (
            os.getenv("MAHOUN_GRAPH_BUILD_ENABLED", "false").lower() == "true"
        )

        if document.content and graph_build_enabled:
            try:
                from mahoun.pipelines.ingestion.minimal_verdict_parser import (
                    parse_verdict_text,
                    validate_verdict_struct,
                )
                from mahoun.pipelines.graph_build import GraphBuildPipeline

                verdict_struct = parse_verdict_text(document.content)
                is_valid, errors = validate_verdict_struct(verdict_struct)
                confidence = verdict_struct.get("_parsing_quality", {}).get(
                    "confidence_score", 0.0
                )

                if is_valid and confidence >= 0.6:
                    graph_pipeline = GraphBuildPipeline()
                    graph_result = graph_pipeline.build_from_verdict(
                        verdict_struct, source_id=doc_id
                    )
                    if graph_result.success:
                        graph_nodes_created = graph_result.nodes_created
                    else:
                        logger.warning(
                            f"Graph build failed for {doc_id}: {graph_result.error}"
                        )
                else:
                    if not is_valid:
                        logger.info(
                            f"Graph build skipped for {doc_id}: invalid verdict structure "
                            f"({len(errors)} errors)"
                        )
                    else:
                        logger.info(
                            f"Graph build skipped for {doc_id}: parsing confidence {confidence:.2f} below threshold"
                        )
            except Exception as e:
                logger.warning(
                    f"Graph build step failed for {doc_id}: {e}", exc_info=True
                )
        elif document.content:
            logger.info("Graph build skipped (MAHOUN_GRAPH_BUILD_ENABLED=false)")

        # Build status message
        # NOTE: Use `ingest_status` to avoid shadowing FastAPI's `status` module
        if indexed:
            message = f"Document ingested and indexed successfully ({chunks_created} chunks, {embeddings_created} embeddings)"
            ingest_status = "success"
        elif chunks_created > 0:
            message = f"Document processed but not fully indexed ({chunks_created} chunks created)"
            ingest_status = "partial"
        else:
            message = "Document metadata stored but content not processed"
            ingest_status = "metadata_only"

        return DocumentIngestResponse(
            doc_id=doc_id,
            status=ingest_status,
            message=message,
            chunks_created=chunks_created,
            embeddings_created=embeddings_created,
            graph_nodes_created=graph_nodes_created,
        )

    except Exception as e:
        logger.error(f"Ingestion failed for document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    include_text: bool = False,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Upload document file (PDF, DOCX, TXT)

    Supported formats:
    - PDF: Requires pdfplumber or pypdf
    - DOCX: Requires python-docx
    - TXT: Native support

    Note: Authentication is optional for file upload.
    If authenticated, user info will be logged for audit purposes.
    Use include_text=true to return full extracted text.
    """
    # Log upload with user info if available
    if current_user:
        logger.info(
            f"File upload by user: {current_user.username} (ID: {current_user.id})"
        )
    else:
        logger.info("File upload by anonymous user")
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
        )

    # Get file extension
    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""

    supported_formats = {"pdf", "docx", "txt", "md"}
    if file_ext not in supported_formats:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported format: {file_ext}. Supported: {sorted(supported_formats)}",
        )

    try:
        # Read file content
        content = await file.read()
        mime = file.content_type or "application/octet-stream"

        import tempfile
        from pathlib import Path

        suffix = f".{file_ext}" if file_ext else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            response = _build_upload_response(
                str(tmp_path),
                filename=file.filename,
                mime=mime,
                include_text=include_text,
            )
        finally:
            try:
                tmp_path.unlink()
            except Exception:
                logger.debug("Temporary upload file cleanup failed", exc_info=True)

        return response

    except Exception as e:
        logger.error(f"File upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )


# ============================================================================
# Phase 6: Async Job-Based Ingestion Endpoints
# ============================================================================


@router.post("/submit", response_model=JobSubmissionResponse)
async def submit_ingestion_job(
    file: UploadFile = File(...),
    doc_type: str = "contract",
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Submit document for async ingestion (Phase 6)

    Returns immediately with job_id. Client should poll /jobs/{job_id} for status.

    Features:
    - Async processing with worker queue
    - Atomic transactions (rollback on failure)
    - Retry logic with exponential backoff
    - Dead Letter Queue for failed jobs
    """
    loader = await get_unified_loader()

    if not loader:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unified loader not available",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
        )

    try:
        # Save file temporarily
        import tempfile
        from pathlib import Path

        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        suffix = f".{file_ext}" if file_ext else ""

        # Create temp file
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb") as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        # Submit to unified loader
        metadata = {
            "filename": file.filename,
            "doc_type": doc_type,
            "uploaded_by": current_user.username if current_user else "anonymous",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }

        job_id = await loader.submit_file(str(tmp_path), metadata)

        logger.info(
            f"Job {job_id} submitted for file {file.filename} "
            f"by {current_user.username if current_user else 'anonymous'}"
        )

        return JobSubmissionResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            submitted_at=datetime.now(timezone.utc),
            message=f"Job submitted successfully. Poll /jobs/{job_id} for status.",
        )

    except Exception as e:
        logger.error(f"Job submission failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job submission failed: {str(e)}",
        )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str, current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get status of an ingestion job

    Poll this endpoint to track job progress.

    Status flow: queued → processing → completed/failed
    """
    loader = await get_unified_loader()

    if not loader:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unified loader not available",
        )

    try:
        status_info = await loader.get_job_status(job_id)

        if status_info.get("status") == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
            )

        job = loader.jobs.get(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
            )

        # Map internal status to API status
        internal_status = status_info.get("status", "pending")
        if internal_status == "pending":
            api_status = JobStatus.QUEUED
        elif internal_status == "processing":
            api_status = JobStatus.PROCESSING
        elif internal_status == "completed":
            api_status = JobStatus.COMPLETED
        elif internal_status == "failed":
            api_status = JobStatus.FAILED
        else:
            api_status = JobStatus.PENDING

        # Build progress info
        progress = None
        if api_status == JobStatus.PROCESSING:
            # Estimate progress based on typical pipeline stages
            progress = {
                "current_step": "processing",
                "percent": 50,  # Mid-way estimate
                "sub_steps": {"vector": True, "graph": False, "sync": False},
            }

        result_data = None
        error_msg = None

        if api_status == JobStatus.COMPLETED:
            result = status_info.get("result")
            if result:
                result_data = {
                    "doc_id": result.doc_id,
                    "vector_status": result.vector_status,
                    "graph_status": result.graph_status,
                    "sync_status": result.sync_status,
                    "node_count": result.node_count,
                }
        elif api_status == JobStatus.FAILED:
            result = status_info.get("result")
            if result and result.errors:
                error_msg = "; ".join(result.errors)

        return JobStatusResponse(
            job_id=job_id,
            status=api_status,
            progress=progress,
            result=result_data,
            error=error_msg,
            retry_count=job.retry_count,
            created_at=datetime.fromtimestamp(job.created_at),
            updated_at=datetime.now(timezone.utc)
            if api_status
            in [JobStatus.PROCESSING, JobStatus.COMPLETED, JobStatus.FAILED]
            else None,
            completed_at=datetime.now(timezone.utc)
            if api_status in [JobStatus.COMPLETED, JobStatus.FAILED]
            else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}",
        )


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status_filter: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    List all ingestion jobs

    Query parameters:
    - status: Filter by status (queued, processing, completed, failed)
    - limit: Max results (default 20)
    - offset: Pagination offset (default 0)
    """
    loader = await get_unified_loader()

    if not loader:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unified loader not available",
        )

    try:
        all_jobs = list(loader.jobs.values())

        # Filter by status if provided
        if status_filter:
            all_jobs = [j for j in all_jobs if j.status == status_filter]

        # Sort by created_at descending
        all_jobs.sort(key=lambda j: j.created_at, reverse=True)

        # Paginate
        total = len(all_jobs)
        paginated_jobs = all_jobs[offset : offset + limit]

        # Convert to response models
        job_responses = []
        for job in paginated_jobs:
            # Map status
            if job.status == "pending":
                api_status = JobStatus.QUEUED
            elif job.status == "processing":
                api_status = JobStatus.PROCESSING
            elif job.status == "completed":
                api_status = JobStatus.COMPLETED
            elif job.status == "failed":
                api_status = JobStatus.FAILED
            else:
                api_status = JobStatus.PENDING

            result_data = None
            error_msg = None

            if job.result:
                if job.result.success:
                    result_data = {
                        "doc_id": job.result.doc_id,
                        "vector_status": job.result.vector_status,
                        "graph_status": job.result.graph_status,
                        "sync_status": job.result.sync_status,
                        "node_count": job.result.node_count,
                    }
                else:
                    if job.result.errors:
                        error_msg = "; ".join(job.result.errors)

            job_responses.append(
                JobStatusResponse(
                    job_id=job.job_id,
                    status=api_status,
                    result=result_data,
                    error=error_msg,
                    retry_count=job.retry_count,
                    created_at=datetime.fromtimestamp(job.created_at),
                    updated_at=datetime.now(timezone.utc)
                    if api_status != JobStatus.QUEUED
                    else None,
                    completed_at=datetime.now(timezone.utc)
                    if api_status in [JobStatus.COMPLETED, JobStatus.FAILED]
                    else None,
                )
            )

        return JobListResponse(
            jobs=job_responses, total=total, page=(offset // limit) + 1, page_size=limit
        )

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}",
        )


# ============================================================================
# Dead Letter Queue (DLQ) Endpoints
# ============================================================================


@router.get("/dlq", response_model=DLQListResponse)
async def list_dlq_items(current_user: Optional[User] = Depends(get_optional_user)):
    """
    List all items in Dead Letter Queue

    Shows failed jobs that couldn't be processed after retries.
    """
    loader = await get_unified_loader()

    if not loader:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unified loader not available",
        )

    try:
        import json
        from pathlib import Path

        dlq_dir = loader.dlq_dir
        dlq_items = []

        # Scan DLQ directory for error files
        if dlq_dir.exists():
            for error_file in dlq_dir.glob("*.error.json"):
                try:
                    with open(error_file, "r") as f:
                        error_data = json.load(f)

                    # Determine error type
                    error_msg = (
                        error_data.get("errors", ["Unknown"])[0]
                        if error_data.get("errors")
                        else "Unknown"
                    )
                    if "memory" in error_msg.lower() or "oom" in error_msg.lower():
                        error_type = DLQErrorType.OOM
                    elif "corrupt" in error_msg.lower():
                        error_type = DLQErrorType.CORRUPTED_FILE
                    elif "parse" in error_msg.lower():
                        error_type = DLQErrorType.PARSE_ERROR
                    elif "timeout" in error_msg.lower():
                        error_type = DLQErrorType.TIMEOUT
                    else:
                        error_type = DLQErrorType.UNKNOWN

                    # Get file name from original path
                    original_path = error_data.get("original_path", "")
                    file_name = Path(original_path).name if original_path else "unknown"

                    dlq_items.append(
                        DLQItem(
                            job_id=error_data.get("job_id", "unknown"),
                            file_name=file_name,
                            failed_at=datetime.fromtimestamp(
                                error_data.get("timestamp", 0)
                            ),
                            error_type=error_type,
                            error_message=error_msg,
                            retry_count=0,  # TODO: Track retry count in DLQ
                            can_retry=True,  # TODO: Determine based on error type
                            original_metadata=None,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse DLQ error file {error_file}: {e}")
                    continue

        # Sort by failed_at descending
        dlq_items.sort(key=lambda x: x.failed_at, reverse=True)

        return DLQListResponse(items=dlq_items, total=len(dlq_items))

    except Exception as e:
        logger.error(f"Failed to list DLQ items: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list DLQ items: {str(e)}",
        )


@router.get("/dlq/{job_id}", response_model=DLQItem)
async def get_dlq_item(
    job_id: str, current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get details of a specific DLQ item
    """
    loader = await get_unified_loader()

    if not loader:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unified loader not available",
        )

    try:
        import json
        from pathlib import Path

        dlq_dir = loader.dlq_dir

        # Find error file for this job_id
        for error_file in dlq_dir.glob("*.error.json"):
            try:
                with open(error_file, "r") as f:
                    error_data = json.load(f)

                if error_data.get("job_id") == job_id:
                    # Found it
                    error_msg = (
                        error_data.get("errors", ["Unknown"])[0]
                        if error_data.get("errors")
                        else "Unknown"
                    )

                    if "memory" in error_msg.lower() or "oom" in error_msg.lower():
                        error_type = DLQErrorType.OOM
                    elif "corrupt" in error_msg.lower():
                        error_type = DLQErrorType.CORRUPTED_FILE
                    elif "parse" in error_msg.lower():
                        error_type = DLQErrorType.PARSE_ERROR
                    elif "timeout" in error_msg.lower():
                        error_type = DLQErrorType.TIMEOUT
                    else:
                        error_type = DLQErrorType.UNKNOWN

                    original_path = error_data.get("original_path", "")
                    file_name = Path(original_path).name if original_path else "unknown"

                    return DLQItem(
                        job_id=job_id,
                        file_name=file_name,
                        failed_at=datetime.fromtimestamp(
                            error_data.get("timestamp", 0)
                        ),
                        error_type=error_type,
                        error_message=error_msg,
                        retry_count=0,
                        can_retry=True,
                        original_metadata=None,
                    )
            except Exception as e:
                logger.warning(f"Failed to parse DLQ error file {error_file}: {e}")
                continue

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"DLQ item {job_id} not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get DLQ item: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DLQ item: {str(e)}",
        )


@router.post("/dlq/{job_id}/retry", response_model=DLQRetryResponse)
async def retry_dlq_job(
    job_id: str, current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Retry a failed job from DLQ

    Creates a new job with the same file and metadata.
    """
    loader = await get_unified_loader()

    if not loader:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unified loader not available",
        )

    try:
        import json
        from pathlib import Path

        dlq_dir = loader.dlq_dir

        # Find the failed file
        failed_file = None
        error_file = None

        for ef in dlq_dir.glob("*.error.json"):
            try:
                with open(ef, "r") as f:
                    error_data = json.load(f)

                if error_data.get("job_id") == job_id:
                    error_file = ef
                    # Find corresponding failed file
                    failed_file = ef.with_suffix("").with_suffix(".failed")
                    break
            except Exception:
                continue

        if not failed_file or not failed_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"DLQ item {job_id} not found or file missing",
            )

        # Submit new job
        metadata = {"retried_from": job_id, "retry_attempt": 1}

        new_job_id = await loader.submit_file(str(failed_file), metadata)

        logger.info(f"Retrying DLQ job {job_id} as new job {new_job_id}")

        return DLQRetryResponse(
            success=True,
            new_job_id=new_job_id,
            message=f"Job resubmitted successfully. New job ID: {new_job_id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry DLQ job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry DLQ job: {str(e)}",
        )


@router.delete("/dlq/{job_id}")
async def delete_dlq_item(
    job_id: str, current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Remove item from DLQ

    Deletes both the failed file and error log.
    """
    loader = await get_unified_loader()

    if not loader:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unified loader not available",
        )

    try:
        import json
        from pathlib import Path

        dlq_dir = loader.dlq_dir
        deleted = False

        # Find and delete files
        for error_file in dlq_dir.glob("*.error.json"):
            try:
                with open(error_file, "r") as f:
                    error_data = json.load(f)

                if error_data.get("job_id") == job_id:
                    # Delete error file
                    error_file.unlink()

                    # Delete corresponding failed file
                    failed_file = error_file.with_suffix("").with_suffix(".failed")
                    if failed_file.exists():
                        failed_file.unlink()

                    deleted = True
                    logger.info(f"Deleted DLQ item {job_id}")
                    break
            except Exception as e:
                logger.warning(f"Failed to process DLQ file {error_file}: {e}")
                continue

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"DLQ item {job_id} not found",
            )

        return {"success": True, "message": f"DLQ item {job_id} deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete DLQ item: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete DLQ item: {str(e)}",
        )


# ============================================================================
# Chunker Configuration Endpoints
# ============================================================================


@router.get("/config/chunker")
async def get_chunker_config(current_user: Optional[User] = Depends(get_optional_user)):
    """
    Get current chunker configuration

    Returns the active chunker type and its configuration parameters.
    This is useful for monitoring and debugging.
    """
    import os

    chunker_type = os.getenv("MAHOUN_CHUNKER_TYPE", "enhanced")

    config = {
        "chunker_type": chunker_type,
        "chunk_size": int(os.getenv("MAHOUN_CHUNK_SIZE", "512")),
        "overlap": int(os.getenv("MAHOUN_CHUNK_OVERLAP", "50")),
    }

    # Add legal-aware specific options if applicable
    if chunker_type in ["legal_aware", "auto"]:
        config["legal_aware_options"] = {
            "preserve_articles": os.getenv("MAHOUN_PRESERVE_ARTICLES", "true").lower()
            == "true",
            "preserve_reasoning": os.getenv("MAHOUN_PRESERVE_REASONING", "true").lower()
            == "true",
            "preserve_citations": os.getenv("MAHOUN_PRESERVE_CITATIONS", "true").lower()
            == "true",
            "min_chunk_size": int(os.getenv("MAHOUN_MIN_CHUNK_SIZE", "100")),
            "max_chunk_size": int(os.getenv("MAHOUN_MAX_CHUNK_SIZE", "1024")),
        }

    # Add graph storage status
    config["graph_storage_enabled"] = (
        os.getenv("MAHOUN_GRAPH_BUILD_ENABLED", "false").lower() == "true"
    )

    return config


@router.post("/config/chunker")
async def update_chunker_config(
    chunker_type: str,
    chunk_size: Optional[int] = None,
    overlap: Optional[int] = None,
    current_user: User = Depends(require_analyst),
):
    """
    Update chunker configuration

    Note: This updates the .env file. Server restart is required for changes to take effect.

    Requires: analyst or admin role

    Args:
        chunker_type: Type of chunker (enhanced, legal_aware, auto)
        chunk_size: Optional chunk size override
        overlap: Optional overlap override
    """
    from pathlib import Path

    # Validate chunker type
    valid_types = ["enhanced", "legal_aware", "auto"]
    if chunker_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid chunker_type: {chunker_type}. Must be one of: {valid_types}",
        )

    # Validate chunk size if provided
    if chunk_size is not None:
        if chunk_size < 100 or chunk_size > 2048:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chunk_size must be between 100 and 2048",
            )

    # Validate overlap if provided
    if overlap is not None:
        if overlap < 0 or overlap > 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="overlap must be between 0 and 200",
            )

    try:
        env_file = Path(".env")

        if not env_file.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=".env file not found",
            )

        # Read current .env
        lines = env_file.read_text().splitlines()

        # Update or add configuration
        def update_or_add(key: str, value: str):
            nonlocal lines
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}"
                    updated = True
                    break
            if not updated:
                lines.append(f"{key}={value}")

        update_or_add("MAHOUN_CHUNKER_TYPE", chunker_type)

        if chunk_size is not None:
            update_or_add("MAHOUN_CHUNK_SIZE", str(chunk_size))

        if overlap is not None:
            update_or_add("MAHOUN_CHUNK_OVERLAP", str(overlap))

        # Write back to .env
        env_file.write_text("\n".join(lines) + "\n")

        logger.info(
            f"Chunker configuration updated by {current_user.username}: "
            f"type={chunker_type}, size={chunk_size}, overlap={overlap}"
        )

        return {
            "status": "updated",
            "chunker_type": chunker_type,
            "chunk_size": chunk_size,
            "overlap": overlap,
            "message": "Configuration updated successfully. Restart the server to apply changes.",
            "restart_command": "make docker-restart",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update chunker config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}",
        )


@router.get("/stats/chunking")
async def get_chunking_stats(current_user: Optional[User] = Depends(get_optional_user)):
    """
    Get chunking statistics from the pipeline

    Returns statistics about chunking performance and quality.
    """
    pipeline = await get_ingestion_pipeline()

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingestion pipeline not available",
        )

    stats = pipeline.get_stats()

    # Extract chunking-specific stats
    chunking_stats = {
        "total_documents": stats.get("documents_ingested", 0),
        "total_chunks": stats.get("total_chunks", 0),
        "avg_chunks_per_document": (
            stats.get("total_chunks", 0) / stats.get("documents_ingested", 1)
            if stats.get("documents_ingested", 0) > 0
            else 0
        ),
        "avg_processing_time_ms": stats.get("avg_processing_time_ms", 0),
        "chunker_type": type(pipeline.chunker).__name__
        if pipeline.chunker
        else "Unknown",
    }

    return chunking_stats
