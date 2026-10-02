# Stage 2: Contract Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Stage 2 Contract Validation from `GOBYSH_ARCHITECTURE_CALIBRATION_SPEC.md`: build `PreservationContract`, `ScopeNormalizer`, `NegationHandler`, and `ContractValidator` in `core/semantics/`, and connect them into `IntentResolver` without breaking any existing APIs or tests.

**Architecture:** Create modular, pure-Python semantic validators:
1. `PreservationContract` in `core/semantics/preservation.py` (first-class preservation semantics: symbols, behaviors, APIs, verification criteria).
2. `ScopeNormalizer` in `core/semantics/scope.py` (cross-platform path normalization, globs, inclusion/exclusion boundary checks).
3. `NegationHandler` in `core/semantics/negation.py` (advanced bilingual negation & negative constraint parsing).
4. `ContractValidator` in `core/semantics/contract_validator.py` (multi-clause semantic consistency & contradiction analysis).
5. Integration into `core/semantics/__init__.py` and `core/intent_resolver.py`.

**Tech Stack:** Python 3.8+ (`dataclasses`, `typing`, `fnmatch`, `pathlib`, `re`, standard library only).

## Global Constraints

- **Preservation First:** Do NOT remove, rename, or break existing attributes, methods, or formats in `core/intent_resolver.py` or `core/semantics/`.
- **Zero Heavy Dependencies:** Standard library only; no external parsers or third-party regex engines.
- **Bilingual Adhesion:** First-class Indonesian (`id`) and English (`en`) support.
- **Fail-Safe Gate:** All 212 unit tests must pass (`python -m unittest discover tests/`) and `goby gate` must exit 0.

---

### Task 1: Preservation Semantics (`core/semantics/preservation.py`)

**Files:**
- Create: `core/semantics/preservation.py`
- Modify: `core/semantics/__init__.py`
- Test: `tests/test_contract_validation.py`

**Interfaces:**
- Produces: `PreservationContract` in `core/semantics/preservation.py`:
  - `PreservationContract(required: bool, protected_symbols: List[str], protected_behaviors: List[str], protected_apis: List[str], invariants: List[str], verification_strategy: List[str])`
  - `to_dict() -> Dict[str, Any]`
  - `from_dict(d: Dict[str, Any]) -> PreservationContract`

- [ ] **Step 1: Write failing test for PreservationContract**

Create `tests/test_contract_validation.py`:

```python
"""Tests for Stage 2 Contract Validation (Goby Calibration)."""

import unittest
from core.semantics.preservation import PreservationContract


class TestPreservationContract(unittest.TestCase):
    """Test suite for first-class PreservationContract."""

    def test_preservation_contract_defaults_and_dict(self):
        pc = PreservationContract(
            required=True,
            protected_symbols=["old_auth_function", "UserModel"],
            protected_behaviors=["existing_login_flow"],
            invariants=["db_schema_stable"],
            verification_strategy=["symbol_existence", "test_suite"],
        )
        self.assertTrue(pc.required)
        self.assertEqual(len(pc.protected_symbols), 2)
        d = pc.to_dict()
        self.assertEqual(d["required"], True)
        self.assertIn("old_auth_function", d["protected_symbols"])

        # Round trip
        restored = PreservationContract.from_dict(d)
        self.assertEqual(restored.protected_symbols, pc.protected_symbols)
        self.assertEqual(restored.protected_behaviors, pc.protected_behaviors)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest tests/test_contract_validation.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.semantics.preservation'`

- [ ] **Step 3: Implement PreservationContract**

Create `core/semantics/preservation.py`:

```python
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
```

Update `core/semantics/__init__.py` to re-export `PreservationContract`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest tests/test_contract_validation.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/semantics/preservation.py core/semantics/__init__.py tests/test_contract_validation.py
git commit -m "feat(semantics): add first-class PreservationContract model"
```

---

### Task 2: Scope Normalization & Boundary Checks (`core/semantics/scope.py`)

**Files:**
- Create: `core/semantics/scope.py`
- Modify: `core/semantics/__init__.py`
- Modify: `tests/test_contract_validation.py`

**Interfaces:**
- Produces: `ScopeNormalizer` in `core/semantics/scope.py`:
  - `ScopeNormalizer.normalize_path(path: str) -> str`
  - `ScopeNormalizer.is_in_scope(file_path: str, scope_patterns: List[str]) -> bool`
  - `ScopeNormalizer.validate_file_targets(targets: List[str], allowed_scopes: List[str]) -> List[str]`

- [ ] **Step 1: Write failing test for ScopeNormalizer**

Append to `tests/test_contract_validation.py`:

```python
from core.semantics.scope import ScopeNormalizer


