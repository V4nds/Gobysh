"""
Preservation Semantics for Gobysh v5.1.
Treats 'do not break / preserve existing behavior' as a first-class contract.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PreservationContract:
    """First-class formal contract defining protected software boundaries."""
    required: bool = False
    protected_symbols: List[str] = field(default_factory=list)
    protected_behaviors: List[str] = field(default_factory=list)
    protected_apis: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)
    verification_strategy: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "required": self.required,
            "protected_symbols": list(self.protected_symbols),
            "protected_behaviors": list(self.protected_behaviors),
            "protected_apis": list(self.protected_apis),
            "invariants": list(self.invariants),
            "verification_strategy": list(self.verification_strategy),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PreservationContract":
        return cls(
            required=bool(data.get("required", False)),
            protected_symbols=list(data.get("protected_symbols", [])),
            protected_behaviors=list(data.get("protected_behaviors", [])),
            protected_apis=list(data.get("protected_apis", [])),
            invariants=list(data.get("invariants", [])),
            verification_strategy=list(data.get("verification_strategy", [])),
        )
