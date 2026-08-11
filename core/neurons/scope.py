import ast
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from core.ccr_engine import NeuronSignal, GateType

def neuron_scope_check(self, code: str) -> NeuronSignal:
    """
    Signal: Are all names used in this code defined within scope?
    Mechanism: AST analysis — extract Load vs Store name nodes.

    HARD GATE — undefined variables cause NameError at runtime.

    Known limitations (documented honestly):
    - Cannot detect variables from outer scope (closure, global, builtins)
    - Cannot check attribute access (x.method())
    - Cannot verify pip package availability
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return NeuronSignal(
            neuron_name="SCOPE",
            gate_type=GateType.HARD,
            passed=False,
            confidence=1.0,
            message="Cannot analyze scope — code has syntax errors.",
            evidence={"reason": "syntax_error"},
            suggestion="Fix syntax errors first (use neuron_syntax_check).",
        )

    # Collect defined names (assigned, imported, function/class defs, params)
    defined: Set[str] = set()
    used: Set[str] = set()
    used_lines: Dict[str, int] = {}

    # Python builtins that are always available
    builtins_set = {
        "print", "len", "range", "int", "str", "float", "bool", "list",
        "dict", "set", "tuple", "type", "isinstance", "issubclass",
        "hasattr", "getattr", "setattr", "delattr", "callable",
        "iter", "next", "enumerate", "zip", "map", "filter", "sorted",
        "reversed", "min", "max", "sum", "abs", "round", "pow",
        "any", "all", "id", "hash", "repr", "format",
        "open", "input", "super", "property", "classmethod", "staticmethod",
        "True", "False", "None", "Exception", "BaseException", "ValueError", "TypeError",
        "KeyError", "IndexError", "AttributeError", "ImportError", "ModuleNotFoundError",
        "RuntimeError", "StopIteration", "OSError", "IOError", "PermissionError",
        "FileNotFoundError", "NotImplementedError", "ZeroDivisionError",
        "AssertionError", "NameError", "SyntaxError", "SystemExit", "KeyboardInterrupt",
        "OverflowError", "MemoryError", "RecursionError", "UnicodeEncodeError", "UnicodeDecodeError",
        "SyntaxWarning", "DeprecationWarning", "UserWarning", "Warning",
        "object", "bytes", "bytearray", "memoryview", "complex",
        "frozenset", "vars", "dir", "globals", "locals", "exec", "eval",
        "compile", "breakpoint", "exit", "quit",
        "__name__", "__file__", "__doc__", "__all__",
    }
    defined.update(builtins_set)

    def extract_target_names(t_node):
        if isinstance(t_node, ast.Name):
            defined.add(t_node.id)
        elif isinstance(t_node, (ast.Tuple, ast.List)):
            for elt in t_node.elts:
                extract_target_names(elt)
        elif isinstance(t_node, ast.Starred):
            extract_target_names(t_node.value)

    for node in ast.walk(tree):
        # Definitions: assignments
        if isinstance(node, ast.Assign):
            for target in node.targets:
                extract_target_names(target)
        # Definitions: augmented assignments (x += 1)
        elif isinstance(node, ast.AugAssign):
            extract_target_names(node.target)
        # Definitions: annotated assignments (x: int = 5)
        elif isinstance(node, ast.AnnAssign):
            extract_target_names(node.target)
        # Definitions: function defs
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined.add(node.name)
            posargs = getattr(node.args, "posonlyargs", [])
            kwargs = getattr(node.args, "kwonlyargs", [])
            for arg in node.args.args + posargs + kwargs:
                defined.add(arg.arg)
            if node.args.vararg:
                defined.add(node.args.vararg.arg)
            if node.args.kwarg:
                defined.add(node.args.kwarg.arg)
        # Definitions: class defs
        elif isinstance(node, ast.ClassDef):
            defined.add(node.name)
        # Definitions: imports
        elif isinstance(node, ast.Import):
            for alias in node.names:
                defined.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                defined.add(alias.asname or alias.name)
        # Definitions: for loop targets
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            extract_target_names(node.target)
        # Definitions: with statement
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars:
                    extract_target_names(item.optional_vars)
        # Definitions: comprehension variables
        elif isinstance(node, ast.comprehension):
            extract_target_names(node.target)
        # Definitions: except handler
        elif isinstance(node, ast.ExceptHandler):
            if node.name:
                defined.add(node.name)
        # Definitions: lambda function parameters
        elif isinstance(node, ast.Lambda):
            posargs = getattr(node.args, "posonlyargs", [])
            kwargs = getattr(node.args, "kwonlyargs", [])
            for arg in node.args.args + posargs + kwargs:
                defined.add(arg.arg)
            if node.args.vararg:
                defined.add(node.args.vararg.arg)
            if node.args.kwarg:
                defined.add(node.args.kwarg.arg)
        # Definitions: named expression (walrus operator)
        elif isinstance(node, ast.NamedExpr):
            extract_target_names(node.target)

        # Usages: name references in Load context
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
            if node.id not in used_lines:
                used_lines[node.id] = getattr(node, "lineno", 0)

    undefined = used - defined
    if not undefined:
        return NeuronSignal(
            neuron_name="SCOPE",
            gate_type=GateType.HARD,
            passed=True,
            confidence=0.85,  # Not 1.0 — cannot check outer scopes
            message="All referenced names are defined within visible scope.",
            evidence={"defined_count": len(defined - builtins_set), "used_count": len(used)},
            suggestion="",
        )

    undefined_with_lines = {
        name: used_lines.get(name, 0) for name in sorted(undefined)
    }
    detail = ", ".join(
        f"{name} (line {line})" if line else name
        for name, line in undefined_with_lines.items()
    )

    return NeuronSignal(
        neuron_name="SCOPE",
        gate_type=GateType.HARD,
        passed=False,
        confidence=0.75,  # Could be false positive (outer scope variable)
        message=f"Potentially undefined names: {detail}",
        evidence={
            "undefined_names": sorted(undefined),
            "undefined_lines": undefined_with_lines,
            "first_line": min((l for l in undefined_with_lines.values() if l), default=0),
        },
        suggestion=f"Verify these names exist: {', '.join(sorted(undefined))}. "
                   f"They may be from outer scope (closure/global) — in that case, safe to proceed.",
    )

