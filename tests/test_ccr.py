"""
Unit Tests for Cognitive Control Room (CCR) Module.
Tests all 8 neurons, triage system, context gate, signal evaluation,
and thought recording.
"""

import os
import sys
import json
import tempfile
import unittest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.ccr_engine import (
    CognitiveControlRoom,
    NeuronSignal,
    ThoughtRecord,
    ContextAssessment,
    GateType,
    TriageLevel,
    ContextTier,
)
from core.state_memory import StateMemoryManager
from core.gca_runner import GroundedCompilerArbitrage


class TestTriage(unittest.TestCase):
    """Tests for the triage classification system."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_skip_for_acknowledgment(self):
        result = self.ccr.triage("ACKNOWLEDGMENT", "TRIVIAL")
        self.assertEqual(result, TriageLevel.SKIP)

    def test_skip_for_trivial_complexity(self):
        result = self.ccr.triage("CODE", "TRIVIAL")
        self.assertEqual(result, TriageLevel.SKIP)

    def test_light_for_text_low(self):
        result = self.ccr.triage("TEXT", "LOW")
        self.assertEqual(result, TriageLevel.LIGHT)

    def test_standard_for_code_moderate(self):
        result = self.ccr.triage("CODE", "MODERATE")
        self.assertEqual(result, TriageLevel.STANDARD)

    def test_full_for_code_high(self):
        result = self.ccr.triage("CODE", "HIGH")
        self.assertEqual(result, TriageLevel.FULL)

    def test_full_for_design(self):
        result = self.ccr.triage("DESIGN", "HIGH")
        self.assertEqual(result, TriageLevel.FULL)


class TestContextGate(unittest.TestCase):
    """Tests for the context assessment system."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_critical_when_no_input(self):
        result = self.ccr.assess_context("hi", {})
        self.assertEqual(result.tier, ContextTier.CRITICAL)
        self.assertFalse(result.is_sufficient)

    def test_sufficient_with_clear_request(self):
        result = self.ccr.assess_context(
            "Tolong buatkan fungsi untuk menghitung rata-rata",
            {"project_description": "Math utility library"}
        )
        self.assertTrue(result.is_sufficient)

    def test_minimum_when_error_without_code(self):
        result = self.ccr.assess_context(
            "Ada error di kode saya, tolong fix bug ini",
            {"project_description": "Web app"}
        )
        # Has error keyword but no code/error_log
        self.assertIn("error_code_or_log", result.missing_info)

    def test_ideal_with_full_context(self):
        result = self.ccr.assess_context(
            "Ada error traceback di fungsi login",
            {
                "code": "def login(): pass",
                "error_log": "Traceback...",
                "project_description": "Auth system",
            }
        )
        self.assertEqual(result.tier, ContextTier.IDEAL)
        self.assertTrue(result.is_sufficient)

    def test_design_task_asks_for_reference(self):
        result = self.ccr.assess_context(
            "Tolong desain ulang tampilan dashboard",
            {}
        )
        self.assertIn("design_reference", result.missing_info)


