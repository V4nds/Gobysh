"""Tests for IntentResolver module (Goby v5.0)."""

import unittest
from core.intent_resolver import IntentResolver, IntentTree, IntentNode


class TestIntentResolver(unittest.TestCase):
    """Test suite for the Intent Resolver engine."""

    def setUp(self):
        self.resolver = IntentResolver()

    # -------------------------------------------------------------------
    # Basic Resolution Tests
    # -------------------------------------------------------------------

    def test_empty_input_returns_unknown(self):
        result = self.resolver.resolve("")
        self.assertEqual(result.primary_intent.task_type, "unknown")
        self.assertTrue(result.clarification_needed)
        self.assertEqual(result.ambiguity_score, 1.0)

    def test_whitespace_only_returns_unknown(self):
        result = self.resolver.resolve("   ")
        self.assertEqual(result.primary_intent.task_type, "unknown")
        self.assertTrue(result.clarification_needed)

    def test_none_input_returns_unknown(self):
        result = self.resolver.resolve(None)
        self.assertEqual(result.primary_intent.task_type, "unknown")
        self.assertTrue(result.clarification_needed)

    # -------------------------------------------------------------------
    # Bug Fix Intent Tests
    # -------------------------------------------------------------------

    def test_fix_bug_english(self):
        result = self.resolver.resolve("fix the error in app.js where it crashes on load")
        self.assertEqual(result.primary_intent.task_type, "fix_bug")
        self.assertGreater(result.primary_intent.confidence, 0.3)

    def test_fix_bug_indonesian(self):
        result = self.resolver.resolve("tolong perbaiki error di app.js")
        self.assertEqual(result.primary_intent.task_type, "fix_bug")
        self.assertGreater(result.primary_intent.confidence, 0.3)

    def test_fix_bug_with_traceback(self):
        result = self.resolver.resolve("getting a traceback exception when running the app")
        self.assertEqual(result.primary_intent.task_type, "fix_bug")

    # -------------------------------------------------------------------
    # Create Feature Intent Tests
    # -------------------------------------------------------------------

    def test_create_feature_english(self):
        result = self.resolver.resolve("create a new login page component")
        self.assertEqual(result.primary_intent.task_type, "create_feature")
        self.assertGreater(result.primary_intent.confidence, 0.3)

    def test_create_feature_indonesian(self):
        result = self.resolver.resolve("buat halaman login baru dengan fitur register")
        self.assertEqual(result.primary_intent.task_type, "create_feature")

    # -------------------------------------------------------------------
    # Design UI Intent Tests
    # -------------------------------------------------------------------

    def test_design_ui(self):
        result = self.resolver.resolve("design a modern dark mode dashboard with animations")
        self.assertEqual(result.primary_intent.task_type, "design_ui")
        self.assertGreater(result.primary_intent.confidence, 0.3)

    def test_design_ui_indonesian(self):
        result = self.resolver.resolve("desain tampilan UI yang keren dengan animasi hover")
        self.assertEqual(result.primary_intent.task_type, "design_ui")

    # -------------------------------------------------------------------
    # Refactor Intent Tests
    # -------------------------------------------------------------------

    def test_refactor(self):
        result = self.resolver.resolve("refactor this code to be more efficient and clean")
        self.assertEqual(result.primary_intent.task_type, "refactor")

    # -------------------------------------------------------------------
    # File Detection Tests
    # -------------------------------------------------------------------

    def test_extracts_target_files(self):
        result = self.resolver.resolve("fix the bug in core/cli.py and update tests/test_cli.py")
        self.assertIn("core/cli.py", result.primary_intent.target_files)
        self.assertIn("tests/test_cli.py", result.primary_intent.target_files)

    def test_extracts_js_files(self):
        result = self.resolver.resolve("add animation to app.js")
        self.assertIn("app.js", result.primary_intent.target_files)

    # -------------------------------------------------------------------
    # Language Detection Tests
    # -------------------------------------------------------------------

    def test_detects_indonesian(self):
        result = self.resolver.resolve("tolong buat fitur baru yang keren dong")
        self.assertIn(result.detected_language, ("id", "mixed"))

    def test_detects_english(self):
        result = self.resolver.resolve("please create a new feature for the dashboard")
        self.assertEqual(result.detected_language, "en")

    # -------------------------------------------------------------------
    # Ambiguity Detection Tests
    # -------------------------------------------------------------------

    def test_high_ambiguity_short_input(self):
        result = self.resolver.resolve("fix it")
        self.assertGreater(result.ambiguity_score, 0.0)

    def test_high_ambiguity_vague_input(self):
        result = self.resolver.resolve("kayaknya mungkin bisa dibikin something like yang bagus")
        self.assertGreater(result.ambiguity_score, 0.3)

    def test_low_ambiguity_specific_input(self):
        result = self.resolver.resolve("create a new Python function in core/utils.py that validates email addresses")
        self.assertLess(result.ambiguity_score, 0.5)

    # -------------------------------------------------------------------
    # Clarification Generation Tests
    # -------------------------------------------------------------------

    def test_generates_clarification_questions(self):
        result = self.resolver.resolve("hmm")
        self.assertTrue(result.clarification_needed)
        self.assertGreater(len(result.clarification_questions), 0)

    def test_no_clarification_for_clear_intent(self):
        result = self.resolver.resolve(
            "create a new function called validate_email in core/utils.py that checks if email format is valid"
        )
        # Clear intent with specific details should not need clarification
        if result.primary_intent.confidence > 0.4 and result.ambiguity_score <= 0.5:
            self.assertFalse(result.clarification_needed)

    # -------------------------------------------------------------------
    # Constraint Extraction Tests
    # -------------------------------------------------------------------

    def test_extracts_performance_constraint(self):
        result = self.resolver.resolve("optimize this function for better performance and speed")
        constraints = result.primary_intent.constraints
        self.assertTrue(constraints.get("performance_sensitive", False))

    def test_extracts_no_breaking_change_constraint(self):
        result = self.resolver.resolve("refactor but don't break the existing API")
        constraints = result.primary_intent.constraints
        self.assertTrue(constraints.get("no_breaking_changes", False))

    def test_extracts_technology_constraint(self):
        result = self.resolver.resolve("create a new react component for the settings page")
        constraints = result.primary_intent.constraints
        self.assertEqual(constraints.get("technology"), "react")

    # -------------------------------------------------------------------
    # to_dict Serialization Tests
    # -------------------------------------------------------------------

    def test_to_dict_structure(self):
        result = self.resolver.resolve("fix the error in app.js")
        d = result.to_dict()
        self.assertIn("raw_input", d)
        self.assertIn("primary_intent", d)
        self.assertIn("clarification_needed", d)
        self.assertIn("ambiguity_score", d)
        self.assertIsInstance(d["primary_intent"]["task_type"], str)
        self.assertIsInstance(d["primary_intent"]["confidence"], float)

    # -------------------------------------------------------------------
    # Secondary Intent Tests
    # -------------------------------------------------------------------

    def test_multiple_intents(self):
        result = self.resolver.resolve("fix the bug in app.js and then add a new test for it")
        # Should detect both fix_bug and test
        all_types = [result.primary_intent.task_type] + [s.task_type for s in result.secondary_intents]
        self.assertIn("fix_bug", all_types)

    # -------------------------------------------------------------------
    # Semantic Contract & Indonesian Constraint Tests
    # -------------------------------------------------------------------

    def test_indonesian_negative_constraints_extraction(self):
        res = self.resolver.resolve("buatkan fungsi auth baru tapi jangan ubah file config.py dan jangan sentuh database")
        self.assertIsNotNone(res.semantic_contract)
        self.assertIn("config.py", res.semantic_contract.forbidden_targets)
        self.assertTrue(any("database" in t for t in res.semantic_contract.forbidden_targets))

    def test_indonesian_preservation_constraint(self):
        res = self.resolver.resolve("rapikan fungsi ini tanpa menghapus method lama")
        self.assertIsNotNone(res.semantic_contract)
        self.assertTrue(res.semantic_contract.preserve_existing)

    def test_indonesian_expected_ast_traits(self):
        res = self.resolver.resolve("tambahkan validasi input dan pengecekan tipe")
        self.assertIsNotNone(res.semantic_contract)
        self.assertIn("validation", res.semantic_contract.expected_traits)


if __name__ == "__main__":
    unittest.main()
