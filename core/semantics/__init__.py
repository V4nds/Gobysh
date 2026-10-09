"""
Goby Semantic Layer v5.1.0
Formal Intermediate Representation, Semantic Specification, and Constraint Models.
"""

from .specification import Requirement, SemanticSpecification
from .constraints import Constraint, ConstraintModel
from .intermediate_representation import SemanticEntity, SemanticIR
from .preservation import PreservationContract
from .scope import ScopeNormalizer
from .negation import NegationHandler, NegationResult
from .contract_validator import ContractValidator, ValidationResult
from .dependency_graph import DependencyGraph
from .depth_engine import DepthEngine, ModuleDepthMetrics

__all__ = [
    "Requirement",
    "SemanticSpecification",
    "Constraint",
    "ConstraintModel",
    "SemanticEntity",
    "SemanticIR",
    "PreservationContract",
    "ScopeNormalizer",
    "NegationHandler",
    "NegationResult",
    "ContractValidator",
    "ValidationResult",
    "DependencyGraph",
    "DepthEngine",
    "ModuleDepthMetrics",
]
