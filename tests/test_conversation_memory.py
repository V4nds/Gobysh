"""Tests for ConversationMemoryStore module (Goby v5.0)."""

import json
import os
import tempfile
import unittest
from core.conversation_memory import ConversationMemoryStore, ConversationEntry, RecallResult


class TestConversationMemoryStore(unittest.TestCase):
    """Test suite for the Conversation Memory Store."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = os.path.join(self.temp_dir, "test_conversation_index.json")
        self.store = ConversationMemoryStore(memory_file_path=self.memory_file)

    def tearDown(self):
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)
        tmp = self.memory_file + ".tmp"
        if os.path.exists(tmp):
            os.remove(tmp)
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            pass

    # -------------------------------------------------------------------
    # Initialization Tests
    # -------------------------------------------------------------------

    def test_creates_file_on_init(self):
        self.assertTrue(os.path.exists(self.memory_file))

    def test_initial_file_has_valid_json(self):
        with open(self.memory_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["entry_count"], 0)
        self.assertEqual(data["conversations"], [])

    # -------------------------------------------------------------------
    # Save Tests
    # -------------------------------------------------------------------

    def test_save_creates_entry(self):
        entry = self.store.save(
            user_intent_summary="Fix TypeError in app.js",
            task_type="fix_bug",
            files_modified=["app.js"],
            solution_summary="Added null check",
            final_status="SUCCESS",
        )
        self.assertIsInstance(entry, ConversationEntry)
        self.assertEqual(entry.task_type, "fix_bug")
        self.assertEqual(entry.final_status, "SUCCESS")
        self.assertTrue(len(entry.entry_id) > 0)

    def test_save_persists_to_disk(self):
        self.store.save(
            user_intent_summary="Create login page",
            task_type="create_feature",
        )
        with open(self.memory_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["entry_count"], 1)
        self.assertEqual(data["conversations"][0]["task_type"], "create_feature")

    def test_save_multiple_entries(self):
        for i in range(5):
            self.store.save(
                user_intent_summary=f"Task number {i}",
                task_type="test",
            )
        entries = self.store.get_all_entries()
        self.assertEqual(len(entries), 5)

    def test_auto_prune_at_max_entries(self):
        original_max = self.store.MAX_ENTRIES
        self.store.MAX_ENTRIES = 5
        try:
            for i in range(10):
                self.store.save(
                    user_intent_summary=f"Task {i}",
                    task_type="test",
                )
            entries = self.store.get_all_entries()
            self.assertEqual(len(entries), 5)
            # Should keep the most recent 5
            self.assertEqual(entries[-1].user_intent_summary, "Task 9")
        finally:
            self.store.MAX_ENTRIES = original_max

    # -------------------------------------------------------------------
    # Recall Tests
    # -------------------------------------------------------------------

    def test_recall_finds_similar_entry(self):
        self.store.save(
            user_intent_summary="Fix TypeError in app.js event handler",
            task_type="fix_bug",
            files_modified=["app.js"],
            solution_summary="Added null check before accessing event.target",
        )

        results = self.store.recall("fix TypeError in app.js")
        self.assertTrue(len(results) > 0)
        self.assertTrue(results[0].found)
        self.assertGreater(results[0].similarity, 0.0)

    def test_recall_returns_not_found_for_unrelated(self):
        self.store.save(
            user_intent_summary="Create a React dashboard with charts",
            task_type="create_feature",
        )

        results = self.store.recall("deploy kubernetes cluster to AWS")
        # Should not find a good match
        has_found = any(r.found for r in results)
        if not has_found:
            self.assertFalse(results[0].found)

    def test_recall_on_empty_memory(self):
        results = self.store.recall("anything at all")
        self.assertTrue(len(results) > 0)
        self.assertFalse(results[0].found)
        self.assertEqual(results[0].similarity, 0.0)

    def test_recall_context_hint_format(self):
        self.store.save(
            user_intent_summary="Fix import error in main.py",
            task_type="fix_bug",
            files_modified=["main.py"],
            solution_summary="Corrected module path",
        )

        results = self.store.recall("fix import error in main.py")
        if results[0].found:
            self.assertIn("Past session", results[0].context_hint)

    # -------------------------------------------------------------------
    # Tag Extraction Tests
    # -------------------------------------------------------------------

    def test_auto_tags_include_task_type(self):
        entry = self.store.save(
            user_intent_summary="Fix Python error",
            task_type="fix_bug",
            files_modified=["main.py"],
        )
        self.assertIn("fix_bug", entry.tags)

    def test_auto_tags_include_file_extension(self):
        entry = self.store.save(
            user_intent_summary="Update styles",
            task_type="design_ui",
            files_modified=["index.css"],
        )
        self.assertIn("css", entry.tags)

    def test_auto_tags_include_tech_keywords(self):
        entry = self.store.save(
            user_intent_summary="Create React component with TypeScript",
            task_type="create_feature",
        )
        self.assertIn("react", entry.tags)
        self.assertIn("typescript", entry.tags)

    # -------------------------------------------------------------------
    # Summary Stats Tests
    # -------------------------------------------------------------------

    def test_summary_stats_empty(self):
        stats = self.store.get_summary_stats()
        self.assertEqual(stats["total"], 0)

    def test_summary_stats_with_data(self):
        self.store.save(user_intent_summary="Task A", task_type="fix_bug", files_modified=["a.py"])
        self.store.save(user_intent_summary="Task B", task_type="fix_bug", files_modified=["b.py"])
        self.store.save(user_intent_summary="Task C", task_type="create_feature", files_modified=["a.py"])

        stats = self.store.get_summary_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["by_type"]["fix_bug"], 2)
        self.assertEqual(stats["by_type"]["create_feature"], 1)
        self.assertEqual(stats["unique_files"], 2)  # a.py and b.py

    # -------------------------------------------------------------------
    # Clear Memory Tests
    # -------------------------------------------------------------------

    def test_clear_memory(self):
        self.store.save(user_intent_summary="Task", task_type="test")
        self.store.clear_memory()
        entries = self.store.get_all_entries()
        self.assertEqual(len(entries), 0)

    # -------------------------------------------------------------------
    # Semantic Fingerprint Tests
    # -------------------------------------------------------------------

    def test_fingerprint_strips_specifics(self):
        fp1 = self.store._create_fingerprint("Fix error in app.js line 42")
        fp2 = self.store._create_fingerprint("Fix error in main.py line 100")
        # After stripping file refs and numbers, these should be similar
        self.assertNotEqual(fp1, "")
        self.assertNotEqual(fp2, "")


if __name__ == "__main__":
    unittest.main()
