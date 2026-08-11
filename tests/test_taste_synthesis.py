import unittest
from core.taste_synthesis import ModernCSSKeywordHeuristic

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

if __name__ == '__main__':
    unittest.main()
