"""
Tests for Data Quality Validation
==================================

Tests for graph data quality validation functionality.
"""

import pytest
from datetime import datetime
from graph.validation.data_quality import (
    DataQualityValidator,
    validate_graph_quality,
    print_quality_report
)


@pytest.fixture
def mock_connection():
    """Mock Neo4j connection"""
    connection = Mock()
    connection.execute_query = Mock()
    return connection


@pytest.fixture
def validator(mock_connection):
    """Create validator instance"""
    return DataQualityValidator(mock_connection)


class TestOrphanNodes:
    """Tests for orphan node detection"""
    
    def test_check_orphan_nodes_found(self, validator, mock_connection):
        """Test detection of orphan nodes"""
        # Mock response with orphan nodes
        mock_connection.execute_query.return_value = [
            {
                'label': 'Article',
                'count': 5,
                'sample_ids': ['art1', 'art2', 'art3']
            },
            {
                'label': 'Person',
                'count': 3,
                'sample_ids': ['p1', 'p2']
            }
        ]
        
        result = validator.check_orphan_nodes()
        
        assert result['total_orphans'] == 8
        assert result['has_orphans'] is True
        assert 'Article' in result['orphans_by_type']
        assert result['orphans_by_type']['Article']['count'] == 5
        assert len(validator.issues) == 2
    
    def test_check_orphan_nodes_none_found(self, validator, mock_connection):
        """Test when no orphan nodes exist"""
        mock_connection.execute_query.return_value = []
        
        result = validator.check_orphan_nodes()
        
        assert result['total_orphans'] == 0
        assert result['has_orphans'] is False
        assert len(validator.issues) == 0
    
    def test_check_orphan_nodes_error(self, validator, mock_connection):
        """Test error handling"""
        mock_connection.execute_query.side_effect = Exception("Connection error")
        
        result = validator.check_orphan_nodes()
        
        assert 'error' in result


class TestDuplicateNodes:
    """Tests for duplicate node detection"""
    
    def test_check_duplicate_nodes_found(self, validator, mock_connection):
        """Test detection of duplicate nodes"""
        mock_connection.execute_query.return_value = [
            {
                'label': 'Article',
                'id': 'art_123',
                'count': 3
            },
            {
                'label': 'Law',
                'id': 'law_456',
                'count': 2
            }
        ]
        
        result = validator.check_duplicate_nodes()
        
        assert result['has_duplicates'] is True
        assert len(result['duplicate_ids']) == 2
        assert len(validator.issues) == 2
        assert validator.issues[0]['severity'] == 'error'
    
    def test_check_duplicate_nodes_none_found(self, validator, mock_connection):
        """Test when no duplicates exist"""
        mock_connection.execute_query.return_value = []
        
        result = validator.check_duplicate_nodes()
        
        assert result['has_duplicates'] is False
        assert len(result['duplicate_ids']) == 0


class TestRequiredProperties:
    """Tests for required property validation"""
    
    def test_check_required_properties_missing(self, validator, mock_connection):
        """Test detection of missing required properties"""
        # Mock responses for different property checks
        mock_connection.execute_query.side_effect = [
            [{'count': 5}],  # Article.id missing
            [{'count': 0}],  # Article.content ok
            [{'count': 2}],  # Article.number missing
            [{'count': 0}],  # Law.id ok
            [{'count': 1}],  # Law.name missing
            [{'count': 0}],  # Verdict.id ok
            [{'count': 0}],  # Verdict.content ok
            [{'count': 0}],  # Person.id ok
            [{'count': 0}],  # Person.name ok
            [{'count': 0}],  # Organization.id ok
            [{'count': 0}],  # Organization.name ok
        ]
        
        result = validator.check_required_properties()
        
        assert result['has_missing'] is True
        assert result['total_missing'] == 8  # 5 + 2 + 1
        assert 'Article' in result['missing_by_type']
        assert result['missing_by_type']['Article']['id'] == 5
    
    def test_check_required_properties_all_present(self, validator, mock_connection):
        """Test when all required properties are present"""
        mock_connection.execute_query.return_value = [{'count': 0}]
        
        result = validator.check_required_properties()
        
        assert result['has_missing'] is False
        assert result['total_missing'] == 0


class TestBrokenRelationships:
    """Tests for broken relationship detection"""
    
    def test_check_broken_relationships_found(self, validator, mock_connection):
        """Test detection of incomplete relationships"""
        mock_connection.execute_query.return_value = [
            {
                'rel_type': 'CITES',
                'count': 10
            },
            {
                'rel_type': 'REFERENCES',
                'count': 5
            }
        ]
        
        result = validator.check_broken_relationships()
        
        assert result['has_broken'] is True
        assert result['total_broken'] == 15
        assert len(result['broken_relationships']) == 2
    
    def test_check_broken_relationships_none_found(self, validator, mock_connection):
        """Test when all relationships are complete"""
        mock_connection.execute_query.return_value = []
        
        result = validator.check_broken_relationships()
        
        assert result['has_broken'] is False
        assert result['total_broken'] == 0


