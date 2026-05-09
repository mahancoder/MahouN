# Remote LLM Training Integration - Complete Architecture

## Executive Summary

**Goal**: Enable laptop (i5/8GB RAM) to submit training jobs to remote H100 GPU server for fine-tuning Llama 70B+ models.

**Current Status**: ✅ System has complete local training infrastructure but NO remote server integration.

**Timeline**: 3-5 days for Option A (REST API - recommended for quick start)

---

## Current System Capabilities (READY ✅)

### 1. Document Upload & Processing
- ✅ **Frontend**: Beautiful React UI with drag & drop (`AdvancedDocumentUpload.tsx`)
- ✅ **API**: `/api/ingest/upload` - File upload endpoint
- ✅ **API**: `/api/ingest/submit` - Async job submission (returns job_id)
- ✅ **API**: `/api/ingest/jobs/{job_id}` - Job status polling
- ✅ **Processing**: TXT/DOCX/PDF native text extraction (100% working)
- ✅ **Job Management**: Async job queue with status tracking

### 2. Training Dataset Preparation
- ✅ **Module**: `mahoun/finetuning/document_to_training.py` - Document → Training examples
- ✅ **Module**: `mahoun/finetuning/quality_filter.py` - Quality filtering
- ✅ **Module**: `mahoun/finetuning/feedback_pipeline.py` - Feedback collection
- ✅ **Module**: `mahoun/finetuning/data_augmentation.py` - Data augmentation

### 3. Training Infrastructure (LOCAL ONLY)
- ✅ **Module**: `mahoun/finetuning/trainer.py` - TrainingManager class
- ✅ **Module**: `mahoun/finetuning/model_registry.py` - Model versioning & metadata
- ✅ **Module**: `mahoun/finetuning/unsloth_runner.py` - Local Unsloth training
- ✅ **API**: `/api/v1/finetuning/*` - Training API endpoints
- ✅ **Frontend**: `TrainingDashboard.tsx` - Training configuration UI

### 4. Model Registry
- ✅ **Storage**: JSON-based model metadata registry
- ✅ **Features**: Job tracking, GGUF paths, metrics, domain filtering
- ✅ **Query**: Get best model by metric, list by domain/status

---

## Critical Gaps (MISSING ❌)

### 1. Remote LLM Server Integration ❌
**Current**: `trainer.py` runs local training with `UnslothRunner`
```python
# Current implementation (LOCAL ONLY)
from .unsloth_runner import UnslothRunner
runner = UnslothRunner(self.config.training)
trainer_stats = runner.train(str(train_file), output_dir)
```

**Need**: HTTP/gRPC client to send jobs to remote H100 server
```python
# Target implementation (REMOTE)
from .remote_client import RemoteTrainingClient
client = RemoteTrainingClient(server_url="https://h100.example.com")
job_id = await client.submit_training_job(dataset_path, config)
```

### 2. Remote Job Management ❌
**Current**: Job tracking is local in-memory
```python
self.job_history: List[Dict[str, Any]] = []  # Local only
```

**Need**: Distributed job queue with remote status polling
- Redis/RabbitMQ for job queue
- Webhook/callback for job completion
- Remote job status API

### 3. File Transfer Mechanism ❌
**Current**: Local file paths
```python
train_file = Path(dataset_path)  # Local filesystem
```

**Need**: Remote file transfer
- Option A: HTTP multipart upload
- Option B: S3/MinIO object storage
- Option C: rsync over SSH

### 4. Model Deployment Pipeline ❌
**Need**:
- Model download API after training completes
- Model versioning & registry (remote)
- Deployment automation

### 5. Authentication & Security ⚠️
**Need**:
- API key authentication for laptop ↔ server
- TLS/SSL encryption
- Rate limiting
- Optional: IP whitelisting

---

## Architecture Options

