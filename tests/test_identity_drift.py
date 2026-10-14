"""
Unit tests for CCR Identity Drift Neuron (neuron_identity_drift).
"""

import unittest
from core.ccr_engine import CognitiveControlRoom, GateType
from core.neurons.identity_drift import neuron_identity_drift_check


class TestIdentityDriftNeuron(unittest.TestCase):

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_clean_goby_code_passes(self):
        code = """
from core.state_memory import StateMemoryManager

class NewFeature:
    def execute(self):
        return True
"""
        signal = neuron_identity_drift_check(self.ccr, code, filepath="core/new_feature.py")
        self.assertTrue(signal.passed)
        self.assertEqual(signal.neuron_name, "IDENTITY_DRIFT")

    def test_pyproject_name_mutation_detected(self):
        alien_pyproject = """
[project]
name = "alien-disassembler-tool"
version = "0.1.0"
description = "Completely different project replacing goby"
"""
        signal = neuron_identity_drift_check(self.ccr, alien_pyproject, filepath="pyproject.toml")
        self.assertFalse(signal.passed)
        self.assertEqual(signal.gate_type, GateType.HARD)
        self.assertIn("Project name mutation", signal.message)

    def test_core_init_deletion_of_foundational_exports(self):
        stripped_init = """
# Stripped out all Goby framework exports
def dummy():
    pass
"""
        signal = neuron_identity_drift_check(self.ccr, stripped_init, filepath="core/__init__.py")
        self.assertFalse(signal.passed)
        self.assertEqual(signal.gate_type, GateType.HARD)
        self.assertIn("Foundational export", signal.message)

    def test_monolithic_alien_injection_detected(self):
        alien_code = """
class BinaryDisassembler:
    def disassemble_x86_binary(self, raw_bytes):
        pass

class AndroidApkDecompiler:
    def decompile(self, apk_path):
        pass
"""
        signal = neuron_identity_drift_check(self.ccr, alien_code, filepath="core/disasm.py")
        self.assertFalse(signal.passed)
        self.assertEqual(signal.gate_type, GateType.HARD)
        self.assertIn("forbidden identity drift", signal.message)

    def test_ccr_engine_integration(self):
        # Verify method exists on CognitiveControlRoom
        self.assertTrue(hasattr(self.ccr, "neuron_identity_drift"))
        sig = self.ccr.neuron_identity_drift("x = 1", filepath="test.py")
        self.assertTrue(sig.passed)


if __name__ == "__main__":
    unittest.main()
