"""
Unit tests for SessionBriefingEngine.
"""

import os
import tempfile
import unittest
from core.session_briefing import SessionBriefingEngine


class TestSessionBriefingEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.briefing_engine = SessionBriefingEngine(workspace_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_snapshot_and_auto_resume(self):
        # Create a session snapshot before shutdown
        briefing_path = self.briefing_engine.create_snapshot(
            last_completed_task="Built User Authentication Middleware",
            current_in_progress="Refactoring JWT Token Refresh Endpoint",
            next_action="Run unit tests for JWT Refresh token expiration"
        )

        self.assertTrue(os.path.exists(briefing_path))

        # Re-open session and trigger auto_resume_briefing()
        resume_data = self.briefing_engine.auto_resume_briefing()

        self.assertTrue(resume_data["has_saved_snapshot"])
        self.assertEqual(resume_data["last_completed_task"], "Built User Authentication Middleware")
        self.assertEqual(resume_data["current_in_progress"], "Refactoring JWT Token Refresh Endpoint")
        self.assertEqual(resume_data["next_action"], "Run unit tests for JWT Refresh token expiration")
        self.assertEqual(resume_data["resume_status"], "READY_TO_CONTINUE")


if __name__ == "__main__":
    unittest.main()
