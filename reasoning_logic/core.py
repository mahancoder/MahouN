"""
Core Data Structures for FOL Reasoning
=======================================

Immutable, hashable data structures for First-Order Logic:
- Terms (constants, variables, functions)
- Atoms (predicates with terms)
- Facts (ground atoms)
- Rules (Horn clauses)
"""

from typing import List, Dict, Any, Set, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TermType(Enum):
    """Type of FOL term"""
    CONSTANT = "constant"
    VARIABLE = "variable"
    FUNCTION = "function"


@dataclass(frozen=True)
class Term:
    """
    First-order logic term (immutable for hashing)
    
    Examples:
        - Constant: Term("PersonA", TermType.CONSTANT)
        - Variable: Term("X", TermType.VARIABLE)
        - Function: Term("father", TermType.FUNCTION, [Term("X", ...)])
    """
    name: str
    term_type: TermType
    args: Tuple['Term', ...] = field(default_factory=tuple)
    
    def __str__(self):
        if self.args:
            args_str = ", ".join(str(arg) for arg in self.args)
            return f"{self.name}({args_str})"
        return self.name
    
    def __repr__(self):
        return f"Term({self.name}, {self.term_type.value})"
    
    def is_variable(self) -> bool:
        return self.term_type == TermType.VARIABLE
    
    def is_constant(self) -> bool:
        return self.term_type == TermType.CONSTANT
    
    def is_ground(self) -> bool:
        """Check if term contains no variables"""
        if self.is_variable():
            return False
        return all(arg.is_ground() for arg in self.args)
    
    def get_variables(self) -> Set['Term']:
        """Extract all variables from term"""
        if self.is_variable():
            return {self}
        variables = set()
        for arg in self.args:
            variables.update(arg.get_variables())
        return variables


@dataclass(frozen=True)
class Atom:
    """
    FOL atomic formula (predicate with terms)
    
    Example: has_obligation(PersonA, LiabilityJ)
    """
    predicate: str
    terms: Tuple[Term, ...] = field(default_factory=tuple)
    
    def __str__(self):
        if self.terms:
            terms_str = ", ".join(str(t) for t in self.terms)
            return f"{self.predicate}({terms_str})"
        return self.predicate
    
    def __repr__(self):
        return f"Atom({self.predicate}, {self.terms})"
    
    def is_ground(self) -> bool:
        """Check if atom contains no variables"""
        return all(term.is_ground() for term in self.terms)
    
    def get_variables(self) -> Set[Term]:
        """Extract all variables from atom"""
        variables = set()
        for term in self.terms:
            variables.update(term.get_variables())
        return variables
    
    def arity(self) -> int:
        """Return number of arguments"""
        return len(self.terms)


@dataclass(frozen=True)
class Fact:
    """
    Ground fact (atom with no variables) - IMMUTABLE
    
    Invariant: All terms must be ground (no variables)
    
    Note: This class is frozen (immutable) to ensure hash stability
    when used in sets and dictionaries.
    """
    predicate: str
    terms: Tuple[Term, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validate that fact is ground (no variables allowed)"""
        # Convert list to tuple if needed (for backward compatibility)
        if isinstance(object.__getattribute__(self, 'terms'), list):
            object.__setattr__(self, 'terms', tuple(object.__getattribute__(self, 'terms')))
        
        # Enforce groundedness invariant
        if not self.is_ground():
            variables = self.get_variables()
            raise ValueError(
                f"Fact must be ground (no variables allowed). "
                f"Got: {self}. Variables: {variables}"
            )
    
    @staticmethod
    def from_expression(expression, metadata: Optional[Dict[str, Any]] = None, 
                       confidence: float = 1.0) -> 'Fact':
        """
        Factory method: Create fact from expression (backward compatibility)
        
        Args:
            expression: Expression object with predicate and terms
            metadata: Optional metadata
            confidence: Confidence score
            
        Returns:
            Fact instance
        """
        predicate = expression.predicate if hasattr(expression, 'predicate') else str(expression)
        terms = tuple(expression.terms) if hasattr(expression, 'terms') else ()
        return Fact(
            predicate=predicate,
            terms=terms,
            metadata=metadata or {},
            confidence=confidence
        )
    
    def is_ground(self) -> bool:
        """Check if fact contains no variables"""
        return all(term.is_ground() for term in self.terms)
    
    def get_variables(self) -> Set[Term]:
        """Extract all variables from fact (should be empty for valid facts)"""
        variables = set()
        for term in self.terms:
            variables.update(term.get_variables())
        return variables
    
    def to_atom(self) -> Atom:
        """Convert to immutable Atom for hashing"""
        return Atom(self.predicate, self.terms)
    
    @property
    def value(self):
        """Extract numeric value from fact if present (for backward compatibility)"""
        if self.terms and len(self.terms) >= 2:
            last_term = self.terms[-1]
            if last_term.term_type == TermType.CONSTANT:
                try:
                    return float(last_term.name)
                except (ValueError, AttributeError):
                    pass
        return None
    
    def __str__(self):
        if self.terms:
            terms_str = ", ".join(str(t) for t in self.terms)
            return f"{self.predicate}({terms_str})"
        return self.predicate


from typing import Union

@dataclass
class Rule:
    """
    FOL Horn clause: conclusion :- premise1, premise2, ...
    
    Example: has_obligation(X, Z) :- is_proxy(X, Y), has_obligation(Y, Z)
    """
    premise: List[Union[Atom, 'Expression']]  # List of atoms (body of rule)
    conclusion: Union[Atom, 'Expression']  # Single atom (head of rule)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    
    def __str__(self):
        premise_str = " ∧ ".join(str(p) for p in self.premise)
        return f"{self.conclusion} :- {premise_str}"
    
    def __repr__(self):
        return f"Rule({self.conclusion} :- {self.premise})"
    
    def get_variables(self) -> Set[Term]:
        """Extract all variables from rule"""
        variables = set()
        for atom in self.premise:
            variables.update(atom.get_variables())
        variables.update(self.conclusion.get_variables())
        return variables


@dataclass
class Expression:
    """
    Parsed FOL expression (for backward compatibility)
    """
    predicate: str
    terms: List[Term] = field(default_factory=list)
    
    def __str__(self):
        if self.terms:
            terms_str = ", ".join(str(t) for t in self.terms)
            return f"{self.predicate}({terms_str})"
        return self.predicate
    
    def to_atom(self) -> Atom:
        """Convert to immutable Atom"""
        return Atom(self.predicate, tuple(self.terms))
