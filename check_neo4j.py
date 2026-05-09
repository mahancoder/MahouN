
import os
import sys

WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_ROOT not in sys.path:
    sys.path.append(WORKSPACE_ROOT)

if not os.getenv("NEO4J_PASSWORD"):
    os.environ["NEO4J_PASSWORD"] = os.getenv("DB_NEO4J_PASSWORD", "dev_password_change_me")

from mahoun.graph.neo4j.connection import get_connection

try:
    conn = get_connection()
    print(f"Connection Object: {conn}")
    print(f"Verifying connection...")
    success = conn.verify_connection()
    print(f"Success: {success}")
except Exception as e:
    print(f"Error: {e}")
