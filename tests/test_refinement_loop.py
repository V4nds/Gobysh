import unittest
from core.ccr_engine import CognitiveControlRoom
from core.failure_memory import FailurePatternStore
from core.lde_detector import LoopDetectionEngine
from core.refinement_loop import CCRRefinementLoop, RefinementResult


class TestRefinementLoop(unittest.TestCase):
    def test_refinement_success_on_valid_code(self):
        ccr = CognitiveControlRoom()
        refiner = CCRRefinementLoop(ccr=ccr)
        result = refiner.run_refinement_cycle("x = 10\nprint(x)")
        self.assertTrue(result.is_resolved)
        self.assertEqual(result.attempts, 1)

    def test_refinement_blocks_invalid_syntax(self):
        ccr = CognitiveControlRoom()
        refiner = CCRRefinementLoop(ccr=ccr)
        result = refiner.run_refinement_cycle("x = ")
        self.assertFalse(result.is_resolved)
        self.assertTrue(result.blocked_by_hard_gate)


if __name__ == "__main__":
    unittest.main()
