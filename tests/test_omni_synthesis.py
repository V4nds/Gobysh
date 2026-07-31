import unittest
from core.omni_synthesis import OmniSynthesisEngine

class TestOmniSynthesis(unittest.TestCase):
    def setUp(self):
        self.engine = OmniSynthesisEngine()

    def test_unbounded_recursion_detection(self):
        code = "def loop(x):\n    return loop(x)"
        res = self.engine.analyze_ast(code)
        self.assertFalse(res.is_synthesized)
        self.assertFalse(res.zero_bypass_ready)
        self.assertIn("Unbounded recursion", res.detected_paradoxes[0])

    def test_infinite_while_loop_detection(self):
        code = "def loop():\n    while True:\n        pass"
        res = self.engine.analyze_ast(code)
        self.assertFalse(res.is_synthesized)
        self.assertIn("infinite while-loop", res.detected_paradoxes[0])

    def test_valid_code_pass(self):
        code = "def add(a, b):\n    return a + b"
        res = self.engine.analyze_ast(code)
        self.assertTrue(res.is_synthesized)
        self.assertTrue(res.zero_bypass_ready)

if __name__ == '__main__':
    unittest.main()
