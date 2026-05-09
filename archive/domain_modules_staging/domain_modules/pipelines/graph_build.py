# pipelines/graph_build.py
import os, argparse, json
from dotenv import load_dotenv
from neo4j import GraphDatabase
from tqdm import tqdm
from ._logging import setup_logger

log = setup_logger("graph")
load_dotenv()

SCHEMA = [
    "CREATE CONSTRAINT case_id IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT law_name IF NOT EXISTS FOR (l:Law) REQUIRE l.name IS UNIQUE",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True)
    ap.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    ap.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    ap.add_argument("--password", default=os.getenv("NEO4J_PASSWORD", "neo4j_password"))
    ap.add_argument("--database", default=os.getenv("NEO4J_DB", "neo4j"))
    ap.add_argument("--wandb", action="store_true", help="Enable W&B logging")
    args = ap.parse_args()

    # W&B init
    if args.wandb:
        import wandb

        wandb.init(project=os.getenv("WANDB_PROJECT", "mahoun"), name="graph_build", reinit=True)
        wandb.config.update({"neo4j_uri": args.uri, "database": args.database})

    drv = GraphDatabase.driver(args.uri, auth=(args.user, args.password))

    total_nodes = 0
    total_edges = 0

    with drv.session(database=args.database) as s:
        for stmt in SCHEMA:
            s.run(stmt)
        for line in tqdm(open(args.jsonl, "r", encoding="utf-8"), desc="neo4j"):
            rec = json.loads(line)
            s.run(
                "MERGE (c:Case {id:$id}) SET c.source=$src, c.category=$cat",
                id=rec["id"],
                src=rec["source"],
                cat=rec.get("meta", {}).get("category", ""),
            )
            total_nodes += 1

            for ref in rec.get("meta", {}).get("law_refs", []):
                s.run("MERGE (l:Law {name:$n})", n=ref)
                s.run(
                    "MATCH (c:Case {id:$cid}),(l:Law {name:$n}) MERGE (c)-[:CITES]->(l)",
                    cid=rec["id"],
                    n=ref,
                )
                total_edges += 1

    log.info(f"Graph build complete: {total_nodes} nodes, {total_edges} edges.")

    if args.wandb:
        wandb.log({"total_nodes": total_nodes, "total_edges": total_edges, "status": "completed"})
        wandb.finish()


if __name__ == "__main__":
    main()
