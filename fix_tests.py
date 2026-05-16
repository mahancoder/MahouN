import re

def fix_tests(path):
    with open(path, 'r') as f:
        content = f.read()

    # Fix test_mutation_outside_context_raises
    content = content.replace('_authorized_write_ctx.active = False', '_authorized_write_ctx.set(False)')
    
    # Fix test_mutation_inside_auth_context_passes
    content = content.replace('_authorized_write_ctx.active = True', 'token = _authorized_write_ctx.set(True)')
    content = content.replace('_authorized_write_ctx.active = False', '_authorized_write_ctx.reset(token)')
    
    # Fix getattr(_authorized_write_ctx, "active", False)
    content = content.replace('getattr(_authorized_write_ctx, "active", False)', '_authorized_write_ctx.get()')

    with open(path, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    fix_tests('tests/test_mutation_boundary.py')
