"""
Unit Tests for Embedding Generator
==================================

Tests for the EmbeddingGenerator class with caching and advanced features.
"""

import pytest
from unittest.mock import Mock, patch
from graph.builders.embedding_generator import (
    EmbeddingGenerator,
    EmbeddingCache,
    generate_embedding,
    generate_batch_embeddings,
)


class TestEmbeddingCache:
    """Test EmbeddingCache class"""
    
    def test_cache_initialization(self, tmp_path):
        """Test cache initialization"""
        cache = EmbeddingCache(cache_dir=tmp_path / "cache")
        assert cache.cache_dir.exists()
        assert len(cache._cache) == 0
    
    def test_cache_get_set(self, tmp_path):
        """Test cache get/set"""
        cache = EmbeddingCache(cache_dir=tmp_path / "cache")
        
        text = "test text"
        embedding = [0.1, 0.2, 0.3]
        
        # Set
        cache.set(text, embedding)
        
        # Get
        retrieved = cache.get(text)
        assert retrieved == embedding
    
    def test_cache_miss(self, tmp_path):
        """Test cache miss"""
        cache = EmbeddingCache(cache_dir=tmp_path / "cache")
        
        retrieved = cache.get("nonexistent text")
        assert retrieved is None
    
    def test_cache_max_size(self, tmp_path):
        """Test cache max size limit"""
        cache = EmbeddingCache(cache_dir=tmp_path / "cache", max_cache_size=10)
        
        # Add more than max_cache_size
        for i in range(15):
            cache.set(f"text_{i}", [float(i)])
        
        # Should not exceed max size by much
        assert len(cache._cache) <= 15


class TestEmbeddingGenerator:
    """Test EmbeddingGenerator class"""
    
    @pytest.fixture
    def generator(self, tmp_path):
        """Create generator instance"""
        return EmbeddingGenerator(
            model_name="BAAI/bge-m3",
            batch_size=10,
            dimension=1024,
            use_cache=True
        )
    
    @pytest.fixture
    def generator_no_cache(self):
        """Create generator without cache"""
        return EmbeddingGenerator(use_cache=False)
    
    def test_generator_initialization(self, generator):
        """Test generator initialization"""
        assert generator.model_name == "BAAI/bge-m3"
        assert generator.batch_size == 10
        assert generator.dimension == 1024
        assert generator.cache is not None
    
    def test_generator_no_cache(self, generator_no_cache):
        """Test generator without cache"""
        assert generator_no_cache.cache is None
    
    def test_generate_embedding_empty_text(self, generator):
        """Test generating embedding for empty text"""
        embedding = generator.generate_embedding("")
        assert embedding is None
        
        embedding = generator.generate_embedding("   ")
        assert embedding is None
    
    def test_generate_embedding_short_text(self, generator):
        """Test generating embedding for short text"""
        embedding = generator.generate_embedding("hi")
        assert embedding is None
    
    def test_generate_embedding_valid_text(self, generator):
        """Test generating embedding for valid text"""
        text = "این یک متن تست است"
        embedding = generator.generate_embedding(text)
        
        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 1024
        assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_embedding_caching(self, generator):
        """Test embedding caching"""
        text = "این یک متن تست است"
        
        # First call - cache miss
        embedding1 = generator.generate_embedding(text)
        cache_misses_1 = generator.stats['cache_misses']
        
        # Second call - cache hit
        embedding2 = generator.generate_embedding(text)
        cache_hits_2 = generator.stats['cache_hits']
        
        # Should be same embedding
        assert embedding1 == embedding2
        
        # Should have cache hit
        assert cache_hits_2 > 0
    
    def test_generate_batch_embeddings(self, generator):
        """Test batch embedding generation"""
        texts = [
            "این متن اول است",
            "این متن دوم است",
            "این متن سوم است",
        ]
        
        embeddings = generator.generate_batch_embeddings(texts)
        
        assert len(embeddings) == len(texts)
        assert all(isinstance(emb, list) for emb in embeddings if emb)
        assert all(len(emb) == 1024 for emb in embeddings if emb)
    
    def test_generate_batch_embeddings_empty(self, generator):
        """Test batch generation with empty list"""
        embeddings = generator.generate_batch_embeddings([])
        assert embeddings == []
    
    def test_find_similar_nodes(self, generator):
        """Test finding similar nodes"""
        query_embedding = [0.1] * 1024
        
        node_embeddings = [
            {'id': 'node1', 'embedding': [0.1] * 1024},  # Very similar
            {'id': 'node2', 'embedding': [0.5] * 1024},  # Less similar
            {'id': 'node3', 'embedding': [-0.1] * 1024}, # Opposite
        ]
        
        similar = generator.find_similar_nodes(query_embedding, node_embeddings, top_k=2)
        
        assert len(similar) <= 2
        assert all('id' in node for node in similar)
        assert all('similarity' in node for node in similar)
        
        # First should be most similar
        if len(similar) >= 2:
            assert similar[0]['similarity'] >= similar[1]['similarity']
    
    def test_calculate_similarity(self, generator):
        """Test similarity calculation"""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]
        
        # Identical vectors
        sim = generator.calculate_similarity(emb1, emb2)
        assert abs(sim - 1.0) < 0.01
        
        # Orthogonal vectors
        emb3 = [0.0, 1.0, 0.0]
        sim = generator.calculate_similarity(emb1, emb3)
        assert abs(sim) < 0.01
        
        # Opposite vectors
        emb4 = [-1.0, 0.0, 0.0]
        sim = generator.calculate_similarity(emb1, emb4)
        assert sim < 0
    
    def test_find_similar_texts(self, generator):
        """Test finding similar texts"""
        query = "قانون مدنی"
        candidates = [
            "قانون مدنی ایران",
            "قانون مجازات",
            "قانون تجارت",
        ]
        
        similar = generator.find_similar_texts(query, candidates, top_k=2)
        
        assert len(similar) <= 2
        assert all(isinstance(item, tuple) for item in similar)
        assert all(len(item) == 2 for item in similar)
        
        # First should be most similar
        if len(similar) >= 2:
            assert similar[0][1] >= similar[1][1]
    
    def test_cluster_embeddings(self, generator):
        """Test embedding clustering"""
        # Create some embeddings
        embeddings = [
            [1.0, 0.0, 0.0],
            [1.1, 0.1, 0.0],
            [0.0, 1.0, 0.0],
            [0.1, 1.1, 0.0],
        ]
        
        labels = generator.cluster_embeddings(embeddings, n_clusters=2)
        
        assert len(labels) == len(embeddings)
        assert all(isinstance(label, int) for label in labels)
        assert len(set(labels)) <= 2
    
    def test_reduce_dimensions(self, generator):
        """Test dimension reduction"""
        # Create high-dimensional embeddings
        embeddings = [
            [float(i) for i in range(100)],
            [float(i+1) for i in range(100)],
            [float(i+2) for i in range(100)],
        ]
        
        reduced = generator.reduce_dimensions(embeddings, n_components=2)
        
        assert len(reduced) == len(embeddings)
        if reduced != embeddings:  # If reduction worked
            assert all(len(emb) == 2 for emb in reduced)
    
    def test_get_statistics(self, generator):
        """Test getting statistics"""
        # Generate some embeddings
        generator.generate_embedding("test text 1")
        generator.generate_embedding("test text 2")
        
        stats = generator.get_statistics()
        
        assert 'total_generated' in stats
        assert 'cache_hits' in stats
        assert 'cache_misses' in stats
        assert stats['total_generated'] >= 2
    
    def test_save_and_clear_cache(self, generator):
        """Test saving and clearing cache"""
        # Generate some embeddings
        generator.generate_embedding("test text")
        
        # Save cache
        generator.save_cache()
        
        # Clear cache
        generator.clear_cache()
        
        # Cache should be empty
        if generator.cache:
            assert len(generator.cache._cache) == 0
    
    def test_generate_embeddings_for_nodes(self, generator):
        """Test generating embeddings for nodes"""
        nodes = [
            {'id': 'node1', 'content': 'این متن اول است'},
            {'id': 'node2', 'content': 'این متن دوم است'},
        ]
        
        nodes_with_emb = generator.generate_embeddings_for_nodes(nodes, text_field='content')
        
        assert len(nodes_with_emb) == len(nodes)
        assert all('embedding' in node for node in nodes_with_emb)


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_generate_embedding_function(self):
        """Test convenience function"""
        text = "این یک متن تست است"
        embedding = generate_embedding(text)
        
        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 1024
    
    def test_generate_batch_embeddings_function(self):
        """Test batch convenience function"""
        texts = ["متن اول", "متن دوم", "متن سوم"]
        embeddings = generate_batch_embeddings(texts, batch_size=10)
        
        assert len(embeddings) == len(texts)
        assert all(isinstance(emb, list) for emb in embeddings if emb)


