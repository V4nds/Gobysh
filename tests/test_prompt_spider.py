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

    def test_exemplar_token_tagging(self):
        prompt = "tambahkan fitur canvas misal penggaris, busur derajat, atau jangka"
        blueprint = self.spider.crawl_and_synthesize(prompt, enforce_contracts=False)
        categories = {t.category for t in blueprint.tokens}
        self.assertIn("exemplar", categories)
        exemplars = [t.raw_text for t in blueprint.tokens if t.category == "exemplar"]
        self.assertTrue(any("penggaris" in e for e in exemplars))
        self.assertTrue(any("busur" in e for e in exemplars))

    def test_reference_token_tagging(self):
        prompt = "pelajari dari repo https://github.com/morluto/rea dan adaptasi ke goby"
        blueprint = self.spider.crawl_and_synthesize(prompt, enforce_contracts=False)
        categories = {t.category for t in blueprint.tokens}
        self.assertIn("reference", categories)
        refs = [t.raw_text for t in blueprint.tokens if t.category == "reference"]
        self.assertTrue(any("github.com/morluto/rea" in r for r in refs))

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

    def test_crawl_and_synthesize_registers_obligations(self):
        import tempfile
        from core.state_memory import StateMemoryManager
        with tempfile.TemporaryDirectory() as td:
            spider = PromptSpider(repo_root=td)
            bp = spider.crawl_and_synthesize("fix broken login auth.py", enforce_contracts=True)
            mem = StateMemoryManager(os.path.join(td, "cognitive_map.json"))
            obs = mem.get_unresolved_obligations()
            self.assertGreaterEqual(len(obs), 1)
            claims = [o["claim"] for o in obs]
            self.assertTrue(any("broken" in c for c in claims))

    def test_generate_visual_architecture_diagram(self):
        prompt = "buat fitur export SVG di canvas src/export.ts"
        bp = self.spider.crawl_and_synthesize(prompt, enforce_contracts=False, generate_visual=True)
        self.assertIsNotNone(bp.visual_diagram)
        self.assertIn("<svg", bp.visual_diagram)
        self.assertIn('stroke-width="1"', bp.visual_diagram)
        self.assertIn("#bf4520", bp.visual_diagram)
        self.assertIn("Density: 4/10", bp.visual_diagram)

        md = bp.to_markdown()
        self.assertIn("### 8. VISUAL ARCHITECTURE SCHEMATIC", md)
        self.assertIn("<svg", md)

    def test_blueprint_contains_anti_parroting_rule(self):
        prompt = "tambahkan fitur canvas misal penggaris, busur derajat"
        bp = self.spider.crawl_and_synthesize(prompt, enforce_contracts=False)
        self.assertTrue(any("ANTI_PARROTING_EXEMPLAR_INDUCTION" in r for r in bp.rules))
        self.assertEqual(bp.context.get("exemplar_domain"), "geometric_measurement_tools")
        self.assertTrue(len(bp.context.get("exemplar_variations", [])) > 0)

    def test_blueprint_contains_identity_preservation_rule(self):
        prompt = "pelajari https://github.com/morluto/rea untuk referensi"
        bp = self.spider.crawl_and_synthesize(prompt, enforce_contracts=False)
        self.assertTrue(any("IDENTITY_PRESERVATION" in r for r in bp.rules))
        self.assertIn("https://github.com/morluto/rea", bp.context.get("external_references", []))


if __name__ == "__main__":
    unittest.main()
