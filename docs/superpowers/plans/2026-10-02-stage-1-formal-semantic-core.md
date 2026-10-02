# Stage 1: Formal Semantic Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the formal Semantic Intermediate Representation (IR), Requirement & Constraint models, and Contradiction Detection engine in `core/semantics/`, cleanly connecting them into `IntentResolver` without breaking any existing Gobysh v5.0 APIs or tests.

**Architecture:** Implement additive modular data structures (`SemanticSpecification`, `Requirement`, `ConstraintModel`, `SemanticIR`) in `core/semantics/` with deterministic contradiction checks and pure-Python serialization. Wire them into `core/intent_resolver.py` so every resolved intent produces both the backward-compatible `SemanticContract` and a formal `SemanticIR`, automatically flagging contradictions as high-priority clarification blockers.

**Tech Stack:** Python 3.8+ (`dataclasses`, `typing`, `json`, `re`, standard library only — no external dependencies).

## Global Constraints

- **Preservation First:** Do NOT remove, rename, or break existing attributes, methods, or formats in `core/intent_resolver.py` (`IntentTree`, `IntentNode`, `SemanticContract`, `IntentResolver.resolve`).
- **Zero Heavy Dependencies:** Pure Python standard library only; do NOT introduce PyYAML or external parsers.
- **Bilingual Adhesion:** Preserve and extend Indonesian (`id`) and English (`en`) keyword extraction.
- **Fail-Safe Gate:** All 203 existing unit tests must continue to pass (`python -m unittest discover tests/`) and `goby gate` must remain at 0 unresolved errors.
- **Explicit Contradiction:** When contradictions are detected between requirements and constraints, set `clarification_needed = True` and bump `ambiguity_score >= 0.8`.

---

### Task 1: Semantic Specification & Requirement Models

**Files:**
- Create: `core/semantics/__init__.py`
- Create: `core/semantics/specification.py`
- Test: `tests/test_semantic_core.py`

**Interfaces:**
- Consumes: Standard library `dataclasses`, `typing`, `uuid`
- Produces: `Requirement`, `SemanticSpecification` in `core/semantics/specification.py`
  - `Requirement(id: str, description: str, source_text: str, action: str, target_entities: List[str], status: str, acceptance_criteria: List[str])`
  - `SemanticSpecification(id: str, language: str, raw_prompt: str, requirements: List[Requirement], metadata: Dict[str, Any])`
  - `SemanticSpecification.to_dict() -> Dict[str, Any]`
  - `SemanticSpecification.from_dict(data: Dict[str, Any]) -> SemanticSpecification`

- [ ] **Step 1: Write the failing test for Requirement and SemanticSpecification**

Create `tests/test_semantic_core.py` with the following test cases:

```python
"""Tests for Stage 1 Formal Semantic Core (Goby Calibration)."""

import unittest
from core.semantics.specification import Requirement, SemanticSpecification


class TestSemanticSpecification(unittest.TestCase):
    """Test suite for Requirement and SemanticSpecification models."""

    def test_requirement_creation_and_defaults(self):
        req = Requirement(
            id="REQ-001",
            description="Add email validation",
            source_text="validate email format",
            action="ADD",
            target_entities=["email_validator"],
        )
        self.assertEqual(req.id, "REQ-001")
        self.assertEqual(req.action, "ADD")
        self.assertEqual(req.status, "UNMAPPED")
        self.assertEqual(req.acceptance_criteria, [])

    def test_semantic_specification_serialization(self):
        req = Requirement(
            id="REQ-001",
            description="Add auth function",
            source_text="tambahkan login",
            action="ADD",
            target_entities=["auth"],
            acceptance_criteria=["token returned"],
        )
        spec = SemanticSpecification(
            id="SPEC-123",
            language="id",
            raw_prompt="tambahkan login tanpa ubah user table",
            requirements=[req],
            metadata={"source": "cli"},
        )
        data = spec.to_dict()
        self.assertEqual(data["id"], "SPEC-123")
        self.assertEqual(data["language"], "id")
        self.assertEqual(len(data["requirements"]), 1)
        self.assertEqual(data["requirements"][0]["id"], "REQ-001")

        # Round trip
        restored = SemanticSpecification.from_dict(data)
        self.assertEqual(restored.id, spec.id)
        self.assertEqual(len(restored.requirements), 1)
        self.assertEqual(restored.requirements[0].description, "Add auth function")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_core.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.semantics'`

