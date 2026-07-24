"""
Unit tests for StateMemoryManager and Crash Recovery Protocol.
"""

import os
import tempfile
import unittest
from core.state_memory import StateMemoryManager


class TestStateMemoryCrashRecovery(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mem_file = os.path.join(self.temp_dir.name, "test_cognitive_map.json")
        self.memory_mgr = StateMemoryManager(memory_file_path=self.mem_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_atomic_write_and_persistence(self):
        self.memory_mgr.set_temporal_variable("checkpoint_task", "TASK_99")
        val = self.memory_mgr.get_temporal_variable("checkpoint_task")
        self.assertEqual(val, "TASK_99")

    def test_crash_recovery_protocol(self):
        # Simulate app crash mid-task
        state = self.memory_mgr.load_state()
        state["active_context"] = {
            "task_id": "CRASHED_TASK_007",
            "error_count": 2,
            "current_state": "RUNNING"
        }
        self.memory_mgr.save_state(state)

        # App re-opens and calls recover_interrupted_session()
        recovered = self.memory_mgr.recover_interrupted_session()

        self.assertEqual(recovered["recovered_state"], "INTERRUPTED_RECOVERED")
        self.assertEqual(recovered["last_task_id"], "CRASHED_TASK_007")
        self.assertEqual(recovered["error_count"], 2)


if __name__ == "__main__":
    unittest.main()
