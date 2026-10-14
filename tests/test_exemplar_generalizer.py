"""
Unit tests for Exemplar Induction & Variation Engine (core/spider/exemplar_generalizer.py).
Verifies:
  1. Concept lifting from concrete exemplars to abstract domains.
  2. Generation of complementary variations (preventing literal parroting).
  3. Formulation of actionable ANTI_PARROTING_EXEMPLAR_INDUCTION rules.
"""

import unittest
from core.spider.exemplar_generalizer import ExemplarGeneralizer, ExemplarInductionResult


class TestExemplarGeneralizer(unittest.TestCase):
    def setUp(self):
        self.generalizer = ExemplarGeneralizer()

    def test_concept_lifting_geometry(self):
        exemplars = ["penggaris", "busur derajat"]
        res = self.generalizer.induce_and_expand(exemplars)
        self.assertEqual(res.inferred_domain, "geometric_measurement_tools")
        self.assertTrue(len(res.variations) > 0)
        self.assertIn("ANTI_PARROTING_EXEMPLAR_INDUCTION", res.guardrail_rule)
        self.assertIn("penggaris", res.guardrail_rule)

    def test_concept_lifting_auth(self):
        exemplars = ["jwt token", "session cookie"]
        res = self.generalizer.induce_and_expand(exemplars)
        self.assertEqual(res.inferred_domain, "authentication_strategies")
        self.assertTrue(any("oauth" in v.lower() or "sso" in v.lower() or "api" in v.lower() for v in res.variations))

    def test_fallback_domain_lifting(self):
        exemplars = ["widget_alpha", "widget_beta"]
        res = self.generalizer.induce_and_expand(exemplars)
        self.assertTrue(len(res.inferred_domain) > 0)
        self.assertIn("ANTI_PARROTING", res.guardrail_rule)

    def test_empty_exemplars_returns_empty_result(self):
        res = self.generalizer.induce_and_expand([])
        self.assertEqual(res.inferred_domain, "generic")
        self.assertEqual(res.variations, [])
        self.assertEqual(res.guardrail_rule, "")


if __name__ == "__main__":
    unittest.main()
