"""
Unit tests for Goby CLI 'spider' and 'diagnose' commands in v5.3.
"""

import json
import subprocess
import unittest


class TestCLISpider(unittest.TestCase):
    def test_cli_spider_json_output(self):
        res = subprocess.run(
            ["python", "-m", "core.cli", "spider", "buat fitur pengukuran sudut baru di canvas", "--json"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIn("role", data)
        self.assertIn("objective", data)
        self.assertIn("tokens", data)
        self.assertIn("prompt_hash", data)

    def test_cli_spider_clarification_exit_code(self):
        res = subprocess.run(
            ["python", "-m", "core.cli", "spider", "rapikan kodenya biar mantap"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("GOBY PROMPT SPIDER", res.stdout)
        self.assertIn("CLARIFICATION NEEDED", res.stdout)

    def test_cli_diagnose_command(self):
        res = subprocess.run(
            ["python", "-m", "core.cli", "diagnose", "tambahkan export svg ke canvas tapi jangan ubah file canvas sama sekali"],
            capture_output=True,
            text=True
        )
        self.assertIn("GOBY FLAW DIAGNOSTICS", res.stdout)
        self.assertIn("CRITICAL", res.stdout)


if __name__ == "__main__":
    unittest.main()
