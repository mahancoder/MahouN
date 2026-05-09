"""
Data Quality Validation for Knowledge Graph
===========================================

Comprehensive data quality checks and validation.
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class DataQualityValidator:
    """
    Data quality validator for knowledge graph
    
    Checks:
    - Orphan nodes (nodes with no relationships)
    - Duplicate nodes (same ID or content)
    - Missing required properties
    - Invalid property values
    - Broken relationships
    - Data consistency
    """
    
    def __init__(self, connection):
        """
        Initialize validator
        
        Args:
            connection: Neo4j connection
        """
        self.connection = connection
        self.issues = []
    
    def check_orphan_nodes(self) -> Dict:
        """
        Find orphan nodes (nodes with no relationships)
        
        Returns:
            Dictionary with orphan node information
        """
        logger.info("Checking for orphan nodes...")
        
        try:
            query = """
            MATCH (n)
            WHERE NOT (n)--()
            WITH labels(n)[0] as label, count(n) as count, collect(n.id)[..10] as sample_ids
            RETURN label, count, sample_ids
            ORDER BY count DESC
            """
            
            results = self.connection.execute_query(query)
            
            orphans_by_type = {}
            total_orphans = 0
            
            for row in results:
                label = row['label']
                count = row['count']
                sample_ids = row['sample_ids']
                
                orphans_by_type[label] = {
                    'count': count,
                    'sample_ids': sample_ids
                }
                
                total_orphans += count
                
                if count > 0:
                    self.issues.append({
                        'type': 'orphan_nodes',
                        'severity': 'warning',
                        'label': label,
                        'count': count,
                        'message': f"Found {count} orphan {label} nodes"
                    })
            
            logger.info(f"Found {total_orphans} orphan nodes across {len(orphans_by_type)} types")
            
            return {
                'total_orphans': total_orphans,
                'orphans_by_type': orphans_by_type,
                'has_orphans': total_orphans > 0
            }
        
        except Exception as e:
            logger.error(f"Failed to check orphan nodes: {e}")
            return {'error': str(e)}
    
    def check_duplicate_nodes(self) -> Dict:
        """
        Find duplicate nodes (same ID or similar content)
        
        Returns:
            Dictionary with duplicate information
        """
        logger.info("Checking for duplicate nodes...")
        
        try:
            # Check for duplicate IDs
            id_query = """
            MATCH (n)
            WHERE n.id IS NOT NULL
            WITH n.id as id, labels(n)[0] as label, count(n) as count
            WHERE count > 1
            RETURN label, id, count
            ORDER BY count DESC
            LIMIT 100
            """
            
            id_results = self.connection.execute_query(id_query)
            
            duplicate_ids = []
            for row in id_results:
                duplicate_ids.append({
                    'label': row['label'],
                    'id': row['id'],
                    'count': row['count']
                })
                
                self.issues.append({
                    'type': 'duplicate_id',
                    'severity': 'error',
                    'label': row['label'],
                    'id': row['id'],
                    'count': row['count'],
                    'message': f"Duplicate ID found: {row['id']} ({row['count']} times)"
                })
            
            logger.info(f"Found {len(duplicate_ids)} duplicate IDs")
            
            return {
                'duplicate_ids': duplicate_ids,
                'has_duplicates': len(duplicate_ids) > 0
            }
        
        except Exception as e:
            logger.error(f"Failed to check duplicate nodes: {e}")
            return {'error': str(e)}
    
    def check_required_properties(self) -> Dict:
        """
        Check for missing required properties
        
        Returns:
            Dictionary with missing property information
        """
        logger.info("Checking required properties...")
        
        try:
            # Define required properties per node type
            required_props = {
                'Article': ['id', 'content', 'number'],
                'Law': ['id', 'name'],
                'Verdict': ['id', 'content'],
                'Person': ['id', 'name'],
                'Organization': ['id', 'name'],
            }
            
            missing_by_type = {}
            
            for label, props in required_props.items():
                for prop in props:
                    query = f"""
                    MATCH (n:{label})
                    WHERE n.{prop} IS NULL OR n.{prop} = ''
                    RETURN count(n) as count
                    """
                    
                    try:
                        result = self.connection.execute_query(query)
                        count = result[0]['count'] if result else 0
                        
                        if count > 0:
                            if label not in missing_by_type:
                                missing_by_type[label] = {}
                            
                            missing_by_type[label][prop] = count
                            
                            self.issues.append({
                                'type': 'missing_property',
                                'severity': 'warning',
                                'label': label,
                                'property': prop,
                                'count': count,
                                'message': f"{count} {label} nodes missing {prop}"
                            })
                    
                    except Exception as e:
                        # Label might not exist
                        logger.debug(f"Could not check {label}.{prop}: {e}")
            
            total_missing = sum(
                sum(props.values()) for props in missing_by_type.values()
            )
            
            logger.info(f"Found {total_missing} nodes with missing required properties")
            
            return {
                'missing_by_type': missing_by_type,
                'total_missing': total_missing,
                'has_missing': total_missing > 0
            }
        
        except Exception as e:
            logger.error(f"Failed to check required properties: {e}")
            return {'error': str(e)}
    
    def check_broken_relationships(self) -> Dict:
        """
        Check for broken relationships (pointing to non-existent nodes)
        
        Returns:
            Dictionary with broken relationship information
        """
        logger.info("Checking for broken relationships...")
        
        try:
            # This is harder to check in Neo4j as it maintains referential integrity
            # But we can check for relationships with missing properties
            query = """
            MATCH ()-[r]->()
            WHERE r.strength IS NULL OR r.confidence IS NULL
            WITH type(r) as rel_type, count(r) as count
            RETURN rel_type, count
            ORDER BY count DESC
            """
            
            results = self.connection.execute_query(query)
            
            broken_rels = []
            total_broken = 0
            
            for row in results:
                rel_type = row['rel_type']
                count = row['count']
                
                broken_rels.append({
                    'type': rel_type,
                    'count': count
                })
                
                total_broken += count
                
                self.issues.append({
                    'type': 'incomplete_relationship',
                    'severity': 'warning',
                    'rel_type': rel_type,
                    'count': count,
                    'message': f"{count} {rel_type} relationships missing properties"
                })
            
            logger.info(f"Found {total_broken} relationships with missing properties")
            
            return {
                'broken_relationships': broken_rels,
                'total_broken': total_broken,
                'has_broken': total_broken > 0
            }
        
        except Exception as e:
            logger.error(f"Failed to check broken relationships: {e}")
            return {'error': str(e)}
    
    def check_data_consistency(self) -> Dict:
        """
        Check data consistency
        
        Returns:
            Dictionary with consistency information
        """
        logger.info("Checking data consistency...")
        
        try:
            consistency_issues = []
            
            # Check 1: Articles should belong to a Law
            query1 = """
            MATCH (a:Article)
            WHERE NOT (a)-[:PART_OF]->(:Law)
            RETURN count(a) as count
            """
            
            try:
                result = self.connection.execute_query(query1)
                count = result[0]['count'] if result else 0
                
                if count > 0:
                    consistency_issues.append({
                        'check': 'articles_without_law',
                        'count': count,
                        'message': f"{count} articles not linked to any law"
                    })
                    
                    self.issues.append({
                        'type': 'consistency',
                        'severity': 'error',
                        'check': 'articles_without_law',
                        'count': count,
                        'message': f"{count} articles not linked to any law"
                    })
            except:
                pass
            
            # Check 2: Verdicts should cite something
            query2 = """
            MATCH (v:Verdict)
            WHERE NOT (v)-[:CITES]->()
            RETURN count(v) as count
            """
            
            try:
                result = self.connection.execute_query(query2)
                count = result[0]['count'] if result else 0
                
                if count > 0:
                    consistency_issues.append({
                        'check': 'verdicts_without_citations',
                        'count': count,
                        'message': f"{count} verdicts with no citations"
                    })
            except:
                pass
            
            logger.info(f"Found {len(consistency_issues)} consistency issues")
            
            return {
                'consistency_issues': consistency_issues,
                'has_issues': len(consistency_issues) > 0
            }
        
        except Exception as e:
            logger.error(f"Failed to check data consistency: {e}")
            return {'error': str(e)}
    
    def validate_all(self) -> Dict:
        """
        Run all validation checks
        
        Returns:
            Complete validation report
        """
        logger.info("Starting comprehensive data quality validation...")
        
        self.issues = []  # Reset issues
        
        start_time = datetime.now()
        
        # Run all checks
        checks = {
            'orphan_nodes': self.check_orphan_nodes(),
            'duplicate_nodes': self.check_duplicate_nodes(),
            'required_properties': self.check_required_properties(),
            'broken_relationships': self.check_broken_relationships(),
            'data_consistency': self.check_data_consistency(),
        }
        
        # Calculate summary
        total_issues = len(self.issues)
        issues_by_severity = defaultdict(int)
        issues_by_type = defaultdict(int)
        
        for issue in self.issues:
            issues_by_severity[issue['severity']] += 1
            issues_by_type[issue['type']] += 1
        
        # Determine overall quality score (0-100)
        # Deduct points for each issue type
        quality_score = 100
        quality_score -= issues_by_severity.get('error', 0) * 5
        quality_score -= issues_by_severity.get('warning', 0) * 1
        quality_score = max(0, quality_score)
        
        # Determine quality level
        if quality_score >= 90:
            quality_level = 'excellent'
        elif quality_score >= 75:
            quality_level = 'good'
        elif quality_score >= 50:
            quality_level = 'fair'
        else:
            quality_level = 'poor'
        
        duration = (datetime.now() - start_time).total_seconds()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration,
            'quality_score': quality_score,
            'quality_level': quality_level,
            'total_issues': total_issues,
            'issues_by_severity': dict(issues_by_severity),
            'issues_by_type': dict(issues_by_type),
            'checks': checks,
            'issues': self.issues,
        }
        
        logger.info(
            f"Validation complete: {quality_level} quality "
            f"(score={quality_score}, issues={total_issues})"
        )
        
        return report
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate human-readable validation report
        
        Args:
            output_file: Optional file path to save report
        
        Returns:
            Report as string
        """
        report = self.validate_all()
        
        lines = []
        lines.append("=" * 80)
        lines.append("DATA QUALITY VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Timestamp: {report['timestamp']}")
        lines.append(f"Duration: {report['duration_seconds']:.2f}s")
        lines.append("")
        lines.append(f"Quality Score: {report['quality_score']}/100 ({report['quality_level'].upper()})")
        lines.append(f"Total Issues: {report['total_issues']}")
        lines.append("")
        
        # Issues by severity
        lines.append("Issues by Severity:")
        for severity, count in report['issues_by_severity'].items():
            lines.append(f"  - {severity.upper()}: {count}")
        lines.append("")
        
        # Issues by type
        lines.append("Issues by Type:")
        for issue_type, count in report['issues_by_type'].items():
            lines.append(f"  - {issue_type}: {count}")
        lines.append("")
        
        # Detailed checks
        lines.append("=" * 80)
        lines.append("DETAILED CHECKS")
        lines.append("=" * 80)
        
        # Orphan nodes
        orphans = report['checks']['orphan_nodes']
        if not orphans.get('error'):
            lines.append(f"\n1. Orphan Nodes: {orphans['total_orphans']} found")
            for label, info in orphans.get('orphans_by_type', {}).items():
                lines.append(f"   - {label}: {info['count']}")
        
        # Duplicates
        duplicates = report['checks']['duplicate_nodes']
        if not duplicates.get('error'):
            dup_count = len(duplicates.get('duplicate_ids', []))
            lines.append(f"\n2. Duplicate Nodes: {dup_count} found")
            for dup in duplicates.get('duplicate_ids', [])[:5]:
                lines.append(f"   - {dup['label']} ID={dup['id']} ({dup['count']} times)")
        
        # Missing properties
        missing = report['checks']['required_properties']
        if not missing.get('error'):
            lines.append(f"\n3. Missing Properties: {missing['total_missing']} found")
            for label, props in missing.get('missing_by_type', {}).items():
                for prop, count in props.items():
                    lines.append(f"   - {label}.{prop}: {count} missing")
        
        # Broken relationships
        broken = report['checks']['broken_relationships']
        if not broken.get('error'):
            lines.append(f"\n4. Incomplete Relationships: {broken['total_broken']} found")
            for rel in broken.get('broken_relationships', [])[:5]:
                lines.append(f"   - {rel['type']}: {rel['count']}")
        
        # Consistency
        consistency = report['checks']['data_consistency']
        if not consistency.get('error'):
            issues = consistency.get('consistency_issues', [])
            lines.append(f"\n5. Consistency Issues: {len(issues)} found")
            for issue in issues:
                lines.append(f"   - {issue['message']}")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        report_text = "\n".join(lines)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"Report saved to {output_file}")
        
        return report_text


# ============================================================================
# Convenience Functions
# ============================================================================

def validate_graph_quality(connection, output_file: Optional[str] = None) -> Dict:
    """
    Quick validation function
    
    Args:
        connection: Neo4j connection
        output_file: Optional file to save report
    
    Returns:
        Validation report
    """
    validator = DataQualityValidator(connection)
    report = validator.validate_all()
    
    if output_file:
        validator.generate_report(output_file)
    
    return report


def print_quality_report(connection):
    """
    Print quality report to console
    
    Args:
        connection: Neo4j connection
    """
    validator = DataQualityValidator(connection)
    report_text = validator.generate_report()
    print(report_text)