### Option A: REST API (RECOMMENDED - 1 week)

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│ Laptop (i5/8GB)                                             │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Frontend   │───▶│  FastAPI     │───▶│  Remote      │ │
│  │   React UI   │    │  Backend     │    │  Training    │ │
│  │              │    │              │    │  Client      │ │
│  └──────────────┘    └──────────────┘    └──────┬───────┘ │
│                                                   │         │
└───────────────────────────────────────────────────┼─────────┘
                                                    │
                                                    │ HTTPS
                                                    │ POST /api/training/submit
                                                    │ GET  /api/training/jobs/{id}
                                                    │
┌───────────────────────────────────────────────────┼─────────┐
│ H100 Server (2x H100 GPU)                         │         │
│                                                    ▼         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  FastAPI     │───▶│  Training    │───▶│  Unsloth     │ │
│  │  Server      │    │  Worker      │    │  Runner      │ │
│  │              │    │  Queue       │    │              │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐                     │
│  │  File        │    │  Model       │                     │
│  │  Storage     │    │  Registry    │                     │
│  └──────────────┘    └──────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

**Pros**:
- Simple HTTP standard
- Firewall-friendly
- Easy to debug
- No infrastructure dependencies

**Cons**:
- File upload slow for large datasets (>1GB)
- Polling overhead for status
- No built-in retry/reliability

**Implementation Steps**:

1. **H100 Server Setup (3-5 days)**:
   - Install FastAPI on H100 server
   - Create training API endpoints:
     * `POST /api/training/submit` - Accept dataset upload, return job_id
     * `GET /api/training/jobs/{job_id}` - Return job status
     * `GET /api/training/models/{model_id}/download` - Download trained model
   - Implement file storage (local disk or MinIO)
   - Implement job queue (simple in-memory or Redis)
   - Add authentication (API key)

2. **Client Integration (2-3 days)**:
   - Create `RemoteTrainingClient` class in `mahoun/finetuning/remote_client.py`
   - Update `trainer.py` to use remote client instead of local `UnslothRunner`
   - Add environment variables for server URL & API key
   - Implement file upload with progress tracking
   - Implement job status polling with exponential backoff

3. **Frontend Updates (1-2 days)**:
   - Training job submission UI already exists ✅
   - Job status monitoring already exists ✅
   - Add model download interface (button to download trained models)

---

### Option B: S3 + Message Queue (PRODUCTION - 1-2 months)

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│ Laptop (i5/8GB)                                             │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐                     │
│  │   Frontend   │───▶│  FastAPI     │                     │
│  │   React UI   │    │  Backend     │                     │
│  └──────────────┘    └──────┬───────┘                     │
│                              │                              │
└──────────────────────────────┼──────────────────────────────┘
                               │
                               │ Upload dataset to S3
                               │ Send message to RabbitMQ
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Infrastructure Layer                                        │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  S3/MinIO    │    │  RabbitMQ    │    │  PostgreSQL  │ │
│  │  Storage     │    │  Queue       │    │  Metadata    │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                               │
                               │ Worker picks up job
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ H100 Server (2x H100 GPU)                                   │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Celery      │───▶│  Training    │───▶│  Unsloth     │ │
│  │  Worker      │    │  Pipeline    │    │  Runner      │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                             │
│  Training completes → Upload model to S3 → Send webhook    │
└─────────────────────────────────────────────────────────────┘
```

**Pros**:
- Scalable to multiple workers
- Async, reliable, fast
- Production-grade
- Built-in retry/failure handling

**Cons**:
- Needs infrastructure (S3, RabbitMQ, PostgreSQL)
- More complex setup
- Higher operational overhead

---

### Option C: SSH + rsync (MINIMAL - 1-2 days)

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│ Laptop (i5/8GB)                                             │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐                     │
│  │   Frontend   │───▶│  FastAPI     │                     │
│  │   React UI   │    │  Backend     │                     │
│  └──────────────┘    └──────┬───────┘                     │
│                              │                              │
│                              │ rsync dataset via SSH        │
│                              │ SSH command to start training│
│                              ▼                              │
└─────────────────────────────────────────────────────────────┘
                               │
                               │ Direct SSH connection
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ H100 Server (2x H100 GPU)                                   │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐                     │
│  │  SSH Server  │───▶│  Training    │                     │
│  │              │    │  Script      │                     │
│  └──────────────┘    └──────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

**Pros**:
- Very simple
- No infrastructure needed
- Fast file transfer (rsync)

**Cons**:
- Manual job execution
- No job queue
- Security concerns (direct SSH access)
- No web UI for server

---

## Recommended Implementation: Option A (REST API)

### Phase 1: H100 Server Setup (3-5 days)

**File**: `h100_server/api/main.py` (NEW)
```python
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import uuid
from datetime import datetime

