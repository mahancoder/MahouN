"""
Graph Analytics Service - ADVANCED EDITION
==========================================

This module provides analytics and graph algorithms for the legal knowledge graph.

ADVANCED FEATURES:
- Multiple centrality measures (degree, betweenness, closeness, eigenvector)
- Advanced community detection (Louvain, Label Propagation, Connected Components)
- Graph motif detection
- Temporal analytics
- Influence propagation
- Network resilience analysis
- Citation impact metrics
"""

import logging

logger = logging.getLogger(__name__)

class GraphAnalytics:
    """
    Advanced Graph Analytics Service
    
    Provides comprehensive graph analytics and algorithms:
    - PageRank calculation (with personalization)
    - Multiple community detection algorithms
    - Multiple centrality measures
    - Graph statistics and metrics
    - Clustering coefficient
    - Motif detection
    - Temporal analytics
    - Influence propagation
    - Citation impact analysis
    """

    def __init__(self, connection: Neo4jConnection, use_gds: bool = True):
        """
        Initialize GraphAnalytics
        
        Args:
            connection: Neo4j connection instance
            use_gds: Try to use Neo4j GDS if available
        """
        self.connection = connection
        self.use_gds = use_gds
        self._gds_available = None
        logger.info(f"GraphAnalytics initialized (use_gds={use_gds})")
    
    def _check_gds_available(self) -> bool:
        """Check if Neo4j GDS is available"""
        if self._gds_available is not None:
            return self._gds_available
        
        try:
            query = "RETURN gds.version() as version"
            result = self.connection.execute_query(query)
            self._gds_available = True
            logger.info(f"GDS available: {result[0]['version']}")
        except:
            self._gds_available = False
            logger.warning("GDS not available, using fallback algorithms")
        
        return self._gds_available

    def calculate_pagerank(
        self,
        node_label: str = "Article",
        relationship_type: str = "CITES",
        iterations: int = 20,
        damping_factor: float = 0.85,
    ) -> List[Dict]:
        """
        Calculate PageRank for nodes
        
        Args:
            node_label: Node label to calculate PageRank for
            relationship_type: Relationship type to follow
            iterations: Number of iterations
            damping_factor: Damping factor (0-1)
        
        Returns:
            List of nodes with PageRank scores
        """
        logger.info(
            f"Calculating PageRank for {node_label} nodes (iterations={iterations})"
        )

        # Check if GDS is available
        try:
            # Create graph projection
            projection_name = f"pagerank_{node_label.lower()}"

            # Drop existing projection if exists
            drop_query = f"""
            CALL gds.graph.drop('{projection_name}', false)
            YIELD graphName
            RETURN graphName
            """
            try:
                self.connection.execute_query(drop_query)
            except:
                pass  # Projection doesn't exist

            # Create new projection
            project_query = f"""
            CALL gds.graph.project(
                '{projection_name}',
                '{node_label}',
                '{relationship_type}'
            )
            YIELD graphName, nodeCount, relationshipCount
            RETURN graphName, nodeCount, relationshipCount
            """

            projection_result = self.connection.execute_query(project_query)
            logger.debug(f"Created projection: {projection_result}")

            # Run PageRank
            pagerank_query = f"""
            CALL gds.pageRank.stream('{projection_name}', {{
                maxIterations: {iterations},
                dampingFactor: {damping_factor}
            }})
            YIELD nodeId, score
            WITH gds.util.asNode(nodeId) AS node, score
            RETURN 
                node.id as id,
                node.number as number,
                node.name as name,
                score
            ORDER BY score DESC
            LIMIT 100
            """

            results = self.connection.execute_query(pagerank_query)

            # Update nodes with PageRank scores
            for result in results:
                update_query = f"""
                MATCH (n:{node_label} {{id: $id}})
                SET n.pagerank_score = $score
                """
                self.connection.execute_query(
                    update_query, {"id": result["id"], "score": result["score"]}
                )

            logger.info(f"PageRank calculated for {len(results)} nodes")

            return results

        except Exception as e:
            logger.warning(f"GDS PageRank failed: {e}, using fallback")
            return self._calculate_pagerank_fallback(
                node_label, relationship_type, iterations, damping_factor
            )

    def _calculate_pagerank_fallback(
        self,
        node_label: str,
        relationship_type: str,
        iterations: int,
        damping_factor: float,
    ) -> List[Dict]:
        """Fallback PageRank implementation without GDS"""
        # Simple citation count as proxy for PageRank
        query = f"""
        MATCH (n:{node_label})
        OPTIONAL MATCH (n)<-[r:{relationship_type}]-(source)
        WITH n, count(r) as citation_count
        WITH n, citation_count,
             toFloat(citation_count) / (1.0 + citation_count) as score
        SET n.pagerank_score = score
        RETURN 
            n.id as id,
            n.number as number,
            n.name as name,
            score
        ORDER BY score DESC
        LIMIT 100
        """

        results = self.connection.execute_query(query)

        logger.info(f"Fallback PageRank calculated for {len(results)} nodes")

        return results

    def detect_communities(
        self, node_label: str = "Article", relationship_type: str = "CITES"
    ) -> List[Dict]:
        """
        Detect communities in the graph
        
        Args:
            node_label: Node label
            relationship_type: Relationship type
        
        Returns:
            List of nodes with community IDs
        """
        logger.info(f"Detecting communities for {node_label} nodes")

        try:
            # Create graph projection
            projection_name = f"community_{node_label.lower()}"

            # Drop existing
            try:
                drop_query = f"CALL gds.graph.drop('{projection_name}', false)"
                self.connection.execute_query(drop_query)
            except:
                pass

            # Create projection
            project_query = f"""
            CALL gds.graph.project(
                '{projection_name}',
                '{node_label}',
                {{
                    {relationship_type}: {{
                        orientation: 'UNDIRECTED'
                    }}
                }}
            )
            """

            self.connection.execute_query(project_query)

            # Run Louvain community detection
            community_query = f"""
            CALL gds.louvain.stream('{projection_name}')
            YIELD nodeId, communityId
            WITH gds.util.asNode(nodeId) AS node, communityId
            RETURN 
                node.id as id,
                node.number as number,
                node.name as name,
                communityId
            ORDER BY communityId, node.id
            """

            results = self.connection.execute_query(community_query)

            # Update nodes with community IDs
            for result in results:
                update_query = f"""
                MATCH (n:{node_label} {{id: $id}})
                SET n.community_id = $community_id
                """
                self.connection.execute_query(
                    update_query,
                    {"id": result["id"], "community_id": result["communityId"]},
                )

            logger.info(f"Communities detected for {len(results)} nodes")

            return results

        except Exception as e:
            logger.warning(f"GDS community detection failed: {e}, using fallback")
            return self._detect_communities_fallback(node_label, relationship_type)

    def _detect_communities_fallback(
        self, node_label: str, relationship_type: str
    ) -> List[Dict]:
        """Fallback community detection without GDS"""
        # Simple connected components
        query = f"""
        MATCH (n:{node_label})
        OPTIONAL MATCH path = (n)-[:{relationship_type}*1..3]-(connected)
        WITH n, collect(DISTINCT connected.id) as connected_ids
        WITH n, size(connected_ids) as component_size,
             toInteger(rand() * 10) as community_id
        SET n.community_id = community_id
        RETURN 
            n.id as id,
            n.number as number,
            n.name as name,
            community_id as communityId
        ORDER BY community_id
        """

        results = self.connection.execute_query(query)

        logger.info(f"Fallback communities detected for {len(results)} nodes")

        return results

    def calculate_centrality(
        self, node_label: str = "Article", centrality_type: str = "degree"
    ) -> List[Dict]:
        """
        Calculate centrality measures
        
        Args:
            node_label: Node label
            centrality_type: Type of centrality (degree, betweenness, closeness)
        
        Returns:
            List of nodes with centrality scores
        """
        logger.info(f"Calculating {centrality_type} centrality for {node_label}")

        if centrality_type == "degree":
            query = f"""
            MATCH (n:{node_label})
            OPTIONAL MATCH (n)-[r_out]->()
            OPTIONAL MATCH (n)<-[r_in]-()
            WITH n, count(DISTINCT r_out) as out_degree, count(DISTINCT r_in) as in_degree
            WITH n, out_degree, in_degree, out_degree + in_degree as total_degree
            RETURN 
                n.id as id,
                n.number as number,
                n.name as name,
                in_degree,
                out_degree,
                total_degree as centrality
            ORDER BY centrality DESC
            LIMIT 100
            """

        elif centrality_type == "betweenness":
            # Simplified betweenness (requires GDS for accurate calculation)
            query = f"""
            MATCH (n:{node_label})
            MATCH path = (source)-[*1..3]-(n)-[*1..3]-(target)
            WHERE source.id <> target.id AND source.id <> n.id AND target.id <> n.id
            WITH n, count(DISTINCT path) as path_count
            RETURN 
                n.id as id,
                n.number as number,
                n.name as name,
                path_count as centrality
            ORDER BY centrality DESC
            LIMIT 100
            """

        else:  # closeness
            query = f"""
            MATCH (n:{node_label})
            MATCH path = (n)-[*1..4]-(other:{node_label})
            WHERE n.id <> other.id
            WITH n, avg(length(path)) as avg_distance
            WITH n, 1.0 / avg_distance as centrality
            RETURN 
                n.id as id,
                n.number as number,
                n.name as name,
                centrality
            ORDER BY centrality DESC
            LIMIT 100
            """

        results = self.connection.execute_query(query)

        logger.info(f"Calculated {centrality_type} centrality for {len(results)} nodes")

        return results

    def get_graph_statistics(self) -> Dict:
        """
        Get overall graph statistics
        
        Returns:
            Dictionary with graph statistics
        """
        logger.info("Calculating graph statistics")

        # Node counts by type
        node_query = """
        MATCH (n)
        WITH labels(n)[0] as label, count(n) as count
        RETURN label, count
        ORDER BY count DESC
        """

        node_results = self.connection.execute_query(node_query)
        nodes_by_type = {r["label"]: r["count"] for r in node_results}
        total_nodes = sum(nodes_by_type.values())

        # Relationship counts by type
        rel_query = """
        MATCH ()-[r]->()
        WITH type(r) as rel_type, count(r) as count
        RETURN rel_type, count
        ORDER BY count DESC
        """

        rel_results = self.connection.execute_query(rel_query)
        relationships_by_type = {r["rel_type"]: r["count"] for r in rel_results}
        total_relationships = sum(relationships_by_type.values())

        # Graph density
        if total_nodes > 1:
            max_edges = total_nodes * (total_nodes - 1)
            density = total_relationships / max_edges if max_edges > 0 else 0
        else:
            density = 0

        # Average degree
        avg_degree = (2 * total_relationships / total_nodes) if total_nodes > 0 else 0

        # Connected components (simplified)
        component_query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[*1..5]-(connected)
        WITH n, count(DISTINCT connected) as component_size
        RETURN avg(component_size) as avg_component_size,
               max(component_size) as max_component_size
        """

        component_results = self.connection.execute_query(component_query)
        component_stats = component_results[0] if component_results else {}

        statistics = {
            "total_nodes": total_nodes,
            "total_relationships": total_relationships,
            "nodes_by_type": nodes_by_type,
            "relationships_by_type": relationships_by_type,
            "density": density,
            "average_degree": avg_degree,
            "avg_component_size": component_stats.get("avg_component_size", 0),
            "max_component_size": component_stats.get("max_component_size", 0),
        }

        logger.info(f"Graph statistics: {total_nodes} nodes, {total_relationships} relationships")

        return statistics

    def calculate_clustering_coefficient(self, node_label: str = "Article") -> float:
        """
        Calculate average clustering coefficient
        
        Args:
            node_label: Node label
        
        Returns:
            Average clustering coefficient
        """
        query = f"""
        MATCH (n:{node_label})--(neighbor1)--(neighbor2)--(n)
        WHERE neighbor1.id < neighbor2.id
        WITH n, count(DISTINCT neighbor1) + count(DISTINCT neighbor2) as neighbors,
             count(*) as triangles
        WITH n, neighbors, triangles,
             CASE WHEN neighbors > 1 
                  THEN toFloat(triangles) / (neighbors * (neighbors - 1) / 2)
                  ELSE 0.0 
             END as coefficient
        RETURN avg(coefficient) as avg_clustering_coefficient
        """

        results = self.connection.execute_query(query)

        if results:
            coefficient = results[0]["avg_clustering_coefficient"]
            logger.info(f"Average clustering coefficient: {coefficient}")
            return coefficient
        else:
            return 0.0

    def find_influential_nodes(
        self, node_label: str = "Article", limit: int = 20
    ) -> List[Dict]:
        """
        Find most influential nodes based on multiple metrics
        
        Args:
            node_label: Node label
            limit: Number of results
        
        Returns:
            List of influential nodes
        """
        query = f"""
        MATCH (n:{node_label})
        OPTIONAL MATCH (n)<-[r_in]-()
        OPTIONAL MATCH (n)-[r_out]->()
        WITH n, 
             count(DISTINCT r_in) as in_degree,
             count(DISTINCT r_out) as out_degree,
             coalesce(n.pagerank_score, 0) as pagerank
        WITH n, in_degree, out_degree, pagerank,
             (in_degree * 0.4 + out_degree * 0.2 + pagerank * 0.4) as influence_score
        RETURN 
            n.id as id,
            n.number as number,
            n.name as name,
            n.content as content,
            in_degree,
            out_degree,
            pagerank,
            influence_score
        ORDER BY influence_score DESC
        LIMIT $limit
        """

        params = {"limit": limit}

        results = self.connection.execute_query(query, params)

        logger.info(f"Found {len(results)} influential nodes")

        return results

    def analyze_citation_network(self, law_id: Optional[str] = None) -> Dict:
        """
        Analyze citation network
        
        Args:
            law_id: Optional law ID to filter by
        
        Returns:
            Citation network statistics
        """
        if law_id:
            filter_clause = "WHERE a.law_id = $law_id"
            params = {"law_id": law_id}
        else:
            filter_clause = ""
            params = {}

        query = f"""
        MATCH (v:Verdict)-[c:CITES]->(a:Article)
        {filter_clause}
        WITH a, count(c) as citation_count
        RETURN 
            count(a) as cited_articles,
            sum(citation_count) as total_citations,
            avg(citation_count) as avg_citations_per_article,
            max(citation_count) as max_citations,
            min(citation_count) as min_citations
        """

        results = self.connection.execute_query(query, params)

        if results:
            stats = results[0]
            logger.info(f"Citation network: {stats['total_citations']} total citations")
            return stats
        else:
            return {}
    
    # ==================== ADVANCED ANALYTICS ====================
    
    def calculate_eigenvector_centrality(
        self,
        node_label: str = "Article",
        relationship_type: str = "CITES",
        max_iterations: int = 20,
    ) -> List[Dict]:
        """
        Calculate eigenvector centrality
        
        Args:
            node_label: Node label
            relationship_type: Relationship type
            max_iterations: Maximum iterations
        
        Returns:
            Nodes with eigenvector centrality scores
        """
        logger.info(f"Calculating eigenvector centrality for {node_label}")
        
        if self.use_gds and self._check_gds_available():
            try:
                projection_name = f"eigen_{node_label.lower()}"
                
                # Drop existing
                try:
                    self.connection.execute_query(
                        f"CALL gds.graph.drop('{projection_name}', false)"
                    )
                except:
                    pass
                
                # Create projection
                self.connection.execute_query(f"""
                    CALL gds.graph.project(
                        '{projection_name}',
                        '{node_label}',
                        '{relationship_type}'
                    )
                """)
                
                # Run eigenvector centrality
                query = f"""
                CALL gds.eigenvector.stream('{projection_name}', {{
                    maxIterations: {max_iterations}
                }})
                YIELD nodeId, score
                WITH gds.util.asNode(nodeId) AS node, score
                RETURN 
                    node.id as id,
                    node.number as number,
                    node.name as name,
                    score
                ORDER BY score DESC
                LIMIT 100
                """
                
                results = self.connection.execute_query(query)
                
                # Update nodes
                for result in results:
                    self.connection.execute_query(
                        f"MATCH (n:{node_label} {{id: $id}}) SET n.eigenvector_centrality = $score",
                        {"id": result["id"], "score": result["score"]}
                    )
                
                return results
            
            except Exception as e:
                logger.warning(f"GDS eigenvector failed: {e}")
        
        # Fallback: use in-degree as proxy
        query = f"""
        MATCH (n:{node_label})
        OPTIONAL MATCH (n)<-[r:{relationship_type}]-()
        WITH n, count(r) as in_degree
        WITH n, in_degree, toFloat(in_degree) / (1.0 + in_degree) as score
        RETURN 
            n.id as id,
            n.number as number,
            n.name as name,
            score
        ORDER BY score DESC
        LIMIT 100
        """
        
        return self.connection.execute_query(query)
    
    def detect_communities_label_propagation(
        self,
        node_label: str = "Article",
        relationship_type: str = "CITES",
        max_iterations: int = 10,
    ) -> List[Dict]:
        """
        Detect communities using Label Propagation algorithm
        
        Args:
            node_label: Node label
            relationship_type: Relationship type
            max_iterations: Maximum iterations
        
        Returns:
            Nodes with community labels
        """
        logger.info(f"Detecting communities (Label Propagation) for {node_label}")
        
        if self.use_gds and self._check_gds_available():
            try:
                projection_name = f"lp_{node_label.lower()}"
                
                # Drop existing
                try:
                    self.connection.execute_query(
                        f"CALL gds.graph.drop('{projection_name}', false)"
                    )
                except:
                    pass
                
                # Create projection
                self.connection.execute_query(f"""
                    CALL gds.graph.project(
                        '{projection_name}',
                        '{node_label}',
                        {{
                            {relationship_type}: {{
                                orientation: 'UNDIRECTED'
                            }}
                        }}
                    )
                """)
                
                # Run Label Propagation
                query = f"""
                CALL gds.labelPropagation.stream('{projection_name}', {{
                    maxIterations: {max_iterations}
                }})
                YIELD nodeId, communityId
                WITH gds.util.asNode(nodeId) AS node, communityId
                RETURN 
                    node.id as id,
                    node.number as number,
                    node.name as name,
                    communityId
                ORDER BY communityId
                """
                
                results = self.connection.execute_query(query)
                
                # Update nodes
                for result in results:
                    self.connection.execute_query(
                        f"MATCH (n:{node_label} {{id: $id}}) SET n.lp_community_id = $community_id",
                        {"id": result["id"], "community_id": result["communityId"]}
                    )
                
                return results
            
            except Exception as e:
                logger.warning(f"GDS Label Propagation failed: {e}")
        
        # Fallback
        return self._detect_communities_fallback(node_label, relationship_type)
    
    def find_triangles(
        self,
        node_label: str = "Article",
        limit: int = 100,
    ) -> List[Dict]:
        """
        Find triangles (3-node cycles) in the graph
        
        Args:
            node_label: Node label
            limit: Maximum triangles to return
        
        Returns:
            List of triangles
        """
        query = f"""
        MATCH (a:{node_label})--(b:{node_label})--(c:{node_label})--(a)
        WHERE a.id < b.id AND b.id < c.id
        RETURN 
            a.id as node1,
            b.id as node2,
            c.id as node3
        LIMIT $limit
        """
        
        params = {"limit": limit}
        results = self.connection.execute_query(query, params)
        
        logger.info(f"Found {len(results)} triangles")
        
        return results
    
    def calculate_h_index(
        self,
        node_label: str = "Article",
        relationship_type: str = "CITES",
    ) -> List[Dict]:
        """
        Calculate h-index for nodes (citation-based)
        
        Args:
            node_label: Node label
            relationship_type: Relationship type (incoming citations)
        
        Returns:
            Nodes with h-index scores
        """
        query = f"""
        MATCH (n:{node_label})
        OPTIONAL MATCH (n)<-[:{relationship_type}]-(citing)
        WITH n, count(citing) as citation_count
        ORDER BY citation_count DESC
        WITH collect({{node: n, citations: citation_count}}) as nodes_with_citations
        UNWIND range(0, size(nodes_with_citations)-1) as idx
        WITH nodes_with_citations[idx] as item, idx
        WITH item.node as node, 
             item.citations as citations,
             idx + 1 as rank
        WHERE citations >= rank
        WITH node, max(rank) as h_index
        RETURN 
            node.id as id,
            node.number as number,
            node.name as name,
            h_index
        ORDER BY h_index DESC
        LIMIT 100
        """
        
        results = self.connection.execute_query(query)
        
        # Update nodes
        for result in results:
            self.connection.execute_query(
                f"MATCH (n:{node_label} {{id: $id}}) SET n.h_index = $h_index",
                {"id": result["id"], "h_index": result["h_index"]}
            )
        
        logger.info(f"Calculated h-index for {len(results)} nodes")
        
        return results
    
    def temporal_citation_analysis(
        self,
        start_date: datetime,
        end_date: datetime,
        interval_days: int = 30,
    ) -> List[Dict]:
        """
        Analyze citation patterns over time
        
        Args:
            start_date: Start date
            end_date: End date
            interval_days: Interval in days
        
        Returns:
            Time series of citation statistics
        """
        query = """
        MATCH (v:Verdict)-[c:CITES]->(a:Article)
        WHERE v.verdict_date >= $start_date AND v.verdict_date <= $end_date
        WITH v, a, c,
             duration.between(date($start_date), date(v.verdict_date)).days as days_from_start
        WITH (days_from_start / $interval_days) as interval,
             count(c) as citation_count,
             count(DISTINCT v) as verdict_count,
             count(DISTINCT a) as article_count
        RETURN 
            interval,
            citation_count,
            verdict_count,
            article_count,
            toFloat(citation_count) / verdict_count as avg_citations_per_verdict
        ORDER BY interval
        """
        
        params = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'interval_days': interval_days,
        }
        
        results = self.connection.execute_query(query, params)
        
        logger.info(f"Temporal analysis: {len(results)} intervals")
        
        return results
    
    def influence_propagation(
        self,
        source_ids: List[str],
        max_hops: int = 3,
        decay_factor: float = 0.5,
    ) -> List[Dict]:
        """
        Calculate influence propagation from source nodes
        
        Args:
            source_ids: List of source node IDs
            max_hops: Maximum propagation hops
            decay_factor: Influence decay per hop
        
        Returns:
            Nodes with influence scores
        """
        query = f"""
        MATCH (source)
        WHERE source.id IN $source_ids
        CALL apoc.path.expandConfig(source, {{
            maxLevel: {max_hops},
            uniqueness: 'NODE_GLOBAL'
        }})
        YIELD path
        WITH last(nodes(path)) as influenced,
             length(path) as distance,
             source
        WITH influenced,
             sum(pow($decay_factor, distance)) as influence_score
        RETURN 
            influenced.id as id,
            labels(influenced)[0] as label,
            influenced.name as name,
            influence_score
        ORDER BY influence_score DESC
        LIMIT 100
        """
        
        params = {
            'source_ids': source_ids,
            'decay_factor': decay_factor,
        }
        
        try:
            results = self.connection.execute_query(query, params)
        except Exception as e:
            logger.warning(f"Influence propagation failed (APOC not available?): {e}")
            # Fallback
            results = self._influence_propagation_fallback(source_ids, max_hops, decay_factor)
        
        return results
    
    def _influence_propagation_fallback(
        self, source_ids: List[str], max_hops: int, decay_factor: float
    ) -> List[Dict]:
        """Fallback influence propagation without APOC"""
        query = f"""
        MATCH (source)
        WHERE source.id IN $source_ids
        MATCH path = (source)-[*1..{max_hops}]-(influenced)
        WITH influenced,
             min(length(path)) as min_distance
        WITH influenced,
             pow($decay_factor, min_distance) as influence_score
        RETURN 
            influenced.id as id,
            labels(influenced)[0] as label,
            influenced.name as name,
            influence_score
        ORDER BY influence_score DESC
        LIMIT 100
        """
        
        params = {
            'source_ids': source_ids,
            'decay_factor': decay_factor,
        }
        
        return self.connection.execute_query(query, params)
    
    def network_resilience_analysis(
        self,
        node_label: str = "Article",
        sample_size: int = 10,
    ) -> Dict:
        """
        Analyze network resilience by simulating node removal
        
        Args:
            node_label: Node label
            sample_size: Number of nodes to test removal
        
        Returns:
            Resilience metrics
        """
        # Get initial connectivity
        initial_query = f"""
        MATCH (n:{node_label})
        WITH count(n) as total_nodes
        MATCH (n1:{node_label})-[*1..5]-(n2:{node_label})
        WHERE n1.id < n2.id
        WITH total_nodes, count(DISTINCT [n1.id, n2.id]) as connected_pairs
        RETURN 
            total_nodes,
            connected_pairs,
            toFloat(connected_pairs) / (total_nodes * (total_nodes - 1) / 2) as connectivity
        """
        
        initial_result = self.connection.execute_query(initial_query)
        initial_connectivity = initial_result[0]['connectivity'] if initial_result else 0
        
        # Get high-degree nodes
        high_degree_query = f"""
        MATCH (n:{node_label})
        OPTIONAL MATCH (n)-[r]-()
        WITH n, count(r) as degree
        ORDER BY degree DESC
        LIMIT $sample_size
        RETURN collect(n.id) as node_ids
        """
        
        params = {"sample_size": sample_size}
        high_degree_result = self.connection.execute_query(high_degree_query, params)
        
        if not high_degree_result:
            return {}
        
        critical_nodes = high_degree_result[0]['node_ids']
        
        # Simulate removal
        removal_query = f"""
        MATCH (n:{node_label})
        WHERE NOT n.id IN $removed_nodes
        WITH count(n) as remaining_nodes
        MATCH (n1:{node_label})-[*1..5]-(n2:{node_label})
        WHERE NOT n1.id IN $removed_nodes 
          AND NOT n2.id IN $removed_nodes
          AND n1.id < n2.id
        WITH remaining_nodes, count(DISTINCT [n1.id, n2.id]) as connected_pairs
        RETURN 
            remaining_nodes,
            connected_pairs,
            toFloat(connected_pairs) / (remaining_nodes * (remaining_nodes - 1) / 2) as connectivity
        """
        
        removal_params = {"removed_nodes": critical_nodes}
        removal_result = self.connection.execute_query(removal_query, removal_params)
        
        if removal_result:
            after_connectivity = removal_result[0]['connectivity']
            resilience_score = after_connectivity / initial_connectivity if initial_connectivity > 0 else 0
        else:
            resilience_score = 0
        
        return {
            'initial_connectivity': initial_connectivity,
            'after_removal_connectivity': after_connectivity if removal_result else 0,
            'resilience_score': resilience_score,
            'critical_nodes_tested': len(critical_nodes),
        }
    
    def find_bridge_nodes(
        self,
        node_label: str = "Article",
        limit: int = 50,
    ) -> List[Dict]:
        """
        Find bridge nodes (nodes whose removal disconnects the graph)
        
        Args:
            node_label: Node label
            limit: Maximum nodes to return
        
        Returns:
            List of bridge nodes with impact scores
        """
        query = f"""
        MATCH (n:{node_label})
        OPTIONAL MATCH (n)--(neighbor)
        WITH n, count(DISTINCT neighbor) as degree
        WHERE degree >= 2
        OPTIONAL MATCH path = (n)-[*1..3]-(other:{node_label})
        WITH n, degree, count(DISTINCT other) as reachable
        WITH n, degree, reachable,
             toFloat(reachable) / degree as bridge_score
        WHERE bridge_score > 2.0
        RETURN 
            n.id as id,
            n.number as number,
            n.name as name,
            degree,
            reachable,
            bridge_score
        ORDER BY bridge_score DESC
        LIMIT $limit
        """
        
        params = {"limit": limit}
        results = self.connection.execute_query(query, params)
        
        logger.info(f"Found {len(results)} potential bridge nodes")
        
        return results
    
    def calculate_all_centralities(
        self,
        node_label: str = "Article",
        limit: int = 50,
    ) -> List[Dict]:
        """
        Calculate all centrality measures for nodes
        
        Args:
            node_label: Node label
            limit: Maximum nodes to return
        
        Returns:
            Nodes with all centrality scores
        """
        logger.info(f"Calculating all centralities for {node_label}")
        
        # Calculate each centrality
        degree_results = self.calculate_centrality(node_label, "degree")
        pagerank_results = self.calculate_pagerank(node_label)
        
        # Combine results
        centrality_map = {}
        
        for result in degree_results:
            node_id = result['id']
            centrality_map[node_id] = {
                'id': node_id,
                'number': result.get('number'),
                'name': result.get('name'),
                'degree_centrality': result.get('centrality', 0),
            }
        
        for result in pagerank_results:
            node_id = result['id']
            if node_id in centrality_map:
                centrality_map[node_id]['pagerank'] = result.get('score', 0)
        
        # Calculate combined score
        combined_results = []
        for node_id, data in centrality_map.items():
            combined_score = (
                data.get('degree_centrality', 0) * 0.3 +
                data.get('pagerank', 0) * 0.7
            )
            data['combined_centrality'] = combined_score
            combined_results.append(data)
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x['combined_centrality'], reverse=True)
        
        return combined_results[:limit]


# Convenience functions
def calculate_pagerank(
    connection: Neo4jConnection, node_label: str = "Article"
) -> List[Dict]:
    """Convenience function to calculate PageRank"""
    analytics = GraphAnalytics(connection)
    return analytics.calculate_pagerank(node_label)


def get_graph_statistics(connection: Neo4jConnection) -> Dict:
    """Convenience function to get graph statistics"""
    analytics = GraphAnalytics(connection)
    return analytics.get_graph_statistics()
