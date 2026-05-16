import re

def clean_gqs(path):
    with open(path, 'r') as f:
        content = f.read()

    # 1. Remove execute_write method from Neo4jConnectionManager
    pattern_mgr = r'    def execute_write\([^)]+\)\s*->\s*List\[Dict\[str,\s*Any\]\]:.*?return session\.execute_write\(write_tx\)'
    content = re.sub(pattern_mgr, '', content, flags=re.DOTALL)

    # 2. Remove execute_write method from GraphQueryService
    pattern_srv = r'    def execute_write\([^)]+\)\s*->\s*List\[Dict\[str,\s*Any\]\]:.*?return self\._connection\.execute_write\(query,\s*params\)'
    content = re.sub(pattern_srv, '', content, flags=re.DOTALL)

    # 3. Replace batch_tx write session with governed transaction, or just remove use_transaction logic for batch_query
    # Since batch_query_async and batch_query were using execute_write, we can strip the transaction branch
    
    with open(path, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    clean_gqs('mahoun/graph/graph_query_service.py')