- [ ] **Step 3: Write minimal implementation for Specification & Requirement**

Create `core/semantics/__init__.py`:
```python
"""
Goby Semantic Layer v5.1.0
Formal Intermediate Representation, Semantic Specification, and Constraint Models.
"""

from .specification import Requirement, SemanticSpecification

__all__ = ["Requirement", "SemanticSpecification"]
```

Create `core/semantics/specification.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_core.py`
Expected: PASS (Ran 2 tests in ...s, OK)

- [ ] **Step 5: Commit**

```bash
git add core/semantics/__init__.py core/semantics/specification.py tests/test_semantic_core.py
git commit -m "feat(semantics): add Requirement and SemanticSpecification models"
```

---

### Task 2: Constraint Model & Contradiction Detection

**Files:**
- Create: `core/semantics/constraints.py`
- Modify: `core/semantics/__init__.py`
- Modify: `tests/test_semantic_core.py`

**Interfaces:**
- Consumes: `Requirement`, `SemanticSpecification` from `core/semantics/specification.py`
- Produces: `Constraint`, `ConstraintModel` in `core/semantics/constraints.py`
  - `Constraint(id: str, constraint_type: str, target: str, description: str, severity: str)`
  - `ConstraintModel(forbidden_targets, preserve_existing, strict_scope, preconditions, postconditions, invariants, protected_symbols, protected_behaviors)`
  - `ConstraintModel.detect_contradictions(target_files: List[str], action: str, target_symbols: List[str]) -> List[str]`

- [ ] **Step 1: Write the failing tests for ConstraintModel and contradiction detection**

Append to `tests/test_semantic_core.py`:

```python
from core.semantics.constraints import Constraint, ConstraintModel


class TestConstraintModel(unittest.TestCase):
    """Test suite for ConstraintModel and deterministic contradiction checks."""

    def test_constraint_model_serialization(self):
        cm = ConstraintModel(
            forbidden_targets=["config.py", "db"],
            preserve_existing=True,
            strict_scope=["core/utils.py"],
            invariants=["database_schema_unchanged"],
            protected_symbols=["UserModel"],
        )
        d = cm.to_dict()
        self.assertIn("config.py", d["forbidden_targets"])
        self.assertTrue(d["preserve_existing"])
        self.assertEqual(d["invariants"], ["database_schema_unchanged"])

        # Round trip
        restored = ConstraintModel.from_dict(d)
        self.assertEqual(restored.forbidden_targets, cm.forbidden_targets)
        self.assertEqual(restored.preserve_existing, cm.preserve_existing)

    def test_contradiction_forbidden_target_in_target_files(self):
        cm = ConstraintModel(
            forbidden_targets=["config.py"],
            preserve_existing=False,
        )
        contradictions = cm.detect_contradictions(
            target_files=["config.py", "main.py"],
            action="MODIFY",
        )
        self.assertEqual(len(contradictions), 1)
        self.assertIn("config.py", contradictions[0])

    def test_contradiction_remove_action_with_preserve_existing(self):
        cm = ConstraintModel(
            preserve_existing=True,
            protected_symbols=["UserModel"],
        )
        contradictions = cm.detect_contradictions(
            target_files=["models.py"],
            action="REMOVE",
            target_symbols=["UserModel"],
        )
        self.assertTrue(any("preserve_existing" in c.lower() or "UserModel" in c for c in contradictions))

    def test_contradiction_strict_scope_violation(self):
        cm = ConstraintModel(
            strict_scope=["core/auth.py"],
        )
        contradictions = cm.detect_contradictions(
            target_files=["core/auth.py", "server/main.py"],
            action="MODIFY",
        )
        self.assertTrue(any("server/main.py" in c for c in contradictions))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_core.py`
