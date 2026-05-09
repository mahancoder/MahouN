"""
Graph Optimizer Job - Official Entrypoint
==========================================
Offline job for graph optimization.

This script:
1. Reads config from configs/graph/optimizer.yaml (or defaults)
2. Connects to Neo4j
3. Runs optimization cycle
4. Produces reports to logs/graph_optimization/

Usage:
    python -m graph.optimizer.run_optimizer_job
    
    # With custom config
    python -m graph.optimizer.run_optimizer_job --config configs/graph/custom_optimizer.yaml
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_optimizer_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load optimizer configuration from YAML file.
    
    Args:
        config_path: Path to config file (defaults to configs/runtime_profile.yaml)
    
    Returns:
        Dictionary with optimizer config
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "configs" / "runtime_profile.yaml"
    else:
        config_path = Path(config_path)
    
    defaults = {
        "checkpoint_interval": 10,
        "report_dir": "logs/graph_optimization",
        "enable_feedback_loop": True
    }
    
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return defaults
    
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f) or {}
        
        optimizer_config = yaml_config.get("training", {}).get("optimizer", {})
        
        # Merge with defaults
        config = {**defaults, **optimizer_config}
        return config
    except ImportError:
        logger.warning("YAML not available, using defaults")
        return defaults
    except Exception as e:
        logger.warning(f"Failed to load config: {e}, using defaults")
        return defaults


def main():
    """Main entrypoint for graph optimizer job"""
    parser = argparse.ArgumentParser(description="Run graph optimization cycle")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to optimizer config YAML file"
    )
    parser.add_argument(
        "--report-dir",
        type=str,
        default=None,
        help="Directory for optimization reports"
    )
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("Graph Optimizer Job - Starting")
    logger.info("="*80)
    
    # Load config
    config = load_optimizer_config(args.config)
    
    # Override with CLI args
    if args.report_dir:
        config["report_dir"] = args.report_dir
    
    # Ensure report directory exists
    report_dir = Path(config["report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Report directory: {report_dir}")
    
    # Get Neo4j connection from runtime config
    try:
        from mahoun.core.runtime_config import get_graph_config
        from mahoun.graph.neo4j.connection import Neo4jConnection
        
        graph_config = get_graph_config()
        
        connection = Neo4jConnection(
            uri=graph_config.get("neo4j_uri", "bolt://localhost:7687"),
            user=graph_config.get("user", "neo4j"),
            password=graph_config.get("password", ""),
            database="neo4j"
        )
        
        logger.info("✅ Connected to Neo4j")
        
        # Import and run optimizer
        from mahoun.graph.optimizer.graph_optimizer import GraphOptimizer
        from mahoun.graph.optimizer.config import GraphOptimizationConfig
        
        opt_config = GraphOptimizationConfig(
            enable_feedback_loop=config.get("enable_feedback_loop", True),
            enable_snapshots=True,
            snapshot_dir=str(report_dir)
        )
        
        optimizer = GraphOptimizer(
            driver=connection.driver,
            config=opt_config,
            logger=logger
        )
        
        logger.info("Starting graph optimization cycle...")
        
        # Run optimization cycle
        optimizer.ensure_schema()
        
        if config.get("enable_feedback_loop", True):
            optimizer.update_edge_weights()
        else:
            optimizer.score_and_flag_edges()
        
        optimizer.apply_degree_capping()
        
        if opt_config.enable_snapshots:
            optimizer.snapshot_state()
        
        logger.info("✅ Graph optimization complete!")
        logger.info(f"Reports saved to {report_dir}")
        logger.info("="*80)
        
        return 0
        
    except ImportError as e:
        logger.error(f"Failed to import optimizer: {e}")
        return 1
    except Exception as e:
        logger.error(f"Optimization failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

