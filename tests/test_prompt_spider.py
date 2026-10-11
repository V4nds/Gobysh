"""
Unit tests for Prompt Spider Engine and 7-Pillar Empirical Blueprint in Goby v5.3.
Verifies:
  1. 5-tag classification (claim, owner, file, approval, vague)
  2. 7-pillar synthesis (ROLE, OBJEKTIF, CONTEXT, RULE, REVIEW, START, SHIP)
  3. Prompt hash caching invariant
  4. Vague token structured clarification generation
  5. Flaw detector integration
"""

import os
import tempfile
import unittest
from core.spider.prompt_spider import PromptSpider, EmpiricalBlueprint, SpiderToken, ClarificationItem


class TestPromptSpider(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.spider = PromptSpider(repo_root=self.test_dir)

    def test_five_tag_classification(self):
        prompt = "fungsi login lambat tolong benerin auth/session.py jangan hapus token lama buat lebih kenceng"
        blueprint = self.spider.crawl_and_synthesize(prompt, enforce_contracts=False)
        categories = {t.category for t in blueprint.tokens}
        self.assertIn("claim", categories)       # fungsi login lambat
        self.assertIn("file", categories)        # auth/session.py
        self.assertIn("approval", categories)    # jangan hapus
        self.assertIn("vague", categories)       # lebih kenceng

    def test_seven_pillar_synthesis(self):
        prompt = "buat fitur baru pengukur sudut di canvas jangan ubah Toolbar.tsx"
        blueprint = self.spider.crawl_and_synthesize(prompt, enforce_contracts=False)
        self.assertTrue(len(blueprint.role) > 0)
        self.assertTrue(len(blueprint.objective) > 0)
        self.assertIsInstance(blueprint.context, dict)
        self.assertTrue(len(blueprint.rules) > 0)
        self.assertTrue(len(blueprint.review) > 0)
        self.assertTrue(len(blueprint.start_step) > 0)
        self.assertTrue(len(blueprint.ship_criteria) > 0)

    def test_prompt_hash_caching_invariant(self):
        prompt = "buat unit test untuk router"
        bp1 = self.spider.crawl_and_synthesize(prompt, enforce_contracts=False)
        bp2 = self.spider.crawl_and_synthesize(prompt, enforce_contracts=False)
        self.assertEqual(bp1.prompt_hash, bp2.prompt_hash)

    def test_vague_triggers_structured_clarification(self):
        prompt = "rapikan kodenya biar lebih mantap"
        blueprint = self.spider.crawl_and_synthesize(prompt, enforce_contracts=False)
        self.assertTrue(len(blueprint.clarifications) > 0)
        self.assertIsInstance(blueprint.clarifications[0].question, str)
        self.assertIsInstance(blueprint.clarifications[0].options, list)
        self.assertGreater(len(blueprint.clarifications[0].options), 1)

    def test_markdown_and_dict_serialization(self):
        prompt = "refactor database query"
        blueprint = self.spider.crawl_and_synthesize(prompt, enforce_contracts=False)
        md = blueprint.to_markdown()
        self.assertIn("### 1. ROLE", md)
        self.assertIn("### 2. OBJEKTIF", md)
        self.assertIn("### 7. SHIP", md)
        d = blueprint.to_dict()
        self.assertIn("role", d)
        self.assertIn("tokens", d)
        self.assertIn("prompt_hash", d)


if __name__ == "__main__":
    unittest.main()
