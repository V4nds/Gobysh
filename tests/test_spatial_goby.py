"""
Deep and Aggressive Spatial Cognitive Benchmark for Goby Framework.
Tests spatial navigation, 2D grid pathing, spatial loop detection & LDE bypass,
concurrent state memory locking, and orchestrated spatial sub-tasks.
"""

import unittest
import threading
import time
import tempfile
import os
from core.state_memory import StateMemoryManager
from core.lde_detector import LoopDetectionEngine
from core.orchestrator import MultitaskOrchestrator, TaskStatus
from core.ccr_engine import CognitiveControlRoom


class TestSpatialGobyCognition(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.memory_file = os.path.join(self.temp_dir.name, "spatial_cognitive_map.json")
        self.state_mgr = StateMemoryManager(memory_file_path=self.memory_file)
        self.lde = LoopDetectionEngine(max_history_size=10)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_spatial_grid_loop_detection_and_bypass(self):
        """
        Simulates an agent trapped in an infinite spatial loop (e.g. Mario bouncing between two blocks).
        Verifies Goby LDE detects the spatial oscillation and triggers a Neuro-Cognitive Bypass.
        """
        spatial_trace = [
            ("mario_attempt_1", "position: (3,2), action: MOVE_RIGHT"),
            ("mario_attempt_2", "position: (3,3), action: MOVE_LEFT"),
            ("mario_attempt_3", "position: (3,2), action: MOVE_RIGHT"),
            ("mario_attempt_4", "position: (3,3), action: MOVE_LEFT"),
        ]

        loop_analysis = None
        for code, output in spatial_trace:
            res = self.lde.record_attempt(code, output)
            if res.is_loop_detected:
                loop_analysis = res
                break

        self.assertIsNotNone(loop_analysis, "LDE failed to detect spatial infinite loop!")
        self.assertTrue(loop_analysis.is_loop_detected)
        self.assertIn(loop_analysis.suggested_action, ["TRIGGER_CANTOR_LATERAL_BYPASS", "TRIGGER_AXIOM_SHIFT_EPIPHANY"])

        # Apply LDE Bypass: Cantor Lateral Leap (warps Mario out of spatial oscillation)
        new_position = (3, 5)
        self.state_mgr.set_temporal_variable("mario_spatial_pos", new_position)
        
        saved_pos = self.state_mgr.get_temporal_variable("mario_spatial_pos")
        self.assertEqual(saved_pos, (3, 5))

    def test_spatial_concurrent_thread_memory_stress(self):
        """
        Aggressively stress-tests StateMemoryManager with 20 parallel worker threads
        updating spatial coordinates simultaneously to ensure zero data corruption or lock contention.
        """
        thread_count = 20
        errors = []

        def worker(thread_id: int):
            try:
                for i in range(10):
                    key = f"thread_{thread_id}_step_{i}"
                    val = {"x": thread_id * 10 + i, "y": i * 2, "status": "ACTIVE"}
                    self.state_mgr.set_temporal_variable(key, val)
                    retrieved = self.state_mgr.get_temporal_variable(key)
                    if retrieved != val:
                        errors.append(f"Mismatch in thread {thread_id}: expected {val}, got {retrieved}")
            except Exception as e:
                errors.append(f"Exception in thread {thread_id}: {e}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread stress test encountered errors: {errors}")
        state = self.state_mgr.load_state()
        self.assertIn("temporal_state", state)
        self.assertGreaterEqual(len(state["temporal_state"]), thread_count * 10)

    def test_spatial_physics_ccr_validation(self):
        """
        Evaluates spatial physics code (gravity, collision, trajectory calculation) through Goby CCR Neurons.
        """
        valid_spatial_physics_code = '''
def calculate_mario_trajectory(pos_x, pos_y, vx, vy, gravity=0.5):
    next_x = pos_x + vx
    next_y = pos_y + vy - gravity
    is_grounded = next_y <= 0
    if is_grounded:
        next_y = 0
        vy = 0
    return {"x": next_x, "y": next_y, "is_grounded": is_grounded}
'''
        ccr = CognitiveControlRoom()
        syn_sig = ccr.neuron_syntax_check(valid_spatial_physics_code)
        self.assertTrue(syn_sig.passed, "Valid physics code failed syntax check")

        scope_sig = ccr.neuron_scope_check(valid_spatial_physics_code)
        self.assertTrue(scope_sig.passed, "Valid physics code failed scope check")

    def test_spatial_orchestrator_multi_agent_pipeline(self):
        """
        Simulates an orchestrated 4-agent spatial Mario pipeline using Goby MultitaskOrchestrator.
        """
        orchestrator = MultitaskOrchestrator(max_workers=4, memory_mgr=self.state_mgr)

        # 1. Perception Task (Scans 10x10 spatial grid ahead)
        def scan_spatial_grid():
            time.sleep(0.01)
            return {"grid_size": (10, 10), "goombas": [(4, 0), (7, 0)], "gaps": [(5, 0)]}

        # 2. Physics & Trajectory Task (Reads output from Perception Task)
        def compute_trajectory():
            time.sleep(0.01)
            grid = orchestrator.completed_tasks["t1_perception"].result
            self.assertIsNotNone(grid)
            return {"jump_vector": (2, 4), "target_x": 6}

        # 3. Action Dispatcher Task (Reads output from Physics Task)
        def dispatch_mario_action():
            time.sleep(0.01)
            traj = orchestrator.completed_tasks["t2_physics"].result
            return f"Mario jumped over gap to x={traj.get('target_x')}"

        # 4. Memory Crystallization Task (Reads output from Action Task)
        def crystallize_spatial_route():
            res = orchestrator.completed_tasks["t3_action"].result
            return f"CRISTALLIZED_ROUTE: {res}"

        orchestrator.add_task("t1_perception", "Perception Grid Scan", scan_spatial_grid, priority=1)
        orchestrator.add_task("t2_physics", "Trajectory Physics", compute_trajectory, depends_on=["t1_perception"], priority=1)
        orchestrator.add_task("t3_action", "Action Dispatcher", dispatch_mario_action, depends_on=["t2_physics"], priority=1)
        orchestrator.add_task("t4_memory", "Memory Crystallization", crystallize_spatial_route, depends_on=["t3_action"], priority=1)

        results = orchestrator.execute_all()

        for tid, task in results.items():
            self.assertEqual(task.status, TaskStatus.SUCCESS, f"Task {tid} failed: {task.error}")

        self.assertIn("CRISTALLIZED_ROUTE", results["t4_memory"].result)


if __name__ == "__main__":
    unittest.main()
