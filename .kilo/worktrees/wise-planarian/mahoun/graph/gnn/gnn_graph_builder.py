# pipelines/gnn/gnn_graph_builder.py
"""
GNN Graph Builder with PyTorch Geometric

ساخت گراف با PyTorch Geometric برای استفاده در GAT Reranking
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

import torch
from torch_geometric.data import Data
from sentence_transformers import SentenceTransformer
import networkx as nx

try:
    from neo4j import GraphDatabase

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

from pipelines._logging import setup_logger

log = setup_logger("gnn_graph_builder")


@dataclass
class GraphStats:
    """Statistics about the built graph"""

    num_nodes: int
    num_edges: int
    num_edge_types: int
    avg_degree: float
    density: float
    num_components: int


class GNNGraphBuilder:
    """
    Build graph using PyTorch Geometric with multiple edge types

    Features:
    - Multiple edge types: CITES, SIMILAR, RELATED, CONTRADICTS
    - Node features: document embeddings + metadata
    - Edge features: similarity scores, types
    - Export to PyG, Neo4j, GraphML formats
    """

    # Edge type constants
    EDGE_CITES = 0
    EDGE_SIMILAR = 1
    EDGE_RELATED = 2
    EDGE_CONTRADICTS = 3

    EDGE_TYPE_NAMES = {
        EDGE_CITES: "CITES",
        EDGE_SIMILAR: "SIMILAR",
        EDGE_RELATED: "RELATED",
        EDGE_CONTRADICTS: "CONTRADICTS",
    }

    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        embed_model: str = "BAAI/bge-m3",
        similarity_threshold_similar: float = 0.85,
        similarity_threshold_related: float = 0.70,
        max_edges_per_node: int = 50,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        """
        Initialize GNN Graph Builder

        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            embed_model: Embedding model name
            similarity_threshold_similar: Threshold for SIMILAR edges
            similarity_threshold_related: Threshold for RELATED edges
            max_edges_per_node: Maximum similarity edges per node
            device: Device for embeddings (cuda/cpu)
        """
        log.info(f"Initializing GNN Graph Builder on {device}")

        self.device = device
        self.similarity_threshold_similar = similarity_threshold_similar
        self.similarity_threshold_related = similarity_threshold_related
        self.max_edges_per_node = max_edges_per_node

        # Load embedding model
        log.info(f"Loading embedding model: {embed_model}")
        self.embed_model = SentenceTransformer(embed_model, device=device)

        # Neo4j connection (optional)
        self.neo4j_driver = None
        if neo4j_uri and NEO4J_AVAILABLE:
            try:
                self.neo4j_driver = GraphDatabase.driver(
                    neo4j_uri, auth=(neo4j_user, neo4j_password)
                )
                log.info("Neo4j connection established")
            except Exception as e:
                log.warning(f"Could not connect to Neo4j: {e}")

        log.info("GNN Graph Builder initialized")

    def build_from_jsonl(
        self,
        jsonl_path: str,
        output_path: Optional[str] = None,
        save_neo4j: bool = False,
        save_graphml: bool = False,
    ) -> Data:
        """
        Build graph from JSONL file

        Args:
            jsonl_path: Path to JSONL file with documents
            output_path: Path to save PyG Data object
            save_neo4j: Whether to save to Neo4j
            save_graphml: Whether to save as GraphML

        Returns:
            PyG Data object
        """
        log.info(f"Building graph from {jsonl_path}")

        # Load documents
        documents = self._load_documents(jsonl_path)
        log.info(f"Loaded {len(documents)} documents")

        # Build graph
        graph_data = self.build_graph(documents)

        # Save
        if output_path:
            self.save_to_pyg(graph_data, output_path)

        if save_neo4j and self.neo4j_driver:
            self.save_to_neo4j(graph_data, documents)

        if save_graphml:
            graphml_path = (
                output_path.replace(".pt", ".graphml") if output_path else "graph.graphml"
            )
            self.save_to_graphml(graph_data, documents, graphml_path)

        return graph_data

    def build_graph(self, documents: List[Dict[str, Any]]) -> Data:
        """
        Build PyG graph from documents

        Args:
            documents: List of document dictionaries

        Returns:
            PyG Data object with node features and edges
        """
        log.info("Building graph...")

        # Create nodes
        node_features, node_mapping, doc_id_to_idx = self._create_nodes(documents)
        log.info(f"Created {len(node_mapping)} nodes")

        # Create edges
        edge_index, edge_attr, edge_types = self._create_edges(
            documents, node_features, doc_id_to_idx
        )
        log.info(f"Created {edge_index.shape[1]} edges")

        # Create PyG Data object
        data = Data(
            x=node_features,
            edge_index=edge_index,
            edge_attr=edge_attr,
            edge_type=edge_types,
            num_nodes=len(node_mapping),
        )

        # Add metadata
        data.doc_ids = list(node_mapping.keys())
        data.doc_id_to_idx = doc_id_to_idx

        # Compute statistics
        stats = self._compute_stats(data)
        log.info(
            f"Graph stats: {stats.num_nodes} nodes, {stats.num_edges} edges, "
            f"avg degree: {stats.avg_degree:.2f}"
        )

        return data

    def _load_documents(self, jsonl_path: str) -> List[Dict[str, Any]]:
        """Load documents from JSONL file"""
        documents = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line)
                documents.append(doc)
        return documents

    def _create_nodes(
        self, documents: List[Dict[str, Any]]
    ) -> Tuple[torch.Tensor, Dict[str, int], Dict[str, int]]:
        """
        Create node features and mappings

        Args:
            documents: List of documents

        Returns:
            node_features: Tensor of shape [num_nodes, feature_dim]
            node_mapping: Dict mapping doc_id to node index
            doc_id_to_idx: Same as node_mapping (for compatibility)
        """
        log.info("Creating node features...")

        # Extract texts and IDs
        texts = []
        doc_ids = []
        for doc in documents:
            text = doc.get("text", doc.get("snippet", ""))
            doc_id = doc.get("id", doc.get("doc_id", f"doc_{len(doc_ids)}"))
            texts.append(text)
            doc_ids.append(doc_id)

        # Compute embeddings
        log.info(f"Computing embeddings for {len(texts)} documents...")
        embeddings = self.embed_model.encode(
            texts,
            batch_size=64,
            show_progress_bar=True,
            convert_to_numpy=False,
            convert_to_tensor=True,
        )

        # Move to CPU for storage
        embeddings = embeddings.cpu()

        # Create mapping
        node_mapping = {doc_id: idx for idx, doc_id in enumerate(doc_ids)}

        log.info(f"Node features shape: {embeddings.shape}")

        return embeddings, node_mapping, node_mapping

    def _create_edges(
        self,
        documents: List[Dict[str, Any]],
        node_features: torch.Tensor,
        doc_id_to_idx: Dict[str, int],
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Create edges with types: CITES, SIMILAR, RELATED

        Args:
            documents: List of documents
            node_features: Node feature tensor
            doc_id_to_idx: Mapping from doc_id to node index

        Returns:
            edge_index: Tensor of shape [2, num_edges]
            edge_attr: Tensor of shape [num_edges, edge_dim]
            edge_types: Tensor of shape [num_edges]
        """
        log.info("Creating edges...")

        edges = []
        edge_weights = []
        edge_types_list = []

        # 1. Extract citation edges
        citation_edges = self._extract_citation_edges(documents, doc_id_to_idx)
        for src, dst in citation_edges:
            edges.append([src, dst])
            edge_weights.append(1.0)
            edge_types_list.append(self.EDGE_CITES)

        log.info(f"Added {len(citation_edges)} citation edges")

        # 2. Compute similarity edges
        similarity_edges = self._compute_similarity_edges(node_features, doc_id_to_idx)

        for src, dst, weight, edge_type in similarity_edges:
            edges.append([src, dst])
            edge_weights.append(weight)
            edge_types_list.append(edge_type)

        log.info(f"Added {len(similarity_edges)} similarity edges")

        # Convert to tensors
        if edges:
            edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
            edge_attr = torch.tensor(edge_weights, dtype=torch.float).unsqueeze(1)
            edge_types = torch.tensor(edge_types_list, dtype=torch.long)
        else:
            # Empty graph
            edge_index = torch.empty((2, 0), dtype=torch.long)
            edge_attr = torch.empty((0, 1), dtype=torch.float)
            edge_types = torch.empty((0,), dtype=torch.long)

        return edge_index, edge_attr, edge_types

    def _extract_citation_edges(
        self, documents: List[Dict[str, Any]], doc_id_to_idx: Dict[str, int]
    ) -> List[Tuple[int, int]]:
        """
        Extract citation relationships from documents

        Args:
            documents: List of documents
            doc_id_to_idx: Mapping from doc_id to node index

        Returns:
            List of (source_idx, target_idx) tuples
        """
        edges = []

        for doc in documents:
            doc_id = doc.get("id", doc.get("doc_id"))
            if doc_id not in doc_id_to_idx:
                continue

            src_idx = doc_id_to_idx[doc_id]

            # Check for citations in metadata
            citations = doc.get("citations", [])
            references = doc.get("references", [])

            for cited_id in citations + references:
                if cited_id in doc_id_to_idx:
                    dst_idx = doc_id_to_idx[cited_id]
                    edges.append((src_idx, dst_idx))

        return edges

    def _compute_similarity_edges(
        self, embeddings: torch.Tensor, doc_id_to_idx: Dict[str, int]
    ) -> List[Tuple[int, int, float, int]]:
        """
        Compute similarity-based edges

        Args:
            embeddings: Node embeddings
            doc_id_to_idx: Mapping from doc_id to node index

        Returns:
            List of (src_idx, dst_idx, weight, edge_type) tuples
        """
        log.info("Computing similarity matrix...")

        # Normalize embeddings
        embeddings_norm = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        # Compute cosine similarity matrix
        similarity_matrix = torch.mm(embeddings_norm, embeddings_norm.t())

        # Remove self-loops
        similarity_matrix.fill_diagonal_(0)

        edges = []
        num_nodes = embeddings.shape[0]

        # For each node, find top-k similar nodes
        for i in range(num_nodes):
            similarities = similarity_matrix[i]

            # Get top-k indices
            top_k = min(self.max_edges_per_node, num_nodes - 1)
            top_values, top_indices = torch.topk(similarities, k=top_k)

            for j, sim_value in zip(top_indices.tolist(), top_values.tolist()):
                if sim_value >= self.similarity_threshold_similar:
                    # SIMILAR edge
                    edges.append((i, j, sim_value, self.EDGE_SIMILAR))
                elif sim_value >= self.similarity_threshold_related:
                    # RELATED edge
                    edges.append((i, j, sim_value, self.EDGE_RELATED))

        log.info(f"Computed {len(edges)} similarity edges")

        return edges

    def _compute_stats(self, data: Data) -> GraphStats:
        """Compute graph statistics"""
        num_nodes = data.num_nodes
        num_edges = data.edge_index.shape[1]

        # Compute degree
        degrees = torch.zeros(num_nodes, dtype=torch.long)
        for i in range(num_edges):
            src = data.edge_index[0, i].item()
            degrees[src] += 1

        avg_degree = degrees.float().mean().item()

        # Density
        max_edges = num_nodes * (num_nodes - 1)
        density = num_edges / max_edges if max_edges > 0 else 0

        # Number of edge types
        num_edge_types = len(torch.unique(data.edge_type))

        # Connected components (approximate)
        num_components = 1  # Simplified

        return GraphStats(
            num_nodes=num_nodes,
            num_edges=num_edges,
            num_edge_types=num_edge_types,
            avg_degree=avg_degree,
            density=density,
            num_components=num_components,
        )

    def save_to_pyg(self, data: Data, path: str):
        """Save PyG Data object to file"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(data, path)
        log.info(f"Saved PyG graph to {path}")

    def save_to_neo4j(self, data: Data, documents: List[Dict[str, Any]]):
        """Save graph to Neo4j database"""
        if not self.neo4j_driver:
            log.warning("Neo4j driver not available")
            return

        log.info("Saving graph to Neo4j...")

        with self.neo4j_driver.session() as session:
            # Clear existing data
            session.run("MATCH (n) DETACH DELETE n")

            # Create nodes
            for idx, doc_id in enumerate(data.doc_ids):
                doc = documents[idx]
                session.run(
                    """
                    CREATE (d:Document {
                        id: $id,
                        text: $text,
                        embedding: $embedding
                    })
                    """,
                    id=doc_id,
                    text=doc.get("text", "")[:1000],  # Limit text length
                    embedding=data.x[idx].tolist(),
                )

            # Create edges
            num_edges = data.edge_index.shape[1]
            for i in range(num_edges):
                src_idx = data.edge_index[0, i].item()
                dst_idx = data.edge_index[1, i].item()
                edge_type = self.EDGE_TYPE_NAMES[data.edge_type[i].item()]
                weight = data.edge_attr[i, 0].item()

                src_id = data.doc_ids[src_idx]
                dst_id = data.doc_ids[dst_idx]

                session.run(
                    f"""
                    MATCH (a:Document {{id: $src_id}})
                    MATCH (b:Document {{id: $dst_id}})
                    CREATE (a)-[r:{edge_type} {{weight: $weight}}]->(b)
                    """,
                    src_id=src_id,
                    dst_id=dst_id,
                    weight=weight,
                )

        log.info("Graph saved to Neo4j")

    def save_to_graphml(self, data: Data, documents: List[Dict[str, Any]], path: str):
        """Save graph as GraphML for NetworkX compatibility"""
        log.info("Converting to NetworkX graph...")

        # Create NetworkX graph
        G = nx.DiGraph()

        # Add nodes
        for idx, doc_id in enumerate(data.doc_ids):
            doc = documents[idx]
            G.add_node(doc_id, text=doc.get("text", "")[:500], embedding=data.x[idx].tolist())

        # Add edges
        num_edges = data.edge_index.shape[1]
        for i in range(num_edges):
            src_idx = data.edge_index[0, i].item()
            dst_idx = data.edge_index[1, i].item()
            edge_type = self.EDGE_TYPE_NAMES[data.edge_type[i].item()]
            weight = data.edge_attr[i, 0].item()

            src_id = data.doc_ids[src_idx]
            dst_id = data.doc_ids[dst_idx]

            G.add_edge(src_id, dst_id, type=edge_type, weight=weight)

        # Save
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        nx.write_graphml(G, path)
        log.info(f"Saved GraphML to {path}")

    def close(self):
        """Close Neo4j connection"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
            log.info("Neo4j connection closed")


# Task 3.1, 3.2, 3.3, 3.4 Complete
