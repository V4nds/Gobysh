"""
Unit tests for VisualDensityGovernor and Anti-Boxification in Goby v5.2.
"""

import unittest
from core.ccr_engine import CognitiveControlRoom
from core.taste_synthesis import VisualDensityGovernor


class TestVisualDensityGovernor(unittest.TestCase):

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_over_encapsulation_detected(self):
        # Code with deeply nested generic wrappers and multiple isolated single-value cards
        bad_code = """
        <div class="container">
            <div class="wrapper">
                <div class="panel">
                    <div class="box">
                        <div class="card p-4"><p>Label 1</p><span>10</span></div>
                        <div class="card p-4"><p>Label 2</p><span>20</span></div>
                        <div class="card p-4"><p>Label 3</p><span>30</span></div>
                    </div>
                </div>
            </div>
        </div>
        """
        eval_res = VisualDensityGovernor.evaluate(bad_code)
        self.assertTrue(eval_res.is_over_encapsulated)
        self.assertGreaterEqual(eval_res.boxification_score, 3)
        self.assertTrue(len(eval_res.detected_anti_patterns) > 0)
        self.assertIn("Anti-Boxification Guardrail", eval_res.suggestion)

    def test_clean_semantic_layout_passes(self):
        # Clean semantic layout using output/canvas/grid directly
        clean_code = """
        <main class="grid grid-cols-3 gap-4">
            <header><h1>Canvas View</h1></header>
            <canvas id="view" width="800" height="600"></canvas>
            <aside class="flex flex-col gap-2">
                <output id="angle">45°</output>
                <output id="status">Active</output>
            </aside>
        </main>
        """
        eval_res = VisualDensityGovernor.evaluate(clean_code)
        self.assertFalse(eval_res.is_over_encapsulated)
        self.assertEqual(len(eval_res.detected_anti_patterns), 0)

    def test_ccr_neuron_boxification_flag(self):
        bad_code = """
        <div class="card-nest">
            <div><div><div><div>
                <div class="card"><p>A</p><span>1</span></div>
                <div class="card"><p>B</p><span>2</span></div>
                <div class="card"><p>C</p><span>3</span></div>
            </div></div></div></div>
        </div>
        """
        sig = self.ccr.neuron_taste_design_check(bad_code)
        self.assertEqual(sig.neuron_name, "TASTE_DESIGN")
        self.assertFalse(sig.passed)
        self.assertIn("OVER_ENCAPSULATION", sig.message)


if __name__ == "__main__":
    unittest.main()
