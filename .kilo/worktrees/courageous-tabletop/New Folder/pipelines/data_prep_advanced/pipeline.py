"""
Advanced Data Preparation Pipeline
===================================
State-of-the-art data preparation with quality assurance
"""

import logging
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import asyncio
import hashlib
from typing import Optional, List, Dict, Any

from .config import DataPrepConfig
from .smart_chunker import SmartChunker, ChunkingStrategy
from .quality_analyzer import QualityAnalyzer
from .orchestrator import DataPrepOrchestrator
from .validation import DataValidator, ValidationReport

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline stages"""
    INGESTION = "ingestion"
    VALIDATION = "validation"
    PREPROCESSING = "preprocessing"
    CHUNKING = "chunking"
    LABELING = "labeling"
    EMBEDDING = "embedding"
    INDEXING = "indexing"


@dataclass
class PipelineResult:
    """Result of pipeline execution"""
    stage: PipelineStage
    success: bool
    input_count: int
    output_count: int
    metrics: Dict[str, Any]
    errors: List[str]
    duration_seconds: float


class AdvancedDataPipeline:
    """
    Advanced data preparation pipeline with:
    - Multi-stage processing
    - Quality assurance at each stage
    - Parallel processing
    - Error recovery
    - Progress tracking
    - Metrics collection
    """
    
    def __init__(
        self,
        config: Optional[DataPrepConfig] = None,
        enable_parallel: bool = True,
        max_workers: int = 4
    ):
        self.config = config or DataPrepConfig()
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        
        # Initialize components
        self.quality_analyzer = QualityAnalyzer(self.config.quality)
        self.chunker = SmartChunker(self.config.chunking)
        self.orchestrator = DataPrepOrchestrator(self.config)
        self.validator = DataValidator()
        
        # State
        self.results: List[PipelineResult] = []
        self.current_stage: Optional[PipelineStage] = None
        
        logger.info(f"AdvancedDataPipeline initialized (parallel={enable_parallel})")
    
    async def run_full_pipeline(
        self,
        input_path: Path,
        output_path: Path,
        stages: Optional[List[PipelineStage]] = None
    ) -> List[PipelineResult]:
        """
        Run complete pipeline
        
        Args:
            input_path: Input directory/file
            output_path: Output directory
            stages: Stages to run (None = all)
            
        Returns:
            List of pipeline results
        """
        if stages is None:
            stages = list(PipelineStage)
        
        logger.info(f"Starting pipeline with {len(stages)} stages")
        
        self.results = []
        current_data = input_path
        
        for stage in stages:
            self.current_stage = stage
            logger.info(f"Running stage: {stage.value}")
            
            try:
                result = await self._run_stage(stage, current_data, output_path)
                self.results.append(result)
                
                if not result.success:
                    logger.error(f"Stage {stage.value} failed")
                    break
                
                # Update input for next stage
                current_data = output_path / stage.value
                
            except Exception as e:
                logger.error(f"Stage {stage.value} error: {e}", exc_info=True)
                self.results.append(PipelineResult(
                    stage=stage,
                    success=False,
                    input_count=0,
                    output_count=0,
                    metrics={},
                    errors=[str(e)],
                    duration_seconds=0.0
                ))
                break
        
        logger.info(f"Pipeline completed: {len(self.results)} stages")
        return self.results
    
    async def _run_stage(
        self,
        stage: PipelineStage,
        input_path: Path,
        output_path: Path
    ) -> PipelineResult:
        """Run a single pipeline stage"""
        import time
        start_time = time.time()
        
        if stage == PipelineStage.INGESTION:
            result = await self._run_ingestion(input_path, output_path)
        elif stage == PipelineStage.VALIDATION:
            result = await self._run_validation(input_path, output_path)
        elif stage == PipelineStage.PREPROCESSING:
            result = await self._run_preprocessing(input_path, output_path)
        elif stage == PipelineStage.CHUNKING:
            result = await self._run_chunking(input_path, output_path)
        elif stage == PipelineStage.LABELING:
            result = await self._run_labeling(input_path, output_path)
        elif stage == PipelineStage.EMBEDDING:
            result = await self._run_embedding(input_path, output_path)
        elif stage == PipelineStage.INDEXING:
            result = await self._run_indexing(input_path, output_path)
        else:
            raise ValueError(f"Unknown stage: {stage}")
        
        result.duration_seconds = time.time() - start_time
        return result
    
    async def _run_ingestion(
        self,
        input_path: Path,
        output_path: Path
    ) -> PipelineResult:
        """Ingest documents from various sources"""
        try:
            from scripts.document_processor.processor import DocumentProcessor
            
            processor = DocumentProcessor()
            
            # Process documents
            documents = processor.process_directory(str(input_path))
            
            # Save
            output_dir = output_path / "ingestion"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            saved_count = 0
            for doc in documents:
                doc_path = output_dir / f"{doc['id']}.json"
                with open(doc_path, 'w', encoding='utf-8') as f:
                    json.dump(doc, f, ensure_ascii=False, indent=2)
                saved_count += 1
            
            return PipelineResult(
                stage=PipelineStage.INGESTION,
                success=True,
                input_count=len(list(input_path.rglob("*"))),
                output_count=saved_count,
                metrics={"documents_processed": saved_count},
                errors=[],
                duration_seconds=0.0
            )
        except Exception as e:
            return PipelineResult(
                stage=PipelineStage.INGESTION,
                success=False,
                input_count=0,
                output_count=0,
                metrics={},
                errors=[str(e)],
                duration_seconds=0.0
            )
    
    async def _run_validation(
        self,
        input_path: Path,
        output_path: Path
    ) -> PipelineResult:
        """Validate document quality"""
        try:
            documents = list(input_path.rglob("*.json"))
            output_dir = output_path / "validation"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            valid_count = 0
            invalid_count = 0
            issues = []
            
            for doc_path in documents:
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        doc = json.load(f)
                    
                    # Validate document
                    report: ValidationReport = self.validator.validate(doc)
                    
                    # Add validation report
                    doc['validation_report'] = {
                        'valid': report.valid,
                        'errors': [issue.message for issue in report.errors],
                        'warnings': [issue.message for issue in report.warnings],
                        'timestamp': report.timestamp.isoformat()
                    }
                    
                    # Save updated document
                    with open(doc_path, 'w', encoding='utf-8') as f:
                        json.dump(doc, f, ensure_ascii=False, indent=2)
                    
                    if report.valid:
                        valid_count += 1
                    else:
                        invalid_count += 1
                        issues.extend([issue.message for issue in report.errors])
                        
                except Exception as e:
                    invalid_count += 1
                    issues.append(f"Error processing {doc_path}: {str(e)}")
            
            return PipelineResult(
                stage=PipelineStage.VALIDATION,
                success=True,
                input_count=len(documents),
                output_count=valid_count,
                metrics={
                    "valid_documents": valid_count,
                    "invalid_documents": invalid_count,
                    "issues_found": len(issues)
                },
                errors=issues,
                duration_seconds=0.0
            )
        except Exception as e:
            return PipelineResult(
                stage=PipelineStage.VALIDATION,
                success=False,
                input_count=0,
                output_count=0,
                metrics={},
                errors=[str(e)],
                duration_seconds=0.0
            )
    
    async def _run_preprocessing(
        self,
        input_path: Path,
        output_path: Path
    ) -> PipelineResult:
        """Preprocess documents"""
        try:
            documents = list(input_path.rglob("*.json"))
            output_dir = output_path / "preprocessing"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            processed_count = 0
            
            for doc_path in documents:
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        doc = json.load(f)
                    
                    # Preprocess text
                    text = doc.get('text', '')
                    processed_text = self._preprocess_text(text)
                    doc['processed_text'] = processed_text
                    
                    # Save updated document
                    with open(doc_path, 'w', encoding='utf-8') as f:
                        json.dump(doc, f, ensure_ascii=False, indent=2)
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error preprocessing {doc_path}: {e}")
            
            return PipelineResult(
                stage=PipelineStage.PREPROCESSING,
                success=True,
                input_count=len(documents),
                output_count=processed_count,
                metrics={"documents_processed": processed_count},
                errors=[],
                duration_seconds=0.0
            )
        except Exception as e:
            return PipelineResult(
                stage=PipelineStage.PREPROCESSING,
                success=False,
                input_count=0,
                output_count=0,
                metrics={},
                errors=[str(e)],
                duration_seconds=0.0
            )
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text"""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove extra newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    async def _run_chunking(
        self,
        input_path: Path,
        output_path: Path
    ) -> PipelineResult:
        """Chunk documents"""
        try:
            documents = list(input_path.rglob("*.json"))
            output_dir = output_path / "chunking"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            chunked_count = 0
            total_chunks = 0
            
            for doc_path in documents:
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        doc = json.load(f)
                    
                    # Extract text
                    text = doc.get('processed_text', doc.get('text', ''))
                    doc_id = doc.get('id', doc_path.stem)
                    
                    # Chunk document
                    chunks = self.chunker.chunk(
                        text=text,
                        doc_id=doc_id,
                        metadata=doc.get('metadata', {})
                    )
                    
                    # Save chunks
                    chunk_dir = output_dir / doc_id
                    chunk_dir.mkdir(parents=True, exist_ok=True)
                    
                    for i, chunk in enumerate(chunks):
                        chunk_path = chunk_dir / f"chunk_{i}.json"
                        with open(chunk_path, 'w', encoding='utf-8') as f:
                            json.dump(chunk.__dict__, f, ensure_ascii=False, indent=2)
                        total_chunks += 1
                    
                    chunked_count += 1
                    
                except Exception as e:
                    logger.error(f"Error chunking {doc_path}: {e}")
            
            return PipelineResult(
                stage=PipelineStage.CHUNKING,
                success=True,
                input_count=len(documents),
                output_count=chunked_count,
                metrics={
                    "documents_chunked": chunked_count,
                    "total_chunks": total_chunks,
                    "avg_chunks_per_doc": total_chunks / max(1, chunked_count)
                },
                errors=[],
                duration_seconds=0.0
            )
        except Exception as e:
            return PipelineResult(
                stage=PipelineStage.CHUNKING,
                success=False,
                input_count=0,
                output_count=0,
                metrics={},
                errors=[str(e)],
                duration_seconds=0.0
            )
    
    async def _run_labeling(
        self,
        input_path: Path,
        output_path: Path
    ) -> PipelineResult:
        """Label chunks"""
        try:
            # Import labeling components
            from pipelines.labeling.combined_labeling_augmentation import EnhancedIntegratedSystem
            
            labeling_system = EnhancedIntegratedSystem()
            
            chunk_dirs = list(input_path.iterdir())
            output_dir = output_path / "labeling"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            labeled_count = 0
            total_chunks = 0
            
            for chunk_dir in chunk_dirs:
                if not chunk_dir.is_dir():
                    continue
                
                chunk_files = list(chunk_dir.rglob("chunk_*.json"))
                total_chunks += len(chunk_files)
                
                # Process chunks
                for chunk_path in chunk_files:
                    try:
                        with open(chunk_path, 'r', encoding='utf-8') as f:
                            chunk_data = json.load(f)
                        
                        # Extract text
                        text = chunk_data.get('text', '')
                        
                        # Label entities
                        labeled_entities = labeling_system.extract_entities(text)
                        
                        # Add labels to chunk
                        chunk_data['labeled_entities'] = [
                            {
                                'text': entity.text,
                                'label': entity.label,
                                'start': entity.start,
                                'end': entity.end,
                                'weight': entity.weight,
                                'context_score': entity.context_score
                            }
                            for entity in labeled_entities
                        ]
                        
                        # Save updated chunk
                        with open(chunk_path, 'w', encoding='utf-8') as f:
                            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
                        
                        labeled_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error labeling {chunk_path}: {e}")
            
            return PipelineResult(
                stage=PipelineStage.LABELING,
                success=True,
                input_count=total_chunks,
                output_count=labeled_count,
                metrics={
                    "chunks_labeled": labeled_count,
                    "total_chunks": total_chunks,
                    "labeling_rate": labeled_count / max(1, total_chunks)
                },
                errors=[],
                duration_seconds=0.0
            )
        except Exception as e:
            return PipelineResult(
                stage=PipelineStage.LABELING,
                success=False,
                input_count=0,
                output_count=0,
                metrics={},
                errors=[str(e)],
                duration_seconds=0.0
            )
    
    async def _run_embedding(
        self,
        input_path: Path,
        output_path: Path
    ) -> PipelineResult:
        """Generate embeddings"""
        try:
            # Import embedding service
            from core.embeddings.embedding_service import EmbeddingService
            
            embedding_service = EmbeddingService()
            
            chunk_dirs = list(input_path.iterdir())
            output_dir = output_path / "embedding"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            embedded_count = 0
            embeddings_list = []
            
            for chunk_dir in chunk_dirs:
                if not chunk_dir.is_dir():
                    continue
                
                chunk_files = list(chunk_dir.rglob("chunk_*.json"))
                
                # Process chunks
                for chunk_path in chunk_files:
                    try:
                        with open(chunk_path, 'r', encoding='utf-8') as f:
                            chunk_data = json.load(f)
                        
                        # Extract text
                        text = chunk_data.get('text', '')
                        
                        # Generate embedding
                        embedding = await embedding_service.embed_text(text)
                        chunk_data['embedding'] = embedding.tolist()
                        embeddings_list.append(embedding)
                        
                        # Save updated chunk
                        with open(chunk_path, 'w', encoding='utf-8') as f:
                            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
                        
                        embedded_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error embedding {chunk_path}: {e}")
            
            # Save embeddings array
            if embeddings_list:
                embeddings_array = np.array(embeddings_list)
                np.save(output_dir / "embeddings.npy", embeddings_array)
            
            return PipelineResult(
                stage=PipelineStage.EMBEDDING,
                success=True,
                input_count=embedded_count,
                output_count=embedded_count,
                metrics={
                    "chunks_embedded": embedded_count,
                    "embedding_dim": len(embeddings_list[0]) if embeddings_list else 0
                },
                errors=[],
                duration_seconds=0.0
            )
        except Exception as e:
            return PipelineResult(
                stage=PipelineStage.EMBEDDING,
                success=False,
                input_count=0,
                output_count=0,
                metrics={},
                errors=[str(e)],
                duration_seconds=0.0
            )
    
    async def _run_indexing(
        self,
        input_path: Path,
        output_path: Path
    ) -> PipelineResult:
        """Index chunks"""
        try:
            # Import indexing service
            from core.indexing.indexing_service import IndexingService
            
            indexing_service = IndexingService(self.config.indexing)
            
            chunk_dirs = list(input_path.iterdir())
            output_dir = output_path / "indexing"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            indexed_count = 0
            chunks = []
            embeddings = []
            
            # Load chunks and embeddings
            for chunk_dir in chunk_dirs:
                if not chunk_dir.is_dir():
                    continue
                
                chunk_files = list(chunk_dir.rglob("chunk_*.json"))
                embeddings_file = chunk_dir / "embeddings.npy"
                
                # Load chunks
                for chunk_path in chunk_files:
                    try:
                        with open(chunk_path, 'r', encoding='utf-8') as f:
                            chunk_data = json.load(f)
                        chunks.append(chunk_data)
                    except Exception as e:
                        logger.error(f"Error loading chunk {chunk_path}: {e}")
                
                # Load embeddings
                if embeddings_file.exists():
                    try:
                        embeddings_array = np.load(embeddings_file)
                        embeddings.extend(embeddings_array.tolist())
                    except Exception as e:
                        logger.error(f"Error loading embeddings {embeddings_file}: {e}")
            
            # Index chunks
            stats = await indexing_service.index_chunks(chunks, embeddings)
            
            # Save index stats
            stats_path = output_dir / "index_stats.json"
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            indexed_count = len(chunks)
            
            return PipelineResult(
                stage=PipelineStage.INDEXING,
                success=True,
                input_count=indexed_count,
                output_count=indexed_count,
                metrics=stats,
                errors=[],
                duration_seconds=0.0
            )
        except Exception as e:
            return PipelineResult(
                stage=PipelineStage.INDEXING,
                success=False,
                input_count=0,
                output_count=0,
                metrics={},
                errors=[str(e)],
                duration_seconds=0.0
            )