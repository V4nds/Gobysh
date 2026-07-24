"""
Unit tests for Loop Detection Engine (LDE).
"""

import unittest
from core.lde_detector import LoopDetectionEngine, levenshtein_distance, similarity_ratio


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


if __name__ == "__main__":
    unittest.main()