class TestNeuronSyntaxCheck(unittest.TestCase):
    """Tests for Neuron 1: Syntax Check."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_valid_code_passes(self):
        code = "x = 1 + 2\nprint(x)"
        signal = self.ccr.neuron_syntax_check(code)
        self.assertTrue(signal.passed)
        self.assertEqual(signal.gate_type, GateType.HARD)
        self.assertEqual(signal.confidence, 1.0)

    def test_invalid_code_fails(self):
        code = "def foo(\n    print('broken"
        signal = self.ccr.neuron_syntax_check(code)
        self.assertFalse(signal.passed)
        self.assertEqual(signal.gate_type, GateType.HARD)
        self.assertIn("SyntaxError", signal.message)
        self.assertIsNotNone(signal.evidence.get("line"))

    def test_empty_code_passes(self):
        signal = self.ccr.neuron_syntax_check("")
        self.assertTrue(signal.passed)


class TestNeuronScopeCheck(unittest.TestCase):
    """Tests for Neuron 2: Scope Integrity Check."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_clean_code_passes(self):
        code = "x = 10\ny = x + 5\nprint(y)"
        signal = self.ccr.neuron_scope_check(code)
        self.assertTrue(signal.passed)

    def test_undefined_variable_detected(self):
        code = "x = 10\nresult = x + undefined_var"
        signal = self.ccr.neuron_scope_check(code)
        self.assertFalse(signal.passed)
        self.assertIn("undefined_var", signal.evidence.get("undefined_names", []))

    def test_import_defines_name(self):
        code = "import os\npath = os.getcwd()"
        signal = self.ccr.neuron_scope_check(code)
        self.assertTrue(signal.passed)

    def test_function_params_are_defined(self):
        code = "def add(a, b):\n    return a + b"
        signal = self.ccr.neuron_scope_check(code)
        self.assertTrue(signal.passed)

    def test_for_loop_variable_defined(self):
        code = "for i in range(10):\n    print(i)"
        signal = self.ccr.neuron_scope_check(code)
        self.assertTrue(signal.passed)

    def test_syntax_error_returns_failure(self):
        code = "def broken(:"
        signal = self.ccr.neuron_scope_check(code)
        self.assertFalse(signal.passed)


class TestNeuronCrossReference(unittest.TestCase):
    """Tests for Neuron 3: Cross-Reference."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()
        self.project_root = os.path.join(os.path.dirname(__file__), "..")

    def test_valid_project_import(self):
        code = "from core.lde_detector import LoopDetectionEngine"
        signal = self.ccr.neuron_cross_reference(code, self.project_root)
        self.assertTrue(signal.passed)

    def test_missing_module_detected(self):
        code = "from core.nonexistent_module import SomeThing"
        signal = self.ccr.neuron_cross_reference(code, self.project_root)
        self.assertFalse(signal.passed)
        self.assertIn("core.nonexistent_module", signal.evidence.get("missing_modules", []))

    def test_no_local_imports_passes(self):
        code = "import os\nimport sys\nprint('hello')"
        signal = self.ccr.neuron_cross_reference(code, self.project_root)
        self.assertTrue(signal.passed)


class TestNeuronGCAExecute(unittest.TestCase):
    """Tests for Neuron 6: GCA Execute."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_passing_command(self):
        signal = self.ccr.neuron_gca_execute(f'"{sys.executable}" -c "print(42)"')
        self.assertTrue(signal.passed)
        self.assertEqual(signal.gate_type, GateType.HARD)
        self.assertEqual(signal.confidence, 1.0)

    def test_failing_command(self):
        signal = self.ccr.neuron_gca_execute(f'"{sys.executable}" -c "raise ValueError()"')
        self.assertFalse(signal.passed)
        self.assertEqual(signal.gate_type, GateType.HARD)


class TestNeuronInfoDensity(unittest.TestCase):
    """Tests for Neuron 7: Information Density."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_substantive_text(self):
        text = (
            "The LoopDetectionEngine uses Levenshtein distance to compare "
            "consecutive error outputs. When similarity exceeds 85%, it triggers "
            "a Meta-Systemic Leap Protocol with dimension expansion."
        )
        signal = self.ccr.neuron_info_density(text)
        self.assertTrue(signal.passed)
        self.assertGreater(signal.evidence["lexical_diversity"], 0.5)
        self.assertEqual(signal.evidence["total_filler_hits"], 0)

    def test_filler_heavy_text(self):
        text = (
            "Basically, generally speaking, at the end of the day, "
            "it should be noted that of course the system works. "
            "As a matter of fact, basically it is generally speaking fine."
        )
        signal = self.ccr.neuron_info_density(text)
        self.assertGreater(signal.evidence["total_filler_hits"], 3)

    def test_empty_text(self):
        signal = self.ccr.neuron_info_density("")
        self.assertFalse(signal.passed)


class TestNeuronConsistency(unittest.TestCase):
    """Tests for Neuron 8: Consistency Check."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_consistent_text(self):
        text = "The timeout is 30 seconds.\nThe retry count is 3."
        signal = self.ccr.neuron_consistency(text)
        self.assertEqual(len(signal.evidence["numeric_conflicts"]), 0)

    def test_text_with_no_claims(self):
        text = "Hello world. This is a simple sentence."
        signal = self.ccr.neuron_consistency(text)
        self.assertEqual(len(signal.evidence["claims"]), 0)