Expected: FAIL with `ImportError: cannot import name 'Constraint' from 'core.semantics.constraints'`

- [ ] **Step 3: Write minimal implementation for ConstraintModel**

Create `core/semantics/constraints.py`:
```python
"""
Constraint Model & Contradiction Detection for Gobysh v5.1.
Enforces deterministic boundaries between user negations, preservation requirements,
and planned target modifications.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os


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
```

Update `core/semantics/__init__.py`:
```python
"""
Goby Semantic Layer v5.1.0
Formal Intermediate Representation, Semantic Specification, and Constraint Models.
"""

from .specification import Requirement, SemanticSpecification
from .constraints import Constraint, ConstraintModel

__all__ = ["Requirement", "SemanticSpecification", "Constraint", "ConstraintModel"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_core.py`
Expected: PASS (Ran 6 tests in ...s, OK)

- [ ] **Step 5: Commit**

```bash
git add core/semantics/constraints.py core/semantics/__init__.py tests/test_semantic_core.py
git commit -m "feat(semantics): add ConstraintModel and contradiction detection"
```

---

### Task 3: Semantic Intermediate Representation (IR) Data Structure & Normalization

**Files:**
- Create: `core/semantics/intermediate_representation.py`
- Modify: `core/semantics/__init__.py`
- Modify: `tests/test_semantic_core.py`

**Interfaces:**
- Consumes: `Requirement`, `SemanticSpecification`, `ConstraintModel`
- Produces: `SemanticEntity`, `SemanticIR` in `core/semantics/intermediate_representation.py`
  - `SemanticEntity(name: str, entity_type: str)`
  - `SemanticIR(specification, intent, entities, constraints, preconditions, postconditions, invariants, protected_symbols, acceptance, contradictions)`
  - `SemanticIR.to_dict() -> Dict[str, Any]`
  - `SemanticIR.to_json(indent: int) -> str`
  - `SemanticIR.to_yaml() -> str` (clean, lightweight deterministic string serializer)
  - `SemanticIR.from_dict(d: Dict[str, Any]) -> SemanticIR`

- [ ] **Step 1: Write the failing tests for SemanticIR**

Append to `tests/test_semantic_core.py`:

```python
from core.semantics.intermediate_representation import SemanticEntity, SemanticIR


class TestSemanticIR(unittest.TestCase):
    """Test suite for Semantic Intermediate Representation (IR)."""

    def test_semantic_ir_creation_and_yaml_export(self):
        spec = SemanticSpecification(
            id="SPEC-001",
            language="en",
            raw_prompt="add user registration",
            requirements=[
                Requirement(id="REQ-1", description="create registration endpoint", action="ADD")
            ]
        )
        constraints = ConstraintModel(
            forbidden_targets=["user_table"],
            preserve_existing=True,
            strict_scope=["auth/"],
            invariants=["schema_stable"],
            protected_symbols=["User"],
        )
        ir = SemanticIR(
            specification=spec,
            intent={"action": "ADD", "target": "auth", "description": "add registration"},
            entities=[SemanticEntity(name="registration_flow", entity_type="feature")],
            constraints=constraints,
            preconditions=["email_input_exists"],
            postconditions=["valid_email => registration_continues"],
            invariants=["schema_stable"],
            protected_symbols=["User"],
            acceptance=["validation_test_passes"],
        )

        d = ir.to_dict()
        self.assertEqual(d["intent"]["action"], "ADD")
        self.assertEqual(len(d["entities"]), 1)
        self.assertEqual(d["constraints"]["forbidden_targets"], ["user_table"])

        # Test pure-Python YAML representation
        yaml_str = ir.to_yaml()
        self.assertIn("specification:", yaml_str)
        self.assertIn("intent:", yaml_str)
        self.assertIn("action: ADD", yaml_str)
        self.assertIn("forbidden:", yaml_str)
        self.assertIn("- user_table", yaml_str)

        # Round trip from dict
        restored = SemanticIR.from_dict(d)
        self.assertEqual(restored.specification.id, "SPEC-001")
        self.assertEqual(restored.entities[0].name, "registration_flow")
        self.assertEqual(restored.constraints.forbidden_targets, ["user_table"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_core.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.semantics.intermediate_representation'`

