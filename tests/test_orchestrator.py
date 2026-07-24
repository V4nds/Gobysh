"""
Unit tests for Multitask Orchestrator Engine.
"""

import time
import unittest
from core.orchestrator import MultitaskOrchestrator, TaskStatus


class TestMultitaskOrchestrator(unittest.TestCase):

    def setUp(self):
        self.orchestrator = MultitaskOrchestrator(max_workers=4)

    def test_parallel_independent_tasks(self):
        def sample_work(item_id, sleep_time):
            time.sleep(sleep_time)
            return f"Done {item_id}"

        self.orchestrator.add_task("task1", "Task 1", sample_work, args=(1, 0.1))
        self.orchestrator.add_task("task2", "Task 2", sample_work, args=(2, 0.1))
        self.orchestrator.add_task("task3", "Task 3", sample_work, args=(3, 0.1))

        results = self.orchestrator.execute_all()

        self.assertEqual(len(results), 3)
        self.assertTrue(all(t.status == TaskStatus.SUCCESS for t in results.values()))
        self.assertEqual(results["task1"].result, "Done 1")
        self.assertEqual(results["task2"].result, "Done 2")

    def test_task_dependencies(self):
        execution_order = []

        def step1():
            execution_order.append("Step 1")
            return 100

        def step2(dep_val):
            execution_order.append("Step 2")
            return dep_val * 2

        self.orchestrator.add_task("step1", "Step 1 Task", step1)
        self.orchestrator.add_task("step2", "Step 2 Task", step2, args=(100,), depends_on=["step1"])

        results = self.orchestrator.execute_all()

        self.assertEqual(results["step1"].status, TaskStatus.SUCCESS)
        self.assertEqual(results["step2"].status, TaskStatus.SUCCESS)
        self.assertEqual(execution_order, ["Step 1", "Step 2"])
        self.assertEqual(results["step2"].result, 200)

    def test_failed_dependency_cancellation(self):
        def failing_task():
            raise RuntimeError("Primary failure")

        def dependent_task():
            return "Should not run"

        self.orchestrator.add_task("fail_t", "Failing Task", failing_task)
        self.orchestrator.add_task("dep_t", "Dependent Task", dependent_task, depends_on=["fail_t"])

        results = self.orchestrator.execute_all()

        self.assertEqual(results["fail_t"].status, TaskStatus.FAILED)
        self.assertEqual(results["dep_t"].status, TaskStatus.CANCELLED)


if __name__ == "__main__":
    unittest.main()