app = FastAPI(title="MAHOUN H100 Training Server")

# Job storage (in-memory for MVP, Redis for production)
jobs = {}

class TrainingJobRequest(BaseModel):
    base_model: str
    training_mode: str
    num_epochs: int
    learning_rate: float
    # ... other config

@app.post("/api/training/submit")
async def submit_training_job(
    dataset: UploadFile = File(...),
    config: TrainingJobRequest = ...
):
    job_id = str(uuid.uuid4())
    
    # Save dataset to disk
    dataset_path = f"/data/datasets/{job_id}.jsonl"
    with open(dataset_path, "wb") as f:
        f.write(await dataset.read())
    
    # Create job
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "dataset_path": dataset_path,
        "config": config.dict(),
        "created_at": datetime.now().isoformat()
    }
    
    # Start training in background (use BackgroundTasks or Celery)
    # background_tasks.add_task(run_training, job_id)
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/training/jobs/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    
    return jobs[job_id]

@app.get("/api/training/models/{model_id}/download")
async def download_model(model_id: str):
    # Return model file
    model_path = f"/data/models/{model_id}/model.gguf"
    return FileResponse(model_path)
```

### Phase 2: Client Integration (2-3 days)

**File**: `mahoun/finetuning/remote_client.py` (NEW)
```python
import httpx
from pathlib import Path
from typing import Dict, Any, Optional

