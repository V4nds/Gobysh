"""
Unit tests for Technical Flaw & Anomaly Diagnostics Framework in Goby v5.3.
Verifies detection across 3 dimensions:
  1. Prompt/Intent Flaws (contradictions, false premises)
  2. Project Topology & Architecture Flaws (double button/capability collision via registry)
  3. Logic & Layout Flaws (text overflow/fixed container trap, unhandled async)
"""

import unittest
from core.diagnostics.flaw_detector import TechnicalFlawDetector, TechnicalFlaw


class TestTechnicalFlawDetector(unittest.TestCase):
    def setUp(self):
        self.detector = TechnicalFlawDetector()

    def test_detect_double_button_collision(self):
        # Memeriksa pembuatan tombol/kontrol yang kapabilitasnya sudah ada di tempat lain
        flaws = self.detector.audit_topology(
            new_capabilities=[("angle_measurement", "SidebarControls.tsx")],
            existing_registry_files=["Toolbar.tsx"]
        )
        self.assertTrue(any(f.dimension == "project_topology" and "collision" in f.title.lower() for f in flaws))
        collision_flaw = next(f for f in flaws if "collision" in f.title.lower())
        self.assertIn("angle_measurement", collision_flaw.description)

    def test_detect_text_overflow_in_fixed_container(self):
        # Cacat layout: teks panjang berada di dalam kotak berukuran kaku tanpa wrapping dinamis
        bad_jsx = """
        <div className="fixed-box h-10 w-32 overflow-hidden">
            <p className="whitespace-nowrap">Ini adalah deskripsi status yang sangat panjang dan tumpah</p>
        </div>
        """
        flaws = self.detector.audit_code_and_layout(bad_jsx, "StatusCard.tsx")
        self.assertTrue(any(f.dimension == "logic_layout" and "overflow" in f.title.lower() for f in flaws))
        overflow_flaw = next(f for f in flaws if "overflow" in f.title.lower())
        self.assertIn("overflow", overflow_flaw.description.lower())

    def test_detect_prompt_contradiction_flaw(self):
        prompt = "tambahkan fitur export svg ke canvas tapi jangan ubah file canvas sama sekali"
        flaws = self.detector.audit_prompt(prompt)
        self.assertTrue(any(f.dimension == "prompt_intent" and "contradict" in f.title.lower() for f in flaws))



if __name__ == "__main__":
    unittest.main()
