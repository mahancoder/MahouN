#!/usr/bin/env python3
"""
switchboard_validation.py
Utility to verify that all registered modules in the Switchboard are actually loadable
and conform to expected interfaces.
"""

import sys
from mahoun.switchboard import switchboard

def validate_module(module_key, expected_methods=None):
    """Validate a single module registration."""
    if module_key not in switchboard._registry:
        print(f"[FAIL] {module_key}: Not registered in switchboard")
        return False
    
    info = switchboard._registry[module_key]
    try:
        instance = switchboard.get_module(module_key)
    except Exception as e:
        print(f"[FAIL] {module_key}: Failed to load - {e}")
        return False
    
    if expected_methods:
        missing = [m for m in expected_methods if not hasattr(instance, m)]
        if missing:
            print(f"[FAIL] {module_key}: Missing methods {missing}")
            return False
    
    print(f"[PASS] {module_key}: Loaded successfully (mode: {info['mode']})")
    return True

def main():
    # Define expected methods for critical modules
    expected_methods = {
        "legal_pipeline": ["process_document"],
        "bias_analyzer": ["analyze_dataset"],
        "smart_cache": ["get", "set"],
        "persian_legal_nlp": ["process"],
        "ultra_bandit_system": ["select_arm", "update"],
        "ultra_graph_query_service": ["execute_query"]
    }
    
    all_passed = True
    for module_key in switchboard._registry:
        methods = expected_methods.get(module_key, [])
        if not validate_module(module_key, methods):
            all_passed = False
    
    if all_passed:
        print("\n[SUCCESS] All modules are testable and interface-compliant.")
        sys.exit(0)
    else:
        print("\n[FAILURE] Some modules failed validation.")
        sys.exit(1)

if __name__ == "__main__":
    main()