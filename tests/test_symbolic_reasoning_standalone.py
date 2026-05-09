#!/usr/bin/env python3
"""
Standalone Symbolic Reasoning Tests
====================================

Direct tests without pytest to avoid import issues.
"""
import sys
import time
from pathlib import Path

# Add mahoun to path
sys.path.insert(0, str(Path(__file__).parent))

from mahoun.reasoning.first_order_logic import (
    FirstOrderLogicEngine,
    Term,
    TermType,
    UnificationError,
    create_atom,
    create_constant,
    create_fact,
    create_function,
    create_rule,
    create_variable,
)
from mahoun.reasoning.forward_chaining import ForwardChainingEngine
from mahoun.reasoning.backward_chaining import BackwardChainingEngine
from mahoun.reasoning.symbolic_reasoner import SymbolicReasoningEngine, ReasoningMode


def test_1_unification_occur_check():
    """TEST 1: Occur check prevents infinite structures"""
    print("\n" + "="*60)
    print("TEST 1: Unification Occur Check")
    print("="*60)
    
    engine = FirstOrderLogicEngine()
    X = create_variable("X")
    f_X = create_function("f", X)
    
    try:
        engine.unify(X, f_X)
        print("❌ FAILED: Occur check should have prevented X = f(X)")
        return False
    except UnificationError as e:
        if "Occur check failed" in str(e):
            print("✅ PASSED: Occur check correctly prevented infinite structure")
            return True
        else:
            print(f"❌ FAILED: Wrong error: {e}")
            return False


def test_2_forward_chaining_transitive_closure():
    """TEST 2: Forward chaining derives all facts in transitive closure"""
    print("\n" + "="*60)
    print("TEST 2: Forward Chaining Transitive Closure")
    print("="*60)
    
    engine = ForwardChainingEngine()
    
    # Facts: parent(a,b), parent(b,c), parent(c,d)
    facts = [
        create_fact("parent", create_constant("a"), create_constant("b")),
        create_fact("parent", create_constant("b"), create_constant("c")),
        create_fact("parent", create_constant("c"), create_constant("d")),
    ]
    
    # Rules for transitive closure
    X = create_variable("X")
    Y = create_variable("Y")
    Z = create_variable("Z")
    
    rules = [
        create_rule(
            create_atom("ancestor", X, Y),
            create_atom("parent", X, Y)
        ),
        create_rule(
            create_atom("ancestor", X, Z),
            create_atom("parent", X, Y),
            create_atom("ancestor", Y, Z)
        ),
    ]
    
    result = engine.infer(facts, rules)
    
    # Expected: 6 ancestor facts
    expected = {
        create_atom("ancestor", create_constant("a"), create_constant("b")),
        create_atom("ancestor", create_constant("b"), create_constant("c")),
        create_atom("ancestor", create_constant("c"), create_constant("d")),
        create_atom("ancestor", create_constant("a"), create_constant("c")),
        create_atom("ancestor", create_constant("b"), create_constant("d")),
        create_atom("ancestor", create_constant("a"), create_constant("d")),
    }
    
    if expected.issubset(result.derived_facts):
        print(f"✅ PASSED: Derived all {len(expected)} expected ancestor facts")
        print(f"   Total facts: {len(result.derived_facts)}")
        print(f"   Iterations: {result.iterations}")
        return True
    else:
        missing = expected - result.derived_facts
        print(f"❌ FAILED: Missing facts: {missing}")
        return False


def test_3_backward_chaining_soundness():
    """TEST 3: Backward chaining only proves valid conclusions"""
    print("\n" + "="*60)
    print("TEST 3: Backward Chaining Soundness")
    print("="*60)
    
    engine = BackwardChainingEngine()
    
    facts = [
        create_fact("parent", create_constant("john"), create_constant("mary")),
    ]
    
    X = create_variable("X")
    Y = create_variable("Y")
    
    rules = [
        create_rule(
            create_atom("ancestor", X, Y),
            create_atom("parent", X, Y)
        ),
    ]
    
    # Valid goal
    valid_goal = create_atom("ancestor", create_constant("john"), create_constant("mary"))
    result_valid = engine.prove(valid_goal, facts, rules)
    
    # Invalid goal
    invalid_goal = create_atom("ancestor", create_constant("mary"), create_constant("john"))
    result_invalid = engine.prove(invalid_goal, facts, rules)
    
    if result_valid.success and not result_invalid.success:
        print("✅ PASSED: Valid goal proved, invalid goal rejected")
        print(f"   Valid solutions: {len(result_valid.solutions)}")
        return True
    else:
        print(f"❌ FAILED: Valid={result_valid.success}, Invalid={result_invalid.success}")
        return False


def test_4_cycle_detection():
    """TEST 4: Cycle detection prevents infinite loops"""
    print("\n" + "="*60)
    print("TEST 4: Cycle Detection")
    print("="*60)
    
    engine = BackwardChainingEngine(max_depth=10)
    
    facts = []
    X = create_variable("X")
    
    # Self-referential rule: p(X) :- p(X)
    rules = [
        create_rule(
            create_atom("p", X),
            create_atom("p", X)
        ),
    ]
    
    goal = create_atom("p", create_constant("a"))
    
    start = time.time()
    result = engine.prove(goal, facts, rules)
    elapsed = time.time() - start
    
    if not result.success and elapsed < 1.0:
        print(f"✅ PASSED: Cycle detected and terminated in {elapsed:.3f}s")
        print(f"   Max depth reached: {result.statistics['max_depth_reached']}")
        return True
    else:
        print(f"❌ FAILED: Success={result.success}, Time={elapsed:.3f}s")
        return False


