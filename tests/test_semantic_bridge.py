"""
Unit tests for Tripartite Semantic Bridge in Goby v5.3.
Verifies bilingual normalization (ID <-> EN <-> AST symbols) and ambiguity disambiguation.
"""

import unittest
from core.spider.semantic_bridge import TripartiteSemanticBridge, NormalizedConcept
from core.translation.symbol_mapper import SymbolMap, Symbol, FileSymbolMap


class TestTripartiteSemanticBridge(unittest.TestCase):
    def setUp(self):
        sym_map = SymbolMap()
        sym_map.add_file(FileSymbolMap(
            file_path="src/canvas/Toolbar.tsx",
            symbols=[Symbol(name="CanvasToolbar", kind="class", file_path="src/canvas/Toolbar.tsx")]
        ))
        sym_map.add_file(FileSymbolMap(
            file_path="src/canvas/tools/AngleMeasure.ts",
            symbols=[Symbol(name="AngleMeasureTool", kind="class", file_path="src/canvas/tools/AngleMeasure.ts")]
        ))
        self.bridge = TripartiteSemanticBridge(symbol_map=sym_map)

    def test_bilingual_action_normalization(self):
        concept = self.bridge.normalize_phrase("bikin tombol ukur sudut")
        self.assertEqual(concept.action, "create_feature")
        self.assertIn("angle_measure", concept.keywords)

    def test_negation_and_preservation_detection(self):
        concept = self.bridge.normalize_phrase("jangan sampai bentrok sama Toolbar.tsx")
        self.assertTrue(concept.has_preservation)
        self.assertIn("Toolbar.tsx", concept.preserved_targets)
        self.assertIn("collision", concept.risk_flags)

    def test_disambiguate_vague_vs_new_entity(self):
        self.assertEqual(self.bridge.classify_token_ambiguity("bikin lebih keren", "create_feature"), "vague")
        self.assertEqual(self.bridge.classify_token_ambiguity("AngleMeasureTool", "create_feature"), "new_entity")
        self.assertEqual(self.bridge.classify_token_ambiguity("modul kompresi data", "create_feature"), "new_entity")

    def test_ast_symbol_resolution(self):
        matches = self.bridge.resolve_ast_entities(["ukur sudut", "toolbar"])
        matched_files = [m.file_path for m in matches]
        self.assertIn("src/canvas/Toolbar.tsx", matched_files)


if __name__ == "__main__":
    unittest.main()
