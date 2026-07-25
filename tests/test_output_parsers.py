"""
Unit tests for Output Parsers module — polyglot test result parsing.
"""

import unittest
from core.output_parsers import (
    StructuredTestResult,
    TestFailureDetail,
    PytestParser,
    JestParser,
    GenericParser,
    detect_runner,
    get_parser,
)


class TestDetectRunner(unittest.TestCase):

    def test_detect_pytest(self):
        self.assertEqual(detect_runner("pytest tests/ -v"), "pytest")

    def test_detect_python_unittest(self):
        self.assertEqual(detect_runner("python -m unittest discover tests/"), "pytest")

    def test_detect_jest(self):
        self.assertEqual(detect_runner("npx jest --coverage"), "jest")

    def test_detect_npm_test(self):
        self.assertEqual(detect_runner("npm test"), "jest")

    def test_detect_unknown_falls_back_to_generic(self):
        self.assertEqual(detect_runner("cargo test"), "generic")


class TestPytestParser(unittest.TestCase):

    def setUp(self):
        self.parser = PytestParser()

    def test_parse_all_passed(self):
        stdout = (
            "tests/test_gca.py::test_run_command_success PASSED\n"
            "tests/test_gca.py::test_run_command_failure PASSED\n"
            "\n"
            "========= 2 passed in 0.45s =========\n"
        )
        result = self.parser.parse(stdout, "", 0)
        self.assertTrue(result.is_success)
        self.assertEqual(result.total, 2)
        self.assertEqual(result.passed, 2)
        self.assertEqual(result.failed, 0)
        self.assertEqual(result.runner, "pytest")

    def test_parse_with_failures(self):
        stdout = (
            "tests/test_math.py::test_add PASSED\n"
            "tests/test_math.py::test_divide FAILED\n"
            "\n"
            "FAILED tests/test_math.py::test_divide - ZeroDivisionError: division by zero\n"
            "\n"
            "========= 1 failed, 1 passed in 0.32s =========\n"
        )
        result = self.parser.parse(stdout, "", 1)
        self.assertFalse(result.is_success)
        self.assertEqual(result.total, 2)
        self.assertEqual(result.passed, 1)
        self.assertEqual(result.failed, 1)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.failures[0].test_name, "test_divide")
        self.assertEqual(result.failures[0].file_path, "tests/test_math.py")

    def test_parse_with_errors_and_skipped(self):
        stdout = "========= 1 failed, 2 passed, 1 skipped, 1 error in 1.20s =========\n"
        result = self.parser.parse(stdout, "", 1)
        self.assertFalse(result.is_success)
        self.assertEqual(result.failed, 1)
        self.assertEqual(result.passed, 2)
        self.assertEqual(result.skipped, 1)
        self.assertEqual(result.errors, 1)


class TestJestParser(unittest.TestCase):

    def setUp(self):
        self.parser = JestParser()

    def test_parse_all_passed(self):
        stdout = (
            " PASS  src/utils.test.js\n"
            "  ✓ adds numbers (3 ms)\n"
            "  ✓ subtracts numbers (1 ms)\n"
            "\n"
            "Tests:       2 passed, 2 total\n"
            "Time:        1.234 s\n"
        )
        result = self.parser.parse(stdout, "", 0)
        self.assertTrue(result.is_success)
        self.assertEqual(result.total, 2)
        self.assertEqual(result.passed, 2)
        self.assertEqual(result.runner, "jest")

    def test_parse_with_failures(self):
        stderr = (
            " FAIL  src/auth.test.js\n"
            "  ✕ should validate token (5 ms)\n"
            "\n"
            "  ● should validate token\n"
            "\n"
            "    TypeError: Cannot read property 'verify' of undefined\n"
            "\n"
            "      at Object.<anonymous> (src/auth.test.js:12:18)\n"
            "\n"
            "Tests:       1 failed, 1 passed, 2 total\n"
        )
        result = self.parser.parse("", stderr, 1)
        self.assertFalse(result.is_success)
        self.assertEqual(result.total, 2)
        self.assertEqual(result.failed, 1)
        self.assertEqual(result.passed, 1)
        self.assertEqual(len(result.failures), 1)
        self.assertIn("validate token", result.failures[0].test_name)


class TestGenericParser(unittest.TestCase):

    def setUp(self):
        self.parser = GenericParser()

    def test_parse_success(self):
        result = self.parser.parse("All checks passed", "", 0)
        self.assertTrue(result.is_success)
        self.assertEqual(result.runner, "generic")

    def test_parse_failure(self):
        result = self.parser.parse("", "error: compilation failed", 1)
        self.assertFalse(result.is_success)
        self.assertEqual(result.failed, 1)

    def test_parse_extracts_error_lines(self):
        stderr = (
            "error[E0308]: mismatched types\n"
            "  --> src/main.rs:15:5\n"
            "thread 'main' panicked at 'assertion failed'\n"
        )
        result = self.parser.parse("", stderr, 1)
        self.assertFalse(result.is_success)
        self.assertGreaterEqual(len(result.failures), 1)


class TestGetParser(unittest.TestCase):

    def test_get_pytest_parser(self):
        self.assertIsInstance(get_parser("pytest"), PytestParser)

    def test_get_jest_parser(self):
        self.assertIsInstance(get_parser("jest"), JestParser)

    def test_get_generic_parser(self):
        self.assertIsInstance(get_parser("generic"), GenericParser)

    def test_get_unknown_returns_generic(self):
        self.assertIsInstance(get_parser("unknown_runner"), GenericParser)


if __name__ == "__main__":
    unittest.main()
