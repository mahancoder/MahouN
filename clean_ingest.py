import ast

def clean_file(path):
    with open(path, 'r') as f:
        source = f.read()

    tree = ast.parse(source)
    nodes_to_keep = []
    
    # We want to remove:
    # 1. Assignment to _unified_loader
    # 2. Function get_unified_loader
    # 3. Any function that has @router.post("/submit"), @router.get("/jobs"), etc.
    # 4. Any function dealing with DLQ
    
    functions_to_remove = {
        'get_unified_loader',
        'submit_ingestion_job',
        'get_job_status',
        'list_jobs',
        'list_dlq_items',
        'get_dlq_item',
        'retry_dlq_item'
    }
    
    lines_to_exclude = set()

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '_unified_loader':
                    for i in range(node.lineno, node.end_lineno + 1):
                        lines_to_exclude.add(i)
        
        if isinstance(node, ast.AsyncFunctionDef) or isinstance(node, ast.FunctionDef):
            if node.name in functions_to_remove:
                # also exclude decorators
                start = node.lineno
                if node.decorator_list:
                    start = node.decorator_list[0].lineno
                for i in range(start, node.end_lineno + 1):
                    lines_to_exclude.add(i)

    # Let's rebuild the file
    lines = source.split('\n')
    new_lines = []
    for i, line in enumerate(lines, 1):
        if i not in lines_to_exclude:
            new_lines.append(line)
            
    # Remove some comments related to Phase 6
    final_lines = []
    skip = False
    for line in new_lines:
        if "# Phase 6: Async Job-Based Ingestion Endpoints" in line or "# Dead Letter Queue (DLQ) Endpoints" in line:
            continue
        final_lines.append(line)

    with open(path, 'w') as f:
        f.write('\n'.join(final_lines))

if __name__ == '__main__':
    clean_file('api/routers/ingest.py')
