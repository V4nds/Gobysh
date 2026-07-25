import sys
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


if __name__ == "__main__":
    unittest.main()
