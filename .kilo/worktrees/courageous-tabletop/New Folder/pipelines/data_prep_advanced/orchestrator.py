"""
Advanced Data Preparation Orchestrator
=======================================
Coordinates all data preparation stages with monitoring and quality control
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

from .config import DataPrepConfig
from .ingestion import AdvancedIngestionPipeline
from .preprocessing import AdvancedPreprocessor
from .smart_chunker import SmartChunker
from .labeling import AdvancedLabeler
from .embedding import AdvancedEmbeddingGenerator
from .indexing import AdvancedIndexer
from .quality_analyzer import QualityAnalyzer
from .monitoring import PipelineMonitor

logger = logging.getLogger(__name__)


@dataclass
class PipelineMetrics:
    """Metrics collected during pipeline execution"""
    
    stage: str
    start_time: float
    end_time: float
    duration: float
    input_count: int
    output_count: int
    success_count: int
    failure_count: int
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0


@dataclass
class PipelineResult:
    """Complete pipeline execution result"""
    
    success: bool
    total_duration: float
    stage_metrics: List[PipelineMetrics]
    output_paths: Dict[str, Path]
    quality_report: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "total_duration": self.total_duration,
            "stages": [
                {
                    "stage": m.stage,
                    "duration": m.duration,
                    "input_count": m.input_count,
                    "output_count": m.output_count,
                    "success_rate": m.success_rate,
                    "metrics": m.metrics
                }
                for m in self.stage_metrics
            ],
            "output_paths": {k: str(v) for k, v in self.output_paths.items()},
            "quality_report": self.quality_report,
            "errors": self.errors
        }


class DataPrepOrchestrator:
    """
    Advanced orchestrator for data preparation pipeline
    
    Features:
    - Multi-stage pipeline execution
    - Quality monitoring at each stage
    - Error handling and recovery
    - Progress tracking
    - Metrics collection
    - W&B integration
    """
    
    def __init__(self, config: DataPrepConfig):
        """
        Initialize orchestrator
        
        Args:
            config: Complete data preparation configuration
        """
        self.config = config
        self.stage_metrics: List[PipelineMetrics] = []
        
        # Initialize components
        self.ingestion = AdvancedIngestionPipeline(config.ingestion)
        self.preprocessor = AdvancedPreprocessor(config.preprocessing)
        self.chunker = SmartChunker(config.chunking)
        self.labeler = AdvancedLabeler(config.labeling)
        self.embedder = AdvancedEmbeddingGenerator(config.embedding)
        self.indexer = AdvancedIndexer(config.indexing)
        self.quality_analyzer = QualityAnalyzer(config.quality)
        self.monitor = PipelineMonitor(config.monitoring)
        
        logger.info("DataPrepOrchestrator initialized")
    
    def run(
        self,
        input_path: Optional[Path] = None,
        output_path: Optional[Path] = None,
        stages: Optional[List[str]] = None
    ) -> PipelineResult:
        """
        Run complete pipeline or specific stages
        
        Args:
            input_path: Input directory (overrides config)
            output_path: Output directory (overrides config)
            stages: List of stages to run (None = all)
            
        Returns:
            PipelineResult with metrics and outputs
        """
        start_time = time.time()
        
        # Setup paths
        input_dir = input_path or self.config.input_dir
        output_dir = output_path or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize monitoring
        self.monitor.start_run(
            run_name=f"data_prep_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Define pipeline stages
        all_stages = [
            "ingestion",
            "preprocessing",
            "chunking",
            "labeling",
            "embedding",
            "indexing"
        ]
        
        stages_to_run = stages if stages else all_stages
        
        logger.info(f"Running pipeline stages: {stages_to_run}")
        
        # Track outputs
        output_paths = {}
        errors = []
        
        try:
            # Stage 1: Ingestion
            if "ingestion" in stages_to_run:
                logger.info("=" * 60)
                logger.info("Stage 1: Document Ingestion")
                logger.info("=" * 60)
                
                ingestion_result = self._run_stage(
                    stage_name="ingestion",
                    func=self.ingestion.process_directory,
                    input_path=input_dir,
                    output_path=output_dir / "ingested"
                )
                
                output_paths["ingested"] = output_dir / "ingested"
                
                if not ingestion_result["success"]:
                    raise RuntimeError("Ingestion stage failed")
            
            # Stage 2: Preprocessing
            if "preprocessing" in stages_to_run:
                logger.info("=" * 60)
                logger.info("Stage 2: Text Preprocessing")
                logger.info("=" * 60)
                
                preprocess_input = output_paths.get("ingested", input_dir)
                preprocess_result = self._run_stage(
                    stage_name="preprocessing",
                    func=self.preprocessor.process_directory,
                    input_path=preprocess_input,
                    output_path=output_dir / "preprocessed"
                )
                
                output_paths["preprocessed"] = output_dir / "preprocessed"
                
                if not preprocess_result["success"]:
                    raise RuntimeError("Preprocessing stage failed")
            
            # Stage 3: Chunking
            if "chunking" in stages_to_run:
                logger.info("=" * 60)
                logger.info("Stage 3: Smart Chunking")
                logger.info("=" * 60)
                
                chunk_input = output_paths.get("preprocessed", input_dir)
                chunk_result = self._run_stage(
                    stage_name="chunking",
                    func=self.chunker.chunk_directory,
                    input_path=chunk_input,
                    output_path=output_dir / "chunks.jsonl"
                )
                
                output_paths["chunks"] = output_dir / "chunks.jsonl"
                
                if not chunk_result["success"]:
                    raise RuntimeError("Chunking stage failed")
            
            # Stage 4: Labeling
            if "labeling" in stages_to_run:
                logger.info("=" * 60)
                logger.info("Stage 4: Entity Labeling")
                logger.info("=" * 60)
                
                label_input = output_paths.get("chunks", input_dir / "chunks.jsonl")
                label_result = self._run_stage(
                    stage_name="labeling",
                    func=self.labeler.label_file,
                    input_path=label_input,
                    output_path=output_dir / "labeled.jsonl"
                )
                
                output_paths["labeled"] = output_dir / "labeled.jsonl"
                
                if not label_result["success"]:
                    raise RuntimeError("Labeling stage failed")
            
            # Stage 5: Embedding
            if "embedding" in stages_to_run:
                logger.info("=" * 60)
                logger.info("Stage 5: Embedding Generation")
                logger.info("=" * 60)
                
                embed_input = output_paths.get("labeled", input_dir / "labeled.jsonl")
                embed_result = self._run_stage(
                    stage_name="embedding",
                    func=self.embedder.generate_from_file,
                    input_path=embed_input,
                    output_path=output_dir / "embeddings.npy"
                )
                
                output_paths["embeddings"] = output_dir / "embeddings.npy"
                
                if not embed_result["success"]:
                    raise RuntimeError("Embedding stage failed")
            
            # Stage 6: Indexing
            if "indexing" in stages_to_run:
                logger.info("=" * 60)
                logger.info("Stage 6: Multi-Index Creation")
                logger.info("=" * 60)
                
                index_input = output_paths.get("labeled", input_dir / "labeled.jsonl")
                embeddings = output_paths.get("embeddings", input_dir / "embeddings.npy")
                
                index_result = self._run_stage(
                    stage_name="indexing",
                    func=self.indexer.build_all_indexes,
                    input_path=index_input,
                    embeddings_path=embeddings,
                    output_dir=output_dir / "indexes"
                )
                
                output_paths["indexes"] = output_dir / "indexes"
                
                if not index_result["success"]:
                    raise RuntimeError("Indexing stage failed")
            
            # Quality analysis
            logger.info("=" * 60)
            logger.info("Quality Analysis")
            logger.info("=" * 60)
            
            quality_report = self.quality_analyzer.analyze_pipeline(
                stage_metrics=self.stage_metrics,
                output_paths=output_paths
            )
            
            # Save quality report
            report_path = output_dir / "quality_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(quality_report, f, indent=2, ensure_ascii=False)
            
            output_paths["quality_report"] = report_path
            
            # Success
            total_duration = time.time() - start_time
            
            result = PipelineResult(
                success=True,
                total_duration=total_duration,
                stage_metrics=self.stage_metrics,
                output_paths=output_paths,
                quality_report=quality_report,
                errors=errors
            )
            
            logger.info("=" * 60)
            logger.info("Pipeline Completed Successfully!")
            logger.info(f"Total Duration: {total_duration:.2f}s")
            logger.info("=" * 60)
            
            # Log to W&B
            self.monitor.log_pipeline_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            errors.append(str(e))
            
            total_duration = time.time() - start_time
            
            result = PipelineResult(
                success=False,
                total_duration=total_duration,
                stage_metrics=self.stage_metrics,
                output_paths=output_paths,
                errors=errors
            )
            
            self.monitor.log_pipeline_result(result)
            
            return result
        
        finally:
            self.monitor.finish_run()
    
    def _run_stage(
        self,
        stage_name: str,
        func: callable,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run a single pipeline stage with monitoring
        
        Args:
            stage_name: Name of the stage
            func: Function to execute
            **kwargs: Arguments for the function
            
        Returns:
            Stage result dictionary
        """
        start_time = time.time()
        
        try:
            # Execute stage
            result = func(**kwargs)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Create metrics
            metrics = PipelineMetrics(
                stage=stage_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                input_count=result.get("input_count", 0),
                output_count=result.get("output_count", 0),
                success_count=result.get("success_count", 0),
                failure_count=result.get("failure_count", 0),
                metrics=result.get("metrics", {})
            )
            
            self.stage_metrics.append(metrics)
            
            # Log to monitor
            self.monitor.log_stage(stage_name, metrics)
            
            logger.info(f"✅ {stage_name} completed in {duration:.2f}s")
            logger.info(f"   Input: {metrics.input_count}, Output: {metrics.output_count}")
            logger.info(f"   Success rate: {metrics.success_rate:.2%}")
            
            return {"success": True, **result}
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            logger.error(f"❌ {stage_name} failed: {e}")
            
            metrics = PipelineMetrics(
                stage=stage_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                input_count=0,
                output_count=0,
                success_count=0,
                failure_count=1,
                metrics={"error": str(e)}
            )
            
            self.stage_metrics.append(metrics)
            self.monitor.log_stage(stage_name, metrics)
            
            return {"success": False, "error": str(e)}
