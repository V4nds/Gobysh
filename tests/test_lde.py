"""
Unit tests for Loop Detection Engine (LDE).
"""

import os
import shutil
import tempfile
import unittest
from core.lde_detector import LoopDetectionEngine, levenshtein_distance, similarity_ratio
from core.failure_memory import FailurePatternStore


class TestLoopDetectionEngine(unittest.TestCase):

    def setUp(self):
        self.lde = LoopDetectionEngine(threshold_similarity=0.85, max_history_size=10)

    def test_levenshtein_distance(self):
        self.assertEqual(levenshtein_distance("kitten", "sitting"), 3)
        self.assertEqual(levenshtein_distance("same", "same"), 0)

    def test_similarity_ratio(self):
        self.assertAlmostEqual(similarity_ratio("hello", "hello"), 1.0)
        self.assertGreater(similarity_ratio("error in line 10", "error in line 10"), 0.99)

    def test_compiler_loop_detection(self):
        err_msg = "TypeError: cannot read property 'id' of undefined at Object.<anonymous> (index.js:15:10)"
        
        # 1st attempt - No loop
        res1 = self.lde.record_attempt("const a = 1;", err_msg)
        self.assertFalse(res1.is_loop_detected)

        # 2nd attempt - No loop yet
        res2 = self.lde.record_attempt("const a = 2;", err_msg)
        self.assertFalse(res2.is_loop_detected)

        # 3rd attempt - Loop detected!
        res3 = self.lde.record_attempt("const a = 3;", err_msg)
        self.assertTrue(res3.is_loop_detected)
        self.assertEqual(res3.loop_type, "COMPILER_LOOP")

    def test_paradoxical_oscillation_detection(self):
        err_a = "Fatal Error in Module A: Class NotFoundException"
        err_b = "Fatal Error in Module B: NullPointerDereference"

        self.lde.record_attempt("code_v1", err_a)
        self.lde.record_attempt("code_v2", err_b)
        self.lde.record_attempt("code_v3", err_a)
        res = self.lde.record_attempt("code_v4", err_b)

        self.assertTrue(res.is_loop_detected)
        self.assertEqual(res.loop_type, "PARADOXICAL_OSCILLATION")


class TestLearningLDE(unittest.TestCase):
    """Tests for preemptive bypass via cross-session failure memory."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory_path = os.path.join(self.temp_dir, "test_patterns.json")
        self.store = FailurePatternStore(memory_file_path=self.memory_path)
        self.lde = LoopDetectionEngine(
            threshold_similarity=0.85,
            max_history_size=10,
            failure_store=self.store,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_check_preemptive_with_known_pattern(self):
        # Record a past failure
        self.store.record_failure(
            error_output="TypeError: Cannot read property 'map' of undefined",
            error_type="TypeError",
            root_cause="Data not initialized before .map() call",
            solution="Added null check before calling .map()",
            language="javascript",
        )

        # Now check preemptive — should recognize instantly (no 3-iteration wait)
        result = self.lde.check_preemptive(
            "TypeError: Cannot read property 'map' of undefined"
        )
        self.assertIsNotNone(result)
        self.assertTrue(result.is_loop_detected)
        self.assertEqual(result.loop_type, "PREEMPTIVE_KNOWN_PATTERN")
        self.assertIsNotNone(result.known_pattern)
        self.assertEqual(result.known_pattern.error_type, "TypeError")

    def test_check_preemptive_no_match(self):
        result = self.lde.check_preemptive("SomeNewError: never seen before")
        self.assertIsNone(result)

    def test_record_resolution_persists(self):
        self.lde.record_resolution(
            error_output="ImportError: No module named 'flask'",
            error_type="ImportError",
            root_cause="Package not in virtualenv",
            solution="pip install flask",
            language="python",
        )

        # Verify it persists
        match = self.store.match_known_pattern("ImportError: No module named 'flask'")
        self.assertIsNotNone(match)

    def test_lde_without_failure_store_still_works(self):
        # Original LDE behavior — no failure store
        lde_basic = LoopDetectionEngine(threshold_similarity=0.85)
        result = lde_basic.check_preemptive("any error")
        self.assertIsNone(result)

        # Normal record_attempt still works
        res = lde_basic.record_attempt("code", "some error")
        self.assertFalse(res.is_loop_detected)


if __name__ == "__main__":
    unittest.main()
