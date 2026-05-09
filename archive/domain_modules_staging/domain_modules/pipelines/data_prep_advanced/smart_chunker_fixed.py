"""
Smart Chunker - Advanced Chunking Strategies
=============================================
Multiple chunking strategies with optimization
"""

import re
from enum import Enum
from typing import Dict, List, Optional
import numpy as np
from collections import defaultdict


class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    FIXED_SIZE = "fixed_size"  # Fixed token/word count
    SENTENCE_BASED = "sentence_based"  # Sentence boundaries
    PARAGRAPH_BASED = "paragraph_based"  # Paragraph boundaries
    SEMANTIC = "semantic"  # Semantic similarity
    SLIDING_WINDOW = "sliding_window"  # Overlapping windows
    HIERARCHICAL = "hierarchical"  # Multi-level chunks
    LEGAL_STRUCTURE = "legal_structure"  # Legal document structure
    ADAPTIVE = "adaptive"  # Adaptive based on content


class Chunk:
    """Chunk with metadata"""
    
    def __init__(
        self,
        id: str,
        text: str,
        start_pos: int,
        end_pos: int,
        token_count: int,
        sentence_count: int,
        strategy: ChunkingStrategy,
        metadata: Dict = None,
        # Quality metrics
        coherence_score: float = 0.0,
        completeness_score: float = 0.0,
        boundary_quality: float = 0.0,
        # Relationships
        parent_id: Optional[str] = None,
        children_ids: List[str] = None,
        prev_chunk_id: Optional[str] = None,
        next_chunk_id: Optional[str] = None,
    ):
        self.id = id
        self.text = text
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.token_count = token_count
        self.sentence_count = sentence_count
        self.strategy = strategy
        self.metadata = metadata or {}
        
        # Quality metrics
        self.coherence_score = coherence_score
        self.completeness_score = completeness_score
        self.boundary_quality = boundary_quality
        
        # Relationships
        self.parent_id = parent_id
        self.children_ids = children_ids or []
        self.prev_chunk_id = prev_chunk_id
        self.next_chunk_id = next_chunk_id


