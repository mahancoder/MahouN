"""
Comprehensive Tests for Advanced RAG Integration
================================================

Tests for GraphEnrichmentService with all advanced features.
"""

import pytest
import asyncio

from graph.services.rag_integration import (
    GraphEnrichmentService,
    EnrichmentCache,
    enrich_rag_results,
    extract_query_entities,
)


class TestEnrichmentCache:
    """Test EnrichmentCache class"""
    
    def test_cache_initialization(self):
        """Test cache initialization"""
        cache = EnrichmentCache(ttl_seconds=60, max_size=100)
        assert cache.ttl_seconds == 60
        assert cache.max_size == 100
        assert len(cache._cache) == 0
    
    def test_cache_get_set(self):
        """Test cache get/set"""
        cache = EnrichmentCache()
        
        key = "test_key"
        value = {"data": "test"}
        
        # Set
        cache.set(key, value)
        
        # Get
        retrieved = cache.get(key)
        assert retrieved == value
    
    def test_cache_miss(self):
        """Test cache miss"""
        cache = EnrichmentCache()
        
        retrieved = cache.get("nonexistent")
        assert retrieved is None
    
    def test_cache_expiration(self):
        """Test cache TTL expiration"""
        import time
        
        cache = EnrichmentCache(ttl_seconds=1)
        
        cache.set("key", {"data": "value"})
        
        # Should exist immediately
        assert cache.get("key") is not None
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get("key") is None
    
    def test_cache_max_size(self):
        """Test cache max size eviction"""
        cache = EnrichmentCache(max_size=5)
        
        # Add more than max_size
        for i in range(10):
            cache.set(f"key_{i}", {"data": i})
        
        # Should not exceed max size
        assert len(cache._cache) <= 5
    
    def test_cache_clear(self):
        """Test cache clear"""
        cache = EnrichmentCache()
        
        cache.set("key1", {"data": 1})
        cache.set("key2", {"data": 2})
        
        cache.clear()
        
        assert len(cache._cache) == 0
        assert cache.get("key1") is None


