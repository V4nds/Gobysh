"""
Unit tests for ComponentCapabilityRegistry and Anti-Collision Engine in Goby v5.2.
"""

import unittest
from core.ccr_engine import CognitiveControlRoom
from core.semantics.capability_registry import ComponentCapabilityRegistry


class TestComponentCapabilityRegistry(unittest.TestCase):

    def setUp(self):
        ComponentCapabilityRegistry.clear()
        self.ccr = CognitiveControlRoom()

    def tearDown(self):
        ComponentCapabilityRegistry.clear()

    def test_extract_capabilities_from_code(self):
        code = """
        function Toolbar() {
            const handleAngleMeasurement = () => {
                measureAngle(p1, p2, p3);
            };
            const resetCanvas = () => {
                clearCanvas();
            };
            return <div className="toolbar"><button onClick={handleAngleMeasurement}>Sudut</button></div>;
        }
        """
        caps = ComponentCapabilityRegistry.extract_capabilities(code)
        self.assertIn("angle_measurement", caps)
        self.assertIn("canvas_reset", caps)

    def test_detect_collision_across_files(self):
        # Register capability in Toolbar.tsx
        ComponentCapabilityRegistry.register(
            capability="angle_measurement",
            component_name="ToolbarControl",
            file_path="src/components/Toolbar.tsx",
            slot="toolbar_dock",
        )

        # Attempt to duplicate in InspectorPanel.tsx
        duplicate_code = """
        function InspectorPanel() {
            return (
                <div className="inspector">
                    <button onClick={measureAngle}>Pengukuran Sudut</button>
                </div>
            );
        }
        """
        collisions = ComponentCapabilityRegistry.detect_collisions(
            file_path="src/components/InspectorPanel.tsx",
            code=duplicate_code,
        )
        self.assertEqual(len(collisions), 1)
        self.assertEqual(collisions[0]["capability"], "angle_measurement")
        self.assertIn("Toolbar.tsx", collisions[0]["message"])

    def test_no_collision_same_file(self):
        # Registering and updating within the same file should NOT trigger collision
        ComponentCapabilityRegistry.register(
            capability="angle_measurement",
            component_name="ToolbarControl",
            file_path="src/components/Toolbar.tsx",
            slot="toolbar_dock",
        )
        code = "<div className='toolbar'><button onClick={measureAngle}>Sudut</button></div>"
        collisions = ComponentCapabilityRegistry.detect_collisions(
            file_path="src/components/Toolbar.tsx",
            code=code,
        )
        self.assertEqual(len(collisions), 0)

    def test_neuron_taste_design_catches_collision(self):
        # Register in File A
        ComponentCapabilityRegistry.register(
            capability="angle_measurement",
            component_name="ToolbarControl",
            file_path="src/components/Toolbar.tsx",
            slot="toolbar_dock",
        )

        # Check File B with CCR neuron
        duplicate_code = "<div className='sidebar'><button onClick={measureAngle}>Hitung Sudut</button></div>"
        sig = self.ccr.neuron_taste_design_check(duplicate_code, file_path="src/components/Sidebar.tsx")
        self.assertEqual(sig.neuron_name, "TASTE_DESIGN")
        self.assertFalse(sig.passed)
        self.assertIn("DUPLICATE_FEATURE_COLLISION", sig.message)
        self.assertIn("Toolbar.tsx", sig.message)


if __name__ == "__main__":
    unittest.main()
