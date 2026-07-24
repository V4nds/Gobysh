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


if __name__ == "__main__":
    unittest.main()