- [ ] **Step 3: Write minimal implementation for SemanticIR**

Create `core/semantics/intermediate_representation.py`:
```python
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
        return cls(
            specification=spec,
            intent=data.get("intent", {}),
            entities=entities,
            constraints=constraints,
            preconditions=list(data.get("preconditions", [])),
            postconditions=list(data.get("postconditions", [])),
            invariants=list(data.get("invariants", [])),
            protected_symbols=list(data.get("protected_symbols", [])),
            acceptance=list(data.get("acceptance", [])),
            contradictions=list(data.get("contradictions", [])),
        )
```

Update `core/semantics/__init__.py`:
```python
"""
Goby Semantic Layer v5.1.0
Formal Intermediate Representation, Semantic Specification, and Constraint Models.
"""

from .specification import Requirement, SemanticSpecification
from .constraints import Constraint, ConstraintModel
from .intermediate_representation import SemanticEntity, SemanticIR

__all__ = [
    "Requirement",
    "SemanticSpecification",
    "Constraint",
    "ConstraintModel",
    "SemanticEntity",
    "SemanticIR",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_core.py`
Expected: PASS (Ran 7 tests in ...s, OK)

- [ ] **Step 5: Commit**

```bash
git add core/semantics/intermediate_representation.py core/semantics/__init__.py tests/test_semantic_core.py
git commit -m "feat(semantics): add SemanticIR data structure with YAML/JSON serialization"
```

---

### Task 4: Connect Semantic Core to `core/intent_resolver.py` & Backwards Compatibility

**Files:**
- Modify: `core/intent_resolver.py`
- Modify: `tests/test_intent_resolver.py`

**Interfaces:**
- Consumes: `Requirement`, `SemanticSpecification`, `ConstraintModel`, `SemanticIR` from `core.semantics`
- Produces:
  - `SemanticContract`: keeps all existing fields (`forbidden_targets`, `preserve_existing`, `strict_scope`, `expected_traits`, `action_verb`), adds `contradictions: List[str]` and `semantic_ir: Optional[Dict[str, Any]]`
  - `IntentTree`: adds `semantic_ir: Optional[SemanticIR] = None`
  - `IntentResolver.resolve()`: creates and attaches `SemanticIR`, checks `detect_contradictions()`, automatically flags contradictions with `clarification_needed = True`, and updates `ambiguity_score` if contradictions exist.

- [ ] **Step 1: Write the failing tests in `tests/test_intent_resolver.py`**

Append to `tests/test_intent_resolver.py`:

```python
    # -------------------------------------------------------------------
    # Stage 1 Calibration: Semantic IR & Contradiction Detection
    # -------------------------------------------------------------------

    def test_semantic_ir_attached_to_intent_tree(self):
        result = self.resolver.resolve("buatkan fitur login baru di auth.py tanpa ubah user_table")
        self.assertIsNotNone(result.semantic_ir)
        self.assertIn("user_table", result.semantic_ir.constraints.forbidden_targets)
        self.assertEqual(result.semantic_ir.intent.get("action"), "create_feature")
        self.assertIn("semantic_ir", result.to_dict())

    def test_contradiction_detection_triggers_clarification(self):
        # User says modify config.py but also says don't touch config.py
        result = self.resolver.resolve("perbaiki bug di config.py tapi jangan ubah config.py")
        self.assertTrue(result.clarification_needed)
        self.assertGreaterEqual(result.ambiguity_score, 0.8)
        self.assertTrue(any("CONTRADICTION" in q for q in result.clarification_questions))
        self.assertGreater(len(result.semantic_contract.contradictions), 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest tests/test_intent_resolver.py -k test_semantic_ir_attached`
Expected: FAIL with `AssertionError: None is not None` (or missing `semantic_ir`)

- [ ] **Step 3: Modify `core/intent_resolver.py`**

