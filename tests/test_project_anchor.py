"""
Unit tests for Project Identity Anchor & Selective Reference Synthesizer (core/semantics/project_anchor.py).
Verifies:
  1. Extraction and identification of project Ground of Being.
  2. 3-Tier reference synthesis (Adopt, Adapt, Reject).
  3. Formulation of IDENTITY_PRESERVATION guardrails.
"""

import os
import tempfile
import unittest
from core.semantics.project_anchor import ProjectIdentityAnchor, ReferenceSynthesisResult


class TestProjectIdentityAnchor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo_dir = self.tmp.name
        # Write mock pyproject.toml
        pyproject_path = os.path.join(self.repo_dir, "pyproject.toml")
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write('''[project]
name = "Gobysh"
version = "5.5.0"
description = "Context Manager & Guardrail Framework untuk AI Coding Agent"
''')
        self.anchor = ProjectIdentityAnchor(repo_root=self.repo_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def test_load_project_identity(self):
        ident = self.anchor.get_identity()
        self.assertEqual(ident.name, "Gobysh")
        self.assertIn("Guardrail", ident.core_purpose)

    def test_3tier_reference_synthesis_rea(self):
        ref = "https://github.com/morluto/rea"
        res = self.anchor.synthesize_reference(ref)
        self.assertIsInstance(res, ReferenceSynthesisResult)
        self.assertTrue(len(res.adopt_principles) > 0)
        self.assertTrue(len(res.adapt_targets) > 0)
        self.assertTrue(len(res.reject_bloat) > 0)
        self.assertIn("IDENTITY_PRESERVATION", res.guardrail_rule)
        self.assertIn("Gobysh", res.guardrail_rule)

    def test_3tier_reference_synthesis_generic(self):
        ref = "https://github.com/someuser/awesome-library"
        res = self.anchor.synthesize_reference(ref)
        self.assertIn("IDENTITY_PRESERVATION", res.guardrail_rule)
        self.assertTrue("adopt" in res.guardrail_rule.lower() and "adapt" in res.guardrail_rule.lower())

    def test_empty_reference_returns_clean(self):
        res = self.anchor.synthesize_reference("")
        self.assertEqual(res.reference, "")
        self.assertEqual(res.guardrail_rule, "")


if __name__ == "__main__":
    unittest.main()
