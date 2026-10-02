"""
Contract Validator for Gobysh v5.1.
Enforces multi-clause semantic consistency, scope boundaries, and non-contradiction
before code generation begins.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .intermediate_representation import SemanticIR
from .scope import ScopeNormalizer


@dataclass
class ValidationResult:
    """Outcome of formal semantic contract validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    severity: str = "PASS"  # PASS | HARD | SOFT | UNKNOWN

    def to_dict(self):
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "severity": self.severity,
        }


class ContractValidator:
    """Formal verifier for SemanticIR contracts."""

    def validate(
        self,
        semantic_ir: SemanticIR,
        workspace_files: Optional[List[str]] = None,
    ) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Contradictions already registered
        if semantic_ir.contradictions:
            for c in semantic_ir.contradictions:
                errors.append(f"CONTRADICTION: {c}")

        # 2. Target files vs Forbidden targets
        target_entities = []
        for req in semantic_ir.specification.requirements:
            target_entities.extend(req.target_entities)

        for tf in target_entities:
            norm_tf = ScopeNormalizer.normalize_path(tf).lower()
            for ft in semantic_ir.constraints.forbidden_targets:
                norm_ft = ScopeNormalizer.normalize_path(ft).lower()
                if norm_ft and (norm_ft == norm_tf or norm_ft in norm_tf or norm_tf in norm_ft):
                    msg = f"FORBIDDEN_TARGET_BREACH: Target entity '{tf}' matches forbidden target '{ft}'."
                    if msg not in errors:
                        errors.append(msg)

        # 3. Scope validation
        if semantic_ir.constraints.strict_scope:
            scope_violations = ScopeNormalizer.validate_file_targets(
                targets=target_entities,
                allowed_scopes=semantic_ir.constraints.strict_scope,
            )
            errors.extend(scope_violations)

        # 4. Action REMOVE on preserve_existing
        action = semantic_ir.intent.get("action", "").upper()
        if semantic_ir.constraints.preserve_existing and action in ("REMOVE", "DELETE"):
            errors.append(
                "PRESERVATION_CONFLICT: Action REMOVE requested while preservation of existing system is mandatory."
            )

        # 5. Missing requirements warning
        if not semantic_ir.specification.requirements and action != "EXPLAIN":
            warnings.append("EMPTY_REQUIREMENTS: Semantic specification has no atomic requirements.")

        is_valid = len(errors) == 0
        severity = "PASS" if is_valid else "HARD"

        return ValidationResult(
            valid=is_valid,
            errors=errors,
            warnings=warnings,
            severity=severity,
        )
