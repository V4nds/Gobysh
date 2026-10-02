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


if __name__ == "__main__":
    unittest.main()
