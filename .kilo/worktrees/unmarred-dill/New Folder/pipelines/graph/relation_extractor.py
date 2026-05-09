import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import List, Dict, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class RelationExtractor(nn.Module):
    """
    Relation extraction component using GNNs to identify and classify relationships
    between legal entities in documents.
    """

    def __init__(self, input_dim: int = 384, hidden_dim: int = 256, num_relations: int = 5):
        """
        Initialize the Relation Extractor.

        Args:
            input_dim: Dimension of input embeddings
            hidden_dim: Dimension of hidden layers
            num_relations: Number of relation types to classify
        """
        super(RelationExtractor, self).__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_relations = num_relations

        # GNN layers for relation extraction
        self.gnn_layer = nn.Linear(input_dim, hidden_dim)

        # Edge classifier to determine relation types
        self.edge_classifier = nn.Linear(hidden_dim * 2, num_relations)

        # Activation functions
        self.activation = nn.ReLU()

    def extract_entities(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Extract legal entities from text using regex patterns.

        Args:
            text: Input text

        Returns:
            List of entities with their type, value, and position (value, type, start, end)
        """
        entities = []

        # Pattern for legal articles (e.g., "article 123", "law 456")
        article_pattern = r"(ماده|حکم|دادنامه|ر\.?)\s*(\d+)"
        matches = re.finditer(article_pattern, text, re.IGNORECASE)
        for match in matches:
            entity_type = "LEGAL_ARTICLE"
            entity_value = f"{match.group(1)} {match.group(2)}"
            start_pos = match.start()
            end_pos = match.end()
            entities.append((entity_value, entity_type, start_pos, end_pos))

        # Pattern for legal entities (e.g., "court", "plaintiff", "defendant")
        legal_entities_pattern = r"(دادگاه|خواهان|خوانده|وکیل|رئیس شعبه| مستشار)"
        matches = re.finditer(legal_entities_pattern, text, re.IGNORECASE)
        for match in matches:
            entity_type = "LEGAL_ENTITY"
            entity_value = match.group(0)
            start_pos = match.start()
            end_pos = match.end()
            entities.append((entity_value, entity_type, start_pos, end_pos))

        return entities

    def create_entity_dependency_graph(
        self, text: str, entities: List[Tuple[str, str, int, int]]
    ) -> torch.Tensor:
        """
        Create a dependency graph based on entity relationships in text.

        Args:
            text: Input text
            entities: List of extracted entities

        Returns:
            Adjacency matrix representing entity relationships
        """
        n_entities = len(entities)
        adj_matrix = torch.zeros((n_entities, n_entities), dtype=torch.float32)

        # Create edges between entities that appear in the same sentence
        sentences = re.split(r"[.!?؟]+", text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Find entities in this sentence
            entity_indices_in_sentence = []
            for i, (entity_val, entity_type, start, end) in enumerate(entities):
                if entity_val in sentence:
                    entity_indices_in_sentence.append(i)

            # Create edges between all pairs of entities in the same sentence
            for i in entity_indices_in_sentence:
                for j in entity_indices_in_sentence:
                    if i != j:
                        adj_matrix[i, j] = 1.0

        return adj_matrix

    def forward(self, entity_embeddings: torch.Tensor, adj_matrix: torch.Tensor) -> torch.Tensor:
        """
        Forward pass to extract relations.

        Args:
            entity_embeddings: Entity embeddings (num_entities x embedding_dim)
            adj_matrix: Adjacency matrix (num_entities x num_entities)

        Returns:
            Relation probabilities (num_entities x num_entities x num_relations)
        """
        # Process entity embeddings through GNN layer
        h = self.activation(self.gnn_layer(entity_embeddings))

        # Compute relations between all pairs of entities
        # This is done by concatenating embeddings of entity pairs
        num_entities = h.size(0)

        # Create all entity pairs
        relations = []
        for i in range(num_entities):
            for j in range(num_entities):
                if i != j:
                    # Concatenate embeddings of entity i and entity j
                    pair_embedding = torch.cat([h[i], h[j]], dim=-1)
                    relation_score = self.edge_classifier(pair_embedding)
                    relations.append(relation_score)

        # Reshape to (num_entities, num_entities, num_relations)
        if relations:
            relations_tensor = torch.stack(relations, dim=0)
            relations_tensor = relations_tensor.view(num_entities, num_entities, -1)
        else:
            relations_tensor = torch.zeros(
                (num_entities, num_entities, self.num_relations),
                dtype=entity_embeddings.dtype,
                device=entity_embeddings.device,
            )

        return F.softmax(relations_tensor, dim=-1)  # Apply softmax to get probabilities

    def extract_relations(self, text: str, entity_embeddings: np.ndarray) -> List[Dict]:
        """
        Extract relations from text.

        Args:
            text: Input text
            entity_embeddings: Entity embeddings

        Returns:
            List of relations in the format {'entity1': ..., 'entity2': ..., 'relation': ..., 'confidence': ...}
        """
        # Extract entities
        entities = self.extract_entities(text)

        if not entities or len(entities) < 2:
            return []  # Need at least 2 entities to form a relation

        # Convert entity embeddings to tensor
        entity_embeddings_tensor = torch.tensor(
            entity_embeddings[: len(entities)], dtype=torch.float32
        )

        # Create dependency graph
        adj_matrix = self.create_entity_dependency_graph(text, entities)

        # Extract relations using GNN
        relation_probs = self.forward(entity_embeddings_tensor, adj_matrix)

        # Convert results to readable format
        relations = []
        for i in range(len(entities)):
            for j in range(len(entities)):
                if i != j:
                    # Get the relation with highest probability
                    relation_scores = relation_probs[i, j]
                    relation_type_idx = torch.argmax(relation_scores).item()
                    confidence = relation_scores[relation_type_idx].item()

                    if confidence > 0.1:  # Only include relations with confidence > 0.1
                        relation_name = self.get_relation_name(relation_type_idx)
                        relations.append(
                            {
                                "entity1": entities[i][0],
                                "entity2": entities[j][0],
                                "relation": relation_name,
                                "confidence": confidence,
                            }
                        )

        # Sort by confidence
        relations.sort(key=lambda x: x["confidence"], reverse=True)
        return relations

    def get_relation_name(self, relation_idx: int) -> str:
        """
        Get relation name based on index.

        Args:
            relation_idx: Index of the relation type

        Returns:
            Name of the relation type
        """
        relation_names = ["REFERENCES", "CITES", "MODIFIES", "IMPLEMENTS", "RELATED_TO"]

        if relation_idx < len(relation_names):
            return relation_names[relation_idx]
        else:
            return f"RELATION_TYPE_{relation_idx}"


# Example usage and testing function
def test_relation_extractor():
    # Sample legal text
    legal_text = """
    دادگاه بدوی در خصوص دعوی آقایان ( ج.ط.) و (الف. ط.) به وکالت از آقای (د. م.) فرزند (ح.) 
    ساکن تهران، به طرفیت آقای (ح. م.) فرزند (ح.) و (ش. ب.) که بعداً آقای (ن. ع.) و خانم (الف. م.) 
    از جانب خوانده ردیف اول اعلام وکالت نموده به خواسته اثبات عقد هبه خواهان با خوانده ردیف اول در سال 1381
    """

    # Create dummy entity embeddings
    entities = [
        ("دادگاه بدوی", "LEGAL_ENTITY", 0, 10),
        ("ماده 1381", "LEGAL_ARTICLE", 150, 160),
        ("عقد هبه", "LEGAL_CONCEPT", 130, 140),
    ]

    entity_embeddings = np.random.rand(len(entities), 384).astype(np.float32)

    # Initialize extractor
    extractor = RelationExtractor(input_dim=384, num_relations=5)

    # Extract relations
    relations = extractor.extract_relations(legal_text, entity_embeddings)

    print("Extracted relations:")
    for relation in relations:
        print(
            f"  {relation['entity1']} --{relation['relation']}--> {relation['entity2']} "
            f"(confidence: {relation['confidence']:.3f})"
        )

    return relations


if __name__ == "__main__":
    test_relation_extractor()