class TestGraphEnrichmentService:
    """Test GraphEnrichmentService class"""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock Neo4j connection"""
        conn = Mock()
        conn.execute_query = Mock(return_value=[])
        return conn
    
    @pytest.fixture
    def service(self, mock_connection):
        """Create service instance"""
        return GraphEnrichmentService(
            connection=mock_connection,
            timeout_ms=1000,
            max_hops=2,
            enable_reranking=True,
            enable_validation=True,
            cache_enabled=True,
        )
    
    def test_service_initialization(self, service):
        """Test service initialization"""
        assert service.timeout_ms == 1000
        assert service.max_hops == 2
        assert service.enable_reranking is True
        assert service.enable_validation is True
        assert service.cache is not None
    
    @pytest.mark.asyncio
    async def test_enrich_retrieval_results_empty(self, service):
        """Test enrichment with empty results"""
        query = "تست"
        results = []
        
        enriched = await service.enrich_retrieval_results(query, results)
        
        assert enriched == []
    
    @pytest.mark.asyncio
    async def test_enrich_retrieval_results_basic(self, service, mock_connection):
        """Test basic enrichment"""
        query = "ماده 10 قانون مدنی"
        results = [
            {
                'id': 'article_1',
                'content': 'محتوای ماده 10',
                'score': 0.8,
            }
        ]
        
        # Mock entity extraction
        with patch.object(service.entity_extractor, 'extract_and_validate') as mock_extract:
            mock_extract.return_value = []
            
            enriched = await service.enrich_retrieval_results(query, results)
            
            assert len(enriched) == 1
            assert 'enriched' in enriched[0]
    
    @pytest.mark.asyncio
    async def test_enrich_with_timeout(self, service):
        """Test enrichment timeout"""
        service.timeout_ms = 1  # Very short timeout
        
        query = "تست"
        results = [{'id': 'test', 'content': 'test'}]
        
        # Should timeout and return original results
        enriched = await service.enrich_retrieval_results(query, results)
        
        assert enriched == results
        assert service.stats['timeouts'] > 0
    
    @pytest.mark.asyncio
    async def test_enrich_with_cache(self, service):
        """Test enrichment caching"""
        query = "تست"
        results = [{'id': 'test', 'content': 'test'}]
        
        with patch.object(service.entity_extractor, 'extract_and_validate') as mock_extract:
            mock_extract.return_value = []
            
            # First call
            enriched1 = await service.enrich_retrieval_results(query, results)
            
            # Second call (should hit cache)
            enriched2 = await service.enrich_retrieval_results(query, results)
            
            assert enriched1 == enriched2
            assert service.stats['cache_hits'] > 0
    
    @pytest.mark.asyncio
    async def test_multihop_context(self, service, mock_connection):
        """Test multi-hop context extraction"""
        result = {'id': 'article_1', 'content': 'test'}
        query_entities = []
        
        # Mock graph query
        mock_connection.execute_query.return_value = [
            {'id': 'related_1', 'type': 'Article', 'hops': 1},
            {'id': 'related_2', 'type': 'Law', 'hops': 2},
        ]
        
        context = await service._get_multihop_context(
            result, query_entities, max_hops=2
        )
        
        assert len(context) == 2
        assert context[0]['id'] == 'related_1'
    
    @pytest.mark.asyncio
    async def test_citation_network_analysis(self, service, mock_connection):
        """Test citation network analysis"""
        result = {'id': 'verdict_1'}
        
        # Mock citation query
        mock_connection.execute_query.return_value = [
            {
                'citations_in': 5,
                'citations_out': 3,
                'cited_ids': ['v1', 'v2'],
                'citing_ids': ['v3', 'v4', 'v5'],
            }
        ]
        
        citations = await service._analyze_citation_network(result)
        
        assert citations['citations_in'] == 5
        assert citations['citations_out'] == 3
    
    @pytest.mark.asyncio
    async def test_authority_score_calculation(self, service, mock_connection):
        """Test authority score calculation"""
        result = {'id': 'article_1'}
        
        # Mock PageRank query
        mock_connection.execute_query.return_value = [
            {'pagerank': 0.85}
        ]
        
        score = await service._calculate_authority_score(result)
        
        assert score == 0.85
    
    def test_temporal_relevance_calculation(self, service):
        """Test temporal relevance calculation"""
        from datetime import datetime, timedelta
        
        # Recent document
        recent_result = {
            'date': (datetime.now() - timedelta(days=30)).isoformat()
        }
        recent_score = service._calculate_temporal_relevance(recent_result)
        assert recent_score > 0.9
        
        # Old document
        old_result = {
            'date': (datetime.now() - timedelta(days=730)).isoformat()
        }
        old_score = service._calculate_temporal_relevance(old_result)
        assert old_score < 0.2
        
        # No date
        no_date_result = {}
        no_date_score = service._calculate_temporal_relevance(no_date_result)
        assert no_date_score == 0.5
    
    def test_reranking_with_graph_signals(self, service):
        """Test re-ranking with graph signals"""
        results = [
            {
                'id': '1',
                'score': 0.5,
                'authority_score': 0.3,
                'temporal_score': 0.4,
                'enrichment_count': 2,
            },
            {
                'id': '2',
                'score': 0.6,
                'authority_score': 0.8,
                'temporal_score': 0.9,
                'enrichment_count': 5,
            },
            {
                'id': '3',
                'score': 0.7,
                'authority_score': 0.1,
                'temporal_score': 0.2,
                'enrichment_count': 0,
            },
        ]
        
        reranked = service._rerank_with_graph_signals(results, [])
        
        # Check that results are reranked
        assert len(reranked) == 3
        assert all('graph_score' in r for r in reranked)
        
        # Result 2 should rank higher due to better graph signals
        assert reranked[0]['id'] == '2'
    
    @pytest.mark.asyncio
    async def test_validation(self, service):
        """Test result validation"""
        results = [
            {'id': '1', 'content': 'محتوا 1'},
            {'id': '2', 'content': 'محتوا 2'},
        ]
        
        validated = await service._validate_results(results, "تست")
        
        assert len(validated) == 2
        assert all('validation_score' in r for r in validated)
        assert all('contradictions' in r for r in validated)
    
    def test_get_statistics(self, service):
        """Test statistics retrieval"""
        stats = service.get_statistics()
        
        assert 'total_enrichments' in stats
        assert 'cache_hits' in stats
        assert 'timeouts' in stats
        assert 'errors' in stats
        assert 'cache_size' in stats
    
    def test_clear_cache(self, service):
        """Test cache clearing"""
        # Add something to cache
        service.cache.set('key', {'data': 'value'})
        
        # Clear
        service.clear_cache()
        
        # Should be empty
        assert len(service.cache._cache) == 0


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.mark.asyncio
    async def test_enrich_rag_results_function(self):
        """Test enrich_rag_results convenience function"""
        mock_connection = Mock()
        mock_connection.execute_query = Mock(return_value=[])
        
        query = "تست"
        results = [{'id': 'test', 'content': 'test'}]
        
        with patch('graph.services.rag_integration.EntityExtractor'):
            enriched = await enrich_rag_results(
                mock_connection,
                query,
                results,
                timeout_ms=1000,
            )
            
            assert isinstance(enriched, list)
    
    def test_extract_query_entities_function(self):
        """Test extract_query_entities convenience function"""
        mock_connection = Mock()
        
        with patch('graph.services.rag_integration.EntityExtractor') as MockExtractor:
            mock_extractor = Mock()
            mock_extractor.extract_and_validate = Mock(return_value=[])
            MockExtractor.return_value = mock_extractor
            
            result = extract_query_entities(mock_connection, "ماده 10")
            
            assert 'entities' in result
            assert 'entity_count' in result
            assert 'has_legal_entities' in result


class TestAdvancedFeatures:
    """Test advanced features"""
    
    @pytest.fixture
    def service(self):
        """Create service with mocks"""
        mock_connection = Mock()
        mock_connection.execute_query = Mock(return_value=[])
        
        return GraphEnrichmentService(
            connection=mock_connection,
            max_hops=3,
            enable_reranking=True,
            enable_validation=True,
        )
    
    @pytest.mark.asyncio
    async def test_legal_precedents_extraction(self, service):
        """Test legal precedent extraction"""
        result = {
            'id': 'verdict_1',
            'type': 'verdict',
        }
        
        service.connection.execute_query.return_value = [
            {
                'id': 'verdict_2',
                'number': '123',
                'date': '2023-01-01',
                'court': 'دیوان عالی',
            }
        ]
        
        precedents = await service._find_legal_precedents(result)
        
        assert len(precedents) == 1
        assert precedents[0]['id'] == 'verdict_2'
    
    @pytest.mark.asyncio
    async def test_reasoning_paths_extraction(self, service):
        """Test reasoning path extraction"""
        from unittest.mock import MagicMock
        
        result = {'id': 'article_1'}
        
        # Mock entity
        entity = MagicMock()
        entity.text = "قانون مدنی"
        query_entities = [entity]
        
        service.connection.execute_query.return_value = [
            {
                'nodes': [
                    {'id': 'article_1', 'type': 'Article'},
                    {'id': 'law_1', 'type': 'Law'},
                ],
                'relationships': ['PART_OF'],
                'path_length': 1,
            }
        ]
        
        paths = await service._extract_reasoning_paths(result, query_entities)
        
        assert len(paths) == 1
        assert paths[0]['path_length'] == 1
    
    @pytest.mark.asyncio
    async def test_embedding_similarity_search(self, service):
        """Test embedding-based similarity search"""
        result = {'id': 'article_1'}
        query_embedding = [0.1] * 1024
        
        # Mock embedding query
        service.connection.execute_query.side_effect = [
            [{'embedding': [0.1] * 1024}],  # Result embedding
            [  # Similar nodes
                {'id': 'article_2', 'content': 'محتوا', 'similarity': 0.95},
                {'id': 'article_3', 'content': 'محتوا', 'similarity': 0.85},
            ]
        ]
        
        similar = await service._find_similar_by_embedding(result, query_embedding)
        
        assert len(similar) == 2
        assert similar[0]['similarity'] > similar[1]['similarity']
    
    @pytest.mark.asyncio
    async def test_parallel_enrichment(self, service):
        """Test parallel enrichment of multiple results"""
        query = "تست"
        results = [
            {'id': f'result_{i}', 'content': f'محتوا {i}', 'score': 0.5}
            for i in range(5)
        ]
        
        with patch.object(service.entity_extractor, 'extract_and_validate') as mock_extract:
            with patch.object(service.embedding_generator, 'generate_embedding') as mock_embed:
                mock_extract.return_value = []
                mock_embed.return_value = [0.1] * 1024
                
                enriched = await service.enrich_retrieval_results(query, results)
                
                # All results should be processed
                assert len(enriched) == 5
                assert all('enriched' in r for r in enriched)


class TestErrorHandling:
    """Test error handling and fallback"""
    
    @pytest.fixture
    def service(self):
        """Create service"""
        mock_connection = Mock()
        return GraphEnrichmentService(connection=mock_connection)
    
    @pytest.mark.asyncio
    async def test_enrichment_error_fallback(self, service):
        """Test fallback on enrichment error"""
        query = "تست"
        results = [{'id': 'test', 'content': 'test'}]
        
        # Force error
        with patch.object(service, '_enrich_results_advanced', side_effect=Exception("Test error")):
            enriched = await service.enrich_retrieval_results(query, results)
            
            # Should return original results
            assert enriched == results
            assert service.stats['errors'] > 0
    
    @pytest.mark.asyncio
    async def test_multihop_context_error(self, service):
        """Test error handling in multi-hop context"""
        result = {'id': 'test'}
        
        # Force error
        service.connection.execute_query.side_effect = Exception("DB error")
        
        context = await service._get_multihop_context(result, [], 2)
        
        # Should return empty list
        assert context == []
    
    @pytest.mark.asyncio
    async def test_citation_network_error(self, service):
        """Test error handling in citation network"""
        result = {'id': 'test'}
        
        # Force error
        service.connection.execute_query.side_effect = Exception("DB error")
        
        citations = await service._analyze_citation_network(result)
        
        # Should return empty dict
        assert citations == {}


class TestPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_enrichment_within_timeout(self):
        """Test that enrichment completes within timeout"""
        import time
        
        mock_connection = Mock()
        mock_connection.execute_query = Mock(return_value=[])
        
        service = GraphEnrichmentService(
            connection=mock_connection,
            timeout_ms=500,
        )
        
        query = "تست"
        results = [{'id': 'test', 'content': 'test'}]
        
        start = time.time()
        
        with patch.object(service.entity_extractor, 'extract_and_validate') as mock_extract:
            mock_extract.return_value = []
            
            enriched = await service.enrich_retrieval_results(query, results)
        
        elapsed_ms = (time.time() - start) * 1000
        
        # Should complete within timeout + overhead
        assert elapsed_ms < 1000
    
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test cache improves performance"""
        mock_connection = Mock()
        mock_connection.execute_query = Mock(return_value=[])
        
        service = GraphEnrichmentService(
            connection=mock_connection,
            cache_enabled=True,
        )
        
        query = "تست"
        results = [{'id': 'test', 'content': 'test'}]
        
        with patch.object(service.entity_extractor, 'extract_and_validate') as mock_extract:
            mock_extract.return_value = []
            
            # First call
            import time
            start1 = time.time()
            await service.enrich_retrieval_results(query, results)
            time1 = time.time() - start1
            
            # Second call (cached)
            start2 = time.time()
            await service.enrich_retrieval_results(query, results)
            time2 = time.time() - start2
            
            # Cached call should be faster
            assert time2 < time1
            assert service.stats['cache_hits'] > 0
