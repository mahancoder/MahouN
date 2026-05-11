"""
Rete Algorithm Implementation
==============================

High-performance pattern matching algorithm for production systems.

The Rete algorithm provides O(1) amortized time for rule matching by:
1. Building a discrimination network
2. Caching partial matches
3. Incremental updates

Performance:
- Traditional: O(R × F × P) where R=rules, F=facts, P=patterns
- Rete: O(F) amortized after network construction

This is THE algorithm used in all high-performance rule engines:
- Drools
- CLIPS
- Jess
- OPS5

Author: MAHOUN Team
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import logging

from reasoning_logic.core import Fact, Rule, Atom, Term
from reasoning_logic.unification import UnificationEngine
from reasoning_logic.parser import FOLConverter, ParseError

logger = logging.getLogger(__name__)


@dataclass
class Token:
    """
    Token flowing through Rete network
    
    Represents a partial match of a rule
    """
    facts: Tuple[Fact, ...]
    bindings: Dict[str, Term]
    
    def __hash__(self):
        return hash((self.facts, tuple(sorted(self.bindings.items()))))


class ReteNode:
    """Base class for Rete network nodes"""
    
    def __init__(self):
        self.children: List['ReteNode'] = []
        self.parent: Optional['ReteNode'] = None
    
    def activate(self, token: Token):
        """Process token and propagate to children"""
        raise NotImplementedError
    
    def add_child(self, child: 'ReteNode'):
        """Add child node"""
        self.children.append(child)
        child.parent = self


class RootNode(ReteNode):
    """Root of Rete network"""
    
    def activate(self, token: Token):
        """Propagate to all children"""
        for child in self.children:
            child.activate(token)


class AlphaNode(ReteNode):
    """
    Alpha node: Tests single fact
    
    Performs constant tests on individual facts
    """
    
    def __init__(self, predicate: str, tests: Optional[List[Tuple[int, Any]]] = None):
        """
        Initialize alpha node
        
        Args:
            predicate: Predicate to match
            tests: List of (term_index, expected_value) tests
        """
        super().__init__()
        self.predicate = predicate
        self.tests = tests if tests is not None else []
        self.memory: Set[Fact] = set()
    
    def activate(self, token: Token):
        """Test fact and propagate if matches"""
        if not token.facts:
            return
        
        fact = token.facts[-1]
        
        # Check predicate
        if fact.predicate != self.predicate:
            return
        
        # Check constant tests
        for term_idx, expected_value in self.tests:
            if term_idx >= len(fact.terms):
                return
            term = fact.terms[term_idx]
            if term.is_constant() and term.name != expected_value:
                return
        
        # Store in memory
        self.memory.add(fact)
        
        # Propagate to children
        for child in self.children:
            child.activate(token)


class BetaNode(ReteNode):
    """
    Beta node: Joins two partial matches
    
    Performs variable consistency checks between facts
    """
    
    def __init__(self, join_tests: Optional[List[Tuple[int, int, int, int]]] = None):
        """
        Initialize beta node
        
        Args:
            join_tests: List of (left_fact_idx, left_term_idx, right_fact_idx, right_term_idx)
        """
        super().__init__()
        self.join_tests = join_tests if join_tests is not None else []
        self.left_memory: Set[Token] = set()
        self.right_memory: Set[Token] = set()
    
    def activate_left(self, token: Token):
        """Activate from left parent"""
        self.left_memory.add(token)
        
        # Try to join with right memory
        for right_token in self.right_memory:
            joined = self._try_join(token, right_token)
            if joined:
                for child in self.children:
                    child.activate(joined)
    
    def activate_right(self, token: Token):
        """Activate from right parent"""
        self.right_memory.add(token)
        
        # Try to join with left memory
        for left_token in self.left_memory:
            joined = self._try_join(left_token, token)
            if joined:
                for child in self.children:
                    child.activate(joined)
    
    def activate(self, token: Token):
        """Default activation (treat as left)"""
        self.activate_left(token)
    
    def _try_join(self, left: Token, right: Token) -> Optional[Token]:
        """
        Try to join two tokens
        
        Returns:
            Joined token or None if join fails
        """
        # Merge bindings
        merged_bindings = {**left.bindings, **right.bindings}
        
        # Check join tests
        for left_fact_idx, left_term_idx, right_fact_idx, right_term_idx in self.join_tests:
            if left_fact_idx >= len(left.facts) or right_fact_idx >= len(right.facts):
                return None
            
            left_fact = left.facts[left_fact_idx]
            right_fact = right.facts[right_fact_idx]
            
            if left_term_idx >= len(left_fact.terms) or right_term_idx >= len(right_fact.terms):
                return None
            
            left_term = left_fact.terms[left_term_idx]
            right_term = right_fact.terms[right_term_idx]
            
            # Try to unify
            unified = UnificationEngine.unify(left_term, right_term, merged_bindings.copy())
            if unified is None:
                return None
            
            merged_bindings = unified
        
        # Create joined token
        return Token(
            facts=left.facts + right.facts,
            bindings=merged_bindings
        )


class ProductionNode(ReteNode):
    """
    Production node: Fires rule when activated
    
    Terminal node that instantiates rule conclusions
    """
    
    def __init__(self, rule: Rule):
        """
        Initialize production node
        
        Args:
            rule: Rule to fire
        """
        super().__init__()
        self.rule = rule
        self.activations: List[Token] = []
    
    def activate(self, token: Token):
        """Fire rule with token bindings"""
        self.activations.append(token)


class ReteNetwork:
    """
    Rete discrimination network
    
    Builds and maintains the Rete network for efficient pattern matching
    """
    
    def __init__(self):
        """Initialize Rete network"""
        self.root = RootNode()
        
        # Indexes
        self.alpha_nodes: Dict[str, List[AlphaNode]] = defaultdict(list)
        self.production_nodes: List[ProductionNode] = []
        
        # Statistics
        self.stats = {
            'alpha_nodes': 0,
            'beta_nodes': 0,
            'production_nodes': 0,
            'network_depth': 0
        }
    
    def add_rule(self, rule: Rule):
        """
        Add rule to network
        
        Compiles rule into Rete network nodes
        
        Args:
            rule: Rule to add
        """
        if not rule.premise:
            # No premises - always fires
            production_node = ProductionNode(rule)
            self.root.add_child(production_node)
            self.production_nodes.append(production_node)
            self.stats['production_nodes'] += 1
            return
        
        # Build alpha network for each premise
        alpha_nodes = []
        for premise in rule.premise:
            alpha_node = self._get_or_create_alpha_node(premise)
            alpha_nodes.append(alpha_node)
        
        # Build beta network to join premises
        if len(alpha_nodes) == 1:
            # Single premise - connect directly to production
            current_node = alpha_nodes[0]
        else:
            # Multiple premises - build join network
            current_node = alpha_nodes[0]
            for alpha_node in alpha_nodes[1:]:
                beta_node = BetaNode()
                current_node.add_child(beta_node)
                alpha_node.add_child(beta_node)
                current_node = beta_node
                self.stats['beta_nodes'] += 1
        
        # Add production node
        production_node = ProductionNode(rule)
        current_node.add_child(production_node)
        self.production_nodes.append(production_node)
        self.stats['production_nodes'] += 1
    
    def _get_or_create_alpha_node(self, premise: Any) -> AlphaNode:
        """
        Get or create alpha node for premise
        
        Args:
            premise: Premise pattern
        
        Returns:
            Alpha node
        """
        # Extract predicate
        if hasattr(premise, 'predicate'):
            predicate = premise.predicate
        else:
            predicate = str(premise)
        
        # Extract constant tests
        tests = []
        if hasattr(premise, 'terms'):
            for i, term in enumerate(premise.terms):
                if term.is_constant():
                    tests.append((i, term.name))
        
        # Check if alpha node already exists
        for alpha_node in self.alpha_nodes[predicate]:
            if alpha_node.tests == tests:
                return alpha_node
        
        # Create new alpha node
        alpha_node = AlphaNode(predicate, tests)
        self.root.add_child(alpha_node)
        self.alpha_nodes[predicate].append(alpha_node)
        self.stats['alpha_nodes'] += 1
        
        return alpha_node
    
    def assert_fact(self, fact: Fact):
        """
        Assert fact into network
        
        Propagates fact through network, triggering rule activations
        
        Args:
            fact: Fact to assert
        """
        # Create token
        token = Token(facts=(fact,), bindings={})
        
        # Find matching alpha nodes
        for alpha_node in self.alpha_nodes.get(fact.predicate, []):
            alpha_node.activate(token)
    
    def get_activations(self) -> List[Tuple[Rule, Token]]:
        """
        Get all rule activations
        
        Returns:
            List of (rule, token) tuples
        """
        activations = []
        for production_node in self.production_nodes:
            for token in production_node.activations:
                activations.append((production_node.rule, token))
        return activations
    
    def clear_activations(self):
        """Clear all activations"""
        for production_node in self.production_nodes:
            production_node.activations.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get network statistics"""
        return self.stats.copy()
    
    def clear_memories(self):
        """
        Clear all node memories to free memory after fixpoint reached
        
        This should be called after forward chaining completes to prevent
        memory leaks in long-running systems.
        
        Warning: Calling this will invalidate any cached partial matches.
        Only call after reasoning is complete.
        """
        # Clear alpha node memories
        for alpha_nodes in self.alpha_nodes.values():
            for node in alpha_nodes:
                node.memory.clear()
        
        # Clear beta node memories recursively
        self._clear_beta_memories_recursive(self.root)
        
        # Clear production node activations
        for prod_node in self.production_nodes:
            prod_node.activations.clear()
        
        logger.debug("Rete network memories cleared")
    
    def _clear_beta_memories_recursive(self, node: ReteNode):
        """Recursively clear beta node memories"""
        if isinstance(node, BetaNode):
            node.left_memory.clear()
            node.right_memory.clear()
        
        for child in node.children:
            self._clear_beta_memories_recursive(child)
    
    def get_memory_usage(self) -> Dict[str, int]:
        """
        Get memory usage statistics for debugging
        
        Returns:
            Dictionary with memory usage metrics
        """
        alpha_memory_size = sum(
            len(node.memory)
            for nodes in self.alpha_nodes.values()
            for node in nodes
        )
        
        beta_memory_size = self._count_beta_memories(self.root)
        
        production_activations = sum(
            len(node.activations)
            for node in self.production_nodes
        )
        
        return {
            'alpha_memory_facts': alpha_memory_size,
            'beta_memory_tokens': beta_memory_size,
            'production_activations': production_activations,
            'total_memory_items': alpha_memory_size + beta_memory_size + production_activations
        }
    
    def _count_beta_memories(self, node: ReteNode) -> int:
        """Recursively count beta memory size"""
        count = 0
        if isinstance(node, BetaNode):
            count += len(node.left_memory) + len(node.right_memory)
        
        for child in node.children:
            count += self._count_beta_memories(child)
        
        return count


