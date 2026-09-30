"""
Unit tests for Goby Deterministic Semantic Alignment Engine.
Measures Faithfulness, Context Relevance, and Semantic Similarity (Indonesian -> Code).
"""

import unittest
from core.ccr_engine import CognitiveControlRoom, GateType
from core.intent_resolver import IntentResolver, SemanticContract
from core.neurons.semantics import neuron_semantic_alignment


class TestSemanticAlignmentNeuron(unittest.TestCase):

    def setUp(self):
        self.ccr = CognitiveControlRoom()
        self.resolver = IntentResolver()

    # -----------------------------------------------------------------------
    # Basic & No-Contract Tests
    # -----------------------------------------------------------------------

    def test_semantic_alignment_with_no_contract_passes(self):
        code = "def add(a, b):\n    return a + b\n"
        sig = neuron_semantic_alignment(self.ccr, code, contract=None)
        self.assertTrue(sig.passed)
        self.assertEqual(sig.neuron_name, "SEMANTIC_ALIGNMENT")
        self.assertEqual(sig.gate_type, GateType.SOFT)

    def test_semantic_alignment_syntax_error_handled(self):
        code = "def broken_syntax(:\n"
        sig = neuron_semantic_alignment(self.ccr, code)
        self.assertFalse(sig.passed)
        self.assertEqual(sig.gate_type, GateType.HARD)
        self.assertIn("Syntax error", sig.message)

    # -----------------------------------------------------------------------
    # Faithfulness Tests (Forbidden targets & Preservation)
    # -----------------------------------------------------------------------

    def test_faithfulness_passes_clean_addition(self):
        code = "def authenticate_user(token):\n    if not token:\n        raise ValueError('Invalid token')\n    return True\n"
        contract = SemanticContract(
            forbidden_targets=["config.py", "database"],
            preserve_existing=False,
            expected_traits=["auth", "validation"]
        )
        sig = neuron_semantic_alignment(self.ccr, code, contract=contract)
        self.assertTrue(sig.passed)
        self.assertEqual(sig.evidence["faithfulness_score"], 1.0)
        self.assertGreaterEqual(sig.evidence["semantic_similarity_score"], 0.8)

    def test_faithfulness_fails_when_forbidden_target_modified(self):
        code = "def update_database(query):\n    return execute(query)\n"
        contract = SemanticContract(
            forbidden_targets=["database"],
            preserve_existing=False
        )
        sig = neuron_semantic_alignment(self.ccr, code, contract=contract)
        self.assertFalse(sig.passed)
        self.assertEqual(sig.gate_type, GateType.HARD)
        self.assertLess(sig.evidence["faithfulness_score"], 0.5)
        self.assertIn("database", str(sig.evidence["violations"]))

    def test_faithfulness_fails_when_deleting_existing_method(self):
        original = "def existing_worker():\n    pass\n\ndef helper():\n    pass\n"
        new_code = "def helper():\n    pass\n"  # existing_worker deleted!
        contract = SemanticContract(preserve_existing=True)
        sig = neuron_semantic_alignment(self.ccr, new_code, contract=contract, original_code=original)
        self.assertFalse(sig.passed)
        self.assertLess(sig.evidence["faithfulness_score"], 1.0)
        self.assertIn("existing_worker", str(sig.evidence["violations"]))

    def test_faithfulness_passes_when_preserving_existing(self):
        original = "def existing_worker():\n    pass\n"
        new_code = "def existing_worker():\n    pass\n\ndef new_feature():\n    return 42\n"
        contract = SemanticContract(preserve_existing=True)
        sig = neuron_semantic_alignment(self.ccr, new_code, contract=contract, original_code=original)
        self.assertTrue(sig.passed)
        self.assertEqual(sig.evidence["faithfulness_score"], 1.0)

    # -----------------------------------------------------------------------
    # Context Relevance Tests (Scope containment)
    # -----------------------------------------------------------------------

    def test_context_relevance_high_when_scoped(self):
        code = "class AuthService:\n    def login(self, u, p):\n        return True\n"
        contract = SemanticContract(strict_scope=["auth", "login"])
        sig = neuron_semantic_alignment(self.ccr, code, contract=contract)
        self.assertGreaterEqual(sig.evidence["context_relevance_score"], 0.8)

    def test_context_relevance_low_when_scope_drift(self):
        code = "class CatAnimation:\n    def purr(self):\n        pass\n"
        contract = SemanticContract(strict_scope=["payment", "invoice"])
        sig = neuron_semantic_alignment(self.ccr, code, contract=contract)
        self.assertLess(sig.evidence["context_relevance_score"], 0.5)

    # -----------------------------------------------------------------------
    # Semantic Similarity Tests (Indonesian Traits -> AST Constructs)
    # -----------------------------------------------------------------------

    def test_semantic_similarity_validates_validation_trait(self):
        code = "def check_age(age):\n    if age < 0:\n        raise ValueError('Negative age')\n    return age\n"
        contract = SemanticContract(expected_traits=["validation"])
        sig = neuron_semantic_alignment(self.ccr, code, contract=contract)
        self.assertGreaterEqual(sig.evidence["semantic_similarity_score"], 0.8)
        self.assertIn("validation", sig.evidence["matched_traits"])

    def test_semantic_similarity_penalizes_missing_trait(self):
        code = "def compute():\n    return 1 + 1\n"
        contract = SemanticContract(expected_traits=["validation", "auth"])
        sig = neuron_semantic_alignment(self.ccr, code, contract=contract)
        self.assertLess(sig.evidence["semantic_similarity_score"], 0.5)

    # -----------------------------------------------------------------------
    # End-to-End Indonesian Intent -> Semantic Alignment Tests
    # -----------------------------------------------------------------------

    def test_end_to_end_indonesian_intent_passes(self):
        user_prompt = "buatkan fungsi validasi email tanpa merusak fungsi lama dan jangan ubah database"
        intent_tree = self.resolver.resolve(user_prompt)

        original_code = "def send_email(to, body):\n    return True\n"
        new_code = """
def send_email(to, body):
    return True

def validate_email(email):
    if '@' not in email:
        raise ValueError('Invalid email format')
    return True
"""
        sig = neuron_semantic_alignment(
            self.ccr,
            new_code,
            contract=intent_tree.semantic_contract,
            original_code=original_code
        )

        self.assertTrue(sig.passed)
        self.assertEqual(sig.evidence["faithfulness_score"], 1.0)
        self.assertGreaterEqual(sig.evidence["context_relevance_score"], 0.7)
        self.assertGreaterEqual(sig.evidence["semantic_similarity_score"], 0.8)


if __name__ == "__main__":
    unittest.main()
