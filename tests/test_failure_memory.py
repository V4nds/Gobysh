"""
Unit tests for Failure Pattern Store — cross-session error memory.
"""

import os
import shutil
import tempfile
import unittest
from core.failure_memory import FailurePatternStore, FailureFingerprint


class TestFailurePatternStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory_path = os.path.join(self.temp_dir, "test_failure_memory.json")
        self.store = FailurePatternStore(memory_file_path=self.memory_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_failure_returns_fingerprint(self):
        fp = self.store.record_failure(
            error_output="TypeError: Cannot read property 'map' of undefined",
            error_type="TypeError",
            root_cause="Variable 'data' was not initialized before .map() call",
            solution="Added null check: if (data) { data.map(...) }",
            language="javascript",
        )
        self.assertIsInstance(fp, FailureFingerprint)
        self.assertEqual(fp.error_type, "TypeError")
        self.assertEqual(fp.language, "javascript")
        self.assertTrue(len(fp.error_hash) > 0)

    def test_match_known_pattern_exact(self):
        self.store.record_failure(
            error_output="TypeError: Cannot read property 'map' of undefined",
            error_type="TypeError",
            root_cause="Uninitialized data",
            solution="Add null check",
            language="javascript",
        )
        match = self.store.match_known_pattern(
            "TypeError: Cannot read property 'map' of undefined"
        )
        self.assertIsNotNone(match)
        self.assertEqual(match.error_type, "TypeError")

    def test_match_known_pattern_similar(self):
        self.store.record_failure(
            error_output="TypeError: Cannot read property 'map' of undefined at UserList.render",
            error_type="TypeError",
            root_cause="Uninitialized data",
            solution="Add null check",
            language="javascript",
        )
        # Slightly different error (different component, same root cause)
        match = self.store.match_known_pattern(
            "TypeError: Cannot read property 'map' of undefined at ProductList.render"
        )
        self.assertIsNotNone(match)

    def test_no_match_for_unrelated_error(self):
        self.store.record_failure(
            error_output="TypeError: Cannot read property 'map' of undefined",
            error_type="TypeError",
            root_cause="Uninitialized data",
            solution="Add null check",
            language="javascript",
        )
        match = self.store.match_known_pattern(
            "SyntaxError: Unexpected token ';' at line 42"
        )
        self.assertIsNone(match)

    def test_persistence_across_instances(self):
        self.store.record_failure(
            error_output="ZeroDivisionError: division by zero",
            error_type="ZeroDivisionError",
            root_cause="Missing denominator check",
            solution="Added if denominator != 0 guard",
            language="python",
        )

        # Create new instance pointing to same file (simulates new session)
        store2 = FailurePatternStore(memory_file_path=self.memory_path)
        match = store2.match_known_pattern("ZeroDivisionError: division by zero")
        self.assertIsNotNone(match)
        self.assertEqual(match.error_type, "ZeroDivisionError")

    def test_get_all_patterns(self):
        self.store.record_failure("Error A", "TypeA", "cause_a", "fix_a", "python")
        self.store.record_failure("Error B", "TypeB", "cause_b", "fix_b", "javascript")
        patterns = self.store.get_all_patterns()
        self.assertEqual(len(patterns), 2)

    def test_clear_patterns(self):
        self.store.record_failure("Error A", "TypeA", "cause_a", "fix_a", "python")
        self.store.clear_patterns()
        patterns = self.store.get_all_patterns()
        self.assertEqual(len(patterns), 0)

    def test_match_increments_success_count(self):
        self.store.record_failure(
            error_output="ImportError: No module named 'requests'",
            error_type="ImportError",
            root_cause="Package not installed",
            solution="pip install requests",
            language="python",
        )
        # First match
        match1 = self.store.match_known_pattern("ImportError: No module named 'requests'")
        self.assertIsNotNone(match1)
        initial_count = match1.success_count

        # Second match — should increment
        match2 = self.store.match_known_pattern("ImportError: No module named 'requests'")
        self.assertIsNotNone(match2)
        self.assertEqual(match2.success_count, initial_count + 1)


if __name__ == "__main__":
    unittest.main()
