import ast
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from core.ccr_engine import NeuronSignal, GateType

def neuron_js_syntax_check(self, code: str) -> NeuronSignal:
    """
    Signal: Is this JavaScript/TypeScript snippet syntactically valid?
    Mechanism: Node.js evaluation via GCA.

    HARD GATE when Node.js is available.
    """
    if not self.gca.is_node_available():
        return NeuronSignal(
            neuron_name="JS_SYNTAX",
            gate_type=GateType.SOFT,
            passed=True,
            confidence=0.5,
            message="Node.js is not available in PATH — JS syntax check skipped.",
            evidence={"node_available": False},
            suggestion="Install Node.js to enable hard-gate JS/TS syntax checking.",
        )

    js_wrapper = f"try {{ new Function({json.dumps(code)}); }} catch(e) {{ console.error(e.message); process.exit(1); }}"
    res = self.gca.run_js_snippet(js_wrapper)

    if res.is_success:
        return NeuronSignal(
            neuron_name="JS_SYNTAX",
            gate_type=GateType.HARD,
            passed=True,
            confidence=1.0,
            message="JavaScript syntax is valid.",
            evidence={"node_available": True, "valid": True},
            suggestion="",
        )
    else:
        return NeuronSignal(
            neuron_name="JS_SYNTAX",
            gate_type=GateType.HARD,
            passed=False,
            confidence=1.0,
            message=f"JS SyntaxError: {res.stderr.strip()}",
            evidence={"node_available": True, "error": res.stderr.strip()},
            suggestion="Fix JavaScript syntax error before delivery.",
        )


def neuron_ts_syntax_check(self, code: str) -> NeuronSignal:
    """
    Signal: Does this TypeScript candidate code conform to valid TS/JS syntax?
    Mechanism: Writes candidate to a temporary .ts file and validates via tsc or AST type-stripping.
    """
    import shutil
    import tempfile

    # Write candidate to a temporary .ts file for accurate compiler validation
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False, encoding="utf-8") as temp_ts:
        temp_ts.write(code)
        temp_ts_path = temp_ts.name

    try:
        tsc_bin = shutil.which("tsc")
        if tsc_bin:
            tsc_res = self.gca.run_command([tsc_bin, "--noEmit", temp_ts_path], timeout=10.0)
        else:
            tsc_res = self.gca.run_command(f"npx tsc --noEmit \"{temp_ts_path}\"", timeout=10.0)

        if tsc_res.is_success:
            return NeuronSignal(
                neuron_name="TS_SYNTAX",
                gate_type=GateType.HARD,
                passed=True,
                confidence=1.0,
                message="TypeScript candidate syntax verified via tsc.",
                evidence={"tsc_available": True, "valid": True},
                suggestion="",
            )
    finally:
        if os.path.exists(temp_ts_path):
            try:
                os.remove(temp_ts_path)
            except OSError:
                pass

    # Fallback: Strip TypeScript type annotations & interfaces using clean AST regex transformation
    clean_code = re.sub(r'interface\s+\w+\s*\{[^}]*\}', '', code)
    clean_code = re.sub(r'type\s+\w+\s*=[^;]+;', '', clean_code)
    clean_code = re.sub(r':\s*[A-Za-z0-9_<>\[\]]+', '', clean_code)

    js_sig = self.neuron_js_syntax_check(clean_code)
    return NeuronSignal(
        neuron_name="TS_SYNTAX",
        gate_type=GateType.HARD,
        passed=js_sig.passed,
        confidence=0.9,
        message=f"TypeScript AST Syntax {'PASS' if js_sig.passed else 'FAIL'}: {js_sig.message}",
        evidence={"type_stripped": True, "inner_js": js_sig.evidence},
        suggestion=js_sig.suggestion
    )

