"""
Constraint Model & Contradiction Detection for Gobysh v5.1.
Enforces deterministic boundaries between user negations, preservation requirements,
and planned target modifications.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Constraint:
    """An individual formal constraint."""
    id: str
    constraint_type: str  # FORBIDDEN_TARGET | PRESERVE_EXISTING | STRICT_SCOPE | PRECONDITION | POSTCONDITION | INVARIANT | PROTECTED_SYMBOL
    target: str = ""
    description: str = ""
    severity: str = "HARD"  # HARD | SOFT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "constraint_type": self.constraint_type,
            "target": self.target,
            "description": self.description,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Constraint":
        return cls(
            id=data.get("id", ""),
            constraint_type=data.get("constraint_type", "FORBIDDEN_TARGET"),
            target=data.get("target", ""),
            description=data.get("description", ""),
            severity=data.get("severity", "HARD"),
        )


@dataclass
class ConstraintModel:
    """Aggregated constraints governing task execution."""
    forbidden_targets: List[str] = field(default_factory=list)
    preserve_existing: bool = False
    strict_scope: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)
    protected_symbols: List[str] = field(default_factory=list)
    protected_behaviors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "forbidden_targets": self.forbidden_targets,
            "preserve_existing": self.preserve_existing,
            "strict_scope": self.strict_scope,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "invariants": self.invariants,
            "protected_symbols": self.protected_symbols,
            "protected_behaviors": self.protected_behaviors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConstraintModel":
        return cls(
            forbidden_targets=list(data.get("forbidden_targets", [])),
            preserve_existing=bool(data.get("preserve_existing", False)),
            strict_scope=list(data.get("strict_scope", [])),
            preconditions=list(data.get("preconditions", [])),
            postconditions=list(data.get("postconditions", [])),
            invariants=list(data.get("invariants", [])),
            protected_symbols=list(data.get("protected_symbols", [])),
            protected_behaviors=list(data.get("protected_behaviors", [])),
        )

    def detect_contradictions(
        self,
        target_files: Optional[List[str]] = None,
        action: str = "ADD",
        target_symbols: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Mechanically detect logical contradictions between constraints and intended actions.
        Returns a list of human-readable contradiction descriptions.
        """
        contradictions: List[str] = []
        target_files = target_files or []
        target_symbols = target_symbols or []
        normalized_action = action.upper().strip()

        # 1. Target files vs Forbidden targets
        for tf in target_files:
            tf_norm = tf.replace("\\", "/").lower()
            for ft in self.forbidden_targets:
                ft_norm = ft.replace("\\", "/").lower()
                if ft_norm and (ft_norm == tf_norm or ft_norm in tf_norm or tf_norm in ft_norm):
                    contradictions.append(
                        f"CONTRADICTION: File '{tf}' is both a target file and explicitly marked forbidden ('{ft}')."
                    )

        # 2. Action REMOVE/DELETE vs preserve_existing
        if self.preserve_existing and normalized_action in ("REMOVE", "DELETE"):
            for sym in target_symbols:
                if sym in self.protected_symbols:
                    contradictions.append(
                        f"CONTRADICTION: Action '{action}' on protected symbol '{sym}' violates preserve_existing constraint."
                    )
            if not target_symbols and target_files:
                contradictions.append(
                    f"CONTRADICTION: Action '{action}' on target files {target_files} contradicts preserve_existing constraint."
                )

        # 3. Strict scope violations
        if self.strict_scope:
            for tf in target_files:
                tf_norm = tf.replace("\\", "/").lower()
                in_scope = False
                for sc in self.strict_scope:
                    sc_norm = sc.replace("\\", "/").lower()
                    if sc_norm in tf_norm or tf_norm in sc_norm:
                        in_scope = True
                        break
                if not in_scope:
                    contradictions.append(
                        f"CONTRADICTION: Target file '{tf}' violates strict_scope constraint {self.strict_scope}."
                    )

        return contradictions