class ReteForwardChaining:
    """
    Forward chaining using Rete algorithm with Neuro-Symbolic parsing

    Provides O(F) amortized performance for rule matching with Legal-DSL validation
    """

    def __init__(self, rules: List[Rule]):
        """
        Initialize Rete-based forward chaining with Legal-DSL validation

        Args:
            rules: List of rules
            
        Raises:
            ParseError: If any rule fails Legal-DSL validation
        """
        self.network = ReteNetwork()
        self.derived_facts: List[Fact] = []
        self.parser = FOLConverter()
        self.ontology_errors: List[str] = []

        logger.info(f"Building Rete network for {len(rules)} rules...")
        
        # PHASE 1: Validate ALL rules before building network (fail-fast)
        validation_errors = []
        for i, rule in enumerate(rules):
            self.parser.validator.reset_errors()
            
            if not self.parser.validator.validate_rule(rule):
                # Collect all validation errors
                for error in self.parser.validator.errors:
                    error_msg = f"Rule {i}: {error.to_feedback()}"
                    validation_errors.append(error_msg)
                    logger.error(error_msg)
        
        # If ANY rule failed validation, abort immediately
        if validation_errors:
            full_error = (
                f"Legal-DSL validation failed for {len(validation_errors)} rule(s):\n" +
                "\n".join(f"  - {err}" for err in validation_errors)
            )
            logger.critical(full_error)
            raise ParseError(full_error)
        
        # PHASE 2: All rules valid - build network
        for rule in rules:
            self.network.add_rule(rule)

        stats = self.network.get_statistics()
        logger.info(f"Network built: {stats['alpha_nodes']} alpha nodes, "
                    f"{stats['beta_nodes']} beta nodes, "
                    f"{stats['production_nodes']} production nodes")
    
    def run(self, initial_facts: List[Fact], max_iterations: int = 1000) -> List[Fact]:
        """
        Run forward chaining with Rete
        
        Args:
            initial_facts: Initial facts
            max_iterations: Maximum iterations
        
        Returns:
            List of derived facts
        """
        # Assert initial facts
        for fact in initial_facts:
            self.network.assert_fact(fact)
        
        # Iterate until fixpoint
        iteration = 0
        new_facts_added = True
        known_facts = set(initial_facts)
        
        while new_facts_added and iteration < max_iterations:
            new_facts_added = False
            iteration += 1
            
            # Get activations
            activations = self.network.get_activations()
            self.network.clear_activations()
            
            # Fire rules
            for rule, token in activations:
                # Instantiate conclusion
                conclusion = self._instantiate_conclusion(rule.conclusion, token.bindings)
                
                if conclusion and conclusion not in known_facts:
                    self.derived_facts.append(conclusion)
                    known_facts.add(conclusion)
                    
                    # Assert new fact
                    self.network.assert_fact(conclusion)
                    new_facts_added = True
        
        logger.info(f"Rete forward chaining completed in {iteration} iterations, "
                   f"derived {len(self.derived_facts)} facts")
        
        return self.derived_facts
    
    def _instantiate_conclusion(self, conclusion: Any, bindings: Dict[str, Term]) -> Optional[Fact]:
        """Instantiate rule conclusion with bindings"""
        if hasattr(conclusion, 'to_atom'):
            conclusion_atom = conclusion.to_atom()
        elif hasattr(conclusion, 'predicate'):
            conclusion_atom = Atom(conclusion.predicate, tuple(conclusion.terms))
        else:
            return None
        
        # Apply bindings
        instantiated = UnificationEngine.apply_bindings(conclusion_atom, bindings)
        
        # Check if ground
        if not instantiated.is_ground():
            return None
        
        return Fact(predicate=instantiated.predicate, terms=list(instantiated.terms))
