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


if __name__ == "__main__":
    unittest.main()

