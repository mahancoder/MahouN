import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging
import re

logger = logging.getLogger(__name__)


class GraphReranker(nn.Module):
    """
    Graph-based reranker for RAG systems using GNNs.
    Implements a lightweight GNN for re-ranking retrieved documents based on their relationships.
    """

    def __init__(
        self, input_dim: int = 384, hidden_dim: int = 256, output_dim: int = 1, num_layers: int = 2
    ):
        """
        Initialize the Graph Reranker.

        Args:
            input_dim: Dimension of input embeddings
            hidden_dim: Dimension of hidden layers
            output_dim: Output dimension (typically 1 for ranking score)
            num_layers: Number of GNN layers
        """
        super(GraphReranker, self).__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_layers = num_layers

        # GNN layers
        self.gnn_layers = nn.ModuleList()
        self.gnn_layers.append(nn.Linear(input_dim, hidden_dim))

        for _ in range(num_layers - 1):
            self.gnn_layers.append(nn.Linear(hidden_dim, hidden_dim))

        # Output layer to compute ranking scores
        self.output_layer = nn.Linear(hidden_dim, output_dim)

        # Activation function
        self.activation = nn.ReLU()

    def create_similarity_graph(
        self, embeddings: np.ndarray, threshold: float = 0.5
    ) -> torch.Tensor:
        """
        Create a similarity graph from embeddings.

        Args:
            embeddings: Document embeddings (num_docs x embedding_dim)
            threshold: Similarity threshold for creating edges

        Returns:
            Adjacency matrix as a torch tensor
        """
        # Calculate cosine similarity matrix
        sim_matrix = cosine_similarity(embeddings)

        # Apply threshold to create adjacency matrix
        adj_matrix = (sim_matrix >= threshold).astype(np.float32)

        # Remove self-loops
        np.fill_diagonal(adj_matrix, 0)

        return torch.tensor(adj_matrix, dtype=torch.float32)

    def create_citation_graph(self, documents: List[Dict]) -> torch.Tensor:
        """
        Create a citation graph based on explicit references in legal documents.

        Args:
            documents: List of documents

        Returns:
            Adjacency matrix representing citation relationships
        """
        docs = [doc.get("text", str(doc)) for doc in documents]
        n_docs = len(docs)

        # Initialize adjacency matrix
        adj_matrix = np.zeros((n_docs, n_docs), dtype=np.float32)

        # Pattern to match legal citations (e.g., "article 123", "law 456", etc.)
        citation_patterns = [
            r"ماده\s+(\d+)",  # "article" in Persian
            r"حکم\s+شماره\s+(\d+)",  # "ruling number"
            r"دادنامه\s+شماره\s+(\d+)",  # "judgment number"
            r"ر\.?\s*\d+",  # "r." followed by number
        ]

        for i, doc_i in enumerate(docs):
            for j, doc_j in enumerate(docs):
                if i != j:
                    # Check if doc_i cites doc_j based on shared legal references
                    for pattern in citation_patterns:
                        matches_i = re.findall(pattern, doc_i, re.IGNORECASE)
                        matches_j = re.findall(pattern, doc_j, re.IGNORECASE)

                        # If both documents reference the same legal article/ruling, create an edge
                        if set(matches_i) & set(matches_j):
                            adj_matrix[i][j] = 1.0
                            break

        return torch.tensor(adj_matrix, dtype=torch.float32)

    def forward(self, embeddings: torch.Tensor, adj_matrix: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the GNN.

        Args:
            embeddings: Node embeddings (num_nodes x embedding_dim)
            adj_matrix: Adjacency matrix (num_nodes x num_nodes)

        Returns:
            Ranking scores for each node (num_nodes x 1)
        """
        # Add self loops to adjacency matrix
        adj_matrix = adj_matrix + torch.eye(
            adj_matrix.size(0), dtype=adj_matrix.dtype, device=adj_matrix.device
        )

        # Normalize adjacency matrix using symmetric normalization (GCN-style)
        rowsum = adj_matrix.sum(dim=1)
        d_inv_sqrt = torch.diag(torch.pow(rowsum, -0.5))
        adj_norm = torch.mm(torch.mm(d_inv_sqrt, adj_matrix), d_inv_sqrt)

        # Apply GNN layers with message passing
        h = embeddings
        for i, layer in enumerate(self.gnn_layers):
            h = layer(h)
            # Apply graph convolution
            h = torch.mm(adj_norm, h)
            h = self.activation(h)

        # Output layer to get ranking scores
        scores = self.output_layer(h)

        return torch.sigmoid(scores)  # Return scores between 0 and 1

    def rerank(
        self,
        query: str,
        retrieved_docs: List[Dict],
        embeddings: np.ndarray,
        method: str = "similarity",
        threshold: float = 0.5,
    ) -> List[Dict]:
        """
        Rerank documents using the GNN-based reranker.

        Args:
            query: User query
            retrieved_docs: Retrieved documents
            embeddings: Document embeddings
            method: Method to create graph ("similarity", "citation", or "combined")
            threshold: Similarity threshold for graph creation

        Returns:
            Reranked list of documents
        """
        if len(retrieved_docs) <= 1:
            return retrieved_docs

        # Convert embeddings to tensor
        embeddings_tensor = torch.tensor(embeddings, dtype=torch.float32)

        # Create graph based on selected method
        if method == "similarity":
            adj_matrix = self.create_similarity_graph(embeddings, threshold)
        elif method == "citation":
            adj_matrix = self.create_citation_graph(retrieved_docs)
        elif method == "combined":
            sim_adj = self.create_similarity_graph(embeddings, threshold)
            cit_adj = self.create_citation_graph(retrieved_docs)
            adj_matrix = torch.max(sim_adj, cit_adj)  # Combine both
        else:
            raise ValueError(
                f"Unknown method: {method}. Use 'similarity', 'citation', or 'combined'"
            )

        # Get ranking scores using GNN
        scores = self.forward(embeddings_tensor, adj_matrix)

        # Sort documents by their scores in descending order
        sorted_indices = torch.argsort(scores, dim=0, descending=True).squeeze().tolist()

        # Handle case where there's only one document
        if not isinstance(sorted_indices, list):
            sorted_indices = [sorted_indices]

        reranked_docs = [retrieved_docs[i] for i in sorted_indices]

        return reranked_docs


# Example usage and testing function
def test_graph_reranker():
    # Create dummy data for testing
    num_docs = 5
    embedding_dim = 384

    # Dummy embeddings
    embeddings = np.random.rand(num_docs, embedding_dim).astype(np.float32)

    # Dummy documents
    documents = []
    for i in range(num_docs):
        doc = {
            "id": i,
            "title": f"Document {i}",
            "text": f"This is document {i} with some legal content. Article 123, ruling 456 mentioned here.",
            "full_doc": {},
        }
        documents.append(doc)

    # Initialize reranker
    reranker = GraphReranker(input_dim=embedding_dim)

    # Test reranking
    query = "legal ruling about article 123"
    reranked_docs = reranker.rerank(query, documents, embeddings, method="combined")

    print("Original order:")
    for i, doc in enumerate(documents):
        print(f"  {i}: {doc['title']}")

    print("\nReranked order:")
    for i, doc in enumerate(reranked_docs):
        print(f"  {i}: {doc['title']}")

    return reranked_docs


if __name__ == "__main__":
    test_graph_reranker()
