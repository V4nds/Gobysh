import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from core import cli


class TestCLI(unittest.TestCase):
    def test_cli_help(self):
        with patch.object(sys, "argv", ["goby", "--help"]):
            with self.assertRaises(SystemExit) as cm:
                cli.main()
            self.assertEqual(cm.exception.code, 0)

    def test_cli_unknown_cmd(self):
        with patch.object(sys, "argv", ["goby", "unknown_cmd"]):
            with self.assertRaises(SystemExit) as cm:
                cli.main()
            self.assertEqual(cm.exception.code, 1)

    def test_cli_check_valid(self):
        with patch.object(sys, "argv", ["goby", "check", "x = 1"]):
            with self.assertRaises(SystemExit) as cm:
                cli.main()
            self.assertEqual(cm.exception.code, 0)

    def test_cli_status(self):
        with patch.object(sys, "argv", ["goby", "status"]):
            with self.assertRaises(SystemExit) as cm:
                cli.main()
            self.assertEqual(cm.exception.code, 0)

    def test_cli_check_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("a = 10\nb = 20\nc = a + b")
            f.flush()
            temp_path = f.name
        try:
            with patch.object(sys, "argv", ["goby", "check", temp_path]):
                with self.assertRaises(SystemExit) as cm:
                    cli.main()
                self.assertEqual(cm.exception.code, 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_cli_check_with_intent_passes(self):
        with patch.object(sys, "argv", ["goby", "check", "def add(a, b): return a + b", "--intent", "buat fungsi tambah"]):
            with self.assertRaises(SystemExit) as cm:
                cli.main()
            self.assertEqual(cm.exception.code, 0)

    def test_cli_check_with_intent_fails_on_violation(self):
        with patch.object(sys, "argv", ["goby", "check", "def update_db(): pass", "--intent", "buat fungsi tapi jangan sentuh db"]):
            with self.assertRaises(SystemExit) as cm:
                cli.main()
            self.assertEqual(cm.exception.code, 1)

    def test_cli_hooks_status(self):
        with patch.object(sys, "argv", ["goby", "hooks", "status"]):
            with self.assertRaises(SystemExit) as cm:
                cli.main()
            self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()

