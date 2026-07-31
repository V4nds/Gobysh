import unittest
import os
from core.universal_memory import UniversalMemoryStore


class TestUniversalMemory(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_universal_consciousness.json"
        self.store = UniversalMemoryStore(memory_file_path=self.test_file)
        self.store.clear_consciousness()

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_crystallize_memory(self):
        mem = self.store.crystallize_memory(
            error_output="RecursionError: maximum recursion depth exceeded at line 42",
            error_type="RecursionError",
            abstract_root_cause="Infinite depth topology",
            universal_heuristic="Topology Bypass: Use stack"
        )
        self.assertEqual(mem.error_type, "RecursionError")
        self.assertEqual(mem.abstract_root_cause, "Infinite depth topology")
        self.assertEqual(mem.universal_heuristic, "Topology Bypass: Use stack")
        self.assertIn("LINE_REF", mem.semantic_signature) # Should abstract line 42

    def test_recall_intuition(self):
        self.store.crystallize_memory(
            error_output="RecursionError: maximum recursion depth exceeded at line 42",
            error_type="RecursionError",
            abstract_root_cause="Infinite depth topology",
            universal_heuristic="Topology Bypass: Use stack"
        )
        
        # Recall with slightly different error but conceptually same
        intuition = self.store.recall_intuition(
            error_output="RecursionError: maximum recursion depth exceeded at line 99",
            error_type="RecursionError"
        )
        self.assertIsNotNone(intuition)
        self.assertEqual(intuition.universal_heuristic, "Topology Bypass: Use stack")

if __name__ == '__main__':
    unittest.main()
