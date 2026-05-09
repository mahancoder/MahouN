#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from mahoun.reasoning import first_order_logic as fol
from mahoun.reasoning import backward_chaining as bc

bc_engine = bc.BackwardChainingEngine(find_all=True)

facts = [
    fol.create_fact("parent", fol.create_constant("john"), fol.create_constant("mary")),
    fol.create_fact("parent", fol.create_constant("john"), fol.create_constant("bob")),
]

X = fol.create_variable("X")
Y = fol.create_variable("Y")

rules = [
    fol.create_rule(
        fol.create_atom("ancestor", X, Y),
        fol.create_atom("parent", X, Y)
    ),
]

# Query: ancestor(john, X)
goal = fol.create_atom("ancestor", fol.create_constant("john"), X)

print(f"Goal: {goal}")
print(f"Facts: {[str(f) for f in facts]}")
print(f"Rules: {[str(r) for r in rules]}")
print(f"find_all: {bc_engine.find_all}")

result = bc_engine.prove(goal, facts, rules)

print(f"\nSuccess: {result.success}")
print(f"Solutions: {len(result.solutions)}")
for i, sol in enumerate(result.solutions):
    print(f"  Solution {i+1}: {sol}")
    if X in sol:
        print(f"    X -> {sol[X]}")
