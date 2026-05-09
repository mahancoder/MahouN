"""
Advanced Tests for Query Service
=================================

Tests for advanced query service features including caching, pagination, and parallel execution.
"""

import pytest
from unittest.mock import Mock, MagicMock

from graph.services.query_service import GraphQueryService, QueryCache


class TestQueryCache:
    """Test QueryCache class"""
    
    def test_cache_initialization(self):
        """Test cache initialization"""
        cache = QueryCache(max_size=100, ttl_seconds=60)
        assert cache.max_size == 100
        assert cache.ttl_seconds == 60
        assert len(cache._cache) == 0
    
    def test_cache_get_set(self):
        """Test cache get/set"""
        cache = QueryCache()
        
        query = "MATCH (n) RETURN n"
        params = {"limit": 10}
        result = [{"id": "1"}, {"id": "2"}]
        
        # Set
        cache.set(query, params, result)
        
        # Get
        cached = cache.get(query, params)
        assert cached == result
    
    def test_cache_miss(self):
        """Test cache miss"""
        cache = QueryCache()
        
        cached = cache.get("MATCH (n) RETURN n", {})
        assert cached is None
    
    def test_cache_ttl_expiration(self):
        """Test TTL expiration"""
        cache = QueryCache(ttl_seconds=1)
        
        query = "MATCH (n) RETURN n"
        params = {}
        result = [{"id": "1"}]
        
        cache.set(query, params, result)
        
        # Should be cached
        assert cache.get(query, params) == result
        
        # Wait for expiration
        import time
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get(query, params) is None
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction"""
        cache = QueryCache(max_size=2)
        
        # Add 3 items
        cache.set("query1", {}, [{"id": "1"}])
        cache.set("query2", {}, [{"id": "2"}])
        cache.set("query3", {}, [{"id": "3"}])
        
        # First should be evicted
        assert cache.get("query1", {}) is None
        assert cache.get("query2", {}) is not None
        assert cache.get("query3", {}) is not None
    
    def test_cache_stats(self):
        """Test cache statistics"""
        cache = QueryCache()
        
        query = "MATCH (n) RETURN n"
        params = {}
        
        # Miss
        cache.get(query, params)
        
        # Set and hit
        cache.set(query, params, [])
        cache.get(query, params)
        
        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['size'] == 1
        assert stats['hit_rate'] == 0.5


class TestAdvancedQueryService:
    """Test advanced query service features"""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock connection"""
        connection = Mock()
        connection.execute_query = MagicMock(return_value=[])
        return connection
    
    @pytest.fixture
    def service(self, mock_connection):
        """Create service instance"""
        return GraphQueryService(mock_connection, enable_cache=True)
    
    def test_service_initialization(self, service):
        """Test service initialization"""
        assert service.cache is not None
        assert service.max_workers == 4
    
    def test_cached_query_execution(self, service, mock_connection):
        """Test cached query execution"""
        query = "MATCH (n) RETURN n"
        params = {"limit": 10}
        result = [{"id": "1"}]
        
        mock_connection.execute_query.return_value = result
        
        # First call - cache miss
        result1 = service._execute_cached_query(query, params)
        assert result1 == result
        assert mock_connection.execute_query.call_count == 1
        
        # Second call - cache hit
        result2 = service._execute_cached_query(query, params)
        assert result2 == result
        assert mock_connection.execute_query.call_count == 1  # Not called again
    
    def test_find_related_articles_with_pagination(self, service, mock_connection):
        """Test find_related_articles with pagination"""
        mock_connection.execute_query.side_effect = [
            [{"total": 100}],  # Count query
            [{"id": f"article_{i}"} for i in range(10)],  # Results
        ]
        
        result = service.find_related_articles(
            "article_1",
            limit=10,
            skip=20,
        )
        
        assert result['total'] == 100
        assert result['limit'] == 10
        assert result['skip'] == 20
        assert result['has_more'] is True
        assert len(result['results']) == 10
    
    def test_advanced_filter(self, service, mock_connection):
        """Test advanced filtering"""
        mock_connection.execute_query.side_effect = [
            [{"total": 50}],  # Count
            [{"n": {"id": f"node_{i}"}} for i in range(10)],  # Results
        ]
        
        filters = {
            "category": "civil",
            "year": {"min": 2020, "max": 2023},
            "status": ["active", "pending"],
        }
        
        result = service.advanced_filter(
            "Law",
            filters,
            limit=10,
            order_by="year",
        )
        
        assert result['total'] == 50
        assert len(result['results']) == 10
    
    def test_aggregate_query(self, service, mock_connection):
        """Test aggregate query"""
        mock_connection.execute_query.return_value = [
            {"group_key": "civil", "count": 100, "avg_year": 2020},
            {"group_key": "criminal", "count": 150, "avg_year": 2019},
        ]
        
        result = service.aggregate_query(
            "Law",
            group_by="category",
            aggregations={
                "count": "count(n)",
                "avg_year": "avg(n.year)",
            },
        )
        
        assert len(result) == 2
        assert result[0]['group_key'] == "civil"
    
    def test_temporal_query(self, service, mock_connection):
        """Test temporal query"""
        mock_connection.execute_query.return_value = [
            {"n": {"id": "verdict_1", "verdict_date": "2023-01-15"}},
            {"n": {"id": "verdict_2", "verdict_date": "2023-02-20"}},
        ]
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        result = service.temporal_query(
            "Verdict",
            "verdict_date",
            start_date,
            end_date,
        )
        
        assert len(result) == 2
    
    def test_get_cache_stats(self, service):
        """Test getting cache stats"""
        stats = service.get_cache_stats()
        assert stats is not None
        assert 'hits' in stats
        assert 'misses' in stats
    
    def test_clear_cache(self, service):
        """Test clearing cache"""
        # Add something to cache
        service.cache.set("query", {}, [])
        assert service.cache.get_stats()['size'] == 1
        
        # Clear
        service.clear_cache()
        assert service.cache.get_stats()['size'] == 0


