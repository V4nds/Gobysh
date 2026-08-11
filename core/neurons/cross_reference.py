import ast
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from core.ccr_engine import NeuronSignal, GateType

def neuron_cross_reference(
    self, code: str, project_root: str
) -> NeuronSignal:
    """
    Signal: Do imported modules/functions actually exist in the project?
    Mechanism: Dynamic scan of project files + AST import extraction.

    HARD GATE — importing non-existent modules causes ImportError.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return NeuronSignal(
            neuron_name="CROSS_REF",
            gate_type=GateType.HARD,
            passed=False,
            confidence=1.0,
            message="Cannot cross-reference — code has syntax errors.",
            evidence={"reason": "syntax_error"},
            suggestion="Fix syntax errors first.",
        )

    # Extract local imports (skip stdlib and pip packages)
    local_imports: List[Dict[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            # Heuristic: local imports often start with '.' or known project prefixes
            if node.level > 0:  # Relative import
                local_imports.append({
                    "module": "." * node.level + (node.module or ""),
                    "names": [a.name for a in node.names],
                    "type": "relative",
                })
            elif node.module.startswith("core"):  # Known project prefix
                local_imports.append({
                    "module": node.module,
                    "names": [a.name for a in node.names],
                    "type": "project",
                })

    if not local_imports:
        return NeuronSignal(
            neuron_name="CROSS_REF",
            gate_type=GateType.HARD,
            passed=True,
            confidence=1.0,
            message="No local project imports to validate.",
            evidence={"imports_checked": 0},
            suggestion="",
        )

    # Scan project for existing modules
    existing_modules = self._scan_project(project_root)
    missing: List[str] = []

    for imp in local_imports:
        module_path = imp["module"].replace(".", os.sep)
        if imp["type"] == "relative":
            module_path = module_path.lstrip(os.sep)

        # Check if module file or package directory exists
        found = False
        for ext in [".py", ""]:
            candidate = os.path.join(project_root, module_path + ext)
            if os.path.exists(candidate):
                found = True
                break
            # Check as package (directory with __init__.py)
            pkg_init = os.path.join(project_root, module_path, "__init__.py")
            if os.path.exists(pkg_init):
                found = True
                break

        if not found and imp["module"] in existing_modules:
            found = True

        if not found:
            missing.append(imp["module"])

    if missing:
        return NeuronSignal(
            neuron_name="CROSS_REF",
            gate_type=GateType.HARD,
            passed=False,
            confidence=0.9,
            message=f"Missing project modules: {', '.join(missing)}",
            evidence={"missing_modules": missing, "checked": len(local_imports)},
            suggestion=f"Verify these modules exist: {', '.join(missing)}",
        )

    return NeuronSignal(
        neuron_name="CROSS_REF",
        gate_type=GateType.HARD,
        passed=True,
        confidence=0.95,
        message=f"All {len(local_imports)} local imports verified against project.",
        evidence={"imports_checked": len(local_imports), "project_modules": list(existing_modules.keys())},
        suggestion="",
    )


def neuron_reference_similarity(
    self, output: str, reference: str
) -> NeuronSignal:
    """
    Signal: How structurally similar is the output to a reference?
    Mechanism: Token/keyword overlap and structural comparison.

    SOFT SIGNAL — similarity is subjective, AI interprets the data.

    Returns RAW DATA (shared keywords, unique elements, overlap ratio)
    for AI to judge — does NOT make pass/fail decision on its own.
    """
    def tokenize(text: str) -> Set[str]:
        tokens = re.findall(r'\b\w{3,}\b', text.lower())
        return set(tokens)

    output_tokens = tokenize(output)
    reference_tokens = tokenize(reference)

    shared = output_tokens & reference_tokens
    output_unique = output_tokens - reference_tokens
    reference_unique = reference_tokens - output_tokens

    total_unique = len(output_tokens | reference_tokens)
    overlap_ratio = len(shared) / total_unique if total_unique > 0 else 0.0

    return NeuronSignal(
        neuron_name="REFERENCE",
        gate_type=GateType.SOFT,
        passed=True,  # Always "passes" — AI decides if similarity is acceptable
        confidence=overlap_ratio,
        message=f"Structural overlap: {overlap_ratio:.1%}. "
                f"Shared: {len(shared)}, Output-unique: {len(output_unique)}, "
                f"Reference-unique: {len(reference_unique)}.",
        evidence={
            "shared_keywords": sorted(shared)[:30],
            "output_unique": sorted(output_unique)[:20],
            "reference_unique": sorted(reference_unique)[:20],
            "structural_overlap": round(overlap_ratio, 3),
            "missing_from_output": sorted(reference_unique)[:20],
        },
        suggestion="",
    )


def _scan_project(self, root: str) -> Dict[str, Dict[str, Any]]:
    """
    Dynamically scan project directory for Python modules.
    Returns a map of module names to their metadata.
    """
    modules: Dict[str, Dict[str, Any]] = {}

    if not os.path.isdir(root):
        return modules

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden dirs and common non-project dirs
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d not in ("__pycache__", "node_modules", ".git", "venv", "env")
        ]

        for filename in filenames:
            if filename.endswith(".py"):
                filepath = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(filepath, root)
                # Convert file path to module notation (Python 3.8+ compatible)
                module_name = rel_path.replace(os.sep, ".")
                if module_name.endswith(".py"):
                    module_name = module_name[:-3]
                if module_name.endswith(".__init__"):
                    module_name = module_name[:-9]

                modules[module_name] = {
                    "path": rel_path,
                    "abs_path": filepath,
                }

    return modules