class SmartChunker:
    """
    Advanced chunking with multiple strategies
    
    Features:
    - Multiple chunking strategies
    - Semantic boundary detection
    - Legal structure awareness
    - Overlap management
    - Quality scoring
    - Hierarchical chunking
    """
    
    def __init__(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.ADAPTIVE,
        target_size: int = 512,
        min_size: int = 256,
        max_size: int = 1024,
        overlap: int = 50,
        preserve_sentences: bool = True,
        preserve_paragraphs: bool = True,
    ):
        self.strategy = strategy
        self.target_size = target_size
        self.min_size = min_size
        self.max_size = max_size
        self.overlap = overlap
        self.preserve_sentences = preserve_sentences
        self.preserve_paragraphs = preserve_paragraphs
        
        # Legal patterns
        self.article_pattern = re.compile(r'ماده\s+[0-9۰-۹]{1,4}')
        self.section_pattern = re.compile(r'(?:بخش|فصل|قسمت)\s+[آ-ی0-9۰-۹]+')
    
    def chunk(
        self,
        text: str,
        doc_id: str = "doc",
        metadata: Optional[Dict] = None
    ) -> List[Chunk]:
        """
        Chunk text using selected strategy
        
        Args:
            text: Input text
            doc_id: Document ID
            metadata: Optional metadata
            
        Returns:
            List of chunks
        """
        metadata = metadata or {}
        
        # Select strategy
        if self.strategy == ChunkingStrategy.ADAPTIVE:
            strategy = self._select_adaptive_strategy(text)
        else:
            strategy = self.strategy
        
        # Apply strategy
        if strategy == ChunkingStrategy.FIXED_SIZE:
            chunks = self._chunk_fixed_size(text, doc_id, metadata)
        elif strategy == ChunkingStrategy.SENTENCE_BASED:
            chunks = self._chunk_sentence_based(text, doc_id, metadata)
        elif strategy == ChunkingStrategy.PARAGRAPH_BASED:
            chunks = self._chunk_paragraph_based(text, doc_id, metadata)
        elif strategy == ChunkingStrategy.SEMANTIC:
            chunks = self._chunk_semantic(text, doc_id, metadata)
        elif strategy == ChunkingStrategy.SLIDING_WINDOW:
            chunks = self._chunk_sliding_window(text, doc_id, metadata)
        elif strategy == ChunkingStrategy.HIERARCHICAL:
            chunks = self._chunk_hierarchical(text, doc_id, metadata)
        elif strategy == ChunkingStrategy.LEGAL_STRUCTURE:
            chunks = self._chunk_legal_structure(text, doc_id, metadata)
        else:
            chunks = self._chunk_sentence_based(text, doc_id, metadata)
        
        # Post-process
        chunks = self._post_process_chunks(chunks)
        
        # Link chunks
        chunks = self._link_chunks(chunks)
        
        # Score quality
        chunks = self._score_chunks(chunks, text)
        
        return chunks
    
    def _select_adaptive_strategy(self, text: str) -> ChunkingStrategy:
        """Select best strategy based on content"""
        # Check if legal document
        has_articles = bool(self.article_pattern.search(text))
        has_sections = bool(self.section_pattern.search(text))
        
        if has_articles or has_sections:
            return ChunkingStrategy.LEGAL_STRUCTURE
        
        # Check structure
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        if len(paragraphs) > 5:
            return ChunkingStrategy.PARAGRAPH_BASED
        
        # Check length
        word_count = len(text.split())
        if word_count < 500:
            return ChunkingStrategy.SENTENCE_BASED
        elif word_count > 5000:
            return ChunkingStrategy.HIERARCHICAL
        
        # Default
        return ChunkingStrategy.SENTENCE_BASED
    
    def _chunk_fixed_size(
        self,
        text: str,
        doc_id: str,
        metadata: Dict
    ) -> List[Chunk]:
        """Fixed-size chunking"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.target_size - self.overlap):
            chunk_words = words[i:i + self.target_size]
            chunk_text = ' '.join(chunk_words)
            
            chunk = Chunk(
                id=f"{doc_id}_chunk_{len(chunks)}",
                text=chunk_text,
                start_pos=i,
                end_pos=i + len(chunk_words),
                token_count=len(chunk_words),
                sentence_count=chunk_text.count('.') + chunk_text.count('؟'),
                strategy=ChunkingStrategy.FIXED_SIZE,
                metadata={**metadata, 'chunk_index': len(chunks)}
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_sentence_based(
        self,
        text: str,
        doc_id: str,
        metadata: Dict
    ) -> List[Chunk]:
        """Sentence-based chunking"""
        # Split into sentences
        sentences = re.split(r'[.!?؟۔]\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        start_pos = 0
        
        for sent in sentences:
            sent_size = len(sent.split())
            
            if current_size + sent_size > self.max_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk = Chunk(
                    id=f"{doc_id}_chunk_{len(chunks)}",
                    text=chunk_text,
                    start_pos=start_pos,
                    end_pos=start_pos + len(current_chunk),
                    token_count=current_size,
                    sentence_count=len(current_chunk),
                    strategy=ChunkingStrategy.SENTENCE_BASED,
                    metadata={**metadata, 'chunk_index': len(chunks)}
                )
                chunks.append(chunk)
                
                # Overlap
                if self.overlap > 0 and len(current_chunk) > 1:
                    overlap_sents = current_chunk[-self.overlap:]
                    current_chunk = overlap_sents
                    current_size = sum(len(s.split()) for s in overlap_sents)
                    start_pos += len(current_chunk) - len(overlap_sents) if self.overlap > 0 else len(current_chunk)
                else:
                    current_chunk = []
                    current_size = 0
                    start_pos += len(current_chunk)
            
            current_chunk.append(sent)
            current_size += sent_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = Chunk(
                id=f"{doc_id}_chunk_{len(chunks)}",
                text=chunk_text,
                start_pos=start_pos,
                end_pos=start_pos + len(current_chunk),
                token_count=current_size,
                sentence_count=len(current_chunk),
                strategy=ChunkingStrategy.SENTENCE_BASED,
                metadata={**metadata, 'chunk_index': len(chunks)}
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_paragraph_based(
        self,
        text: str,
        doc_id: str,
        metadata: Dict
    ) -> List[Chunk]:
        """Paragraph-based chunking"""
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        start_pos = 0
        
        for para in paragraphs:
            para_size = len(para.split())
            
            if (current_size + para_size > self.max_size and current_chunk) or \
               (current_size + para_size > self.min_size and self.preserve_paragraphs):
                # Create chunk
                chunk_text = '\n\n'.join(current_chunk)
                chunk = Chunk(
                    id=f"{doc_id}_chunk_{len(chunks)}",
                    text=chunk_text,
                    start_pos=start_pos,
                    end_pos=start_pos + len(current_chunk),
                    token_count=current_size,
                    sentence_count=chunk_text.count('.') + chunk_text.count('؟'),
                    strategy=ChunkingStrategy.PARAGRAPH_BASED,
                    metadata={**metadata, 'chunk_index': len(chunks)}
                )
                chunks.append(chunk)
                
                # Overlap
                if self.overlap > 0 and len(current_chunk) > 1:
                    overlap_paras = current_chunk[-self.overlap:]
                    current_chunk = overlap_paras
                    current_size = sum(len(p.split()) for p in overlap_paras)
                    start_pos += len(current_chunk) - len(overlap_paras) if self.overlap > 0 else len(current_chunk)
                else:
                    current_chunk = []
                    current_size = 0
                    start_pos += len(current_chunk)
            
            current_chunk.append(para)
            current_size += para_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunk = Chunk(
                id=f"{doc_id}_chunk_{len(chunks)}",
                text=chunk_text,
                start_pos=start_pos,
                end_pos=start_pos + len(current_chunk),
                token_count=current_size,
                sentence_count=chunk_text.count('.') + chunk_text.count('؟'),
                strategy=ChunkingStrategy.PARAGRAPH_BASED,
                metadata={**metadata, 'chunk_index': len(chunks)}
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_legal_structure(
        self,
        text: str,
        doc_id: str,
        metadata: Dict
    ) -> List[Chunk]:
        """Legal document structure-based chunking"""
        # Find articles
        article_matches = list(self.article_pattern.finditer(text))
        
        chunks = []
        start_pos = 0
        
        # If no articles found, use sentence-based
        if not article_matches:
            return self._chunk_sentence_based(text, doc_id, metadata)
        
        # Create chunks for each article
        for i, match in enumerate(article_matches):
            article_start = match.start()
            
            # Add chunk for text before article (if any)
            if article_start > start_pos:
                pre_text = text[start_pos:article_start].strip()
                if pre_text:
                    chunk = Chunk(
                        id=f"{doc_id}_chunk_{len(chunks)}",
                        text=pre_text,
                        start_pos=start_pos,
                        end_pos=article_start,
                        token_count=len(pre_text.split()),
                        sentence_count=pre_text.count('.') + pre_text.count('؟'),
                        strategy=ChunkingStrategy.LEGAL_STRUCTURE,
                        metadata={**metadata, 'chunk_index': len(chunks), 'type': 'preamble'}
                    )
                    chunks.append(chunk)
            
            # Determine article end
            article_end = article_matches[i + 1].start() if i + 1 < len(article_matches) else len(text)
            article_text = text[article_start:article_end].strip()
            
            # Create chunk for article
            chunk = Chunk(
                id=f"{doc_id}_chunk_{len(chunks)}",
                text=article_text,
                start_pos=article_start,
                end_pos=article_end,
                token_count=len(article_text.split()),
                sentence_count=article_text.count('.') + article_text.count('؟'),
                strategy=ChunkingStrategy.LEGAL_STRUCTURE,
                metadata={**metadata, 'chunk_index': len(chunks), 'type': 'article', 'article_number': match.group(0)}
            )
            chunks.append(chunk)
            
            start_pos = article_end
        
        return chunks
    
    def _chunk_semantic(
        self,
        text: str,
        doc_id: str,
        metadata: Dict
    ) -> List[Chunk]:
        """Semantic similarity-based chunking"""
        # This is a simplified version - in practice, you would use embeddings
        sentences = re.split(r'[.!?؟۔]\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        start_pos = 0
        
        for i, sent in enumerate(sentences):
            sent_size = len(sent.split())
            
            # Simple semantic similarity check (in practice, use embeddings)
            should_break = False
            if i > 0 and current_chunk:
                # Check if topic changes (simplified)
                prev_sent = current_chunk[-1]
                curr_words = set(sent.lower().split())
                prev_words = set(prev_sent.lower().split())
                similarity = len(curr_words & prev_words) / len(curr_words | prev_words) if (curr_words | prev_words) else 0
                should_break = similarity < 0.1  # Low similarity
            
            if (current_size + sent_size > self.target_size and current_chunk) or should_break:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk = Chunk(
                    id=f"{doc_id}_chunk_{len(chunks)}",
                    text=chunk_text,
                    start_pos=start_pos,
                    end_pos=start_pos + len(current_chunk),
                    token_count=current_size,
                    sentence_count=len(current_chunk),
                    strategy=ChunkingStrategy.SEMANTIC,
                    metadata={**metadata, 'chunk_index': len(chunks)}
                )
                chunks.append(chunk)
                
                # Overlap
                if self.overlap > 0 and len(current_chunk) > 1:
                    overlap_sents = current_chunk[-self.overlap:]
                    current_chunk = overlap_sents
                    current_size = sum(len(s.split()) for s in overlap_sents)
                    start_pos += len(current_chunk) - len(overlap_sents) if self.overlap > 0 else len(current_chunk)
                else:
                    current_chunk = []
                    current_size = 0
                    start_pos += len(current_chunk)
            
            current_chunk.append(sent)
            current_size += sent_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = Chunk(
                id=f"{doc_id}_chunk_{len(chunks)}",
                text=chunk_text,
                start_pos=start_pos,
                end_pos=start_pos + len(current_chunk),
                token_count=current_size,
                sentence_count=len(current_chunk),
                strategy=ChunkingStrategy.SEMANTIC,
                metadata={**metadata, 'chunk_index': len(chunks)}
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_sliding_window(
        self,
        text: str,
        doc_id: str,
        metadata: Dict
    ) -> List[Chunk]:
        """Sliding window chunking"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words) - self.target_size + 1, self.target_size - self.overlap):
            chunk_words = words[i:i + self.target_size]
            chunk_text = ' '.join(chunk_words)
            
            chunk = Chunk(
                id=f"{doc_id}_chunk_{len(chunks)}",
                text=chunk_text,
                start_pos=i,
                end_pos=i + len(chunk_words),
                token_count=len(chunk_words),
                sentence_count=chunk_text.count('.') + chunk_text.count('؟'),
                strategy=ChunkingStrategy.SLIDING_WINDOW,
                metadata={**metadata, 'chunk_index': len(chunks), 'window_start': i}
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_hierarchical(
        self,
        text: str,
        doc_id: str,
        metadata: Dict
    ) -> List[Chunk]:
        """Hierarchical chunking"""
        # First chunk by paragraphs
        para_chunks = self._chunk_paragraph_based(text, doc_id, metadata)
        
        # Then chunk large paragraphs further
        final_chunks = []
        for chunk in para_chunks:
            if chunk.token_count > self.max_size:
                # Split large chunk
                sub_text = chunk.text
                sub_chunks = self._chunk_sentence_based(sub_text, f"{chunk.id}_sub", chunk.metadata)
                
                # Update parent-child relationships
                for i, sub_chunk in enumerate(sub_chunks):
                    sub_chunk.parent_id = chunk.id
                    chunk.children_ids.append(sub_chunk.id)
                    if i > 0:
                        sub_chunk.prev_chunk_id = sub_chunks[i-1].id
                    if i < len(sub_chunks) - 1:
                        sub_chunk.next_chunk_id = sub_chunks[i+1].id
                
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def _post_process_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Post-process chunks"""
        # Remove empty chunks
        chunks = [c for c in chunks if c.text.strip()]
        
        # Merge small chunks
        merged_chunks = []
        current_chunk = None
        
        for chunk in chunks:
            if current_chunk is None:
                current_chunk = chunk
            elif current_chunk.token_count + chunk.token_count <= self.max_size:
                # Merge chunks
                current_chunk.text += '\n\n' + chunk.text
                current_chunk.end_pos = chunk.end_pos
                current_chunk.token_count += chunk.token_count
                current_chunk.sentence_count += chunk.sentence_count
                current_chunk.metadata.update(chunk.metadata)
            else:
                merged_chunks.append(current_chunk)
                current_chunk = chunk
        
        if current_chunk:
            merged_chunks.append(current_chunk)
        
        return merged_chunks
    
    def _link_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Link chunks in sequence"""
        for i in range(len(chunks)):
            if i > 0:
                chunks[i].prev_chunk_id = chunks[i-1].id
            if i < len(chunks) - 1:
                chunks[i].next_chunk_id = chunks[i+1].id
        return chunks
    
    def _score_chunks(self, chunks: List[Chunk], original_text: str) -> List[Chunk]:
        """Score chunk quality"""
        for chunk in chunks:
            # Coherence score (simplified)
            chunk.coherence_score = min(1.0, chunk.token_count / self.target_size)
            
            # Completeness score (simplified)
            chunk.completeness_score = 1.0 if chunk.token_count >= self.min_size else chunk.token_count / self.min_size
            
            # Boundary quality (simplified)
            chunk.boundary_quality = 1.0  # In practice, check for clean sentence boundaries
        
        return chunks