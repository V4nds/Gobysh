import ast
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from core.ccr_engine import NeuronSignal, GateType

def neuron_js_syntax_check(self, code: str) -> NeuronSignal:
    """
    Signal: Is this JavaScript/TypeScript snippet syntactically valid?
    Mechanism: Node.js evaluation via GCA --check syntax mode.

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

    is_esm = bool(re.search(r'\b(import|export)\b', code))
    suffix = ".mjs" if is_esm else ".js"

    with tempfile.NamedTemporaryFile(suffix=suffix, mode="w", delete=False, encoding="utf-8") as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name

    try:
        node_bin = getattr(self.gca, "_node_path", "node")
        res = self.gca.run_command(f'"{node_bin}" --check "{temp_path}"', timeout=5.0)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

    if res.is_success:
        return NeuronSignal(
            neuron_name="JS_SYNTAX",
            gate_type=GateType.HARD,
            passed=True,
            confidence=1.0,
            message="JavaScript syntax is valid.",
            evidence={"node_available": True, "valid": True, "esm": is_esm},
            suggestion="",
        )
    else:
        err_msg = res.stderr.strip() or res.stdout.strip()
        return NeuronSignal(
            neuron_name="JS_SYNTAX",
            gate_type=GateType.HARD,
            passed=False,
            confidence=1.0,
            message=f"JS SyntaxError: {err_msg}",
            evidence={"node_available": True, "error": err_msg, "esm": is_esm},
            suggestion="Fix JavaScript syntax error before delivery.",
        )


def neuron_ts_syntax_check(self, code: str) -> NeuronSignal:
    """
    Signal: Does this TypeScript candidate code conform to valid TS/JS syntax?
    Mechanism: In-memory compiler diagnostics via ts.transpileModule or AST type-stripping.
    """
    if not self.gca.is_node_available():
        return NeuronSignal(
            neuron_name="TS_SYNTAX",
            gate_type=GateType.SOFT,
            passed=True,
            confidence=0.5,
            message="Node.js is not available in PATH — TS syntax check skipped.",
            evidence={"node_available": False},
            suggestion="Install Node.js to enable TS syntax checking.",
        )

    node_eval_script = f"""
try {{
    const ts = require('typescript');
    const res = ts.transpileModule({json.dumps(code)}, {{
        compilerOptions: {{ jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ESNext }},
        reportDiagnostics: true
    }});
    if (res.diagnostics && res.diagnostics.length > 0) {{
        const msg = res.diagnostics.map(d => typeof d.messageText === 'string' ? d.messageText : d.messageText.messageText).join('; ');
        console.error(msg);
        process.exit(1);
    }}
    process.exit(0);
}} catch(e) {{
    if (e.code === 'MODULE_NOT_FOUND') {{
        process.exit(42);
    }}
    console.error(e.message);
    process.exit(1);
}}
"""
    node_bin = getattr(self.gca, "_node_path", "node")
    res = self.gca.run_command([node_bin, "-e", node_eval_script], timeout=5.0)

    if res.exit_code == 0:
        return NeuronSignal(
            neuron_name="TS_SYNTAX",
            gate_type=GateType.HARD,
            passed=True,
            confidence=1.0,
            message="TypeScript syntax verified via compiler transpileModule.",
            evidence={"transpile_verified": True},
            suggestion="",
        )
    elif res.exit_code != 42:
        err = res.stderr.strip() or res.stdout.strip()
        return NeuronSignal(
            neuron_name="TS_SYNTAX",
            gate_type=GateType.HARD,
            passed=False,
            confidence=1.0,
            message=f"TS SyntaxError: {err}",
            evidence={"error": err},
            suggestion="Fix TypeScript syntax error before delivery.",
        )

    # Fallback if 'typescript' is not in node_modules:
    clean_code = re.sub(r'import\s+type\s+[^;]+;', '', code)
    clean_code = re.sub(r'interface\s+\w+\s*\{[^}]*\}', '', clean_code)
    clean_code = re.sub(r'type\s+\w+\s*=[^;]+;', '', clean_code)
    clean_code = re.sub(r'<[^>]+>', ' null ', clean_code)

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
