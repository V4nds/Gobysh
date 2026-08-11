"""
Unit tests for the Unresolved File Error Ledger (closed-loop awareness)
and the `goby gate` / `goby status` CLI integration.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.state_memory import StateMemoryManager
from core import cli


class TestValidationLedger(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger_path = os.path.join(self.tmp.name, "ledger.json")
        self.mem = StateMemoryManager(memory_file_path=self.ledger_path)

    def tearDown(self):
        self.tmp.cleanup()

    def _record(self, rel_file, passed, gate=None, message=""):
        self.mem.record_file_validation(
            file_path=os.path.join(self.tmp.name, rel_file),
            passed=passed,
            blocked=not passed,
            gate=gate,
            summary="summary",
            signals=[],
            error_message=message,
            code_hash="hash123",
        )

    def test_failed_file_appears_as_unresolved(self):
        self._record("a.py", passed=False, gate="SCOPE", message="undefined x")
        unresolved = self.mem.get_unresolved_errors()
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0]["gate"], "SCOPE")
        self.assertEqual(unresolved[0]["message"], "undefined x")
        self.assertTrue(unresolved[0]["file"].endswith("a.py"))

    def test_passing_file_removes_from_unresolved(self):
        self._record("a.py", passed=False, gate="SCOPE")
        self._record("a.py", passed=True, gate=None)
        self.assertEqual(self.mem.get_unresolved_errors(), [])

    def test_only_failed_files_reported(self):
        self._record("good.py", passed=True)
        self._record("bad.py", passed=False, gate="SYNTAX", message="bad indent")
        unresolved = self.mem.get_unresolved_errors()
        self.assertEqual(len(unresolved), 1)
        self.assertIn("bad.py", unresolved[0]["file"])

    def test_clear_validation_ledger(self):
        self._record("a.py", passed=False, gate="SCOPE")
        self.mem.clear_validation_ledger()
        self.assertEqual(self.mem.get_unresolved_errors(), [])

    def test_persistence_across_instances(self):
        self._record("a.py", passed=False, gate="SCOPE")
        second_mgr = StateMemoryManager(memory_file_path=self.ledger_path)
        self.assertEqual(len(second_mgr.get_unresolved_errors()), 1)


class TestGobyGateCLI(unittest.TestCase):

    def _patch_mem(self, mem):
        return patch("core.cli.StateMemoryManager", lambda _path: mem)

    def test_gate_clean_exit_zero(self):
        with tempfile.TemporaryDirectory() as td:
            mem = StateMemoryManager(memory_file_path=os.path.join(td, "l.json"))
            with self._patch_mem(mem), patch.object(sys, "argv", ["goby", "gate"]):
                with self.assertRaises(SystemExit) as cm:
                    cli.main()
                self.assertEqual(cm.exception.code, 0)

    def test_gate_dirty_exit_one(self):
        with tempfile.TemporaryDirectory() as td:
            mem = StateMemoryManager(memory_file_path=os.path.join(td, "l.json"))
            mem.record_file_validation(
                file_path=os.path.join(td, "bad.py"),
                passed=False, blocked=True, gate="SCOPE",
                error_message="undefined var", code_hash="abc",
            )
            with self._patch_mem(mem), patch.object(sys, "argv", ["goby", "gate"]):
                with self.assertRaises(SystemExit) as cm:
                    cli.main()
                self.assertEqual(cm.exception.code, 1)

    def test_check_bad_file_feeds_ledger_then_gate_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            bad_file = os.path.join(td, "bad.py")
            with open(bad_file, "w", encoding="utf-8") as f:
                f.write("def calc():\n    return missing_var * 2\n")
            mem = StateMemoryManager(memory_file_path=os.path.join(td, "l.json"))

            with self._patch_mem(mem), patch.object(sys, "argv", ["goby", "check", bad_file]):
                with self.assertRaises(SystemExit) as cm:
                    cli.main()
                self.assertEqual(cm.exception.code, 1)

            unresolved = mem.get_unresolved_errors()
            self.assertEqual(len(unresolved), 1)
            self.assertTrue(unresolved[0]["file"].endswith("bad.py"))
            self.assertEqual(unresolved[0]["gate"], "SCOPE")

            with self._patch_mem(mem), patch.object(sys, "argv", ["goby", "gate"]):
                with self.assertRaises(SystemExit) as cm:
                    cli.main()
                self.assertEqual(cm.exception.code, 1)

    def test_check_fixed_file_clears_ledger_then_gate_passes(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = os.path.join(td, "fix.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("def calc():\n    return missing_var * 2\n")
            mem = StateMemoryManager(memory_file_path=os.path.join(td, "l.json"))

            with self._patch_mem(mem), patch.object(sys, "argv", ["goby", "check", file_path]):
                with self.assertRaises(SystemExit) as cm:
                    cli.main()
                self.assertEqual(cm.exception.code, 1)
            self.assertEqual(len(mem.get_unresolved_errors()), 1)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("def calc():\n    rate = 0.1\n    return 100 * (1 + rate)\n")
            with self._patch_mem(mem), patch.object(sys, "argv", ["goby", "check", file_path]):
                with self.assertRaises(SystemExit) as cm:
                    cli.main()
                self.assertEqual(cm.exception.code, 0)
            self.assertEqual(mem.get_unresolved_errors(), [])

            with self._patch_mem(mem), patch.object(sys, "argv", ["goby", "gate"]):
                with self.assertRaises(SystemExit) as cm:
                    cli.main()
                self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
