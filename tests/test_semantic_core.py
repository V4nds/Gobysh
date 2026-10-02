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
