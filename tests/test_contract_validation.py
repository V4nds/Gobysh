"""Tests for Stage 2 Contract Validation (Goby Calibration)."""

import unittest
from core.semantics.preservation import PreservationContract


class TestPreservationContract(unittest.TestCase):
    """Test suite for first-class PreservationContract."""

    def test_preservation_contract_defaults_and_dict(self):
        pc = PreservationContract(
            required=True,
            protected_symbols=["old_auth_function", "UserModel"],
            protected_behaviors=["existing_login_flow"],
            invariants=["db_schema_stable"],
            verification_strategy=["symbol_existence", "test_suite"],
        )
        self.assertTrue(pc.required)
        self.assertEqual(len(pc.protected_symbols), 2)
        d = pc.to_dict()
        self.assertEqual(d["required"], True)
        self.assertIn("old_auth_function", d["protected_symbols"])

        # Round trip
        restored = PreservationContract.from_dict(d)
        self.assertEqual(restored.protected_symbols, pc.protected_symbols)
        self.assertEqual(restored.protected_behaviors, pc.protected_behaviors)


from core.semantics.scope import ScopeNormalizer


class TestScopeNormalizer(unittest.TestCase):
    """Test suite for ScopeNormalizer path normalization and glob boundaries."""

    def test_normalize_path(self):
        self.assertEqual(ScopeNormalizer.normalize_path("core\\cli.py"), "core/cli.py")
        self.assertEqual(ScopeNormalizer.normalize_path("./src/auth/"), "src/auth")
        self.assertEqual(ScopeNormalizer.normalize_path("  /app/index.js  "), "app/index.js")

    def test_is_in_scope_exact_and_directory(self):
        scopes = ["core/", "tests/test_cli.py"]
        self.assertTrue(ScopeNormalizer.is_in_scope("core/intent_resolver.py", scopes))
        self.assertTrue(ScopeNormalizer.is_in_scope("tests/test_cli.py", scopes))
        self.assertFalse(ScopeNormalizer.is_in_scope("benchmarks/sim.py", scopes))

    def test_is_in_scope_glob_patterns(self):
        scopes = ["core/**/*.py", "*.md"]
        self.assertTrue(ScopeNormalizer.is_in_scope("core/semantics/specification.py", scopes))
        self.assertTrue(ScopeNormalizer.is_in_scope("README.md", scopes))
        self.assertFalse(ScopeNormalizer.is_in_scope("core/semantics/data.json", scopes))

    def test_validate_file_targets_returns_violations(self):
        targets = ["core/cli.py", "secret/passwords.txt"]
        scopes = ["core/"]
        violations = ScopeNormalizer.validate_file_targets(targets, scopes)
        self.assertEqual(len(violations), 1)
        self.assertIn("secret/passwords.txt", violations[0])


if __name__ == "__main__":
    unittest.main()

