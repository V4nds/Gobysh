import ast
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from core.ccr_engine import NeuronSignal, GateType

def neuron_syntax_check(self, code: str) -> NeuronSignal:
    """
    Signal: Is this code syntactically valid?
    Mechanism: ast.parse()

    HARD GATE — if syntax is invalid, code CANNOT be output.
    """
    try:
        ast.parse(code)
        return NeuronSignal(
            neuron_name="SYNTAX",
            gate_type=GateType.HARD,
            passed=True,
            confidence=1.0,
            message="Syntax is valid.",
            evidence={"valid": True},
            suggestion="",
        )
    except SyntaxError as e:
        return NeuronSignal(
            neuron_name="SYNTAX",
            gate_type=GateType.HARD,
            passed=False,
            confidence=1.0,
            message=f"SyntaxError: {e.msg} at line {e.lineno}",
            evidence={
                "error_type": "SyntaxError",
                "message": e.msg or "",
                "line": e.lineno,
                "offset": e.offset,
                "text": (e.text or "").strip(),
            },
            suggestion=f"Fix syntax error at line {e.lineno}: {e.msg}",
        )