class TestDataConsistency:
    """Tests for data consistency checks"""
    
    def test_check_data_consistency_issues_found(self, validator, mock_connection):
        """Test detection of consistency issues"""
        mock_connection.execute_query.side_effect = [
            [{'count': 10}],  # Articles without law
            [{'count': 5}],   # Verdicts without citations
        ]
        
        result = validator.check_data_consistency()
        
        assert result['has_issues'] is True
        assert len(result['consistency_issues']) >= 1
    
    def test_check_data_consistency_no_issues(self, validator, mock_connection):
        """Test when data is consistent"""
        mock_connection.execute_query.return_value = [{'count': 0}]
        
        result = validator.check_data_consistency()
        
        # May have no issues or empty list
        assert 'consistency_issues' in result


class TestValidateAll:
    """Tests for comprehensive validation"""
    
    def test_validate_all_excellent_quality(self, validator, mock_connection):
        """Test validation with excellent quality"""
        # Mock all checks returning no issues
        mock_connection.execute_query.return_value = []
        
        report = validator.validate_all()
        
        assert 'quality_score' in report
        assert report['quality_score'] >= 90
        assert report['quality_level'] == 'excellent'
        assert 'timestamp' in report
        assert 'duration_seconds' in report
    
    def test_validate_all_with_issues(self, validator, mock_connection):
        """Test validation with various issues"""
        # Mock responses with issues
        def mock_query(*args, **kwargs):
            query = args[0] if args else kwargs.get('query', '')
            
            # Orphan nodes query
            if 'NOT (n)--()' in query:
                return [{'label': 'Article', 'count': 5, 'sample_ids': ['a1']}]
            # Duplicate IDs query
            elif 'count > 1' in query:
                return [{'label': 'Law', 'id': 'law1', 'count': 2}]
            # Default
            else:
                return [{'count': 0}]
        
        mock_connection.execute_query.side_effect = mock_query
        
        report = validator.validate_all()
        
        assert report['total_issues'] > 0
        assert report['quality_score'] < 100
        assert 'checks' in report
        assert 'issues' in report
    
    def test_validate_all_quality_levels(self, validator, mock_connection):
        """Test different quality levels"""
        # Test poor quality (many errors)
        validator.issues = [
            {'severity': 'error', 'type': 'test'} for _ in range(25)
        ]
        mock_connection.execute_query.return_value = []
        
        report = validator.validate_all()
        
        # With 25 errors (25*5=125 points deducted), score should be 0
        assert report['quality_score'] == 0
        assert report['quality_level'] == 'poor'


class TestGenerateReport:
    """Tests for report generation"""
    
    def test_generate_report_format(self, validator, mock_connection):
        """Test report generation format"""
        mock_connection.execute_query.return_value = []
        
        report_text = validator.generate_report()
        
        assert 'DATA QUALITY VALIDATION REPORT' in report_text
        assert 'Quality Score:' in report_text
        assert 'Total Issues:' in report_text
        assert 'DETAILED CHECKS' in report_text
    
    def test_generate_report_to_file(self, validator, mock_connection, tmp_path):
        """Test saving report to file"""
        mock_connection.execute_query.return_value = []
        
        output_file = tmp_path / "quality_report.txt"
        report_text = validator.generate_report(str(output_file))
        
        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        assert 'DATA QUALITY VALIDATION REPORT' in content


class TestConvenienceFunctions:
    """Tests for convenience functions"""
    
    def test_validate_graph_quality(self, mock_connection):
        """Test quick validation function"""
        mock_connection.execute_query.return_value = []
        
        report = validate_graph_quality(mock_connection)
        
        assert 'quality_score' in report
        assert 'checks' in report
    
    def test_validate_graph_quality_with_file(self, mock_connection, tmp_path):
        """Test validation with file output"""
        mock_connection.execute_query.return_value = []
        
        output_file = tmp_path / "report.txt"
        report = validate_graph_quality(mock_connection, str(output_file))
        
        assert output_file.exists()
        assert 'quality_score' in report
    
    def test_print_quality_report(self, mock_connection, capsys):
        """Test printing report to console"""
        mock_connection.execute_query.return_value = []
        
        print_quality_report(mock_connection)
        
        captured = capsys.readouterr()
        assert 'DATA QUALITY VALIDATION REPORT' in captured.out


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_validator_with_none_connection(self):
        """Test validator with None connection"""
        validator = DataQualityValidator(None)
        
        # Should handle gracefully
        assert validator.connection is None
    
    def test_multiple_validations(self, validator, mock_connection):
        """Test running validation multiple times"""
        mock_connection.execute_query.return_value = []
        
        report1 = validator.validate_all()
        report2 = validator.validate_all()
        
        # Issues should be reset between runs
        assert report1['total_issues'] == report2['total_issues']
    
    def test_large_number_of_issues(self, validator, mock_connection):
        """Test handling large number of issues"""
        # Mock many duplicates
        duplicates = [
            {'label': f'Type{i}', 'id': f'id{i}', 'count': 2}
            for i in range(100)
        ]
        mock_connection.execute_query.return_value = duplicates
        
        result = validator.check_duplicate_nodes()
        
        assert len(result['duplicate_ids']) == 100
        assert len(validator.issues) == 100
