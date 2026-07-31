import unittest
from core.consciousness_engine import ConsciousnessEngine
from core.universal_memory import UniversalMemoryStore
import os

class TestConsciousnessEngine(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_conscious.json"
        self.store = UniversalMemoryStore(memory_file_path=self.test_file)
        self.engine = ConsciousnessEngine(universal_store=self.store)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_trigger_reflection(self):
        past_errors = [
            {"error_type": "RecursionError", "error_output": "maximum recursion depth exceeded at line 10"}
        ]
        # Trigger success reflection
        self.engine.trigger_consciousness_reflection(
            final_successful_output="Success!",
            past_errors=past_errors
        )
        
        memories = self.store.get_all_memories()
        self.assertEqual(len(memories), 1)
        self.assertIn("Topology Bypass", memories[0].universal_heuristic)

if __name__ == '__main__':
    unittest.main()