class TestScopeNormalizer(unittest.TestCase):
    """Test suite for ScopeNormalizer path normalization and glob boundaries."""

    def test_normalize_path(self):
        self.assertEqual(ScopeNormalizer.normalize_path("core\\cli.py"), "core/cli.py")
        self.assertEqual(ScopeNormalizer.normalize_path("./src/auth/"), "src/auth")
        self.assertEqual(ScopeNormalizer.normalize_path("  /app/index.js  "), "app/index.js")

    def test_is_in_scope_exact_and_directory(self):
        scopes = ["core/", "tests/test_cli.py"]
        self.assertTrue(ScopeNormalizer.is_in_scope("core/intent_resolver.py", scopes))
        self.assertTrue(ScopeNormalizer.is_in_scope("tests/test_cli.py", scopes))
        self.assertFalse(ScopeNormalizer.is_in_scope("benchmarks/sim.py", scopes))

    def test_is_in_scope_glob_patterns(self):
        scopes = ["core/**/*.py", "*.md"]
        self.assertTrue(ScopeNormalizer.is_in_scope("core/semantics/specification.py", scopes))
        self.assertTrue(ScopeNormalizer.is_in_scope("README.md", scopes))
        self.assertFalse(ScopeNormalizer.is_in_scope("core/semantics/data.json", scopes))

    def test_validate_file_targets_returns_violations(self):
        targets = ["core/cli.py", "secret/passwords.txt"]
        scopes = ["core/"]
        violations = ScopeNormalizer.validate_file_targets(targets, scopes)
        self.assertEqual(len(violations), 1)
        self.assertIn("secret/passwords.txt", violations[0])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest tests/test_contract_validation.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.semantics.scope'`

- [ ] **Step 3: Implement ScopeNormalizer**

Create `core/semantics/scope.py`:

```python
"""
Scope Normalizer for Gobysh v5.1.
Enforces strict file and directory boundaries, cross-platform path normalization,
and glob matching.
"""

import fnmatch
from typing import List


class ScopeNormalizer:
    """Utilities for path and scope validation."""

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize path across OS boundaries (POSIX style, stripped)."""
        if not path:
            return ""
        norm = path.strip().replace("\\", "/")
        while norm.startswith("./"):
            norm = norm[2:]
        norm = norm.strip("/")
        return norm

    @classmethod
    def is_in_scope(cls, file_path: str, scope_patterns: List[str]) -> bool:
        """Check if file_path matches any allowed scope pattern."""
        if not scope_patterns:
            return True  # Unrestricted scope

        norm_file = cls.normalize_path(file_path)

        for pat in scope_patterns:
            norm_pat = cls.normalize_path(pat)
            if not norm_pat:
                continue

            # Exact match
            if norm_file == norm_pat:
                return True

            # Directory prefix match (e.g. "core" matches "core/cli.py")
            if norm_file.startswith(norm_pat + "/"):
                return True

            # Glob pattern match
            if any(char in norm_pat for char in "*?[]"):
                if fnmatch.fnmatch(norm_file, norm_pat):
                    return True
                # Support ** globbing
                if "**" in norm_pat:
                    import re
                    regex_pat = re.escape(norm_pat).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
                    if re.match(f"^{regex_pat}$", norm_file):
                        return True

        return False

    @classmethod
    def validate_file_targets(cls, targets: List[str], allowed_scopes: List[str]) -> List[str]:
        """Return list of error messages for any targets outside allowed scopes."""
        if not allowed_scopes:
            return []
        violations = []
        for target in targets:
            if not cls.is_in_scope(target, allowed_scopes):
                violations.append(
                    f"SCOPE_VIOLATION: Target '{target}' is outside allowed scope: {allowed_scopes}"
                )
        return violations
```

Update `core/semantics/__init__.py` to export `ScopeNormalizer`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest tests/test_contract_validation.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/semantics/scope.py core/semantics/__init__.py tests/test_contract_validation.py
git commit -m "feat(semantics): add ScopeNormalizer with glob matching and path boundaries"
```

---

### Task 3: Advanced Bilingual Negation Handling (`core/semantics/negation.py`)

**Files:**
- Create: `core/semantics/negation.py`
- Modify: `core/semantics/__init__.py`
- Modify: `tests/test_contract_validation.py`

**Interfaces:**
- Produces: `NegationResult`, `NegationHandler` in `core/semantics/negation.py`:
  - `NegationResult(forbidden_targets: List[str], forbidden_actions: List[str], preserve_demanded: bool, negative_phrases: List[str])`
  - `NegationHandler.parse_negations(text: str) -> NegationResult`

- [ ] **Step 1: Write failing test for NegationHandler**

Append to `tests/test_contract_validation.py`:

```python
from core.semantics.negation import NegationHandler


