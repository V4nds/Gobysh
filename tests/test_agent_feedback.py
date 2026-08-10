"""
Unit tests for Goby Agent Control Protocol (GobyFeedback & STRATEGY_CHANGE_REQUIRED state transitions).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import core
from core.ccr_engine import CognitiveControlRoom, GobyFeedback
import goby_agent_impact_runner


class TestAgentControlProtocol(unittest.TestCase):

    def setUp(self):
        self.ccr = CognitiveControlRoom()

    def test_verify_candidate_with_feedback_clean(self):
        code = "a = 10\nb = 20\nc = a + b"
        fb = self.ccr.verify_candidate_with_feedback(code)
        self.assertTrue(fb.verified)
        self.assertFalse(fb.blocked)
        self.assertEqual(fb.status, "VERIFIED")
        self.assertFalse(fb.strategy_change_required)

    def test_verify_candidate_with_feedback_scope_blocked(self):
        code = "def calc():\n    return undefined_price * 10"
        fb = self.ccr.verify_candidate_with_feedback(code)
        self.assertFalse(fb.verified)
        self.assertTrue(fb.blocked)
        self.assertEqual(fb.status, "BLOCKED")
        self.assertEqual(fb.gate, "SCOPE")
        self.assertIn("SCOPE BLOCKED", fb.suggestion)

    def test_verify_candidate_with_feedback_strategy_change_required(self):
        code = "const users = props.data; users.map(u => u.id);"
        err_log = "TypeError: Cannot read property 'map' of undefined"

        # Attempt 1: Normal record
        fb1 = self.ccr.verify_candidate_with_feedback(code, language="js", error_context=err_log, attempt=1)
        
        # Attempt 2: Identical candidate & error -> LDE triggers STRATEGY_CHANGE_REQUIRED
        fb2 = self.ccr.verify_candidate_with_feedback(code, language="js", error_context=err_log, attempt=2)
        
        self.assertTrue(fb2.blocked)
        self.assertTrue(fb2.repeated_failure)
        self.assertTrue(fb2.strategy_change_required)
        self.assertEqual(fb2.status, "STRATEGY_CHANGE_REQUIRED")
        self.assertEqual(fb2.gate, "LDE")
        self.assertIn("LDE REPEATED FAILURE", fb2.suggestion)

    def test_top_level_verify_with_feedback_helper(self):
        fb = core.verify_with_feedback("x = 1; y = 2")
        self.assertEqual(fb.status, "VERIFIED")

    def test_agent_impact_runner_trials(self):
        agent = goby_agent_impact_runner.ReferenceAgentAdapter()
        evaluator = goby_agent_impact_runner.ReferenceEvaluator()

        task = {
            "task_id": "test-task",
            "candidates": ["def calc(): return missing * 2", "def calc(): return 42"],
            "error_logs": ["NameError: missing"],
            "expected_success": True
        }

        res_control = goby_agent_impact_runner.run_trial(agent, evaluator, task, "CONTROL", 1)
        res_goby = goby_agent_impact_runner.run_trial(agent, evaluator, task, "GOBY_LDE", 1)

        self.assertTrue(res_control.success)
        self.assertTrue(res_goby.success)
        self.assertGreaterEqual(res_goby.attempts, 2)
        self.assertGreaterEqual(res_goby.goby_blocks, 1)


if __name__ == "__main__":
    unittest.main()
