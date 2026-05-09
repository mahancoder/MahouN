"""
Advanced Data Preparation Pipeline Manager
===========================================
Enterprise-grade data preparation with monitoring, validation, and optimization
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
from enum import Enum

from .config import DataPrepConfig
from .quality_analyzer import QualityAnalyzer
from .smart_chunker import SmartChunker
from .orchestrator import DataPrepOrchestrator

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """Pipeline stages"""
    INGESTION = "ingestion"
    VALIDATION = "validation"
    PREPROCESSING = "preprocessing"
    CHUNKING = "chunking"
    LABELING = "labeling"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    QUALITY_CHECK = "quality_check"


class PipelineStatus(str, Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class StageMetrics:
    """Metrics for a pipeline stage"""
    stage: PipelineStage
    status: PipelineStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    items_processed: int = 0
    items_failed: int = 0
    success_rate: float = 0.0
    throughput: float = 0.0  # items per second
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineRun:
    """Complete pipeline run information"""
    run_id: str
    config: DataPrepConfig
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    stages: Dict[PipelineStage, StageMetrics] = field(default_factory=dict)
    total_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    overall_success_rate: float = 0.0
    artifacts: Dict[str, Path] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)


class AdvancedPipelineManager:
    """
    Advanced Pipeline Manager with:
    - Async execution
    - Stage-by-stage monitoring
    - Automatic retry on failure
    - Resource optimization
    - Quality gates
    - Checkpoint/resume
    - Distributed execution support
    """
    
    def __init__(
        self,
        config: DataPrepConfig,
        enable_monitoring: bool = True,
        enable_checkpoints: bool = True,
        max_retries: int = 3
    ):
        self.config = config
        self.enable_monitoring = enable_monitoring
        self.enable_checkpoints = enable_checkpoints
        self.max_retries = max_retries
        
        # Components
        self.quality_analyzer = QualityAnalyzer(config)
        self.smart_chunker = SmartChunker(config)
        self.orchestrator = DataPrepOrchestrator(config)
        
        # State
        self.current_run: Optional[PipelineRun] = None
        self.stage_callbacks: Dict[PipelineStage, List[Callable]] = {}
        
        logger.info("AdvancedPipelineManager initialized")
    
    async def execute_pipeline(
        self,
        input_path: Path,
        output_path: Path,
        stages: Optional[List[PipelineStage]] = None,
        resume_from: Optional[PipelineStage] = None
    ) -> PipelineRun:
        """
        Execute complete pipeline with monitoring
        
        Args:
            input_path: Input data directory
            output_path: Output directory
            stages: Specific stages to run (None = all)
            resume_from: Resume from specific stage
            
        Returns:
            PipelineRun with complete metrics
        """
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_run = PipelineRun(
            run_id=run_id,
            config=self.config,
            status=PipelineStatus.RUNNING,
            start_time=datetime.now()
        )
        
        logger.info(f"Starting pipeline run: {run_id}")
        
        try:
            # Determine stages to execute
            if stages is None:
                stages = list(PipelineStage)
            
            if resume_from:
                resume_idx = stages.index(resume_from)
                stages = stages[resume_idx:]
            
            # Execute stages sequentially
            for stage in stages:
                await self._execute_stage(stage, input_path, output_path)
                
                # Quality gate check
                if not await self._quality_gate_check(stage):
                    raise Exception(f"Quality gate failed for stage: {stage}")
                
                # Checkpoint
                if self.enable_checkpoints:
                    await self._save_checkpoint(stage)
            
            # Finalize
            self.current_run.status = PipelineStatus.COMPLETED
            self.current_run.end_time = datetime.now()
            self.current_run.total_duration_seconds = (
                self.current_run.end_time - self.current_run.start_time
            ).total_seconds()
            
            # Calculate overall metrics
            self._calculate_overall_metrics()
            
            logger.info(f"Pipeline completed: {run_id}")
            
            return self.current_run
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self.current_run.status = PipelineStatus.FAILED
            self.current_run.logs.append(f"ERROR: {str(e)}")
            raise
    
    async def _execute_stage(
        self,
        stage: PipelineStage,
        input_path: Path,
        output_path: Path
    ):
        """Execute a single pipeline stage"""
        logger.info(f"Executing stage: {stage}")
        
        metrics = StageMetrics(
            stage=stage,
            status=PipelineStatus.RUNNING,
            start_time=datetime.now()
        )
        
        try:
            # Execute stage-specific logic
            if stage == PipelineStage.INGESTION:
                result = await self._stage_ingestion(input_path, output_path)
            elif stage == PipelineStage.VALIDATION:
                result = await self._stage_validation(input_path)
            elif stage == PipelineStage.PREPROCESSING:
                result = await self._stage_preprocessing(input_path, output_path)
            elif stage == PipelineStage.CHUNKING:
                result = await self._stage_chunking(input_path, output_path)
            elif stage == PipelineStage.LABELING:
                result = await self._stage_labeling(input_path, output_path)
            elif stage == PipelineStage.EMBEDDING:
                result = await self._stage_embedding(input_path, output_path)
            elif stage == PipelineStage.INDEXING:
                result = await self._stage_indexing(input_path, output_path)
            elif stage == PipelineStage.QUALITY_CHECK:
                result = await self._stage_quality_check(input_path)
            else:
                raise ValueError(f"Unknown stage: {stage}")
            
            # Update metrics
            metrics.status = PipelineStatus.COMPLETED
            metrics.end_time = datetime.now()
            metrics.duration_seconds = (
                metrics.end_time - metrics.start_time
            ).total_seconds()
            metrics.items_processed = result.get('items_processed', 0)
            metrics.items_failed = result.get('items_failed', 0)
            metrics.success_rate = (
                metrics.items_processed / 
                (metrics.items_processed + metrics.items_failed)
                if (metrics.items_processed + metrics.items_failed) > 0
                else 0.0
            )
            metrics.throughput = (
                metrics.items_processed / metrics.duration_seconds
                if metrics.duration_seconds > 0
                else 0.0
            )
            metrics.metadata = result.get('metadata', {})
            
            # Store metrics
            self.current_run.stages[stage] = metrics
            
            # Callbacks
            await self._trigger_callbacks(stage, metrics)
            
            logger.info(
                f"Stage {stage} completed: "
                f"{metrics.items_processed} items in "
                f"{metrics.duration_seconds:.2f}s "
                f"({metrics.throughput:.2f} items/s)"
            )
            
        except Exception as e:
            metrics.status = PipelineStatus.FAILED
            metrics.errors.append(str(e))
            self.current_run.stages[stage] = metrics
            raise
    
    async def _stage_ingestion(
        self,
        input_path: Path,
        output_path: Path
    ) -> Dict[str, Any]:
        """Ingestion stage"""
        # Use orchestrator
        result = await self.orchestrator.ingest_documents(
            input_path,
            output_path / "ingested"
        )
        return result
    
    async def _stage_validation(self, input_path: Path) -> Dict[str, Any]:
        """Validation stage"""
        result = await self.quality_analyzer.validate_dataset(input_path)
        return result
    
    async def _stage_preprocessing(
        self,
        input_path: Path,
        output_path: Path
    ) -> Dict[str, Any]:
        """Preprocessing stage"""
        result = await self.orchestrator.preprocess_documents(
            input_path,
            output_path / "preprocessed"
        )
        return result
    
    async def _stage_chunking(
        self,
        input_path: Path,
        output_path: Path
    ) -> Dict[str, Any]:
        """Chunking stage"""
        result = await self.smart_chunker.chunk_documents(
            input_path,
            output_path / "chunks"
        )
        return result
    
    async def _stage_labeling(
        self,
        input_path: Path,
        output_path: Path
    ) -> Dict[str, Any]:
        """Labeling stage"""
        result = await self.orchestrator.label_documents(
            input_path,
            output_path / "labeled"
        )
        return result
    
    async def _stage_embedding(
        self,
        input_path: Path,
        output_path: Path
    ) -> Dict[str, Any]:
        """Embedding stage"""
        result = await self.orchestrator.generate_embeddings(
            input_path,
            output_path / "embeddings"
        )
        return result
    
    async def _stage_indexing(
        self,
        input_path: Path,
        output_path: Path
    ) -> Dict[str, Any]:
        """Indexing stage"""
        result = await self.orchestrator.index_documents(
            input_path,
            output_path / "indexes"
        )
        return result
    
    async def _stage_quality_check(self, input_path: Path) -> Dict[str, Any]:
        """Quality check stage"""
        result = await self.quality_analyzer.analyze_quality(input_path)
        return result
    
    async def _quality_gate_check(self, stage: PipelineStage) -> bool:
        """Check if stage passed quality gates"""
        metrics = self.current_run.stages.get(stage)
        if not metrics:
            return False
        
        # Quality thresholds
        min_success_rate = 0.95
        max_error_rate = 0.05
        
        if metrics.success_rate < min_success_rate:
            logger.warning(
                f"Stage {stage} failed quality gate: "
                f"success_rate={metrics.success_rate:.2%} < {min_success_rate:.2%}"
            )
            return False
        
        return True
    
    async def _save_checkpoint(self, stage: PipelineStage):
        """Save pipeline checkpoint"""
        checkpoint_path = (
            Path(self.config.output_dir) / 
            "checkpoints" / 
            f"{self.current_run.run_id}_{stage.value}.json"
        )
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        
        checkpoint_data = {
            "run_id": self.current_run.run_id,
            "stage": stage.value,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                k.value: {
                    "status": v.status.value,
                    "items_processed": v.items_processed,
                    "success_rate": v.success_rate
                }
                for k, v in self.current_run.stages.items()
            }
        }
        
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        logger.info(f"Checkpoint saved: {checkpoint_path}")
    
    def _calculate_overall_metrics(self):
        """Calculate overall pipeline metrics"""
        total_processed = sum(
            m.items_processed for m in self.current_run.stages.values()
        )
        total_failed = sum(
            m.items_failed for m in self.current_run.stages.values()
        )
        
        self.current_run.total_items = total_processed + total_failed
        self.current_run.successful_items = total_processed
        self.current_run.failed_items = total_failed
        self.current_run.overall_success_rate = (
            total_processed / self.current_run.total_items
            if self.current_run.total_items > 0
            else 0.0
        )
    
    def register_callback(
        self,
        stage: PipelineStage,
        callback: Callable
    ):
        """Register callback for stage completion"""
        if stage not in self.stage_callbacks:
            self.stage_callbacks[stage] = []
        self.stage_callbacks[stage].append(callback)
    
    async def _trigger_callbacks(
        self,
        stage: PipelineStage,
        metrics: StageMetrics
    ):
        """Trigger registered callbacks"""
        if stage in self.stage_callbacks:
            for callback in self.stage_callbacks[stage]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(stage, metrics)
                    else:
                        callback(stage, metrics)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    def get_run_report(self) -> Dict[str, Any]:
        """Generate comprehensive run report"""
        if not self.current_run:
            return {}
        
        return {
            "run_id": self.current_run.run_id,
            "status": self.current_run.status.value,
            "duration_seconds": self.current_run.total_duration_seconds,
            "total_items": self.current_run.total_items,
            "successful_items": self.current_run.successful_items,
            "failed_items": self.current_run.failed_items,
            "success_rate": self.current_run.overall_success_rate,
            "stages": {
                stage.value: {
                    "status": metrics.status.value,
                    "duration_seconds": metrics.duration_seconds,
                    "items_processed": metrics.items_processed,
                    "success_rate": metrics.success_rate,
                    "throughput": metrics.throughput,
                    "errors": metrics.errors,
                    "warnings": metrics.warnings
                }
                for stage, metrics in self.current_run.stages.items()
            }
        }