class RemoteTrainingClient:
    """
    Client for submitting training jobs to remote H100 server.
    """
    
    def __init__(
        self,
        server_url: str,
        api_key: str,
        timeout: int = 300
    ):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        
        self.client = httpx.AsyncClient(
            base_url=self.server_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout
        )
    
    async def submit_training_job(
        self,
        dataset_path: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Submit training job to remote server.
        
        Returns:
            job_id: Remote job identifier
        """
        # Upload dataset
        with open(dataset_path, "rb") as f:
            files = {"dataset": f}
            data = {"config": json.dumps(config)}
            
            response = await self.client.post(
                "/api/training/submit",
                files=files,
                data=data
            )
            response.raise_for_status()
        
        result = response.json()
        return result["job_id"]
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status from remote server."""
        response = await self.client.get(f"/api/training/jobs/{job_id}")
        response.raise_for_status()
        return response.json()
    
    async def download_model(
        self,
        model_id: str,
        output_path: str
    ) -> None:
        """Download trained model from remote server."""
        response = await self.client.get(
            f"/api/training/models/{model_id}/download",
            follow_redirects=True
        )
        response.raise_for_status()
        
        Path(output_path).write_bytes(response.content)
```

### Phase 3: Update TrainingManager (1 day)

**File**: `mahoun/finetuning/trainer.py` (UPDATE)
```python
async def start_training_job(
    self, 
    dataset_path: str, 
    base_model_name: Optional[str] = None,
    domain: str = "general",
    tags: Optional[List[str]] = None,
    use_remote: bool = True  # NEW PARAMETER
) -> str:
    """
    Start a fine-tuning job (local or remote).
    """
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Check if remote training is enabled
    if use_remote and os.getenv("MAHOUN_REMOTE_TRAINING_ENABLED") == "true":
        # Use remote H100 server
        from .remote_client import RemoteTrainingClient
        
        client = RemoteTrainingClient(
            server_url=os.getenv("MAHOUN_H100_SERVER_URL"),
            api_key=os.getenv("MAHOUN_H100_API_KEY")
        )
        
        remote_job_id = await client.submit_training_job(
            dataset_path=dataset_path,
            config=self.config.dict()
        )
        
        # Store remote job mapping
        self.registry.register(ModelMetadata(
            job_id=job_id,
            remote_job_id=remote_job_id,  # NEW FIELD
            base_model=self.config.training.base_model,
            dataset_path=dataset_path,
            status="training_remote",
            domain=domain,
            tags=tags or []
        ))
        
        logger.info(f"Job {job_id} submitted to remote server: {remote_job_id}")
        return job_id
    
    else:
        # Use local training (existing code)
        # ... existing local training logic ...
```

---

## Environment Variables

**Laptop `.env`**:
```bash
# Remote Training Configuration
MAHOUN_REMOTE_TRAINING_ENABLED=true
MAHOUN_H100_SERVER_URL=https://h100.example.com
MAHOUN_H100_API_KEY=your-secret-api-key-here

# Fallback to local if remote unavailable
MAHOUN_LOCAL_TRAINING_FALLBACK=true
```

**H100 Server `.env`**:
```bash
# Server Configuration
MAHOUN_SERVER_MODE=training_server
MAHOUN_API_KEY=your-secret-api-key-here

# Storage
MAHOUN_DATASET_STORAGE_PATH=/data/datasets
MAHOUN_MODEL_STORAGE_PATH=/data/models

# GPU Configuration
CUDA_VISIBLE_DEVICES=0,1  # 2x H100
```

---

## Security Considerations

1. **API Key Authentication**: Use Bearer token in Authorization header
2. **TLS/SSL**: HTTPS only for production
3. **Rate Limiting**: Limit requests per IP/API key
4. **File Size Limits**: Max 10GB per dataset upload
5. **IP Whitelisting**: Optional - restrict to known IPs
6. **Audit Logging**: Log all training job submissions

---

## Testing Strategy

### Unit Tests
- `test_remote_client.py` - Test RemoteTrainingClient
- `test_trainer_remote.py` - Test TrainingManager with remote mode

### Integration Tests
- `test_remote_integration.py` - End-to-end remote training flow
- Mock H100 server for CI/CD

### Manual Testing
1. Upload document via frontend
2. Submit training job
3. Poll job status
4. Download trained model

---

## Deployment Checklist

### H100 Server
- [ ] Install FastAPI, Uvicorn, Unsloth
- [ ] Configure CUDA environment
- [ ] Set up file storage directories
- [ ] Generate API key
- [ ] Configure firewall (allow HTTPS)
- [ ] Set up systemd service for FastAPI
- [ ] Configure Nginx reverse proxy (optional)
- [ ] Set up monitoring (Prometheus/Grafana)

### Laptop
- [ ] Update `.env` with H100 server URL & API key
- [ ] Test remote client connection
- [ ] Verify file upload works
- [ ] Test job submission & status polling
- [ ] Test model download

---

## Timeline

**Week 1 (Days 1-3)**: H100 Server Setup
- Day 1: Install dependencies, create FastAPI server
- Day 2: Implement training endpoints, file storage
- Day 3: Test local training on H100 server

**Week 1 (Days 4-5)**: Client Integration
- Day 4: Create RemoteTrainingClient, update TrainingManager
- Day 5: Integration testing, bug fixes

**Week 2 (Days 6-7)**: Frontend & Polish
- Day 6: Frontend updates, model download UI
- Day 7: End-to-end testing, documentation

---

## Success Criteria

✅ Laptop can submit training job to H100 server via HTTPS
✅ H100 server processes job and returns status
✅ Laptop can poll job status and see progress
✅ Laptop can download trained model after completion
✅ Frontend UI shows remote training status
✅ System gracefully falls back to local training if remote unavailable

---

## Next Steps

1. **Immediate**: Create `mahoun/finetuning/remote_client.py`
2. **Next**: Update `mahoun/finetuning/trainer.py` to support remote mode
3. **Then**: Create H100 server FastAPI application
4. **Finally**: Test end-to-end flow

**Ready to proceed with implementation?**
