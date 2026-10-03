import ast
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from core.ccr_engine import NeuronSignal, GateType
from core.taste_synthesis import ModernCSSKeywordHeuristic, VisualDensityGovernor
from core.semantics.capability_registry import ComponentCapabilityRegistry

def neuron_taste_design_check(self, code: str, content_type: str = "CODE", file_path: str = "") -> NeuronSignal:
    """
    Signal: Does this code conform to modern Taste Design, Anti-Boxification,
    and prevent feature collision across layout components?
    """
    # Only strict check if code contains UI elements (html, css, jsx, tsx)
    is_ui = any(tag in code.lower() for tag in ["<div", "classname=", "style=", "<style", "document.create"])

    if not is_ui:
        return NeuronSignal(
            neuron_name="TASTE_DESIGN",
            gate_type=GateType.SOFT,
            passed=True,
            confidence=1.0,
            message="Code is not a UI component, skipping Taste Design check.",
        )

    evaluation = ModernCSSKeywordHeuristic.evaluate(code)
    density_eval = VisualDensityGovernor.evaluate(code)
    collisions = ComponentCapabilityRegistry.detect_collisions(file_path, code)

    evidence = {
        "scores": evaluation.__dict__,
        "density": density_eval.__dict__,
        "collisions": collisions,
    }

    # Priority 1: Feature collision / duplication across components
    if collisions:
        collision_msg = collisions[0]["message"]
        return NeuronSignal(
            neuron_name="TASTE_DESIGN",
            gate_type=GateType.HARD if content_type == "DESIGN" else GateType.SOFT,
            passed=False,
            confidence=0.95,
            message=f"DUPLICATE_FEATURE_COLLISION: {collision_msg}",
            evidence=evidence,
            suggestion="Reference existing component capability instead of duplicating controls across layouts.",
        )

    # Priority 2: Over-encapsulation (Boxification)
    if density_eval.is_over_encapsulated:
        return NeuronSignal(
            neuron_name="TASTE_DESIGN",
            gate_type=GateType.SOFT,
            passed=False,
            confidence=0.85,
            message=f"OVER_ENCAPSULATION (Boxification): {density_eval.detected_anti_patterns[0]}",
            evidence=evidence,
            suggestion=density_eval.suggestion,
        )

    # Legacy / Soft fallback check for slop
    if evaluation.is_slop:
        return NeuronSignal(
            neuron_name="TASTE_DESIGN",
            gate_type=GateType.HARD if content_type == "DESIGN" else GateType.SOFT,
            passed=False,
            confidence=0.9,
            message="UI Code detected as SLOP (lacking multi-dimensional aesthetics).",
            evidence=evidence,
            suggestion=evaluation.bypass_suggestion,
        )

    return NeuronSignal(
        neuron_name="TASTE_DESIGN",
        gate_type=GateType.SOFT,
        passed=True,
        confidence=0.8,
        message="Modern Taste Design detected (clean density, no collisions).",
        evidence=evidence,
        suggestion=evaluation.bypass_suggestion if evaluation.bypass_suggestion else None,
    )