class TestNegationHandler(unittest.TestCase):
    """Test suite for advanced bilingual negation parsing."""

    def test_indonesian_compound_negations(self):
        text = "buatkan auth tapi dilarang keras mengubah schema database dan jangan pernah sentuh file auth.conf"
        res = NegationHandler.parse_negations(text)
        self.assertIn("auth.conf", res.forbidden_targets)
        self.assertTrue(any("schema" in t or "database" in t for t in res.forbidden_targets))
        self.assertGreater(len(res.negative_phrases), 0)

    def test_english_scoped_negations(self):
        text = "refactor the payment module without touching payment_gateway.py or altering legacy tables"
        res = NegationHandler.parse_negations(text)
        self.assertIn("payment_gateway.py", res.forbidden_targets)
        self.assertTrue(res.preserve_demanded)

    def test_preservation_negation_markers(self):
        text = "rapikan fungsi tanpa menghapus backward compatibility"
        res = NegationHandler.parse_negations(text)
        self.assertTrue(res.preserve_demanded)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest tests/test_contract_validation.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.semantics.negation'`

- [ ] **Step 3: Implement NegationHandler**

Create `core/semantics/negation.py`:

```python
"""
Advanced Bilingual Negation Handler for Gobysh v5.1.
Extracts negative constraints, forbidden targets, and preservation directives
from complex Indonesian and English natural language inputs.
"""

from dataclasses import dataclass, field
import re
from typing import List


@dataclass
class NegationResult:
    """Structured extraction of user negative directives."""
    forbidden_targets: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)
    preserve_demanded: bool = False
    negative_phrases: List[str] = field(default_factory=list)


class NegationHandler:
    """Extractor for bilingual negation boundaries."""

    # Regex patterns for negative target extraction
    _PATTERNS = [
        # Indonesian: jangan/tidak boleh/dilarang/tanpa [pernah/keras] ubah/sentuh/edit/hapus/ganti [file] <target>
        r'(?:jangan|tidak boleh|dilarang(?:\s+keras)?|tanpa)\s+(?:pernah\s+)?(?:ubah|mengubah|ganti|edit|sentuh|menyentuh|hapus|menghapus|merusak)\s+(?:file\s+|tabel\s+|table\s+)?([a-zA-Z0-9_./\-]+)',
        # Indonesian: jangan [pernah] sentuh <target>
        r'(?:jangan|tidak boleh|dilarang)\s+(?:pernah\s+)?(?:sentuh|menyentuh)\s+([a-zA-Z0-9_./\-]+)',
        # English: do not/don't/never/without [ever] touch/modify/alter/change/delete/remove [file/table] <target>
        r'(?:do\s+not|don\'?t|never|without)\s+(?:ever\s+)?(?:touch|modify|alter|altering|change|changing|delete|remove|removing)\s+(?:file\s+|table\s+)?([a-zA-Z0-9_./\-]+)',
        # English: forbidden to / prohibited from modifying <target>
        r'(?:forbidden\s+to|prohibited\s+from)\s+(?:touch|modify|change|edit)\s+([a-zA-Z0-9_./\-]+)',
    ]

    _PRESERVATION_MARKERS = [
        "tanpa menghapus", "tanpa merusak", "tanpa ubah method lama",
        "tanpa menghapus method", "tanpa menghapus fungsi", "preserve",
        "keep existing", "jangan hapus", "don't delete", "don't remove",
        "backward compatibility", "kompatibilitas", "legacy",
        "tanpa mengganggu", "without touching", "without breaking",
    ]

    @classmethod
    def parse_negations(cls, text: str) -> NegationResult:
        if not text:
            return NegationResult()

        text_lower = text.lower()
        forbidden_targets: List[str] = []
        negative_phrases: List[str] = []

        # 1. Extract targets matching negative patterns
        for pat in cls._PATTERNS:
            for match in re.finditer(pat, text_lower):
                target = match.group(1).strip()
                phrase = match.group(0).strip()
                if target and target not in ("file", "table", "tabel", "fungsi", "method", "ini"):
                    if target not in forbidden_targets:
                        forbidden_targets.append(target)
                if phrase not in negative_phrases:
                    negative_phrases.append(phrase)

        # 2. Check preservation demand
        preserve_demanded = any(m in text_lower for m in cls._PRESERVATION_MARKERS)

        return NegationResult(
            forbidden_targets=forbidden_targets,
            preserve_demanded=preserve_demanded,
            negative_phrases=negative_phrases,
        )
```