In `core/intent_resolver.py`:
1. Import `Requirement`, `SemanticSpecification`, `ConstraintModel`, `SemanticEntity`, `SemanticIR` from `core.semantics`.
2. Add `contradictions: List[str] = field(default_factory=list)` and `semantic_ir_dict: Optional[Dict[str, Any]] = None` to `SemanticContract`.
3. Add `semantic_ir: Optional[SemanticIR] = None` to `IntentTree`.
4. Update `IntentTree.to_dict()` to include `"semantic_ir": self.semantic_ir.to_dict() if self.semantic_ir else None` and `"contradictions": self.semantic_contract.contradictions`.
5. In `IntentResolver.resolve()`:
   - Normalize task_type to action verb.
   - Construct `ConstraintModel` from the extracted forbidden targets, preservation, and scope.
   - Run `cm.detect_contradictions(target_files=primary.target_files, action=primary.task_type)`.
   - Build `SemanticSpecification` with an initial `Requirement(id="REQ-001", description=primary.description, source_text=raw_input, action=primary.task_type, target_entities=primary.target_files)`.
   - Construct `SemanticIR` combining the spec, intent summary, entities, constraint model, and detected contradictions.
   - If contradictions exist:
     - Set `tree.clarification_needed = True`
     - Prepend to `clarification_questions`: `f"[CONTRADICTION DETECTED] {contradictions[0]} Please clarify."`
     - Elevate `tree.ambiguity_score = max(tree.ambiguity_score, 0.85)`
   - Attach `semantic_ir` to both `SemanticContract` and `IntentTree`.

- [ ] **Step 4: Run tests to verify all pass**

Run: `.venv\Scripts\python.exe -m unittest tests/test_intent_resolver.py`
Expected: PASS (All test cases including Indonesian constraints, legacy methods, and new semantic tests pass)

- [ ] **Step 5: Commit**

```bash
git add core/intent_resolver.py tests/test_intent_resolver.py
git commit -m "feat(intent): connect formal SemanticIR and contradiction detection to IntentResolver"
```

---

### Task 5: Integration, CLI Verification, and Completion Gate

**Files:**
- Modify: `core/cli.py` (if needed to display contradictions / IR in `goby intent`)
- Test: `tests/test_cli.py`
- Test: Full test suite (`python -m unittest discover tests/`)

**Interfaces:**
- Consumes: `goby intent` CLI command
- Produces: CLI output with structured `semantic_contract`, `semantic_ir`, and explicit contradiction warning if present.

- [ ] **Step 1: Check CLI handling for intent output**

Review `core/cli.py` around `handle_intent`:
Ensure `goby intent` prints the structured JSON from `IntentTree.to_dict()`, and if `contradictions` exist, displays:
`[GOBY INTENT] [!] Contradictions detected: ...`

- [ ] **Step 2: Run CLI tests**

Run: `.venv\Scripts\python.exe -m unittest tests/test_cli.py`
Expected: PASS

- [ ] **Step 3: Run full regression test suite**

Run: `.venv\Scripts\python.exe -m unittest discover tests/`
Expected: PASS (All 203+ tests pass without errors)

- [ ] **Step 4: Run Goby Gate check**

Run: `goby gate`
Expected: Exit Code 0 (`[GOBY GATE] Ledger clean: 0 unresolved file errors. Workspace ready.`)

- [ ] **Step 5: Commit**

```bash
git add core/cli.py tests/test_cli.py
git commit -m "feat(cli): enhance goby intent with semantic IR output and contradiction alerts"
```

---

## Self-Review Checklist

1. **Spec coverage:** Implements all Stage 1 components from Section 30 of `GOBYSH_ARCHITECTURE_CALIBRATION_SPEC.md` (`SemanticSpecification`, `SemanticIR`, `ConstraintModel`, `RequirementModel`, connected to `IntentResolver`).
2. **No Placeholders:** All code snippets, commands, interfaces, and expected results are fully written out.
3. **Type consistency:** `Requirement`, `SemanticSpecification`, `ConstraintModel`, `SemanticIR`, `SemanticEntity` types match across all tasks.
4. **Preservation:** Retains 100% of existing `IntentResolver`, `SemanticContract`, and `IntentTree` interfaces and tests.
