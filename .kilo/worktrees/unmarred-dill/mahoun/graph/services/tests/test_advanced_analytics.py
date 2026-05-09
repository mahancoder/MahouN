"""
Advanced Tests for Analytics Service
====================================

Tests for advanced analytics features including multiple centrality measures,
temporal analysis, and influence propagation.
"""

import pytest
from unittest.mock import Mock, MagicMock

from graph.services.analytics_service import GraphAnalytics


class TestAdvancedAnalytics:
    """Test advanced analytics features"""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock connection"""
        connection = Mock()
        connection.execute_query = MagicMock(return_value=[])
        return connection
    
    @pytest.fixture
    def analytics(self, mock_connection):
        """Create analytics instance"""
        return GraphAnalytics(mock_connection, use_gds=False)
    
    def test_analytics_initialization(self, analytics):
        """Test analytics initialization"""
        assert analytics.use_gds is False
        assert analytics._gds_available is None
    
    def test_eigenvector_centrality(self, analytics, mock_connection):
        """Test eigenvector centrality calculation"""
        mock_connection.execute_query.return_value = [
            {"id": "article_1", "number": "10", "name": "ماده 10", "score": 0.95},
            {"id": "article_2", "number": "20", "name": "ماده 20", "score": 0.85},
        ]
        
        results = analytics.calculate_eigenvector_centrality("Article")
        
        assert len(results) == 2
        assert results[0]['score'] == 0.95
    
    def test_label_propagation_communities(self, analytics, mock_connection):
        """Test label propagation community detection"""
        mock_connection.execute_query.return_value = [
            {"id": "article_1", "number": "10", "name": "ماده 10", "communityId": 1},
            {"id": "article_2", "number": "20", "name": "ماده 20", "communityId": 1},
            {"id": "article_3", "number": "30", "name": "ماده 30", "communityId": 2},
        ]
        
        results = analytics.detect_communities_label_propagation("Article")
        
        assert len(results) == 3
        # Check that we have at least 2 communities
        communities = set(r['communityId'] for r in results)
        assert len(communities) >= 2
    
    def test_find_triangles(self, analytics, mock_connection):
        """Test triangle detection"""
        mock_connection.execute_query.return_value = [
            {"node1": "a1", "node2": "a2", "node3": "a3"},
            {"node1": "a1", "node2": "a3", "node3": "a4"},
        ]
        
        results = analytics.find_triangles("Article", limit=10)
        
        assert len(results) == 2
        assert "node1" in results[0]
        assert "node2" in results[0]
        assert "node3" in results[0]
    
    def test_h_index_calculation(self, analytics, mock_connection):
        """Test h-index calculation"""
        mock_connection.execute_query.return_value = [
            {"id": "article_1", "number": "10", "name": "ماده 10", "h_index": 15},
            {"id": "article_2", "number": "20", "name": "ماده 20", "h_index": 12},
        ]
        
        results = analytics.calculate_h_index("Article")
        
        assert len(results) == 2
        assert results[0]['h_index'] == 15
    
    def test_temporal_citation_analysis(self, analytics, mock_connection):
        """Test temporal citation analysis"""
        mock_connection.execute_query.return_value = [
            {
                "interval": 0,
                "citation_count": 100,
                "verdict_count": 50,
                "article_count": 30,
                "avg_citations_per_verdict": 2.0,
            },
            {
                "interval": 1,
                "citation_count": 150,
                "verdict_count": 60,
                "article_count": 35,
                "avg_citations_per_verdict": 2.5,
            },
        ]
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        results = analytics.temporal_citation_analysis(
            start_date, end_date, interval_days=30
        )
        
        assert len(results) == 2
        assert results[0]['citation_count'] == 100
        assert results[1]['citation_count'] == 150
    
    def test_influence_propagation(self, analytics, mock_connection):
        """Test influence propagation"""
        mock_connection.execute_query.return_value = [
            {"id": "node1", "label": "Article", "name": "ماده 1", "influence_score": 1.0},
            {"id": "node2", "label": "Article", "name": "ماده 2", "influence_score": 0.5},
            {"id": "node3", "label": "Article", "name": "ماده 3", "influence_score": 0.25},
        ]
        
        results = analytics.influence_propagation(
            ["source1", "source2"],
            max_hops=3,
            decay_factor=0.5,
        )
        
        assert len(results) == 3
        # Check that influence decreases
        assert results[0]['influence_score'] >= results[1]['influence_score']
        assert results[1]['influence_score'] >= results[2]['influence_score']
    
    def test_network_resilience_analysis(self, analytics, mock_connection):
        """Test network resilience analysis"""
        mock_connection.execute_query.side_effect = [
            # Initial connectivity
            [{"total_nodes": 100, "connected_pairs": 500, "connectivity": 0.1}],
            # High degree nodes
            [{"node_ids": ["node1", "node2", "node3"]}],
            # After removal
            [{"remaining_nodes": 97, "connected_pairs": 300, "connectivity": 0.06}],
        ]
        
        results = analytics.network_resilience_analysis("Article", sample_size=3)
        
        assert 'initial_connectivity' in results
        assert 'after_removal_connectivity' in results
        assert 'resilience_score' in results
        assert results['critical_nodes_tested'] == 3
    
    def test_find_bridge_nodes(self, analytics, mock_connection):
        """Test finding bridge nodes"""
        mock_connection.execute_query.return_value = [
            {
                "id": "article_1",
                "number": "10",
                "name": "ماده 10",
                "degree": 5,
                "reachable": 20,
                "bridge_score": 4.0,
            },
            {
                "id": "article_2",
                "number": "20",
                "name": "ماده 20",
                "degree": 3,
                "reachable": 10,
                "bridge_score": 3.3,
            },
        ]
        
        results = analytics.find_bridge_nodes("Article", limit=10)
        
        assert len(results) == 2
        assert results[0]['bridge_score'] >= results[1]['bridge_score']
    
    def test_calculate_all_centralities(self, analytics, mock_connection):
        """Test calculating all centrality measures"""
        # Mock multiple calls for different centrality measures
        mock_connection.execute_query.side_effect = [
            # Degree centrality
            [
                {"id": "a1", "number": "10", "name": "ماده 10", "centrality": 10},
                {"id": "a2", "number": "20", "name": "ماده 20", "centrality": 8},
            ],
            # PageRank (multiple calls for GDS)
            [],  # Drop projection
            [],  # Create projection
            [
                {"id": "a1", "number": "10", "name": "ماده 10", "score": 0.5},
                {"id": "a2", "number": "20", "name": "ماده 20", "score": 0.3},
            ],
        ]
        
        results = analytics.calculate_all_centralities("Article", limit=10)
        
        assert len(results) > 0
        # Check that combined centrality is calculated
        if results:
            assert 'combined_centrality' in results[0]


class TestGDSIntegration:
    """Test GDS integration"""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock connection"""
        connection = Mock()
        connection.execute_query = MagicMock(return_value=[])
        return connection
    
    @pytest.fixture
    def analytics_with_gds(self, mock_connection):
        """Create analytics with GDS enabled"""
        return GraphAnalytics(mock_connection, use_gds=True)
    
    def test_check_gds_available(self, analytics_with_gds, mock_connection):
        """Test checking GDS availability"""
        mock_connection.execute_query.return_value = [{"version": "2.5.0"}]
        
        available = analytics_with_gds._check_gds_available()
        
        assert available is True
        assert analytics_with_gds._gds_available is True
    
    def test_check_gds_not_available(self, analytics_with_gds, mock_connection):
        """Test GDS not available"""
        mock_connection.execute_query.side_effect = Exception("GDS not found")
        
        available = analytics_with_gds._check_gds_available()
        
        assert available is False
        assert analytics_with_gds._gds_available is False


class TestEdgeCases:
    """Test edge cases"""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock connection"""
        connection = Mock()
        connection.execute_query = MagicMock(return_value=[])
        return connection
    
    @pytest.fixture
    def analytics(self, mock_connection):
        """Create analytics instance"""
        return GraphAnalytics(mock_connection)
    
    def test_empty_graph(self, analytics, mock_connection):
        """Test analytics on empty graph"""
        mock_connection.execute_query.return_value = []
        
        results = analytics.find_triangles("Article")
        assert results == []
    
    def test_single_node_graph(self, analytics, mock_connection):
        """Test analytics on single node"""
        mock_connection.execute_query.return_value = [
            {"id": "node1", "score": 1.0}
        ]
        
        results = analytics.calculate_eigenvector_centrality("Article")
        assert len(results) == 1
    
    def test_disconnected_graph(self, analytics, mock_connection):
        """Test analytics on disconnected graph"""
        mock_connection.execute_query.return_value = [
            {"total_nodes": 100, "connected_pairs": 0, "connectivity": 0.0}
        ]
        
        stats = analytics.get_graph_statistics()
        # Should handle disconnected graph gracefully
        assert stats is not None