class TestParallelExecution:
    """Test parallel query execution"""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock connection"""
        connection = Mock()
        connection.execute_query = MagicMock(return_value=[{"id": "1"}])
        return connection
    
    @pytest.fixture
    def service(self, mock_connection):
        """Create service instance"""
        return GraphQueryService(mock_connection, enable_cache=False)
    
    def test_parallel_search(self, service, mock_connection):
        """Test parallel search execution"""
        queries = [
            ("q1", "قانون مدنی"),
            ("q2", "قانون مجازات"),
            ("q3", "قانون تجارت"),
        ]
        
        mock_connection.execute_query.return_value = [{"id": "result"}]
        
        results = service.parallel_search(queries, limit=10)
        
        assert len(results) == 3
        assert "q1" in results
        assert "q2" in results
        assert "q3" in results


class TestSubgraphExtraction:
    """Test subgraph extraction"""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock connection"""
        connection = Mock()
        return connection
    
    @pytest.fixture
    def service(self, mock_connection):
        """Create service instance"""
        return GraphQueryService(mock_connection, enable_cache=False)
    
    def test_get_subgraph(self, service, mock_connection):
        """Test subgraph extraction"""
        mock_connection.execute_query.return_value = [{
            'nodes': [
                {'id': 'node1', 'labels': ['Article']},
                {'id': 'node2', 'labels': ['Article']},
            ],
            'relationships': [
                {'source': 'node1', 'target': 'node2', 'type': 'CITES'},
            ],
        }]
        
        result = service.get_subgraph("node1", radius=2)
        
        assert 'nodes' in result
        assert 'relationships' in result
        assert len(result['nodes']) == 2


class TestEdgeCases:
    """Test edge cases"""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock connection"""
        connection = Mock()
        connection.execute_query = MagicMock(return_value=[])
        return connection
    
    @pytest.fixture
    def service(self, mock_connection):
        """Create service instance"""
        return GraphQueryService(mock_connection)
    
    def test_empty_results(self, service, mock_connection):
        """Test handling empty results"""
        mock_connection.execute_query.return_value = []
        
        result = service.find_related_articles("nonexistent")
        assert result['results'] == []
        assert result['total'] == 0
    
    def test_service_without_cache(self, mock_connection):
        """Test service without cache"""
        service = GraphQueryService(mock_connection, enable_cache=False)
        assert service.cache is None
        assert service.get_cache_stats() is None