def test_5_hybrid_reasoning():
    """TEST 5: Hybrid reasoning combines forward and backward"""
    print("\n" + "="*60)
    print("TEST 5: Hybrid Reasoning")
    print("="*60)
    
    engine = SymbolicReasoningEngine()
    
    # Facts
    engine.add_fact(create_fact("parent", create_constant("a"), create_constant("b")))
    engine.add_fact(create_fact("parent", create_constant("b"), create_constant("c")))
    
    # Rules
    X = create_variable("X")
    Y = create_variable("Y")
    Z = create_variable("Z")
    
    engine.add_rule(create_rule(
        create_atom("ancestor", X, Y),
        create_atom("parent", X, Y)
    ))
    
    engine.add_rule(create_rule(
        create_atom("ancestor", X, Z),
        create_atom("parent", X, Y),
        create_atom("ancestor", Y, Z)
    ))
    
    # Goal: ancestor(a, c)
    goal = create_atom("ancestor", create_constant("a"), create_constant("c"))
    
    result = engine.query(goal, mode=ReasoningMode.HYBRID)
    
    if result.success and result.mode == ReasoningMode.HYBRID:
        print("✅ PASSED: Hybrid reasoning succeeded")
        print(f"   Forward facts: {len(result.forward_result.derived_facts) if result.forward_result else 0}")
        print(f"   Backward solutions: {len(result.backward_result.solutions) if result.backward_result else 0}")
        return True
    else:
        print(f"❌ FAILED: Success={result.success}, Mode={result.mode}")
        return False


def test_6_determinism():
    """TEST 6: Forward chaining is deterministic"""
    print("\n" + "="*60)
    print("TEST 6: Determinism")
    print("="*60)
    
    engine = ForwardChainingEngine()
    
    facts = [
        create_fact("p", create_constant("a")),
        create_fact("q", create_constant("b")),
    ]
    
    X = create_variable("X")
    Y = create_variable("Y")
    
    rules = [
        create_rule(create_atom("r", X), create_atom("p", X)),
        create_rule(create_atom("s", X, Y), create_atom("p", X), create_atom("q", Y)),
    ]
    
    # Run 5 times
    results = [engine.infer(facts, rules) for _ in range(5)]
    
    # Check all results are identical
    first_facts = results[0].derived_facts
    all_same = all(r.derived_facts == first_facts for r in results[1:])
    
    if all_same:
        print("✅ PASSED: All 5 runs produced identical results")
        print(f"   Derived facts: {len(first_facts)}")
        return True
    else:
        print("❌ FAILED: Non-deterministic results")
        return False


def test_7_performance_large_kb():
    """TEST 7: Performance with large knowledge base"""
    print("\n" + "="*60)
    print("TEST 7: Performance (Large KB)")
    print("="*60)
    
    engine = ForwardChainingEngine(max_iterations=10000)
    
    # Chain of 50 nodes
    n = 50
    facts = [
        create_fact("edge", create_constant(f"n{i}"), create_constant(f"n{i+1}"))
        for i in range(n)
    ]
    
    X = create_variable("X")
    Y = create_variable("Y")
    Z = create_variable("Z")
    
    rules = [
        create_rule(
            create_atom("path", X, Y),
            create_atom("edge", X, Y)
        ),
        create_rule(
            create_atom("path", X, Z),
            create_atom("edge", X, Y),
            create_atom("path", Y, Z)
        ),
    ]
    
    start = time.time()
    result = engine.infer(facts, rules)
    elapsed = time.time() - start
    
    expected_paths = n * (n + 1) // 2
    
    if len(result.derived_facts) >= expected_paths and elapsed < 5.0:
        print(f"✅ PASSED: {len(result.derived_facts)} facts in {elapsed:.3f}s")
        print(f"   Expected: {expected_paths}, Iterations: {result.iterations}")
        return True
    else:
        print(f"❌ FAILED: Facts={len(result.derived_facts)}, Time={elapsed:.3f}s")
        return False


def test_8_proof_auditability():
    """TEST 8: Proof hashes are deterministic and unique"""
    print("\n" + "="*60)
    print("TEST 8: Proof Auditability")
    print("="*60)
    
    engine = FirstOrderLogicEngine()
    
    clause1 = create_fact("p", create_constant("a"))
    clause2 = create_fact("p", create_constant("b"))
    subst = {}
    
    # Same clause should produce same hash
    hashes1 = [engine.compute_proof_hash(clause1, subst) for _ in range(5)]
    deterministic = len(set(hashes1)) == 1
    
    # Different clauses should produce different hashes
    hash1 = engine.compute_proof_hash(clause1, subst)
    hash2 = engine.compute_proof_hash(clause2, subst)
    unique = hash1 != hash2
    
    # Hash should be SHA-256 (64 hex chars)
    valid_format = len(hash1) == 64 and all(c in "0123456789abcdef" for c in hash1)
    
    if deterministic and unique and valid_format:
        print("✅ PASSED: Proof hashes are deterministic, unique, and SHA-256")
        print(f"   Sample hash: {hash1[:16]}...")
        return True
    else:
        print(f"❌ FAILED: Deterministic={deterministic}, Unique={unique}, Format={valid_format}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("SYMBOLIC REASONING ENGINE - HARD TESTS")
    print("="*70)
    
    tests = [
        test_1_unification_occur_check,
        test_2_forward_chaining_transitive_closure,
        test_3_backward_chaining_soundness,
        test_4_cycle_detection,
        test_5_hybrid_reasoning,
        test_6_determinism,
        test_7_performance_large_kb,
        test_8_proof_auditability,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
