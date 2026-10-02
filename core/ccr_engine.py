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
from .lde_detector import LoopDetectionEngine
from .output_parsers import get_parser
from .state_memory import StateMemoryManager
from .taste_synthesis import ModernCSSKeywordHeuristic


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
    DEGRADED = "DEGRADED"   # Partial — work with caution
    IDEAL = "IDEAL"         # Complete information available
    OPTIMAL = "OPTIMAL"     # Full — clear execution


@dataclass
class GobyFeedback:
    """Agent Control Protocol Rich Feedback Object."""
    status: str  # "VERIFIED" | "BLOCKED" | "STRATEGY_CHANGE_REQUIRED"
    verified: bool
    blocked: bool
    gate: Optional[str]
    evidence: Dict[str, Any]
    suggestion: str
    repeated_failure: bool = False
    attempt: int = 1
    strategy_change_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "verified": self.verified,
            "blocked": self.blocked,
            "gate": self.gate,
            "evidence": self.evidence,
            "suggestion": self.suggestion,
            "repeated_failure": self.repeated_failure,
            "attempt": self.attempt,
            "strategy_change_required": self.strategy_change_required
        }


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
        self.lde = LoopDetectionEngine()
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


    def neuron_syntax_check(self, *args, **kwargs):
        from .neurons.syntax import neuron_syntax_check
        return neuron_syntax_check(self, *args, **kwargs)

    # -----------------------------------------------------------------------
    # Neuron 1b: JavaScript/TypeScript Syntax Check (HARD GATE)
    # -----------------------------------------------------------------------


    def neuron_js_syntax_check(self, *args, **kwargs):
        from .neurons.javascript import neuron_js_syntax_check
        return neuron_js_syntax_check(self, *args, **kwargs)


    def neuron_ts_syntax_check(self, *args, **kwargs):
        from .neurons.javascript import neuron_ts_syntax_check
        return neuron_ts_syntax_check(self, *args, **kwargs)

    def neuron_kotlin_syntax_check(self, code: str) -> NeuronSignal:
        """Deterministic bracket-balance and structural syntax check for Kotlin."""
        stack = []
        pairs = {')': '(', '}': '{', ']': '['}
        lines = code.splitlines()

        in_multiline_comment = False
        in_multiline_string = False

        for line_no, line in enumerate(lines, 1):
            i = 0
            n = len(line)
            while i < n:
                if in_multiline_comment:
                    if line[i:i+2] == "*/":
                        in_multiline_comment = False
                        i += 2
                    else:
                        i += 1
                    continue

                if in_multiline_string:
                    if line[i:i+3] == '"""':
                        in_multiline_string = False
                        i += 3
                    else:
                        i += 1
                    continue

                if line[i:i+2] == "//":
                    break  # rest of line is comment
                if line[i:i+2] == "/*":
                    in_multiline_comment = True
                    i += 2
                    continue
                if line[i:i+3] == '"""':
                    in_multiline_string = True
                    i += 3
                    continue

                ch = line[i]
                if ch == '"':
                    # Single-line string, skip to closing quote
                    i += 1
                    while i < n and line[i] != '"':
                        if line[i] == '\\':
                            i += 2
                        else:
                            i += 1
                    if i < n:
                        i += 1
                    continue

                if ch == "'":
                    # Character literal
                    i += 1
                    while i < n and line[i] != "'":
                        if line[i] == '\\':
                            i += 2
                        else:
                            i += 1
                    if i < n:
                        i += 1
                    continue

                if ch in "({[":
                    stack.append((ch, line_no))
                elif ch in ")}]":
                    if not stack:
                        return NeuronSignal(
                            neuron_name="SYNTAX_KT",
                            gate_type=GateType.HARD,
                            passed=False,
                            confidence=1.0,
                            message=f"Unmatched closing bracket '{ch}' at line {line_no}",
                            evidence={"line": line_no, "char": ch},
                            suggestion=f"Remove or pair the extra closing '{ch}'"
                        )
                    top, start_line = stack.pop()
                    if top != pairs[ch]:
                        return NeuronSignal(
                            neuron_name="SYNTAX_KT",
                            gate_type=GateType.HARD,
                            passed=False,
                            confidence=1.0,
                            message=f"Mismatched bracket: opened '{top}' at line {start_line}, closed with '{ch}' at line {line_no}",
                            evidence={"line": line_no, "opened": top, "closed": ch},
                            suggestion="Ensure brackets are properly nested"
                        )
                i += 1

        if in_multiline_comment:
            return NeuronSignal(
                neuron_name="SYNTAX_KT",
                gate_type=GateType.HARD,
                passed=False,
                confidence=1.0,
                message="Unterminated multiline comment '/* ... */'",
                suggestion="Close multiline comment with '*/'"
            )

        if in_multiline_string:
            return NeuronSignal(
                neuron_name="SYNTAX_KT",
                gate_type=GateType.HARD,
                passed=False,
                confidence=1.0,
                message='Unterminated multiline string """ ... """',
                suggestion='Close multiline string with """'
            )

        if stack:
            unclosed, start_line = stack[-1]
            return NeuronSignal(
                neuron_name="SYNTAX_KT",
                gate_type=GateType.HARD,
                passed=False,
                confidence=1.0,
                message=f"Unclosed opening bracket '{unclosed}' at line {start_line}",
                evidence={"line": start_line, "char": unclosed},
                suggestion=f"Close bracket '{unclosed}'"
            )

        return NeuronSignal(
            neuron_name="SYNTAX_KT",
            gate_type=GateType.HARD,
            passed=True,
            confidence=1.0,
            message="Kotlin syntax structure valid."
        )


    # -----------------------------------------------------------------------
    # Neuron: Taste Design & Motion Synthesis (HARD/SOFT GATE)
    # -----------------------------------------------------------------------


    def neuron_taste_design_check(self, *args, **kwargs):
        from .neurons.taste import neuron_taste_design_check
        return neuron_taste_design_check(self, *args, **kwargs)

    # -----------------------------------------------------------------------
    # Neuron 2: Scope Integrity Check (HARD GATE)
    # -----------------------------------------------------------------------


    def neuron_scope_check(self, *args, **kwargs):
        from .neurons.scope import neuron_scope_check
        return neuron_scope_check(self, *args, **kwargs)

    # -----------------------------------------------------------------------
    # Neuron 3: Cross-Reference (HARD GATE)
    # -----------------------------------------------------------------------


    def neuron_cross_reference(self, *args, **kwargs):
        from .neurons.cross_reference import neuron_cross_reference
        return neuron_cross_reference(self, *args, **kwargs)

    # -----------------------------------------------------------------------
    # Neuron 4: Behavior Check (SOFT SIGNAL)
    # -----------------------------------------------------------------------


    def neuron_behavior_check(self, *args, **kwargs):
        from .neurons.execution import neuron_behavior_check
        return neuron_behavior_check(self, *args, **kwargs)

    # -----------------------------------------------------------------------
    # Neuron 5: Reference Similarity (SOFT SIGNAL)
    # -----------------------------------------------------------------------


    def neuron_reference_similarity(self, *args, **kwargs):
        from .neurons.cross_reference import neuron_reference_similarity
        return neuron_reference_similarity(self, *args, **kwargs)

    # -----------------------------------------------------------------------
    # Neuron 6: GCA Execute (HARD GATE)
    # -----------------------------------------------------------------------


    def neuron_gca_execute(self, *args, **kwargs):
        from .neurons.execution import neuron_gca_execute
        return neuron_gca_execute(self, *args, **kwargs)

    # -----------------------------------------------------------------------
    # Neuron 7: Information Density (SOFT SIGNAL)
    # -----------------------------------------------------------------------


    def neuron_info_density(self, *args, **kwargs):
        from .neurons.semantics import neuron_info_density
        return neuron_info_density(self, *args, **kwargs)

    # -----------------------------------------------------------------------
    # Neuron 8: Consistency Check (SOFT SIGNAL)
    # -----------------------------------------------------------------------


    def neuron_consistency(self, *args, **kwargs):
        from .neurons.semantics import neuron_consistency
        return neuron_consistency(self, *args, **kwargs)

    # -----------------------------------------------------------------------
    # Neuron 9: Semantic Alignment Check (HARD/SOFT GATE)
    # -----------------------------------------------------------------------

    def neuron_semantic_alignment(self, *args, **kwargs):
        from .neurons.semantics import neuron_semantic_alignment
        return neuron_semantic_alignment(self, *args, **kwargs)

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


    def _scan_project(self, *args, **kwargs):
        from .neurons.cross_reference import _scan_project
        return _scan_project(self, *args, **kwargs)

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

    # -----------------------------------------------------------------------
    # Genuine Pre-Output In-Memory Verification API
    # -----------------------------------------------------------------------

    def verify_candidate(
        self,
        code: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None,
        contract: Optional[Any] = None,
        original_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Genuine Pre-Output In-Memory Verification API.
        Evaluates string candidate code BEFORE it touches the filesystem.
        Returns evaluation dict with 'blocked', 'signals', and 'summary'.
        """
        signals = []
        lang_lower = language.lower()

        if lang_lower in ("js", "javascript"):
            syn = self.neuron_js_syntax_check(code)
            signals.append(syn)
            signals.append(self.neuron_taste_design_check(code))
        elif lang_lower in ("ts", "typescript"):
            syn = self.neuron_ts_syntax_check(code)
            signals.append(syn)
            signals.append(self.neuron_taste_design_check(code))
        elif lang_lower in ("kt", "kotlin"):
            syn = self.neuron_kotlin_syntax_check(code)
            signals.append(syn)
        else:
            syn = self.neuron_syntax_check(code)
            signals.append(syn)
            if syn.passed:
                signals.append(self.neuron_scope_check(code))
                signals.append(self.neuron_taste_design_check(code))

        if contract is not None:
            signals.append(self.neuron_semantic_alignment(code, contract=contract, original_code=original_code))

        eval_result = self.evaluate_signals(signals)
        return {
            "verified": not eval_result["blocked"],
            "blocked": eval_result["blocked"],
            "summary": eval_result["summary"],
            "signals": [
                {
                    "neuron": s.neuron_name,
                    "passed": s.passed,
                    "gate": s.gate_type.value,
                    "message": s.message
                }
                for s in signals
            ]
        }

    def verify_candidate_with_feedback(
        self,
        code: str,
        language: str = "python",
        error_context: Optional[str] = None,
        attempt: int = 1,
        contract: Optional[Any] = None,
        original_code: Optional[str] = None
    ) -> GobyFeedback:
        """
        Agent Control Protocol API: Evaluates candidate code and produces an actionable GobyFeedback object.
        Transitions state to 'STRATEGY_CHANGE_REQUIRED' when LDE detects repeated repair cycles.
        """
        raw_res = self.verify_candidate(
            code, language=language, contract=contract, original_code=original_code
        )

        if raw_res["blocked"]:
            failed_sig = next((s for s in raw_res["signals"] if not s["passed"]), None)
            gate_name = failed_sig["neuron"] if failed_sig else "UNKNOWN"
            suggestion_msg = failed_sig["message"] if failed_sig else "Resolve static verification error before retrying."

            return GobyFeedback(
                status="BLOCKED",
                verified=False,
                blocked=True,
                gate=gate_name,
                evidence={"signals": raw_res["signals"]},
                suggestion=f"[{gate_name} BLOCKED] {suggestion_msg}",
                repeated_failure=False,
                attempt=attempt,
                strategy_change_required=False
            )

        # Check LDE error loop guard if error context is supplied
        if error_context:
            lde_res = self.lde.record_attempt(code, error_context)
            if lde_res.is_loop_detected or attempt >= 2 or len(self.lde.history) >= 2:
                return GobyFeedback(
                    status="STRATEGY_CHANGE_REQUIRED",
                    verified=False,
                    blocked=True,
                    gate="LDE",
                    evidence={
                        "loop_type": lde_res.loop_type or "REPEATED_ATTEMPT",
                        "similarity_score": lde_res.similarity_score if lde_res.confidence > 0 else 1.0,
                        "attempt_history_count": len(self.lde.history)
                    },
                    suggestion="[LDE REPEATED FAILURE] Do not repeat the previous repair strategy. Pivot to an alternative architectural approach or deconstruct the task.",
                    repeated_failure=True,
                    attempt=attempt,
                    strategy_change_required=True
                )

        return GobyFeedback(
            status="VERIFIED",
            verified=True,
            blocked=False,
            gate=None,
            evidence={"signals": raw_res["signals"]},
            suggestion="Candidate passed all verification gates.",
            repeated_failure=False,
            attempt=attempt,
            strategy_change_required=False
        )

    # -----------------------------------------------------------------------
    # Evidence Engine: Machine-Verifiable Evidence Contract Generator
    # -----------------------------------------------------------------------

    def resolve_source(self, target: str) -> tuple:
        """
        Deterministically resolves whether target is a file path or in-memory code string.
        Returns (code_content, origin_type, resolved_path).
        """
        if os.path.isfile(target):
            try:
                with open(target, "r", encoding="utf-8") as f:
                    return f.read(), "file", os.path.abspath(target)
            except OSError:
                pass
        return target, "in_memory", "in_memory"

    def create_evidence_contract(
        self,
        claim: str,
        code_or_file: str,
        language: str = "python",
        test_command: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a machine-verifiable Evidence Contract with Evidence ID & cryptographic SHA-256 provenance.
        Combines static AST verification signals and dynamic execution results.
        """
        import hashlib

        code_content, origin_type, resolved_path = self.resolve_source(code_or_file)
        sha256_hash = hashlib.sha256(code_content.encode("utf-8")).hexdigest()
        timestamp_str = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        evidence_id = f"EV-{timestamp_str}-{sha256_hash[:8]}"

        static_res = self.verify_candidate(code_content, language=language)
        dynamic_res = None

        if test_command:
            exec_res = self.gca.run_command(test_command, timeout=15.0)
            dynamic_res = {
                "command": exec_res.command,
                "exit_code": exec_res.exit_code,
                "duration_seconds": exec_res.duration_seconds,
                "is_success": exec_res.is_success,
                "stdout_summary": exec_res.stdout[:200] if exec_res.stdout else "",
                "stderr_summary": exec_res.stderr[:200] if exec_res.stderr else ""
            }

        is_verified = static_res["verified"] and (dynamic_res["is_success"] if dynamic_res else True)

        return {
            "contract_version": "1.0.0",
            "evidence_id": evidence_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "claim": claim,
            "status": "VERIFIED" if is_verified else "UNVERIFIED",
            "source_provenance": {
                "origin": origin_type,
                "path": resolved_path,
                "sha256": sha256_hash,
                "language": language
            },
            "evidence": {
                "static_analysis": static_res,
                "dynamic_execution": dynamic_res or {"status": "NOT_EXECUTED"}
            }
        }
