"""
Unit tests for Goby v5.5 REA-Inspired Evidence-Obligation Exit Gate.
Verifies:
1. Deterministic Workspace Code Fingerprinting (SHA-256).
2. Dynamic Test Evidence Recording & Anti-Stale Guardrails.
3. Task Obligation Ledger & Fail-Closed Unknowns.
4. Comprehensive 3-Pillar Exit Gate Evaluation.
"""

import os
import tempfile
import unittest
from core.state_memory import StateMemoryManager, calculate_workspace_code_hash


class TestEvidenceObligationGate(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mem_path = os.path.join(self.temp_dir.name, "cognitive_map.json")
        self.mem = StateMemoryManager(self.mem_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_calculate_workspace_code_hash(self):
        f1 = os.path.join(self.temp_dir.name, "app.py")
        with open(f1, "w", encoding="utf-8") as f:
            f.write("print('hello')\n")
        h1 = calculate_workspace_code_hash(self.temp_dir.name)
        self.assertEqual(len(h1), 64)

        # Modify file and verify hash changes
        with open(f1, "w", encoding="utf-8") as f:
            f.write("print('world')\n")
        h2 = calculate_workspace_code_hash(self.temp_dir.name)
        self.assertNotEqual(h1, h2)

    def test_gate_evaluation_clean_when_fresh(self):
        f1 = os.path.join(self.temp_dir.name, "main.py")
        with open(f1, "w", encoding="utf-8") as f:
            f.write("x = 1\n")
        whash = calculate_workspace_code_hash(self.temp_dir.name)

        # Record passing test with matching workspace hash
        self.mem.record_test_execution(
            command="pytest",
            exit_code=0,
            duration_seconds=1.0,
            output_summary="OK",
            workspace_hash=whash,
        )
        verdict = self.mem.evaluate_exit_gate(self.temp_dir.name)
        self.assertTrue(verdict["passed"])
        self.assertEqual(verdict["verdict"], "PASS")
        self.assertEqual(verdict["pillars"]["dynamic_evidence"]["freshness"], "FRESH")

    def test_gate_evaluation_blocks_when_stale(self):
        f1 = os.path.join(self.temp_dir.name, "main.py")
        with open(f1, "w", encoding="utf-8") as f:
            f.write("x = 1\n")
        whash = calculate_workspace_code_hash(self.temp_dir.name)
        self.mem.record_test_execution(
            command="pytest",
            exit_code=0,
            duration_seconds=1.0,
            output_summary="OK",
            workspace_hash=whash,
        )

        # Edit file after test execution -> evidence becomes stale!
        with open(f1, "w", encoding="utf-8") as f:
            f.write("x = 2\n")

        verdict = self.mem.evaluate_exit_gate(self.temp_dir.name)
        self.assertFalse(verdict["passed"])
        self.assertEqual(verdict["verdict"], "BLOCKED")
        self.assertEqual(verdict["pillars"]["dynamic_evidence"]["freshness"], "STALE")
        self.assertTrue(any("stale" in r.lower() for r in verdict["block_reasons"]))

    def test_gate_evaluation_blocks_on_unresolved_obligation(self):
        whash = calculate_workspace_code_hash(self.temp_dir.name)
        self.mem.record_test_execution(
            command="pytest",
            exit_code=0,
            duration_seconds=1.0,
            output_summary="OK",
            workspace_hash=whash,
        )

        ob_id = self.mem.record_obligation("Fix authentication", source="prompt_spider")
        self.assertIsNotNone(ob_id)
        verdict = self.mem.evaluate_exit_gate(self.temp_dir.name)
        self.assertFalse(verdict["passed"])
        self.assertEqual(verdict["verdict"], "BLOCKED")
        self.assertEqual(len(verdict["pillars"]["obligations"]["open_obligations"]), 1)

        # Resolve obligation
        resolved = self.mem.resolve_obligation(ob_id, status="VERIFIED")
        self.assertTrue(resolved)
        verdict2 = self.mem.evaluate_exit_gate(self.temp_dir.name)
        self.assertTrue(verdict2["passed"])
        self.assertEqual(verdict2["verdict"], "PASS")

    def test_gate_evaluation_blocks_on_static_error(self):
        whash = calculate_workspace_code_hash(self.temp_dir.name)
        self.mem.record_test_execution(
            command="pytest",
            exit_code=0,
            duration_seconds=1.0,
            output_summary="OK",
            workspace_hash=whash,
        )
        # Record bad file in validation ledger
        bad_file = os.path.join(self.temp_dir.name, "syntax_error.py")
        self.mem.record_file_validation(
            file_path=bad_file,
            passed=False,
            blocked=True,
            gate="CCR_SYNTAX",
            error_message="Invalid syntax",
        )
        verdict = self.mem.evaluate_exit_gate(self.temp_dir.name)
        self.assertFalse(verdict["passed"])
        self.assertEqual(verdict["verdict"], "BLOCKED")
        self.assertEqual(len(verdict["pillars"]["static_integrity"]["unresolved"]), 1)


if __name__ == "__main__":
    unittest.main()