Update `core/semantics/__init__.py` to export `NegationHandler` and `NegationResult`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest tests/test_contract_validation.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/semantics/negation.py core/semantics/__init__.py tests/test_contract_validation.py
git commit -m "feat(semantics): add NegationHandler for deep bilingual negation extraction"
```

---

### Task 4: Contract Validator (`core/semantics/contract_validator.py`)

**Files:**
- Create: `core/semantics/contract_validator.py`
- Modify: `core/semantics/__init__.py`
- Modify: `tests/test_contract_validation.py`

**Interfaces:**
- Produces: `ValidationResult`, `ContractValidator` in `core/semantics/contract_validator.py`:
  - `ValidationResult(valid: bool, errors: List[str], warnings: List[str], severity: str)`
  - `ContractValidator.validate(semantic_ir: SemanticIR, workspace_files: Optional[List[str]]) -> ValidationResult`

- [ ] **Step 1: Write failing test for ContractValidator**

Append to `tests/test_contract_validation.py`:

```python
from core.semantics.contract_validator import ContractValidator, ValidationResult
from core.semantics.intermediate_representation import SemanticIR
from core.semantics.specification import SemanticSpecification, Requirement
from core.semantics.constraints import ConstraintModel


class TestContractValidator(unittest.TestCase):
    """Test suite for ContractValidator."""

    def test_valid_contract_passes(self):
        spec = SemanticSpecification(id="S1", raw_prompt="add foo", requirements=[Requirement(id="R1", description="add foo")])
        ir = SemanticIR(
            specification=spec,
            intent={"action": "create_feature", "target": "core/foo.py"},
            constraints=ConstraintModel(),
        )
        validator = ContractValidator()
        res = validator.validate(ir)
        self.assertTrue(res.valid)
        self.assertEqual(len(res.errors), 0)

    def test_contradiction_fails_validation(self):
        spec = SemanticSpecification(id="S1", raw_prompt="add foo", requirements=[Requirement(id="R1", description="add foo")])
        ir = SemanticIR(
            specification=spec,
            intent={"action": "create_feature", "target": "config.py"},
            constraints=ConstraintModel(forbidden_targets=["config.py"]),
            contradictions=["File config.py is forbidden"],
        )
        validator = ContractValidator()
        res = validator.validate(ir)
        self.assertFalse(res.valid)
        self.assertEqual(res.severity, "HARD")
        self.assertGreater(len(res.errors), 0)

    def test_strict_scope_violation_fails_validation(self):
        spec = SemanticSpecification(id="S1", raw_prompt="add foo", requirements=[Requirement(id="R1", description="add foo", target_entities=["secret/key.pem"])])
        ir = SemanticIR(
            specification=spec,
            intent={"action": "modify", "target": "secret/key.pem"},
            constraints=ConstraintModel(strict_scope=["core/"]),
        )
        validator = ContractValidator()
        res = validator.validate(ir)
        self.assertFalse(res.valid)
        self.assertTrue(any("SCOPE_VIOLATION" in err for err in res.errors))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest tests/test_contract_validation.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.semantics.contract_validator'`

- [ ] **Step 3: Implement ContractValidator**

Create `core/semantics/contract_validator.py`:

```python
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
```

Update `core/semantics/__init__.py` to export `ContractValidator` and `ValidationResult`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest tests/test_contract_validation.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/semantics/contract_validator.py core/semantics/__init__.py tests/test_contract_validation.py
git commit -m "feat(semantics): add ContractValidator for multi-clause consistency and scope boundaries"
```

---

### Task 5: Connect Stage 2 Modules into `core/intent_resolver.py` & Full Verification Gate

**Files:**
- Modify: `core/intent_resolver.py`
- Modify: `core/semantics/intermediate_representation.py` (add `preservation: Optional[PreservationContract]` to `SemanticIR`)
- Test: Full test suite (`python -m unittest discover tests/`)
- Run: `goby gate`

- [ ] **Step 1: Enhance `SemanticIR` with `preservation: Optional[PreservationContract]`**

Update `core/semantics/intermediate_representation.py` to import `PreservationContract` and add `preservation: Optional[PreservationContract] = None` to `SemanticIR`.

- [ ] **Step 2: Connect `NegationHandler`, `ScopeNormalizer`, and `ContractValidator` into `IntentResolver`**

In `core/intent_resolver.py`:
- Use `NegationHandler.parse_negations()` in `_extract_semantic_contract()`.
- Use `ScopeNormalizer.normalize_path()` on target files and strict scope.
- Run `ContractValidator().validate(semantic_ir)` in `resolve()`.
- If `validation_res.valid is False`, append validation errors to `clarification_questions` and set `clarification_needed = True`.

- [ ] **Step 3: Run all unit tests**

Run: `.venv\Scripts\python.exe -m unittest discover tests/`
Expected: PASS (All tests pass including all Stage 1 and Stage 2 test suites)

- [ ] **Step 4: Run Goby Gate check**

Run: `goby gate`
Expected: Exit code 0 (`[GOBY GATE] Ledger clean: 0 unresolved file errors. Workspace ready.`)

- [ ] **Step 5: Commit**

```bash
git add core/intent_resolver.py core/semantics/intermediate_representation.py
git commit -m "feat(intent): connect PreservationContract, NegationHandler, and ContractValidator to IntentResolver"
```
