import unittest
from core.semantics.depth_engine import DepthEngine, ModuleDepthMetrics

class TestDepthEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DepthEngine()

    def test_deep_module_calculation(self):
        code = """
class DataVault:
    def __init__(self, secret: str):
        self._secret = secret
        self._cache = {}

    def retrieve(self, token: str) -> str:
        if token in self._cache:
            return self._cache[token]
        # Rich internal logic
        hashed = 0
        for ch in self._secret:
            hashed = (hashed * 31 + ord(ch)) % 1000007
        result = f"{token}:{hashed}"
        self._cache[token] = result
        return result
"""
        metrics = self.engine.analyze_source(code, "vault.py")
        self.assertIsInstance(metrics, ModuleDepthMetrics)
        self.assertEqual(metrics.classification, "DEEP")
        self.assertGreaterEqual(metrics.mdi_score, 2.0)
        self.assertEqual(len(metrics.anti_patterns), 0)

    def test_shallow_module_detection(self):
        code = """
class DumbWrapper:
    def __init__(self, inner):
        self.inner = inner

    def do_a(self, x):
        return self.inner.do_a(x)

    def do_b(self, y):
        return self.inner.do_b(y)

    def do_c(self, z):
        return self.inner.do_c(z)
"""
        metrics = self.engine.analyze_source(code, "wrapper.py")
        self.assertEqual(metrics.classification, "SHALLOW")
        self.assertLess(metrics.mdi_score, 1.5)
        # Should detect pass-through delegation
        delegates = [ap for ap in metrics.anti_patterns if ap["type"] == "PASS_THROUGH_DELEGATION"]
        self.assertGreaterEqual(len(delegates), 2)

    def test_parameter_bloat_detection(self):
        code = """
def bloated_func(a, b, c, d, e, f, g):
    return a + b
"""
        metrics = self.engine.analyze_source(code, "bloated.py")
        bloat = [ap for ap in metrics.anti_patterns if ap["type"] == "PARAMETER_BLOAT"]
        self.assertEqual(len(bloat), 1)

    def test_ccr_architectural_depth_advisory(self):
        from core.ccr_engine import CognitiveControlRoom
        ccr = CognitiveControlRoom()
        shallow_code = """
class TrivialProxy:
    def __init__(self, target):
        self.target = target
    def m1(self): return self.target.m1()
    def m2(self): return self.target.m2()
    def m3(self): return self.target.m3()
"""
        # Default: advisory (SOFT gate)
        res = ccr.verify_candidate(shallow_code, language="python", check_depth=True, escalate_depth=False)
        self.assertFalse(res["blocked"])
        depth_signals = [s for s in res["signals"] if s["neuron"] == "ARCHITECTURAL_DEPTH"]
        self.assertEqual(len(depth_signals), 1)
        self.assertFalse(depth_signals[0]["passed"])
        self.assertIn("shallow", depth_signals[0]["message"])
        self.assertEqual(depth_signals[0]["gate"], "SOFT")

    def test_ccr_architectural_depth_escalated_hard_gate(self):
        from core.ccr_engine import CognitiveControlRoom
        ccr = CognitiveControlRoom()
        shallow_code = """
class TrivialProxy:
    def __init__(self, target):
        self.target = target
    def m1(self): return self.target.m1()
    def m2(self): return self.target.m2()
    def m3(self): return self.target.m3()
"""
        # Escalated: triggers HARD GATE block
        res = ccr.verify_candidate(shallow_code, language="python", check_depth=True, escalate_depth=True)
        self.assertTrue(res["blocked"])
        hard_fails = res.get("hard_failures", [])
        self.assertTrue(any(f["neuron"] == "ARCHITECTURAL_DEPTH" for f in hard_fails))
        depth_signals = [s for s in res["signals"] if s["neuron"] == "ARCHITECTURAL_DEPTH"]
        self.assertEqual(depth_signals[0]["gate"], "HARD")
        self.assertIn("[ESCALATED HARD GATE]", depth_signals[0]["message"])

    def test_validate_filepath_escalated_hard_gate_integration(self):
        import tempfile
        import os
        from core.ccr_engine import CognitiveControlRoom
        from core.state_memory import StateMemoryManager
        from core.cli import validate_filepath

        ccr = CognitiveControlRoom()
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
            f.write("""
class PointlessWrapper:
    def __init__(self, inner):
        self.inner = inner
    def a(self): return self.inner.a()
    def b(self): return self.inner.b()
    def c(self): return self.inner.c()
""")
            temp_path = f.name

        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as mf:
            mem_path = mf.name

        try:
            mem = StateMemoryManager(mem_path)
            passed = validate_filepath(temp_path, ccr, memory=mem, verbose=False)
            self.assertFalse(passed)

            unresolved = mem.get_unresolved_errors()
            self.assertEqual(len(unresolved), 1)
            self.assertEqual(unresolved[0]["gate"], "ARCHITECTURAL_DEPTH")
            self.assertTrue(unresolved[0]["blocked"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(mem_path):
                os.remove(mem_path)

    def test_hooks_pre_invocation_telemetry_alert(self):
        import tempfile
        import os
        from core.state_memory import StateMemoryManager
        from core.hooks import handle_pre_invocation

        with tempfile.TemporaryDirectory() as tmpdir:
            mem_path = os.path.join(tmpdir, "cognitive_map.json")
            mem = StateMemoryManager(mem_path)
            mem.record_file_validation(
                file_path=os.path.join(tmpdir, "shallow_module.py"),
                passed=False,
                blocked=True,
                gate="ARCHITECTURAL_DEPTH",
                summary="BLOCKED by ARCHITECTURAL_DEPTH",
                error_message="Module is an extreme shallow wrapper"
            )

            res = handle_pre_invocation({"workspacePaths": [tmpdir]})
            self.assertIn("injectSteps", res)
            msg = res["injectSteps"][0]["ephemeralMessage"]
            self.assertIn("GOBY AGGRESSIVE TELEMETRY & HARD GATE ALERT", msg)
            self.assertIn("ARCHITECTURAL_DEPTH", msg)
            self.assertIn("Ousterhout's Law", msg)

    def test_html_report_generation(self):
        from core.semantics.depth_engine import DepthEngine
        from core.cli import generate_architecture_report
        import os

        engine = DepthEngine()
        metrics = engine.analyze_source("def foo():\n    return 42\n", "foo.py")
        report_path = generate_architecture_report([metrics])
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Goby Architecture Review", content)
            self.assertIn("foo.py", content)
            self.assertIn("mermaid", content.lower())
        # Cleanup temp file
        try:
            os.remove(report_path)
        except OSError:
            pass

if __name__ == "__main__":
    unittest.main()
