"""
Cognitive Control Room (CCR) for Goby Framework.
Internal cognitive validation engine — provides neuron-based signals
for AI (the brain) to validate its own outputs before delivery.

Architecture: AI = Brain (controller), Neurons = Signal providers (tools).
Neurons measure and report. AI decides and acts.
"""

import ast
import enum
import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .gca_runner import GroundedCompilerArbitrage
from .state_memory import StateMemoryManager


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GateType(enum.Enum):
    """Determines whether a neuron signal can be overridden by AI."""
    HARD = "HARD"   # Programmatic block — AI CANNOT override
    SOFT = "SOFT"   # Advisory signal — AI decides


class TriageLevel(enum.Enum):
    """Controls which neurons are activated for a given task."""
    SKIP = "SKIP"           # No review: greetings, acknowledgments
    LIGHT = "LIGHT"         # Soft signals only: text explanations
    STANDARD = "STANDARD"   # Hard gates + relevant soft: code modifications
    FULL = "FULL"           # All neurons: new code, architecture, design


class ContextTier(enum.Enum):
    """Classifies how complete the available context is."""
    CRITICAL = "CRITICAL"   # Insufficient — must ask before proceeding
    MINIMUM = "MINIMUM"     # Enough to start, may be suboptimal
    IDEAL = "IDEAL"         # Complete information available


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class NeuronSignal:
    """Signal returned by a neuron to the AI (brain)."""
    neuron_name: str
    gate_type: GateType
    passed: bool
    confidence: float
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    suggestion: str = ""


@dataclass
class ThoughtRecord:
    """Record of one thought and all neuron signals it received."""
    thought_id: str
    content: str
    content_type: str           # "CODE", "TEXT", "DESIGN"
    neuron_signals: List[NeuronSignal] = field(default_factory=list)
    ai_decision: str = ""       # "APPROVED", "REJECTED", "REFINED"
    refinement_count: int = 0
    timestamp: str = ""


@dataclass
class ContextAssessment:
    """Result of context sufficiency assessment."""
    tier: ContextTier
    is_sufficient: bool
    missing_info: List[str] = field(default_factory=list)
    suggested_questions: List[str] = field(default_factory=list)
    context_score: float = 0.0


# ---------------------------------------------------------------------------
# Cognitive Control Room
# ---------------------------------------------------------------------------