class TestNeuronReferenceSimilarity(unittest.TestCase):
    """Tests for Neuron 5: Reference Similarity."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_high_similarity(self):
        output = "The header contains a logo, navigation menu, and search bar."
        reference = "The header should have a logo, navigation links, and a search input."
        signal = self.ccr.neuron_reference_similarity(output, reference)
        self.assertTrue(signal.passed)  # Always passes — AI interprets
        self.assertGreater(signal.evidence["structural_overlap"], 0.3)
        self.assertGreater(len(signal.evidence["shared_keywords"]), 0)

    def test_low_similarity(self):
        output = "The footer has copyright information."
        reference = "A carousel displays hero images with call-to-action buttons."
        signal = self.ccr.neuron_reference_similarity(output, reference)
        self.assertLess(signal.evidence["structural_overlap"], 0.3)


class TestEvaluateSignals(unittest.TestCase):
    """Tests for the signal evaluation system (Hard Gate blocker)."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_blocked_by_hard_failure(self):
        signals = [
            NeuronSignal("SYNTAX", GateType.HARD, False, 1.0, "Syntax error", {}, "Fix it"),
            NeuronSignal("DENSITY", GateType.SOFT, True, 0.8, "OK", {}, ""),
        ]
        result = self.ccr.evaluate_signals(signals)
        self.assertTrue(result["blocked"])
        self.assertFalse(result["ai_can_override"])
        self.assertEqual(len(result["hard_failures"]), 1)

    def test_not_blocked_all_pass(self):
        signals = [
            NeuronSignal("SYNTAX", GateType.HARD, True, 1.0, "OK", {}, ""),
            NeuronSignal("SCOPE", GateType.HARD, True, 0.85, "OK", {}, ""),
        ]
        result = self.ccr.evaluate_signals(signals)
        self.assertFalse(result["blocked"])
        self.assertTrue(result["ai_can_override"])

    def test_soft_warnings_not_blocking(self):
        signals = [
            NeuronSignal("SYNTAX", GateType.HARD, True, 1.0, "OK", {}, ""),
            NeuronSignal("DENSITY", GateType.SOFT, False, 0.3, "Low density", {}, "Add substance"),
        ]
        result = self.ccr.evaluate_signals(signals)
        self.assertFalse(result["blocked"])
        self.assertEqual(len(result["soft_warnings"]), 1)