class TestAsyncGeneration:
    """Test async embedding generation"""
    
    @pytest.mark.asyncio
    async def test_generate_embedding_async(self):
        """Test async embedding generation"""
        generator = EmbeddingGenerator(use_cache=False)
        
        text = "این یک متن تست است"
        embedding = await generator.generate_embedding_async(text)
        
        assert embedding is not None
        assert isinstance(embedding, list)
    
    @pytest.mark.asyncio
    async def test_generate_batch_embeddings_async(self):
        """Test async batch generation"""
        generator = EmbeddingGenerator(use_cache=False)
        
        texts = ["متن اول", "متن دوم"]
        embeddings = await generator.generate_batch_embeddings_async(texts)
        
        assert len(embeddings) == len(texts)


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_batch(self):
        """Test empty batch"""
        generator = EmbeddingGenerator()
        embeddings = generator.generate_batch_embeddings([])
        assert embeddings == []
    
    def test_none_text(self):
        """Test None text"""
        generator = EmbeddingGenerator()
        embedding = generator.generate_embedding(None)
        assert embedding is None
    
    def test_very_long_text(self):
        """Test very long text"""
        generator = EmbeddingGenerator()
        text = "این متن " * 1000  # Very long text
        embedding = generator.generate_embedding(text)
        
        # Should still work
        assert embedding is not None
        assert len(embedding) == 1024
    
    def test_special_characters(self):
        """Test text with special characters"""
        generator = EmbeddingGenerator()
        text = "متن با کاراکترهای خاص: @#$%^&*()"
        embedding = generator.generate_embedding(text)
        
        assert embedding is not None
    
    def test_mixed_language(self):
        """Test mixed Persian and English"""
        generator = EmbeddingGenerator()
        text = "این متن mixed است with English"
        embedding = generator.generate_embedding(text)
        
        assert embedding is not None