class CognitiveControlRoom:
    """
    Neuron toolkit for AI's internal cognitive control.

    This class is NOT an autonomous decision maker. It provides
    measurement signals (neurons) that the AI (brain) uses to validate
    its own thoughts before outputting them.

    Neurons measure. AI decides.
    """

    MAX_THOUGHT_HISTORY = 20
    MAX_REFINEMENTS = 2  # Harmonized with AGENTS.md (2 attempts before LDE)

    # Common filler phrases (multi-language)
    FILLER_PHRASES = [
        "pada dasarnya", "secara umum", "di sisi lain", "dengan kata lain",
        "sebagaimana diketahui", "perlu diketahui bahwa", "tentu saja",
        "basically", "generally speaking", "in other words", "as we know",
        "it should be noted", "needless to say", "of course",
        "as a matter of fact", "at the end of the day", "all things considered",
    ]

    def __init__(
        self,
        state_memory: Optional[StateMemoryManager] = None,
        gca: Optional[GroundedCompilerArbitrage] = None,
        max_thought_history: int = 20,
        max_refinements: int = 2,
    ):
        self.state_memory = state_memory
        self.gca = gca or GroundedCompilerArbitrage(default_timeout=15.0)
        self.MAX_THOUGHT_HISTORY = max_thought_history
        self.MAX_REFINEMENTS = max_refinements

    # -----------------------------------------------------------------------
    # Triage — AI uses this to decide review depth
    # -----------------------------------------------------------------------

    def triage(self, content_type: str, complexity: str) -> TriageLevel:
        """
        Classify the required review level for a given task.

        Args:
            content_type: "ACKNOWLEDGMENT", "TEXT", "CODE", "DESIGN"
            complexity: "TRIVIAL", "LOW", "MODERATE", "HIGH"

        Returns:
            TriageLevel indicating which neurons should be activated.
        """
        content_type = content_type.upper()
        complexity = complexity.upper()

        if content_type == "ACKNOWLEDGMENT" or complexity == "TRIVIAL":
            return TriageLevel.SKIP

        if content_type == "TEXT" and complexity in ("LOW", "MODERATE"):
            return TriageLevel.LIGHT

        if content_type == "CODE" and complexity in ("LOW", "MODERATE"):
            return TriageLevel.STANDARD

        # CODE+HIGH, DESIGN, or anything else
        return TriageLevel.FULL

    # -----------------------------------------------------------------------
    # Context Gate — assess whether AI has enough info to proceed
    # -----------------------------------------------------------------------

    def assess_context(
        self, user_input: str, available_context: Optional[Dict[str, Any]] = None
    ) -> ContextAssessment:
        """
        Evaluate whether the provided context is sufficient for processing.

        Returns a ContextAssessment with tier (CRITICAL/MINIMUM/IDEAL),
        missing info list, and suggested questions for the user.
        """
        context = available_context or {}
        missing: List[str] = []
        questions: List[str] = []
        score = 0.0

        input_stripped = user_input.strip()

        # --- Check 1: Is there any substantive input at all? ---
        if len(input_stripped) < 5:
            missing.append("substantive_input")
            questions.append("Bisa jelaskan lebih detail apa yang ingin kamu lakukan?")
        else:
            score += 0.25

        # --- Check 2: Does the input contain error context? ---
        has_error_keywords = any(
            kw in input_stripped.lower()
            for kw in ["error", "bug", "gagal", "failed", "traceback", "exception", "crash"]
        )
        has_code = bool(context.get("code")) or bool(context.get("error_log"))

        if has_error_keywords and not has_code:
            missing.append("error_code_or_log")
            questions.append("Bisa kirimkan kode atau error log yang terkait?")
        elif has_error_keywords and has_code:
            score += 0.25

        # --- Check 3: Is there a description of what's being worked on? ---
        has_project_context = bool(context.get("project_description")) or bool(
            context.get("file_context")
        )
        if not has_project_context:
            if has_error_keywords:
                missing.append("project_description")
                questions.append("Apa yang sedang kamu kerjakan saat error ini muncul?")
            score += 0.1
        else:
            score += 0.25

        # --- Check 4: For design tasks, is there a reference? ---
        is_design_task = any(
            kw in input_stripped.lower()
            for kw in ["desain", "design", "ui", "ux", "layout", "tampilan", "warna", "style"]
        )
        has_reference = bool(context.get("design_reference"))
        if is_design_task and not has_reference:
            missing.append("design_reference")
            questions.append("Apakah kamu punya referensi desain atau contoh yang diinginkan?")
        elif is_design_task and has_reference:
            score += 0.25

        # If not a design task, give the remaining score
        if not is_design_task:
            score += 0.25

        score = min(score, 1.0)

        # --- Determine tier ---
        if "substantive_input" in missing:
            tier = ContextTier.CRITICAL
        elif len(missing) >= 2:
            tier = ContextTier.CRITICAL
        elif len(missing) == 1:
            tier = ContextTier.MINIMUM
        else:
            tier = ContextTier.IDEAL

        return ContextAssessment(
            tier=tier,
            is_sufficient=(tier != ContextTier.CRITICAL),
            missing_info=missing,
            suggested_questions=questions,
            context_score=round(score, 2),
        )

    # -----------------------------------------------------------------------
    # Neuron 1: Syntax Check (HARD GATE)
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Neuron 1b: JavaScript/TypeScript Syntax Check (HARD GATE)
    # -----------------------------------------------------------------------

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


    # -----------------------------------------------------------------------
    # Neuron 2: Scope Integrity Check (HARD GATE)
    # -----------------------------------------------------------------------

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

        # Python builtins that are always available
        builtins_set = {
            "print", "len", "range", "int", "str", "float", "bool", "list",
            "dict", "set", "tuple", "type", "isinstance", "issubclass",
            "hasattr", "getattr", "setattr", "delattr", "callable",
            "iter", "next", "enumerate", "zip", "map", "filter", "sorted",
            "reversed", "min", "max", "sum", "abs", "round", "pow",
            "any", "all", "id", "hash", "repr", "format",
            "open", "input", "super", "property", "classmethod", "staticmethod",
            "True", "False", "None", "Exception", "ValueError", "TypeError",
            "KeyError", "IndexError", "AttributeError", "ImportError",
            "RuntimeError", "StopIteration", "OSError", "IOError",
            "FileNotFoundError", "NotImplementedError", "ZeroDivisionError",
            "AssertionError", "NameError", "SyntaxError", "SystemExit",
            "object", "bytes", "bytearray", "memoryview", "complex",
            "frozenset", "vars", "dir", "globals", "locals", "exec", "eval",
            "compile", "breakpoint", "exit", "quit",
            "__name__", "__file__", "__doc__", "__all__",
        }
        defined.update(builtins_set)

        for node in ast.walk(tree):
            # Definitions: assignments
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined.add(target.id)
                    elif isinstance(target, ast.Tuple):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name):
                                defined.add(elt.id)
            # Definitions: augmented assignments (x += 1)
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Name):
                    defined.add(node.target.id)
            # Definitions: annotated assignments (x: int = 5)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    defined.add(node.target.id)
            # Definitions: function defs
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined.add(node.name)
                for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
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
            elif isinstance(node, ast.For):
                if isinstance(node.target, ast.Name):
                    defined.add(node.target.id)
                elif isinstance(node.target, ast.Tuple):
                    for elt in node.target.elts:
                        if isinstance(elt, ast.Name):
                            defined.add(elt.id)
            # Definitions: with statement
            elif isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        defined.add(item.optional_vars.id)
            # Definitions: comprehension variables
            elif isinstance(node, ast.comprehension):
                if isinstance(node.target, ast.Name):
                    defined.add(node.target.id)
            # Definitions: except handler
            elif isinstance(node, ast.ExceptHandler):
                if node.name:
                    defined.add(node.name)
            # Definitions: named expression (walrus operator)
            elif isinstance(node, ast.NamedExpr):
                if isinstance(node.target, ast.Name):
                    defined.add(node.target.id)

            # Usages: name references in Load context
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)

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

        return NeuronSignal(
            neuron_name="SCOPE",
            gate_type=GateType.HARD,
            passed=False,
            confidence=0.75,  # Could be false positive (outer scope variable)
            message=f"Potentially undefined names: {', '.join(sorted(undefined))}",
            evidence={"undefined_names": sorted(undefined)},
            suggestion=f"Verify these names exist: {', '.join(sorted(undefined))}. "
                       f"They may be from outer scope (closure/global) — in that case, safe to proceed.",
        )

    # -----------------------------------------------------------------------
    # Neuron 3: Cross-Reference (HARD GATE)
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Neuron 4: Behavior Check (SOFT SIGNAL)
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Neuron 5: Reference Similarity (SOFT SIGNAL)
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Neuron 6: GCA Execute (HARD GATE)
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Neuron 7: Information Density (SOFT SIGNAL)
    # -----------------------------------------------------------------------

    def neuron_info_density(self, text: str) -> NeuronSignal:
        """
        Signal: Raw text statistics for AI to judge substance vs filler.
        Mechanism: Word counting, lexical diversity, filler phrase detection.

        SOFT SIGNAL — returns raw metrics, AI interprets.
        """
        words = re.findall(r'\b\w+\b', text.lower())
        total_words = len(words)

        if total_words == 0:
            return NeuronSignal(
                neuron_name="DENSITY",
                gate_type=GateType.SOFT,
                passed=False,
                confidence=1.0,
                message="Text is empty.",
                evidence={"total_words": 0},
                suggestion="Provide substantive content.",
            )

        unique_words = set(words)
        lexical_diversity = len(unique_words) / total_words

        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        avg_sentence_length = total_words / max(len(sentences), 1)

        # Count filler phrase occurrences
        text_lower = text.lower()
        filler_counts: Dict[str, int] = {}
        total_filler_hits = 0
        for filler in self.FILLER_PHRASES:
            count = text_lower.count(filler)
            if count > 0:
                filler_counts[filler] = count
                total_filler_hits += count

        filler_ratio = total_filler_hits / max(len(sentences), 1)

        return NeuronSignal(
            neuron_name="DENSITY",
            gate_type=GateType.SOFT,
            passed=True,  # Always "passes" — AI decides from raw data
            confidence=lexical_diversity,
            message=(
                f"Words: {total_words}, Unique: {len(unique_words)}, "
                f"Diversity: {lexical_diversity:.2%}, "
                f"Avg sentence: {avg_sentence_length:.1f} words, "
                f"Filler hits: {total_filler_hits}"
            ),
            evidence={
                "total_words": total_words,
                "unique_words": len(unique_words),
                "lexical_diversity": round(lexical_diversity, 3),
                "avg_sentence_length": round(avg_sentence_length, 1),
                "sentence_count": len(sentences),
                "filler_phrase_counts": filler_counts,
                "total_filler_hits": total_filler_hits,
                "filler_ratio_per_sentence": round(filler_ratio, 2),
            },
            suggestion="",
        )

    # -----------------------------------------------------------------------
    # Neuron 8: Consistency Check (SOFT SIGNAL)
    # -----------------------------------------------------------------------

    def neuron_consistency(self, text: str) -> NeuronSignal:
        """
        Signal: Extract claims, detect numeric conflicts and negation pairs.
        Mechanism: Regex-based claim and number extraction.

        SOFT SIGNAL — returns extracted data, AI judges contradictions.
        """
        claims: List[Dict[str, Any]] = []
        numeric_conflicts: List[Dict[str, Any]] = []
        negation_pairs: List[Dict[str, Any]] = []

        lines = text.split("\n")

        # --- Extract numeric claims ---
        number_pattern = re.compile(
            r'(\b\w[\w\s]{2,30})\b(?:adalah|=|:|\bsebesar\b|\bof\b|\bis\b)\s*(\d+[\d.,]*\s*\w*)',
            re.IGNORECASE,
        )
        numeric_claims: List[Tuple[str, str, int]] = []
        for line_no, line in enumerate(lines, 1):
            for match in number_pattern.finditer(line):
                context = match.group(1).strip().lower()
                value = match.group(2).strip()
                claims.append({"text": match.group(0).strip(), "line": line_no, "type": "numeric"})
                numeric_claims.append((context, value, line_no))

        # Check for conflicting numbers with same context
        seen_contexts: Dict[str, List[Tuple[str, int]]] = {}
        for context, value, line_no in numeric_claims:
            key = re.sub(r'\s+', ' ', context)[:30]
            if key not in seen_contexts:
                seen_contexts[key] = []
            seen_contexts[key].append((value, line_no))

        for context, values in seen_contexts.items():
            if len(values) >= 2:
                unique_vals = set(v for v, _ in values)
                if len(unique_vals) > 1:
                    numeric_conflicts.append({
                        "context": context,
                        "values": [{"value": v, "line": ln} for v, ln in values],
                    })

        # --- Extract negation pairs ---
        negation_patterns = [
            (r'(?:mendukung|support)\s+(.+)', r'(?:tidak|not)\s+(?:mendukung|support|kompatibel|compatible)\s+(.+)'),
            (r'(?:menggunakan|using|use)\s+(.+)', r'(?:tidak|not)\s+(?:menggunakan|using|use)\s+(.+)'),
        ]

        positive_claims: List[Tuple[str, int]] = []
        negative_claims: List[Tuple[str, int]] = []

        for line_no, line in enumerate(lines, 1):
            for pos_pattern, neg_pattern in negation_patterns:
                pos_match = re.search(pos_pattern, line, re.IGNORECASE)
                neg_match = re.search(neg_pattern, line, re.IGNORECASE)
                if pos_match:
                    positive_claims.append((pos_match.group(0), line_no))
                if neg_match:
                    negative_claims.append((neg_match.group(0), line_no))

        for pos_text, pos_line in positive_claims:
            for neg_text, neg_line in negative_claims:
                if pos_line != neg_line:
                    negation_pairs.append({
                        "positive": {"text": pos_text, "line": pos_line},
                        "negative": {"text": neg_text, "line": neg_line},
                    })

        has_issues = len(numeric_conflicts) > 0 or len(negation_pairs) > 0

        return NeuronSignal(
            neuron_name="CONSISTENCY",
            gate_type=GateType.SOFT,
            passed=True,  # Always "passes" — AI judges from data
            confidence=0.6 if has_issues else 0.9,
            message=(
                f"Claims extracted: {len(claims)}. "
                f"Numeric conflicts: {len(numeric_conflicts)}. "
                f"Negation pairs: {len(negation_pairs)}."
            ),
            evidence={
                "claims": claims[:20],
                "numeric_conflicts": numeric_conflicts,
                "negation_pairs": negation_pairs,
                "total_lines_analyzed": len(lines),
            },
            suggestion=(
                f"Found {len(numeric_conflicts)} numeric conflict(s) and "
                f"{len(negation_pairs)} potential negation pair(s). Review carefully."
                if has_issues else ""
            ),
        )

    # -----------------------------------------------------------------------
    # Signal Evaluator — Hard Gate blocker
    # -----------------------------------------------------------------------

    def evaluate_signals(self, signals: List[NeuronSignal]) -> Dict[str, Any]:
        """
        Evaluate all neuron signals. Hard Gate failures BLOCK output
        programmatically — AI cannot override.

        Returns:
            {
                "blocked": bool,
                "hard_failures": [...],
                "soft_warnings": [...],
                "ai_can_override": bool,
                "summary": str
            }
        """
        hard_failures = [s for s in signals if s.gate_type == GateType.HARD and not s.passed]
        soft_warnings = [s for s in signals if s.gate_type == GateType.SOFT and not s.passed]

        if hard_failures:
            return {
                "blocked": True,
                "hard_failures": [
                    {"neuron": s.neuron_name, "message": s.message, "suggestion": s.suggestion}
                    for s in hard_failures
                ],
                "soft_warnings": [
                    {"neuron": s.neuron_name, "message": s.message}
                    for s in soft_warnings
                ],
                "ai_can_override": False,
                "summary": f"BLOCKED by {len(hard_failures)} hard gate(s): "
                           f"{', '.join(s.neuron_name for s in hard_failures)}",
            }

        return {
            "blocked": False,
            "hard_failures": [],
            "soft_warnings": [
                {"neuron": s.neuron_name, "message": s.message, "confidence": s.confidence}
                for s in soft_warnings
            ],
            "ai_can_override": True,
            "summary": (
                f"PASSED all hard gates. {len(soft_warnings)} soft warning(s)."
                if soft_warnings else "PASSED all gates. No warnings."
            ),
        }

    # -----------------------------------------------------------------------
    # Design Questionnaire Generator
    # -----------------------------------------------------------------------

    def generate_design_questionnaire(self, design_type: str = "general") -> List[Dict[str, Any]]:
        """
        Generate structured questions for users who are not design experts.
        AI uses this when it detects the user struggles to describe preferences.
        """
        base_questions = [
            {
                "category": "Layout",
                "question": "How should content be arranged?",
                "options": ["Single column (top to bottom)", "Two columns side by side",
                            "Grid/card layout", "Dashboard with sidebar"],
            },
            {
                "category": "Spacing",
                "question": "How dense should elements be?",
                "options": ["Compact/dense", "Medium spacing", "Spacious/lots of whitespace"],
            },
            {
                "category": "Color",
                "question": "Preferred color scheme?",
                "options": ["Dark mode", "Light mode", "Colorful/vibrant", "Neutral/minimal"],
            },
            {
                "category": "Typography",
                "question": "Text style preference?",
                "options": ["Clean/modern (sans-serif)", "Classic/formal (serif)", "Monospace/technical"],
            },
            {
                "category": "Complexity",
                "question": "How much information per screen?",
                "options": ["Simple — few elements, focused", "Moderate — balanced info density",
                            "Rich — many elements, data-heavy"],
            },
        ]

        if design_type.lower() in ("web", "website", "webapp"):
            base_questions.extend([
                {
                    "category": "Navigation",
                    "question": "Navigation style?",
                    "options": ["Top navbar", "Left sidebar", "Bottom tabs", "Hamburger menu"],
                },
                {
                    "category": "Interaction",
                    "question": "Interaction style?",
                    "options": ["Static pages", "Smooth animations/transitions",
                                "Highly interactive/dynamic"],
                },
            ])

        return base_questions

    # -----------------------------------------------------------------------
    # Thought Recording (with auto-pruning)
    # -----------------------------------------------------------------------

    def record_thought(self, thought: ThoughtRecord) -> None:
        """
        Save a thought record to StateMemory with auto-pruning.
        Keeps max MAX_THOUGHT_HISTORY records.
        """
        if not self.state_memory:
            return

        thought.timestamp = thought.timestamp or time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
        )

        state = self.state_memory.load_state()
        history = state.get("thought_history", [])

        # Auto-prune: keep only the most recent entries
        if len(history) >= self.MAX_THOUGHT_HISTORY:
            history = history[-(self.MAX_THOUGHT_HISTORY - 1):]

        # Serialize ThoughtRecord to dict
        record = {
            "thought_id": thought.thought_id,
            "content_type": thought.content_type,
            "ai_decision": thought.ai_decision,
            "refinement_count": thought.refinement_count,
            "timestamp": thought.timestamp,
            "neuron_summary": [
                {"name": s.neuron_name, "passed": s.passed, "gate": s.gate_type.value}
                for s in thought.neuron_signals
            ],
        }
        history.append(record)
        state["thought_history"] = history
        self.state_memory.save_state(state)

    def get_thought_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent thought records from StateMemory."""
        if not self.state_memory:
            return []

        state = self.state_memory.load_state()
        history = state.get("thought_history", [])
        return history[-limit:]

    # -----------------------------------------------------------------------
    # Internal Helpers
    # -----------------------------------------------------------------------

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
                    # Convert file path to module notation
                    module_name = rel_path.replace(os.sep, ".").removesuffix(".py")
                    if module_name.endswith(".__init__"):
                        module_name = module_name.removesuffix(".__init__")

                    modules[module_name] = {
                        "path": rel_path,
                        "abs_path": filepath,
                    }

        return modules

    def _calculate_lexical_diversity(self, text: str) -> float:
        """Calculate unique words / total words ratio."""
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 0.0
        return len(set(words)) / len(words)

    def _extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extract factual claims (statements with numbers or assertions)."""
        claims = []
        lines = text.split("\n")
        for line_no, line in enumerate(lines, 1):
            # Lines with numbers likely contain factual claims
            if re.search(r'\d+', line) and len(line.strip()) > 10:
                claims.append({"text": line.strip(), "line": line_no})
        return claims
