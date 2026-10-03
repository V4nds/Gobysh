"""
Unit tests for DialecticalContract and Anti-Sycophancy Intent Engine in Goby v5.2.
"""

import unittest
from core.intent_resolver import IntentResolver, IntentNode
from core.semantics.specification import DialecticalContract, SemanticSpecification


class TestDialecticalContract(unittest.TestCase):

    def test_dialectical_contract_serialization(self):
        contract = DialecticalContract(
            naive_assumptions=["Assumes trivial state without synchronization."],
            tradeoffs_identified=["Risk of UI boxification."],
            counter_vector="Use inline telemetry instead of cards.",
            anti_template_flag=True,
            is_sycophantic=True,
        )
        data = contract.to_dict()
        self.assertEqual(data["naive_assumptions"], ["Assumes trivial state without synchronization."])
        self.assertTrue(data["anti_template_flag"])
        self.assertTrue(data["is_sycophantic"])

        deserialized = DialecticalContract.from_dict(data)
        self.assertEqual(deserialized.counter_vector, "Use inline telemetry instead of cards.")
        self.assertTrue(deserialized.is_sycophantic)

    def test_semantic_specification_with_dialectical(self):
        dia = DialecticalContract(
            naive_assumptions=["naive"],
            tradeoffs_identified=["tradeoff"],
            counter_vector="counter",
            anti_template_flag=False,
            is_sycophantic=True,
        )
        spec = SemanticSpecification(
            id="SPEC-001",
            raw_prompt="buat fitur baru",
            dialectical_contract=dia,
        )
        d = spec.to_dict()
        self.assertIn("dialectical_contract", d)
        self.assertTrue(d["dialectical_contract"]["is_sycophantic"])

        loaded = SemanticSpecification.from_dict(d)
        self.assertIsNotNone(loaded.dialectical_contract)
        self.assertEqual(loaded.dialectical_contract.counter_vector, "counter")

    def test_intent_resolver_generates_dialectical_alert_for_ui(self):
        resolver = IntentResolver()
        tree = resolver.resolve("desain tampilan dashboard dengan tema modern")
        self.assertIsNotNone(tree.dialectical_contract)
        self.assertTrue(tree.dialectical_contract.is_sycophantic)
        self.assertTrue(tree.dialectical_contract.anti_template_flag)
        self.assertTrue(len(tree.dialectical_contract.tradeoffs_identified) > 0)
        self.assertIn("boxification", tree.dialectical_contract.tradeoffs_identified[0].lower())

    def test_intent_resolver_feature_creation_tradeoff(self):
        resolver = IntentResolver()
        tree = resolver.resolve("buat fitur pengukuran sudut baru di canvas")
        self.assertIsNotNone(tree.dialectical_contract)
        self.assertTrue(tree.dialectical_contract.is_sycophantic)
        self.assertTrue(any("duplikasi" in t.lower() or "duplication" in t.lower() for t in tree.dialectical_contract.tradeoffs_identified))


if __name__ == "__main__":
    unittest.main()
