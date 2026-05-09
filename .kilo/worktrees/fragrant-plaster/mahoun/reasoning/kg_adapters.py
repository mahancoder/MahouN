"""
Knowledge Graph Adapters
========================

Adapters to fetch graph-derived signals from external systems (e.g., Neo4j)
for use in the reasoning engine.
"""


from typing import Dict, List


class Neo4jKGAdapter:
    """
    Lightweight adapter over the Neo4j Python driver.

    Provides a simple `influence` signal based on outgoing relations
    (CITES, CO_CITATION, REFERS_TO) per node, normalized to [0,1].
    """

    def __init__(self, uri: str, user: str, password: str):
        try:
            from neo4j import GraphDatabase  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "neo4j driver is required. Install with: pip install neo4j"
            ) from e
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        try:
            self._driver.close()
        except Exception:
            pass

    def influence(self, evidences: List[Dict]) -> List[float]:
        ids = [e.get("doc_id", "") for e in evidences]
        if not ids:
            return []
        q = (
            "MATCH (e:Article) WHERE e.doc_id IN $ids "
            "OPTIONAL MATCH (e)-[r:CITES|CO_CITATION|REFERS_TO]->() "
            "RETURN e.doc_id AS id, count(r) AS deg"
        )
        with self._driver.session() as s:
            rows = s.run(q, ids=ids).data()
        m = {r["id"]: r["deg"] for r in rows}
        vals = [float(m.get(i, 0.0)) for i in ids]
        if not vals:
            return []
        lo, hi = min(vals), max(vals)
        return [(v - lo) / (hi - lo) if hi > lo else 0.0 for v in vals]

