import ast
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from core.ccr_engine import NeuronSignal, GateType

def neuron_behavior_check(
    self, code: str, expected_behavior: Dict[str, Any]
) -> NeuronSignal:
    """
    Signal: Does this code produce output matching expected behavior?
    Mechanism: Execute via GCA, compare output against expectations.

    SOFT SIGNAL — behavior matching requires AI interpretation.

    expected_behavior = {
        "success_indicators": ["expected output", ...],
        "failure_indicators": ["error", "traceback", ...],
        "description": "what this code should do"
    }
    """
    result = self.gca.run_python_snippet(code, timeout=10.0)
    combined_output = (result.stdout + " " + result.stderr).lower()

    success_indicators = expected_behavior.get("success_indicators", [])
    failure_indicators = expected_behavior.get("failure_indicators", [])

    success_matches = [
        ind for ind in success_indicators if ind.lower() in combined_output
    ]
    failure_matches = [
        ind for ind in failure_indicators if ind.lower() in combined_output
    ]

    passed = result.is_success and len(failure_matches) == 0
    if success_indicators:
        passed = passed and len(success_matches) > 0

    confidence = 0.5
    if passed and success_matches:
        confidence = min(0.5 + 0.1 * len(success_matches), 0.95)
    elif failure_matches:
        confidence = min(0.5 + 0.15 * len(failure_matches), 0.95)

    return NeuronSignal(
        neuron_name="BEHAVIOR",
        gate_type=GateType.SOFT,
        passed=passed,
        confidence=confidence,
        message=(
            f"Behavior check {'PASSED' if passed else 'FAILED'}. "
            f"Exit code: {result.exit_code}. "
            f"Success matches: {len(success_matches)}/{len(success_indicators)}. "
            f"Failure matches: {len(failure_matches)}."
        ),
        evidence={
            "exit_code": result.exit_code,
            "stdout_preview": result.stdout[:500] if result.stdout else "",
            "stderr_preview": result.stderr[:500] if result.stderr else "",
            "success_matches": success_matches,
            "failure_matches": failure_matches,
            "duration": result.duration_seconds,
        },
        suggestion=(
            f"Code failed behavior check. Failure indicators found: {failure_matches}"
            if not passed else ""
        ),
    )


def neuron_gca_execute(self, test_command: str) -> NeuronSignal:
    """
    Signal: Does this test command pass with Exit Code 0?
    Mechanism: Delegates to existing GroundedCompilerArbitrage.

    HARD GATE — Exit Code != 0 is empirical proof of failure.
    """
    result = self.gca.run_command(test_command)

    return NeuronSignal(
        neuron_name="GCA",
        gate_type=GateType.HARD,
        passed=result.is_success,
        confidence=1.0,
        message=(
            f"GCA {'PASSED' if result.is_success else 'FAILED'}: "
            f"Exit Code {result.exit_code} in {result.duration_seconds}s"
        ),
        evidence={
            "command": test_command,
            "exit_code": result.exit_code,
            "stdout_preview": result.stdout[:500] if result.stdout else "",
            "stderr_preview": result.stderr[:500] if result.stderr else "",
            "duration": result.duration_seconds,
        },
        suggestion=(
            f"Test failed. Stderr: {result.stderr[:200]}" if not result.is_success else ""
        ),
    )

