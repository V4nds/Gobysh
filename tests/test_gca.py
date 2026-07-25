"""
Unit tests for Grounded Compiler Arbitrage (GCA).
"""

import unittest
from core.gca_runner import GroundedCompilerArbitrage


class TestGroundedCompilerArbitrage(unittest.TestCase):

    def setUp(self):
        self.gca = GroundedCompilerArbitrage(default_timeout=5.0)

    def test_run_command_success(self):
        res = self.gca.run_python_snippet("print('Goby GCA Online')")
        self.assertTrue(res.is_success)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("Goby GCA Online", res.stdout)

    def test_run_command_failure(self):
        res = self.gca.run_python_snippet("raise ValueError('Empirical Failure Test')")
        self.assertFalse(res.is_success)
        self.assertNotEqual(res.exit_code, 0)
        self.assertIn("ValueError: Empirical Failure Test", res.stderr)

    def test_run_timeout(self):
        res = self.gca.run_python_snippet("import time; time.sleep(10)", timeout=1.0)
        self.assertFalse(res.is_success)
        self.assertIn("timed out", res.stderr.lower())

    # --- Polyglot GCA Tests (v1.2.0) ---

    def test_is_node_available_returns_bool(self):
        result = self.gca.is_node_available()
        self.assertIsInstance(result, bool)

    def test_run_js_snippet_when_node_available(self):
        if not self.gca.is_node_available():
            self.skipTest("Node.js not available in PATH")
        res = self.gca.run_js_snippet("console.log('Goby JS Online')")
        self.assertTrue(res.is_success)
        self.assertIn("Goby JS Online", res.stdout)

    def test_run_js_snippet_when_node_unavailable(self):
        gca = GroundedCompilerArbitrage(default_timeout=5.0)
        gca._node_path = "nonexistent_node_binary_xyz"
        res = gca.run_js_snippet("console.log('test')")
        self.assertFalse(res.is_success)
        self.assertIn("not available", res.stderr.lower())

    def test_run_test_suite_returns_structured_result(self):
        from core.output_parsers import StructuredTestResult
        result = self.gca.run_test_suite("python -m unittest tests.test_gca.TestGroundedCompilerArbitrage.test_run_command_success -v")
        self.assertIsInstance(result, StructuredTestResult)
        self.assertEqual(result.runner, "pytest")
        self.assertTrue(result.is_success)

    def test_run_test_suite_with_explicit_runner(self):
        from core.output_parsers import StructuredTestResult
        result = self.gca.run_test_suite(
            "python -m unittest tests.test_gca.TestGroundedCompilerArbitrage.test_run_command_success -v",
            runner="pytest"
        )
        self.assertIsInstance(result, StructuredTestResult)


if __name__ == "__main__":
    unittest.main()
