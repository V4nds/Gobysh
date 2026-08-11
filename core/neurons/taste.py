import ast
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from core.ccr_engine import NeuronSignal, GateType
from core.taste_synthesis import ModernCSSKeywordHeuristic

def neuron_taste_design_check(self, code: str, content_type: str = "CODE") -> NeuronSignal:
    """
    Signal: Does this code conform to modern Taste Design and Motion Synthesis?
    (ThreeJS, GSAP, Design DNA, Lottie, Genjutsu)

    Mechanism: Delegates evaluation to the ModernCSSKeywordHeuristic (Right Brain) 
    to calculate a multi-dimensional aesthetic score.
    """
    # Only strict check if code contains UI elements (html, css, jsx, tsx)
    is_ui = any(tag in code.lower() for tag in ["<div", "className=", "style=", "<style", "document.create"])

    if not is_ui:
        return NeuronSignal(
            neuron_name="TASTE_DESIGN",
            gate_type=GateType.SOFT,
            passed=True,
            confidence=1.0,
            message="Code is not a UI component, skipping Taste Design check.",
        )

    evaluation = ModernCSSKeywordHeuristic.evaluate(code)

    if evaluation.is_slop:
        return NeuronSignal(
            neuron_name="TASTE_DESIGN",
            gate_type=GateType.HARD if content_type == "DESIGN" else GateType.SOFT,
            passed=False,
            confidence=0.9,
            message="UI Code detected as SLOP (lacking multi-dimensional aesthetics).",
            evidence={"scores": evaluation.__dict__},
            suggestion=evaluation.bypass_suggestion,
        )

    return NeuronSignal(
        neuron_name="TASTE_DESIGN",
        gate_type=GateType.SOFT,
        passed=True,
        confidence=0.8,
        message="Modern Taste Design detected.",
        evidence={"scores": evaluation.__dict__},
        suggestion=evaluation.bypass_suggestion if evaluation.bypass_suggestion else None,
    )

