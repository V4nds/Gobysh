"""
Semantic Specification & Requirement Models for Gobysh v5.1.
Provides formal tracking of user requirements across translation boundaries.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
import uuid


@dataclass
class Requirement:
    """A formal atomic requirement derived from human intent."""
    id: str
    description: str
    source_text: str = ""
    action: str = "ADD"  # ADD | MODIFY | FIX | REMOVE | EXPLAIN | TEST | CONFIGURE
    target_entities: List[str] = field(default_factory=list)
    status: str = "UNMAPPED"  # UNMAPPED | MAPPED | VERIFIED | VIOLATED
    acceptance_criteria: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "source_text": self.source_text,
            "action": self.action,
            "target_entities": self.target_entities,
            "status": self.status,
            "acceptance_criteria": self.acceptance_criteria,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Requirement":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            description=data.get("description", ""),
            source_text=data.get("source_text", ""),
            action=data.get("action", "ADD"),
            target_entities=list(data.get("target_entities", [])),
            status=data.get("status", "UNMAPPED"),
            acceptance_criteria=list(data.get("acceptance_criteria", [])),
        )


@dataclass
class SemanticSpecification:
    """Formal semantic specification encapsulating all atomic requirements."""
    id: str
    language: str = "unknown"  # id | en | mixed | unknown
    raw_prompt: str = ""
    requirements: List[Requirement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "language": self.language,
            "raw_prompt": self.raw_prompt,
            "requirements": [req.to_dict() for req in self.requirements],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SemanticSpecification":
        reqs = [
            Requirement.from_dict(r) if isinstance(r, dict) else r
            for r in data.get("requirements", [])
        ]
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            language=data.get("language", "unknown"),
            raw_prompt=data.get("raw_prompt", ""),
            requirements=reqs,
            metadata=data.get("metadata", {}),
        )
