import unittest
from core.taste_synthesis import ModernCSSKeywordHeuristic, VisualDensityGovernor, EditorialDiagramHeuristic

class TestModernCSSKeywordHeuristic(unittest.TestCase):
    
    def test_evaluate_slop(self):
        # Code with very basic HTML/CSS, no modern keywords
        code = "<div><h1>Hello World</h1><p>Basic text</p></div>"
        evaluation = ModernCSSKeywordHeuristic.evaluate(code)
        
        self.assertTrue(evaluation.is_slop)
        self.assertEqual(evaluation.total_score, 0)
        self.assertTrue("Taste Synthesis Bypass Triggered" in evaluation.bypass_suggestion)

    def test_evaluate_spatial_only(self):
        # Code with flex/grid but no visual or motion depth should still be considered slop
        # as per rule: is_slop = total_score < 3 or (spatial == 0 and visual == 0)
        # Wait, if spatial=1, visual=0, motion=0, total=1 -> slop
        code = "<div style='display: flex;'></div>"
        evaluation = ModernCSSKeywordHeuristic.evaluate(code)
        self.assertTrue(evaluation.is_slop)
        
    def test_evaluate_modern_taste(self):
        # Code with bento layout, gsap motion, and layered shadows
        code = '''
            <div class="bento-box" style="display: grid; gap: 1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                <div class="card gsap-animate">
                    <p style="font-size: clamp(1rem, 2vw, 2rem);">Content</p>
                </div>
            </div>
        '''
        evaluation = ModernCSSKeywordHeuristic.evaluate(code)
        
        self.assertFalse(evaluation.is_slop)
        self.assertGreaterEqual(evaluation.spatial_score, 3) # bento, grid, clamp
        self.assertGreaterEqual(evaluation.motion_score, 1)  # gsap
        self.assertGreaterEqual(evaluation.visual_score, 1)  # box-shadow
        self.assertGreaterEqual(evaluation.total_score, 5)

    def test_evaluate_genjutsu(self):
        # Code containing threejs and webgl 
        code = '''
            import * as THREE from 'three';
            const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('canvas') });
            // Add particles
        '''
        evaluation = ModernCSSKeywordHeuristic.evaluate(code)
        
        # In JS files without UI tags it might not be passed to evaluate by CCR, but evaluate handles it.
        # total_score = 3 (three, webgl, canvas, particles = 4)
        self.assertFalse(evaluation.is_slop)
        self.assertEqual(evaluation.genjutsu_score, 4)


class TestEditorialDiagramHeuristic(unittest.TestCase):

    def test_editorial_diagram_optimal_density(self):
        # Crisp SVG schematic with 1px hairlines and 1 focal accent
        svg = '''
        <svg viewBox="0 0 800 400">
            <rect x="50" y="50" width="120" height="60" stroke="#2d3142" stroke-width="1" fill="#f5f5f5" />
            <rect x="250" y="50" width="120" height="60" stroke="#bf4520" stroke-width="1" fill="#ffffff" />
            <line x1="170" y1="80" x2="250" y2="80" stroke="#2d3142" stroke-width="1" />
        </svg>
        '''
        res = EditorialDiagramHeuristic.evaluate(svg)
        self.assertFalse(res.is_cluttered)
        self.assertFalse(res.is_mermaid_slop)
        self.assertFalse(res.has_heavy_strokes)
        self.assertFalse(res.has_rainbow_accents)
        self.assertEqual(res.focal_accent_count, 1)  # #bf4520

    def test_editorial_diagram_mermaid_slop(self):
        # 12 flat unstyled nodes in flat spaghetti
        mermaid = '''
        graph TD
            A[Start] --> B[Step 1]
            B --> C[Step 2]
            C --> D[Step 3]
            D --> E[Step 4]
            E --> F[Step 5]
            F --> G[Step 6]
            G --> H[Step 7]
            H --> I[Step 8]
            I --> J[Step 9]
            J --> K[Step 10]
        '''
        res = EditorialDiagramHeuristic.evaluate(mermaid)
        self.assertTrue(res.is_mermaid_slop)
        self.assertTrue(res.is_cluttered)
        self.assertIn("Mermaid Slop", res.anti_patterns[0])

    def test_editorial_diagram_rainbow_accents(self):
        # 5 distinct vibrant colors on nodes
        svg = '''
        <svg viewBox="0 0 800 400">
            <rect fill="#ff0000" stroke-width="1" />
            <rect fill="#00ff00" stroke-width="1" />
            <rect fill="#0000ff" stroke-width="1" />
            <rect fill="#ff00ff" stroke-width="1" />
            <rect fill="#ffff00" stroke-width="1" />
        </svg>
        '''
        res = EditorialDiagramHeuristic.evaluate(svg)
        self.assertTrue(res.has_rainbow_accents)
        self.assertTrue(res.is_cluttered)
        self.assertGreater(res.focal_accent_count, 3)

    def test_editorial_diagram_heavy_strokes(self):
        # SVG with 4px heavy borders
        svg = '''
        <svg viewBox="0 0 800 400">
            <rect x="10" y="10" width="100" height="50" stroke="#333" stroke-width="4px" />
        </svg>
        '''
        res = EditorialDiagramHeuristic.evaluate(svg)
        self.assertTrue(res.has_heavy_strokes)


if __name__ == '__main__':
    unittest.main()
