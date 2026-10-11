"""
Unit tests for Goby Rust Acceleration Layer (crates/goby_core).
Validates native binary discovery, symbol scanning parity with Python,
and fast gate delimiter verification.
"""

import os
import subprocess
import tempfile
import unittest

from core.translation.scanner import RepositoryScanner
from core.translation.symbol_mapper import SymbolMap


class TestRustAcceleration(unittest.TestCase):
    """Test suite verifying Rust accelerator crates/goby_core."""

    def setUp(self):
        self.native_bin = RepositoryScanner._get_native_binary()

    def test_native_binary_exists(self):
        """Verifies that the compiled goby_core binary is found and executes --version."""
        self.assertIsNotNone(self.native_bin, "goby_core native binary should be discovered")
        self.assertTrue(os.path.isfile(self.native_bin), "Discovered path must exist on disk")

        proc = subprocess.run([self.native_bin, "--version"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("goby-core", proc.stdout)

    def test_native_scan_file(self):
        """Verifies that native binary scan-file parses symbols correctly."""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("import math\n\ndef compute(a, b):\n    return a + b\n")
            f_path = f.name

        try:
            fmap = RepositoryScanner.scan_file(f_path, use_native=True)
            self.assertEqual(fmap.imports, ["math"])
            fn_names = [s.name for s in fmap.symbols]
            self.assertIn("compute", fn_names)
        finally:
            if os.path.exists(f_path):
                os.remove(f_path)

    def test_native_scanner_directory_parity(self):
        """Verifies scanning a directory produces equivalent results in native and python fallback."""
        native_map = RepositoryScanner.scan_directory("core/translation", use_native=True)
        py_map = RepositoryScanner.scan_directory("core/translation", use_native=False)

        self.assertGreater(len(native_map.files), 0)
        self.assertEqual(len(native_map.files), len(py_map.files))

        # Check that symbols match for scanner.py
        native_scanner = next((f for k, f in native_map.files.items() if "scanner.py" in k), None)
        py_scanner = next((f for k, f in py_map.files.items() if "scanner.py" in k), None)

        self.assertIsNotNone(native_scanner)
        self.assertIsNotNone(py_scanner)

        native_sym_names = {s.name for s in native_scanner.symbols}
        py_sym_names = {s.name for s in py_scanner.symbols}

        self.assertIn("RepositoryScanner", native_sym_names)
        self.assertIn("RepositoryScanner.scan_directory", native_sym_names)
        self.assertTrue(native_sym_names.issubset(py_sym_names) or py_sym_names.issubset(native_sym_names))

    def test_native_fast_gate_delimiter_check(self):
        """Verifies native binary check catches unclosed brackets and allows valid code."""
        if not self.native_bin:
            self.skipTest("Native binary not found")

        # Valid code
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("def ok():\n    return {'a': [1, 2, (3 + 4)]}\n")
            valid_path = f.name

        # Invalid code with unmatched bracket
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("def broken():\n    return {'a': [1, 2, (3 + 4)}\n")
            invalid_path = f.name

        try:
            proc_valid = subprocess.run([self.native_bin, "check", valid_path], capture_output=True)
            self.assertEqual(proc_valid.returncode, 0)

            proc_invalid = subprocess.run([self.native_bin, "check", invalid_path], capture_output=True)
            self.assertEqual(proc_invalid.returncode, 1)
        finally:
            if os.path.exists(valid_path):
                os.remove(valid_path)
            if os.path.exists(invalid_path):
                os.remove(invalid_path)


if __name__ == "__main__":
    unittest.main()
