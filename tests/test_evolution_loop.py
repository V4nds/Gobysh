import unittest
from core.evolution_loop import SelfEvolutionEngine

class TestEvolutionLoop(unittest.TestCase):
    def setUp(self):
        self.engine = SelfEvolutionEngine()

    def test_evolution_cycle_bfm(self):
        res = self.engine.run_evolution_cycle()
        self.assertEqual(res["total_benchmarks"], 3)
        self.assertEqual(res["bypass_frequency_metric"], 0.0)
        self.assertEqual(res["status"], "ZERO_BYPASS_ACHIEVED")

if __name__ == '__main__':
    unittest.main()
