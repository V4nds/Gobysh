"""
Semantic Intermediate Representation (IR) for Gobysh v5.1.
Serves as the central adhesive schema between human intent, AI planning,
and mechanical code verification.
"""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Optional
import uuid

from .specification import Requirement, SemanticSpecification
from .constraints import ConstraintModel
from .preservation import PreservationContract


@dataclass
class SemanticEntity:
    """A high-level semantic entity extracted from prompt or codebase."""
    name: str
    entity_type: str = "feature"  # feature | function | class | module | table | file

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.entity_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SemanticEntity":
        return cls(
            name=data.get("name", ""),
            entity_type=data.get("type", data.get("entity_type", "feature")),
        )


@dataclass
class SemanticIR:
    """
    Formal Semantic Intermediate Representation (IR).
    Aligns with GOBYSH_ARCHITECTURE_CALIBRATION_SPEC Section 7.
    """
    specification: SemanticSpecification
    intent: Dict[str, Any] = field(default_factory=dict)
    entities: List[SemanticEntity] = field(default_factory=list)
    constraints: ConstraintModel = field(default_factory=ConstraintModel)
    preservation: Optional[PreservationContract] = None
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)
    protected_symbols: List[str] = field(default_factory=list)
    acceptance: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "specification": self.specification.to_dict(),
            "intent": self.intent,
            "entities": [e.to_dict() for e in self.entities],
            "constraints": self.constraints.to_dict(),
            "preservation": self.preservation.to_dict() if self.preservation else None,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "invariants": self.invariants,
            "protected_symbols": self.protected_symbols,
            "acceptance": self.acceptance,
            "contradictions": self.contradictions,
        }


    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_yaml(self) -> str:
        """Lightweight deterministic YAML serialization without external dependencies."""
        lines = [
            "specification:",
            f"  id: {self.specification.id}",
            f"  language: {self.specification.language}",
            "",
            "intent:",
            f"  action: {self.intent.get('action', 'ADD')}",
            f"  target: {self.intent.get('target', '')}",
            f"  description: {self.intent.get('description', '')}",
            "",
            "entities:",
        ]
        if self.entities:
            for ent in self.entities:
                lines.append(f"  - name: {ent.name}")
                lines.append(f"    type: {ent.entity_type}")
        else:
            lines.append("  []")

        lines.extend([
            "",
            "constraints:",
            "  forbidden:",
        ])
        if self.constraints.forbidden_targets:
            for ft in self.constraints.forbidden_targets:
                lines.append(f"    - {ft}")
        else:
            lines.append("    []")

        lines.append("  preserve:")
        if self.constraints.preserve_existing or self.invariants:
            if self.constraints.preserve_existing:
                lines.append("    - existing_behavior")
            for inv in self.invariants:
                lines.append(f"    - {inv}")
        else:
            lines.append("    []")

        lines.append("  scope:")
        if self.constraints.strict_scope:
            for sc in self.constraints.strict_scope:
                lines.append(f"    - {sc}")
        else:
            lines.append("    []")

        lines.extend(["", "preconditions:"])
        for p in self.preconditions:
            lines.append(f"  - {p}")
        if not self.preconditions:
            lines.append("  []")

        lines.extend(["", "postconditions:"])
        for q in self.postconditions:
            lines.append(f"  - {q}")
        if not self.postconditions:
            lines.append("  []")

        lines.extend(["", "invariants:"])
        for inv in self.invariants:
            lines.append(f"  - {inv}")
        if not self.invariants:
            lines.append("  []")

        lines.extend(["", "protected_symbols:"])
        for sym in self.protected_symbols:
            lines.append(f"  - {sym}")
        if not self.protected_symbols:
            lines.append("  []")

        lines.extend(["", "acceptance:"])
        for acc in self.acceptance:
            lines.append(f"  - {acc}")
        if not self.acceptance:
            lines.append("  []")

        if self.contradictions:
            lines.extend(["", "contradictions:"])
            for c in self.contradictions:
                lines.append(f"  - {c}")

        return "\n".join(lines) + "\n"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SemanticIR":
        spec_data = data.get("specification", {})
        spec = (
            SemanticSpecification.from_dict(spec_data)
            if isinstance(spec_data, dict)
            else SemanticSpecification(id=str(uuid.uuid4())[:8])
        )
        entities = [
            SemanticEntity.from_dict(e) if isinstance(e, dict) else e
            for e in data.get("entities", [])
        ]
        const_data = data.get("constraints", {})
        constraints = (
            ConstraintModel.from_dict(const_data)
            if isinstance(const_data, dict)
            else ConstraintModel()
        )
        pres_data = data.get("preservation")
        preservation = (
            PreservationContract.from_dict(pres_data)
            if isinstance(pres_data, dict)
            else None
        )
        return cls(
            specification=spec,
            intent=data.get("intent", {}),
            entities=entities,
            constraints=constraints,
            preservation=preservation,
            preconditions=list(data.get("preconditions", [])),
            postconditions=list(data.get("postconditions", [])),
            invariants=list(data.get("invariants", [])),
            protected_symbols=list(data.get("protected_symbols", [])),
            acceptance=list(data.get("acceptance", [])),
            contradictions=list(data.get("contradictions", [])),
        )

