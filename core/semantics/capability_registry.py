"""
Component Capability Registry & Anti-Collision Engine for Goby v5.2.
Prevents duplicate / leaked features across different layout surfaces
(e.g., creating the same angle measurement controls in both Toolbar and Sidebar).
"""

from dataclasses import dataclass, field
import os
import re
from typing import Any, Dict, List, Optional, Set


@dataclass
class CapabilityEntry:
    """Registered capability bound to a specific component and layout slot."""
    capability: str
    component_name: str
    file_path: str
    slot: Optional[str] = None  # e.g., 'primary_canvas', 'toolbar_dock', 'sidebar_panel', 'telemetry_hud'
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability": self.capability,
            "component_name": self.component_name,
            "file_path": self.file_path,
            "slot": self.slot,
            "metadata": self.metadata,
        }


class ComponentCapabilityRegistry:
    """
    Central registry and anti-collision validator for UI component capabilities.
    Maintains Single Source of Truth (SSOT) across the repository component tree.
    """

    _registry: Dict[str, List[CapabilityEntry]] = {}

    # Known capability semantic mapping patterns
    CAPABILITY_PATTERNS = {
        "angle_measurement": [
            r"\bmeasure_?angle\b", r"\bcalc_?angle\b", r"\bangle_?measurement\b",
            r"\bhandle_?angle\b", r"\bsudut\b", r"\bprotractor\b"
        ],
        "canvas_reset": [
            r"\breset_?canvas\b", r"\bclear_?canvas\b", r"\breset_?view\b",
            r"\bhandle_?reset\b", r"\breset_?state\b"
        ],
        "zoom_control": [
            r"\bzoom_?in\b", r"\bzoom_?out\b", r"\bhandle_?zoom\b",
            r"\bzoom_?level\b", r"\bset_?zoom\b"
        ],
        "file_export": [
            r"\bexport_?svg\b", r"\bexport_?png\b", r"\bexport_?pdf\b",
            r"\bhandle_?export\b", r"\bdownload_?canvas\b"
        ],
        "theme_toggle": [
            r"\btoggle_?theme\b", r"\bdark_?mode\b", r"\blight_?mode\b",
            r"\btheme_?switcher\b"
        ],
    }

    @classmethod
    def register(
        cls,
        capability: str,
        component_name: str,
        file_path: str,
        slot: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CapabilityEntry:
        """Register a capability to a component and file."""
        clean_file = file_path.replace("\\", "/") if file_path else ""
        norm_file = clean_file.lower()
        entry = CapabilityEntry(
            capability=capability,
            component_name=component_name,
            file_path=clean_file,
            slot=slot,
            metadata=metadata or {},
        )
        if capability not in cls._registry:
            cls._registry[capability] = []

        # Avoid exact duplicate registration
        existing = [e for e in cls._registry[capability] if e.file_path.lower() == norm_file and e.component_name == component_name]
        if not existing:
            cls._registry[capability].append(entry)
        return entry

    @classmethod
    def get_entries_for_capability(cls, capability: str) -> List[CapabilityEntry]:
        return cls._registry.get(capability, [])

    @classmethod
    def extract_capabilities(cls, code: str) -> List[str]:
        """Extract recognizable capability signatures from source code."""
        code_lower = code.lower()
        extracted: Set[str] = set()

        for cap, patterns in cls.CAPABILITY_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, code_lower):
                    extracted.add(cap)
                    break

        return sorted(list(extracted))

    @classmethod
    def detect_collisions(cls, file_path: str, code: str) -> List[Dict[str, Any]]:
        """
        Detect if newly introduced code attempts to re-implement or duplicate
        an existing capability that is already bound to another component.
        """
        clean_file = file_path.replace("\\", "/") if file_path else ""
        norm_file = clean_file.lower()
        detected_caps = cls.extract_capabilities(code)
        collisions: List[Dict[str, Any]] = []

        for cap in detected_caps:
            existing_entries = cls.get_entries_for_capability(cap)
            for entry in existing_entries:
                # If registered in a different file, it's a cross-component collision
                if entry.file_path and entry.file_path.lower() != norm_file:
                    collisions.append({
                        "capability": cap,
                        "current_file": clean_file,
                        "registered_file": entry.file_path,
                        "component_name": entry.component_name,
                        "slot": entry.slot,
                        "message": (
                            f"Feature Collision Detected: Capability '{cap}' is already implemented in "
                            f"'{entry.file_path}' ({entry.component_name}). Duplicating controls in "
                            f"'{clean_file}' creates leaked redundant features across layouts."
                        ),
                    })
        return collisions


    @classmethod
    def clear(cls) -> None:
        """Clear all registered capabilities."""
        cls._registry.clear()
