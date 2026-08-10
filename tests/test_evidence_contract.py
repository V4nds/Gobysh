"""
Unit tests for Goby v4.1 Evidence Contract Engine and Genuine Pre-Output Verification.
"""

import unittest
from core.ccr_engine import CognitiveControlRoom
import core


class TestEvidenceEngine(unittest.TestCase):

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_in_memory_verify_candidate_clean(self):
        code = "x = 100\ny = 200\nz = x + y\nprint(z)"
        res = self.ccr.verify_candidate(code, language="python")
        self.assertTrue(res["verified"])
        self.assertFalse(res["blocked"])
        self.assertEqual(len(res["signals"]), 3)

    def test_in_memory_verify_candidate_undefined_scope(self):
        code = "def process():\n    return missing_price * 10\n"
        res = self.ccr.verify_candidate(code, language="python")
        self.assertFalse(res["verified"])
        self.assertTrue(res["blocked"])

    def test_ts_syntax_check_neuron(self):
        ts_code = "const val: number = 42; function add(a: number, b: number): number { return a + b; }"
        sig = self.ccr.neuron_ts_syntax_check(ts_code)
        self.assertTrue(sig.passed)
        self.assertEqual(sig.neuron_name, "TS_SYNTAX")

    def test_create_evidence_contract(self):
        claim = "Bug fixed in core calculation"
        code = "def calculate_sum(a, b):\n    return a + b\n"
        contract = self.ccr.create_evidence_contract(
            claim=claim,
            code_or_file=code,
            language="python",
            test_command=None
        )
        self.assertEqual(contract["contract_version"], "1.0.0")
        self.assertEqual(contract["claim"], claim)
        self.assertEqual(contract["status"], "VERIFIED")
        self.assertIn("static_analysis", contract["evidence"])

    def test_top_level_package_verify_helper(self):
        res = core.verify("a = 5\nb = a * 2")
        self.assertTrue(res["verified"])


if __name__ == "__main__":
    unittest.main()
