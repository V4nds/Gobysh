"""
Unit tests for Antigravity Lifecycle Hooks in Goby v5.0.0.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.hooks import (
    normalize_file_path,
    extract_modified_files,
    handle_post_tool_use,
    handle_pre_invocation,
    handle_stop_gate,
    install_lifecycle_hooks,
    get_hooks_config,
    cli_entry,
)
from core.state_memory import StateMemoryManager


class TestLifecycleHooks(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = self.temp_dir.name
        self.memory_path = os.path.join(self.workspace, "cognitive_map.json")
        self.memory = StateMemoryManager(self.memory_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_normalize_file_path(self):
        # Existing file
        test_file = os.path.join(self.workspace, "sample.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("x = 1\n")

        norm = normalize_file_path(f'"{test_file}"', base_dir=self.workspace)
        self.assertIsNotNone(norm)
        self.assertTrue(os.path.samefile(norm, test_file))

        # Relative path
        norm_rel = normalize_file_path("sample.py", base_dir=self.workspace)
        self.assertIsNotNone(norm_rel)
        self.assertTrue(os.path.samefile(norm_rel, test_file))

        # Non-existent file
        norm_none = normalize_file_path("non_existent.py", base_dir=self.workspace)
        self.assertIsNone(norm_none)

    def test_extract_modified_files_from_transcript(self):
        test_file = os.path.join(self.workspace, "script.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("print('hello')\n")

        transcript_path = os.path.join(self.workspace, "transcript.jsonl")
        step_entry = {
            "step_index": 1,
            "tool_calls": [
                {
                    "name": "write_to_file",
                    "args": {
                        "TargetFile": test_file,
                        "CodeContent": "print('hello')"
                    }
                }
            ]
        }
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(step_entry) + "\n")

        payload = {
            "transcriptPath": transcript_path,
            "workspacePaths": [self.workspace]
        }

        with patch("subprocess.run") as mock_git:
            mock_git.return_value = MagicMock(returncode=1)
            files = extract_modified_files(payload)

        self.assertIn(os.path.abspath(test_file), files)

    def test_extract_modified_files_from_git(self):
        test_file = os.path.join(self.workspace, "component.ts")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("export const val = 42;\n")

        payload = {
            "workspacePaths": [self.workspace]
        }

        with patch("subprocess.run") as mock_git:
            mock_git.return_value = MagicMock(
                returncode=0,
                stdout=" M component.ts\n?? ignored.txt\n"
            )
            files = extract_modified_files(payload)

        self.assertIn(os.path.abspath(test_file), files)

    def test_handle_post_tool_use(self):
        test_file = os.path.join(self.workspace, "valid.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("def add(a: int, b: int) -> int:\n    return a + b\n")

        payload = {
            "workspacePaths": [self.workspace]
        }

        with patch("core.hooks.extract_modified_files", return_value=[test_file]):
            out = handle_post_tool_use(payload)

        # Output must be empty dict per Antigravity spec
        self.assertEqual(out, {})

        # Verify cognitive_map.json recorded file validation
        mem = StateMemoryManager(self.memory_path)
        unresolved = mem.get_unresolved_errors()
        self.assertEqual(len(unresolved), 0)

    def test_handle_pre_invocation_clean(self):
        payload = {"workspacePaths": [self.workspace]}
        out = handle_pre_invocation(payload)
        self.assertEqual(out, {})

    def test_handle_pre_invocation_with_unresolved_errors(self):
        self.memory.record_file_validation(
            file_path=os.path.join(self.workspace, "broken.py"),
            passed=False,
            blocked=True,
            gate="CCR_SYNTAX",
            error_message="invalid syntax at line 12",
        )

        payload = {"workspacePaths": [self.workspace]}
        out = handle_pre_invocation(payload)

        self.assertIn("injectSteps", out)
        steps = out["injectSteps"]
        self.assertTrue(len(steps) > 0)
        self.assertIn("ephemeralMessage", steps[0])
        self.assertIn("broken.py", steps[0]["ephemeralMessage"])

    def test_handle_stop_gate_clean(self):
        payload = {"workspacePaths": [self.workspace]}
        out = handle_stop_gate(payload)
        self.assertEqual(out.get("decision"), "allow")

    def test_handle_stop_gate_blocked_on_unresolved_errors(self):
        self.memory.record_file_validation(
            file_path=os.path.join(self.workspace, "syntax_fail.py"),
            passed=False,
            blocked=True,
            gate="CCR_SYNTAX",
            error_message="SyntaxError on line 1",
        )

        payload = {"workspacePaths": [self.workspace]}
        out = handle_stop_gate(payload)

        self.assertEqual(out.get("decision"), "continue")
        self.assertIn("reason", out)
        self.assertIn("syntax_fail.py", out["reason"])

    def test_install_lifecycle_hooks(self):
        res = install_lifecycle_hooks(target_dir=self.workspace)
        self.assertTrue(res["installed"])
        hooks_json_path = Path(self.workspace) / ".agents" / "hooks.json"
        self.assertTrue(hooks_json_path.exists())

        with open(hooks_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("goby-lifecycle", data)
        spec = data["goby-lifecycle"]
        self.assertIn("PostToolUse", spec)
        self.assertIn("PreInvocation", spec)
        self.assertIn("Stop", spec)

    def test_cli_entry_status_and_install(self):
        with patch("sys.stdout.write") as mock_stdout:
            cli_entry("status")
            mock_stdout.assert_called()


if __name__ == "__main__":
    unittest.main()
