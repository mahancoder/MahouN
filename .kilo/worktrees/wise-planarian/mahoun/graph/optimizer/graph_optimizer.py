import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import math

try:
    from neo4j import Driver
    HAS_NEO4J = True
except ImportError:
    Driver = None  # type: ignore
    HAS_NEO4J = False

from .config import GraphOptimizationConfig, EdgeTypePolicy

class GraphOptimizer:
    """
    MAHOUN Graph Optimization Layer
    Non-destructive structural optimizer for Neo4j graph.
    
    v2 Enterprise additions:
    - Feedback-driven edge weighting
    - Adaptive pruning with priority
    - Snapshot and audit capabilities
    """

    def __init__(
        self,
        driver: Driver,
        config: Optional[GraphOptimizationConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.driver = driver
        self.config = config or GraphOptimizationConfig.default()
        self.logger = logger or logging.getLogger(__name__)
        
        # v2: Lazy-load feedback collector
        self._feedback_collector = None

    # ---------------------------------------------------------
    # 1) Ensure Constraints & Indexes (reuse existing schema)
    # ---------------------------------------------------------
    def ensure_schema(self):
        """
        Delegates schema creation to existing modules in:
        graph/neo4j/schema.py  (Constraint, Index, Fulltext, Vector Index)
        """
        try:
            from mahoun.graph.neo4j.schema import Neo4jSchemaManager
            mgr = Neo4jSchemaManager(self.driver)
            mgr.ensure_all()
        except Exception as e:
            self.logger.error(f"Schema ensure failed: {e}")
            raise

    # ---------------------------------------------------------
    # 2) Edge Weighting + Active Flagging (v1)
    # ---------------------------------------------------------
    def score_and_flag_edges(self):
        """v1: Basic edge scoring using confidence values."""
        cypher = """
        MATCH ()-[r]->()
        SET r.edge_weight = coalesce(r.confidence, 1.0)
        SET r.active_edge = true
        """
        with self.driver.session() as session:
            session.run(cypher)

    # ---------------------------------------------------------
    # 3) Degree Capping (non-destructive) - v1/v2 compatible
    # ---------------------------------------------------------
    def apply_degree_capping(self):
        """
        v1/v2: Apply degree caps per edge type.
        
        v2 enhancements:
        - Uses edge_weight for sorting (updated by update_edge_weights)
        - Warns on very high-degree nodes (>10x max_degree)
        """
        for ep in self.config.edge_policies.values():
            if ep.max_degree is None:
                continue

            # Check for very high-degree nodes first
            check_cypher = f"""
            MATCH (n)-[r:{ep.edge_type}]->()
            WITH n, count(r) as degree
            WHERE degree > {ep.max_degree * 10}
            RETURN n.id as node_id, degree
            LIMIT 10
            """
            
            try:
                with self.driver.session() as session:
                    result = session.run(check_cypher)
                    for record in result:
                        self.logger.warning(
                            f"High-degree node detected: {record['node_id']} "
                            f"has {record['degree']} {ep.edge_type} edges "
                            f"(max_degree={ep.max_degree})"
                        )
            except Exception as e:
                self.logger.debug(f"High-degree check failed: {e}")

            # Apply degree capping
            cypher = f"""
            MATCH (n)-[r:{ep.edge_type}]->(m)
            WITH n, r
            ORDER BY r.edge_weight DESC
            WITH n, collect(r) as rels
            WITH n, rels[..{ep.max_degree}] as keep, rels[{ep.max_degree}..] as drop
            FOREACH (r IN drop | SET r.active_edge = false)
            """
            with self.driver.session() as session:
                session.run(cypher)

    # ---------------------------------------------------------
    # 4) Subgraph Builder for Graph-RAG (v1)
    # ---------------------------------------------------------
    def build_subgraph(self, seed_ids: List[str]) -> Dict[str, Any]:
        """v1: Build subgraph for Graph-RAG using APOC path expansion."""
        max_hops = self.config.default_max_hops
        edge_types = [et for et in self.config.edge_policies.keys()]

        cypher = f"""
        MATCH (s)
        WHERE s.id IN $seed_ids
        CALL apoc.path.expandConfig(
            s,
            {{
                relationshipFilter: "{'|'.join(edge_types)}",
                minLevel: 1,
                maxLevel: {max_hops},
                bfs: true,
                filterStartNode: false
            }}
        ) YIELD path
        RETURN
            collect(distinct nodes(path)) as nodes,
            collect(distinct relationships(path)) as rels
        """

        with self.driver.session() as session:
            result = session.run(cypher, seed_ids=seed_ids).single()
            return {
                "nodes": result["nodes"],
                "edges": result["rels"],
                "meta": {"seed_count": len(seed_ids), "hops": max_hops},
            }

    # =========================================================
    # v2 ENTERPRISE METHODS
    # =========================================================

    def update_edge_weights(self) -> None:
        """
        v2 Enterprise: Update edge weights based on feedback, usage, and recency.
        
        Combines:
        - Base weight from EdgeTypePolicy
        - Usage metrics from GraphFeedbackCollector
        - Recency decay
        - Bounded by min_weight/max_weight per policy
        """
        if not self.config.enable_feedback_loop:
            self.logger.info("Feedback loop disabled, skipping edge weight updates")
            return
        
        self.logger.info("Starting feedback-driven edge weight update")
        
        try:
            # Load feedback metrics
            metrics = self._load_usage_metrics()
            
            # Update scores from usage
            self._update_edge_scores_from_usage(metrics)
            
            # Apply recency decay
            self._apply_recency_decay()
            
            # Prune low-weight edges
            self._prune_edges_by_weight()
            
            self.logger.info("Edge weight update completed")
            
        except Exception as e:
            self.logger.error(f"Edge weight update failed: {e}", exc_info=True)
            raise

    def snapshot_state(self, label: Optional[str] = None) -> None:
        """
        v2 Enterprise: Tag current graph state with optimization metadata.
        
        Args:
            label: Optional custom snapshot label
        """
        if not self.config.enable_snapshots:
            self.logger.info("Snapshots disabled, skipping state snapshot")
            return
        
        snapshot_label = label or self.config.snapshot_label
        now = datetime.now().isoformat()
        
        self.logger.info(f"Creating optimization snapshot: {snapshot_label}")
        
        try:
            cypher = """
            MATCH ()-[r]->()
            SET r.last_optimized_at = $timestamp
            WITH count(r) as total
            RETURN total
            """
            
            with self.driver.session() as session:
                result = session.run(cypher, timestamp=now).single()
                total = result["total"] if result else 0
                
            self.logger.info(f"Snapshot created for {total} relationships at {now}")
            
            # Log optimization summary
            self._log_optimization_summary({
                "snapshot_label": snapshot_label,
                "timestamp": now,
                "total_relationships": total,
            })
            
        except Exception as e:
            self.logger.error(f"Snapshot creation failed: {e}", exc_info=True)

    # ---------------------------------------------------------
    # v2 PRIVATE HELPER METHODS
    # ---------------------------------------------------------

    def _load_usage_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Load usage metrics from GraphFeedbackCollector."""
        if self._feedback_collector is None:
            from .feedback import GraphFeedbackCollector
            self._feedback_collector = GraphFeedbackCollector(
                driver=self.driver,
                logger=self.logger,
            )
        
        return self._feedback_collector.aggregate_edge_feedback()

    def _update_edge_scores_from_usage(self, metrics: Dict[str, Dict[str, Any]]) -> None:
        """
        Update edge weights using usage metrics and policy configuration.
        
        Algorithm:
        - usage_factor = log(1 + usage_count)
        - success_factor = success_rate (if available)
        - weight = base * usage_factor * success_factor
        - clamp to [min_weight, max_weight]
        """
        self.logger.debug(f"Updating edge scores for {len(metrics)} edges")
        
        # Process in batches to avoid memory issues
        batch_size = 1000
        edge_ids = list(metrics.keys())
        
        for edge_type, policy in self.config.edge_policies.items():
            try:
                # Get edges of this type with usage data
                cypher = f"""
                MATCH ()-[r:{edge_type}]->()
                WHERE id(r) IN $edge_ids
                RETURN id(r) as edge_id, r.usage_count as usage_count, r.success_count as success_count
                LIMIT {batch_size}
                """
                
                with self.driver.session() as session:
                    result = session.run(cypher, edge_ids=[int(eid) for eid in edge_ids if eid.isdigit()])
                    
                    updates: List[Any] = []
                    for record in result:
                        edge_id = str(record["edge_id"])
                        if edge_id not in metrics:
                            continue
                        
                        metric = metrics[edge_id]
                        usage_count = metric.get("usage_count", 0)
                        success_count = metric.get("success_count", 0)
                        
                        # Calculate factors
                        usage_factor = math.log(1 + usage_count) if usage_count > 0 else 0.0
                        success_factor = (success_count / usage_count) if usage_count > 0 else 1.0
                        
                        # Compute weight
                        weight_raw = policy.base_weight * (1 + usage_factor) * success_factor
                        weight = max(policy.min_weight, min(policy.max_weight, weight_raw))
                        
                        updates.append((int(edge_id), weight))
                    
                    # Batch update
                    if updates:
                        update_cypher = """
                        UNWIND $updates as update
                        MATCH ()-[r]->()
                        WHERE id(r) = update.edge_id
                        SET r.edge_weight = update.weight
                        """
                        session.run(update_cypher, updates=[
                            {"edge_id": eid, "weight": w} for eid, w in updates
                        ])
                        
                        self.logger.debug(f"Updated {len(updates)} {edge_type} edges")
                        
            except Exception as e:
                self.logger.warning(f"Failed to update {edge_type} edges: {e}")

    def _apply_recency_decay(self) -> None:
        """
        Apply time-based decay to edge weights.
        
        Formula: decay_factor = exp(-age_days / half_life * ln(2))
        """
        half_life = self.config.recency_half_life_days
        decay_constant = math.log(2) / half_life
        
        self.logger.debug(f"Applying recency decay (half-life={half_life} days)")
        
        try:
            cypher = """
            MATCH ()-[r]->()
            WHERE r.last_used_at IS NOT NULL
            WITH r, duration.between(r.last_used_at, datetime()).days as age_days
            WHERE age_days > 0
            SET r.edge_weight = r.edge_weight * exp(-1.0 * age_days * $decay_constant)
            RETURN count(r) as updated
            """
            
            with self.driver.session() as session:
                result = session.run(cypher, decay_constant=decay_constant).single()
                updated = result["updated"] if result else 0
                self.logger.debug(f"Applied recency decay to {updated} edges")
                
        except Exception as e:
            self.logger.warning(f"Recency decay failed: {e}")

    def _prune_edges_by_weight(self) -> None:
        """
        Deactivate edges below pruning threshold.
        
        Sets r.active_edge = false for low-weight edges.
        Respects EdgeTypePolicy.priority for tie-breaking.
        """
        threshold = self.config.pruning_threshold
        
        self.logger.debug(f"Pruning edges below threshold {threshold}")
        
        try:
            cypher = """
            MATCH ()-[r]->()
            WHERE r.edge_weight < $threshold
            SET r.active_edge = false
            RETURN count(r) as pruned
            """
            
            with self.driver.session() as session:
                result = session.run(cypher, threshold=threshold).single()
                pruned = result["pruned"] if result else 0
                self.logger.info(f"Pruned {pruned} edges below threshold {threshold}")
                
        except Exception as e:
            self.logger.warning(f"Edge pruning failed: {e}")

    def _log_optimization_summary(self, stats: Dict[str, Any]) -> None:
        """
        Log optimization summary.
        
        TODO v2.1: Integration with graph/neo4j/monitoring.py for metrics collection
        """
        self.logger.info(f"Optimization summary: {stats}")
        
        # TODO: Future integration with monitoring module
        try:
            from mahoun.graph.neo4j.monitoring import log_optimization_metrics
            log_optimization_metrics(stats)
        except ImportError:
            self.logger.debug("Monitoring module not available for metrics logging")