class TestThoughtRecording(unittest.TestCase):
    """Tests for thought recording with auto-pruning."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory_path = os.path.join(self.temp_dir, "test_cognitive_map.json")
        self.state_memory = StateMemoryManager(memory_file_path=self.memory_path)
        self.ccr = CognitiveControlRoom(
            state_memory=self.state_memory, max_thought_history=5
        )

    def test_record_and_retrieve(self):
        thought = ThoughtRecord(
            thought_id="t-001",
            content="print('hello')",
            content_type="CODE",
            ai_decision="APPROVED",
            refinement_count=0,
        )
        self.ccr.record_thought(thought)
        history = self.ccr.get_thought_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["thought_id"], "t-001")

    def test_auto_pruning(self):
        for i in range(10):
            thought = ThoughtRecord(
                thought_id=f"t-{i:03d}",
                content=f"code_{i}",
                content_type="CODE",
                ai_decision="APPROVED",
            )
            self.ccr.record_thought(thought)

        history = self.ccr.get_thought_history(limit=100)
        # Max is 5, so only 5 most recent should exist
        self.assertLessEqual(len(history), 5)
        # Most recent should be t-009
        self.assertEqual(history[-1]["thought_id"], "t-009")

    def test_no_state_memory_no_crash(self):
        ccr_no_mem = CognitiveControlRoom(state_memory=None)
        thought = ThoughtRecord(
            thought_id="t-test", content="x", content_type="CODE"
        )
        # Should not raise
        ccr_no_mem.record_thought(thought)
        result = ccr_no_mem.get_thought_history()
        self.assertEqual(result, [])

    def tearDown(self):
        if os.path.exists(self.memory_path):
            os.remove(self.memory_path)
        os.rmdir(self.temp_dir)


class TestDesignQuestionnaire(unittest.TestCase):
    """Tests for design questionnaire generation."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_general_questionnaire(self):
        questions = self.ccr.generate_design_questionnaire("general")
        self.assertGreaterEqual(len(questions), 5)
        categories = [q["category"] for q in questions]
        self.assertIn("Layout", categories)
        self.assertIn("Color", categories)

    def test_web_questionnaire_has_extra(self):
        questions = self.ccr.generate_design_questionnaire("web")
        categories = [q["category"] for q in questions]
        self.assertIn("Navigation", categories)
        self.assertIn("Interaction", categories)


class TestNeuronJSSyntax(unittest.TestCase):
    """Tests for JavaScript/TypeScript syntax check neuron."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_valid_js_syntax(self):
        sig = self.ccr.neuron_js_syntax_check("const x = 10; console.log(x);")
        self.assertEqual(sig.neuron_name, "JS_SYNTAX")
        self.assertTrue(sig.passed or sig.evidence.get("node_available") is False)

    def test_invalid_js_syntax(self):
        sig = self.ccr.neuron_js_syntax_check("const x = ;")
        self.assertEqual(sig.neuron_name, "JS_SYNTAX")
        if sig.evidence.get("node_available"):
            self.assertFalse(sig.passed)
            self.assertEqual(sig.gate_type, GateType.HARD)


class TestNeuronTasteDesign(unittest.TestCase):
    """Regression: the full CCR -> neurons.taste -> ModernCSSKeywordHeuristic path
    must run without NameError on UI code (import fix in core/neurons/taste.py)."""

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_ui_code_returns_signal_not_error(self):
        sig = self.ccr.neuron_taste_design_check("<div style='display: flex;'></div>")
        self.assertEqual(sig.neuron_name, "TASTE_DESIGN")
        self.assertIsInstance(sig.passed, bool)
        self.assertIn("scores", sig.evidence)

    def test_non_ui_code_skips_heuristic(self):
        sig = self.ccr.neuron_taste_design_check("def calc():\n    return 1")
        self.assertEqual(sig.neuron_name, "TASTE_DESIGN")
        self.assertTrue(sig.passed)
        self.assertEqual(sig.evidence, {})



    def test_kotlin_syntax_check(self):
        ccr = CognitiveControlRoom()
        valid_kt = """
        package com.test
        class TestClass(val x: Int) {
            fun add(y: Int): Int {
                return x + y
            }
        }
        """
        sig_valid = ccr.neuron_kotlin_syntax_check(valid_kt)
        self.assertTrue(sig_valid.passed)

        invalid_kt = """
        class TestClass {
            fun add(y: Int): Int {
                return (x + y
            }
        """
        sig_invalid = ccr.neuron_kotlin_syntax_check(invalid_kt)
        self.assertFalse(sig_invalid.passed)
        self.assertTrue("bracket" in sig_invalid.message.lower())


if __name__ == "__main__":
    unittest.main()

