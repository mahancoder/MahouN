"""
Graph-Vector Sync Service
=========================
Manages "Dual-Write" synchronization between Vector Store and Graph Database.

Responsibility:
1. When ingestion happens, embed document.
2. Write to ChromaDB (for fast global search).
3. Write to Neo4j Node (for context-aware graph traversal).
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio

from mahoun.pipelines.ingestion.enhanced_embedding import EnhancedEmbeddingService
from mahoun.pipelines.vector_store.manager import VectorStoreManager

logger = logging.getLogger(__name__)


class GraphVectorSync:
    """
    Synchronization service for Graph and Vector stores.

    Ensures that for every semantic chunk:
    - It exists in ChromaDB (with metadata)
    - If it corresponds to a Graph Node (Verdict/Article), the vector is injected there too.
    """

    def __init__(
        self, neo4j_driver=None, vector_manager: Optional[VectorStoreManager] = None
    ):
        self.neo4j = neo4j_driver
        self.vector_manager = vector_manager or VectorStoreManager()
        self.embedding_service = EnhancedEmbeddingService(backend="auto")

        logger.info("GraphVectorSync initialized")

    async def sync_document(
        self,
        doc_id: str,
        text: str,
        node_label: str = "Document",
        metadata: Dict[str, Any] = None,
    ):
        """
        Embed and sync a single document to both stores.
        """
        try:
            # 1. Generate Embedding (GGUF)
            # Returns list of floats directly
            embedding = self.embedding_service.embed_texts([text])[0]

            # 2. Write to ChromaDB
            self.vector_manager.add_documents(
                documents=[text],
                metadatas=[metadata or {}],
                ids=[doc_id],
                embeddings=[embedding],
            )
            logger.info(f" synced to ChromaDB: {doc_id}")

            # 3. Write to Neo4j (if driver available)
            if self.neo4j:
                await self._inject_neo4j_embedding(doc_id, node_label, embedding)

        except Exception as e:
            logger.error(f"Sync failed for {doc_id}: {e}")
            raise e

    async def _inject_neo4j_embedding(
        self, doc_id: str, label: str, embedding: List[float]
    ):
        """Inject embedding vector into specific Neo4j node."""
        query = f"""
        MATCH (n:{label} {{id: $doc_id}})
        SET n.embedding = $embedding
        RETURN count(n) as updated
        """

        # Use existing Neo4j session/driver mechanism
        # Assuming self.neo4j is a driver or session wrapper
        try:
            with self.neo4j.session() as session:
                result = session.run(query, doc_id=doc_id, embedding=embedding)
                record = result.single()
                if record and record["updated"] > 0:
                    logger.info(
                        f"✅ Injected vector into Neo4j node ({label}: {doc_id})"
                    )
                else:
                    logger.warning(
                        f"⚠️ Node not found in Neo4j ({label}: {doc_id}) - Vector orphan created"
                    )
        except Exception as e:
            logger.error(f"Neo4j vector injection failed: {e}")
            # We don't raise here to allow partial success (ChromaDB ok)

    async def backfill_graph_vectors(self, label: str = "Verdict"):
        """
        Scan all nodes of a label, generate embeddings, and update them.
        Useful for migration.
        """
        if not self.neo4j:
            logger.error("No Neo4j driver available for backfill")
            return

        fetch_query = f"MATCH (n:{label}) WHERE n.content IS NOT NULL AND n.embedding IS NULL RETURN n.id as id, n.content as content"

        with self.neo4j.session() as session:
            result = session.run(fetch_query)
            nodes = [record for record in result]

        logger.info(f"Found {len(nodes)} {label} nodes needing embedding backfill")

        for record in nodes:
            await self.sync_document(
                doc_id=record["id"], text=record["content"], node_label=label
            )

        logger.info(f"Backfill complete for {label}")
