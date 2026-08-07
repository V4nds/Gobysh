"""
Loop Detection Engine (LDE) for Goby Framework.
Detects logic loops, compiler failure cycles, and paradoxical oscillations.
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def similarity_ratio(s1: str, s2: str) -> float:
    """Compute normalized similarity ratio between 0.0 and 1.0."""
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(s1, s2)
    return 1.0 - (dist / max_len)


@dataclass
class LoopAnalysisResult:
    is_loop_detected: bool
    loop_type: Optional[str]  # 'COMPILER_LOOP', 'PARADOXICAL_OSCILLATION', 'STATIC_OVER_OPTIMIZATION', 'PREEMPTIVE_KNOWN_PATTERN', 'TIMEOUT_MEMORY_LOOP'
    confidence: float
    message: str
    suggested_action: str
    known_pattern: Optional[Any] = None  # FailureFingerprint when preemptive match found


class LoopDetectionEngine:
    """
    Monitors execution history and detects structural or semantic repetitions.
    Supports dynamic sensitivity (Neuro-Plasticity) based on Bypass Frequency Metric (BFM).
    """

    def __init__(self, threshold_similarity: float = 0.85, max_history_size: int = 10, failure_store=None):
        self.base_threshold = threshold_similarity
        self.threshold_similarity = threshold_similarity
        self.max_history_size = max_history_size
        self.history: List[Tuple[str, str]] = []  # List of (code_hash, output_str)
        self.failure_store = failure_store  # Optional FailurePatternStore for cross-session memory

    def adjust_sensitivity_based_on_bfm(self, bfm: float) -> None:
        """
        Neuro-Plasticity: Adjusts detection sensitivity based on stress (BFM).
        High BFM (frequent bypasses) = lower threshold (more sensitive to loops).
        Low BFM (smart AI) = higher threshold (less sensitive, avoids false positives).
        """
        if bfm > 0.5:
            # High error rate -> very sensitive
            self.threshold_similarity = max(0.60, self.base_threshold - 0.15)
        elif bfm > 0.2:
            self.threshold_similarity = max(0.70, self.base_threshold - 0.10)
        elif bfm == 0.0:
            # Zero bypass -> very strict
            self.threshold_similarity = min(0.95, self.base_threshold + 0.05)
        else:
            self.threshold_similarity = self.base_threshold

    def _normalize_output(self, output: str) -> str:
        """Strip dynamic timestamps and memory addresses for deterministic hashing."""
        output = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', output)
        output = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?', 'TIMESTAMP', output)
        output = re.sub(r'\s+', ' ', output).strip()
        return output

    def record_attempt(self, code: str, output: str) -> LoopAnalysisResult:
        """
        Records a new execution attempt and checks if a loop has occurred.
        """
        code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
        norm_output = self._normalize_output(output)

        self.history.append((code_hash, norm_output))
        if len(self.history) > self.max_history_size:
            self.history.pop(0)

        return self.analyze()

    def analyze(self) -> LoopAnalysisResult:
        """Analyzes the current history window for repeating patterns."""
        if len(self.history) < 2:
            return LoopAnalysisResult(
                is_loop_detected=False,
                loop_type=None,
                confidence=0.0,
                message="Insufficient execution history.",
                suggested_action="PROCEED_NORMAL"
            )

        outputs = [out for _, out in self.history]
        hashes = [h for h, _ in self.history]

        # 1. Check for Compiler Loop (Same output repeatedly)
        recent_output = outputs[-1]
        previous_output = outputs[-2]
        sim = similarity_ratio(recent_output, previous_output)

        if sim >= self.threshold_similarity and len(recent_output) > 0:
            count_similar = sum(1 for o in outputs if similarity_ratio(o, recent_output) >= self.threshold_similarity)
            if count_similar >= 3:
                return LoopAnalysisResult(
                    is_loop_detected=True,
                    loop_type="COMPILER_LOOP",
                    confidence=sim,
                    message=f"Detected repetitive compiler/runtime error across {count_similar} attempts. (Non-Euclidean Trap)",
                    suggested_action="TRIGGER_AXIOM_SHIFT_EPIPHANY"
                )

        # 2. Check for Paradoxical Oscillation (Ping-pong between state A and state B)
        if len(outputs) >= 4:
            if similarity_ratio(outputs[-1], outputs[-3]) >= 0.9 and similarity_ratio(outputs[-2], outputs[-4]) >= 0.9:
                if similarity_ratio(outputs[-1], outputs[-2]) < 0.6:
                    return LoopAnalysisResult(
                        is_loop_detected=True,
                        loop_type="PARADOXICAL_OSCILLATION",
                        confidence=0.95,
                        message="Oscillating between two conflicting failure states. (Paradox)",
                        suggested_action="TRIGGER_CANTOR_LATERAL_BYPASS"
                    )

        # 3. Check for Static Over-Optimization (Code changes, but logic/error remains constant)
        if len(hashes) >= 3 and len(set(hashes[-3:])) == 3:  # 3 distinct code attempts
            sims = [similarity_ratio(outputs[-1], outputs[-i]) for i in range(2, min(4, len(outputs) + 1))]
            if all(s >= 0.85 for s in sims):
                return LoopAnalysisResult(
                    is_loop_detected=True,
                    loop_type="STATIC_OVER_OPTIMIZATION",
                    confidence=0.90,
                    message="Code refactored 3+ times without changing underlying runtime failure. (P vs NP Trap)",
                    suggested_action="TRIGGER_HEURISTIC_INTUITION_SYSTEM_1"
                )

        # 4. Check for Timeout/Memory Limit (Topology Bypass)
        if len(outputs) >= 2 and any(term in recent_output.lower() for term in ["timeout", "memoryerror", "maximum recursion depth"]):
            return LoopAnalysisResult(
                is_loop_detected=True,
                loop_type="TIMEOUT_MEMORY_LOOP",
                confidence=0.90,
                message="Hit computational boundary (Time/Memory).",
                suggested_action="TRIGGER_TOPOLOGY_METAPHORICAL_BYPASS"
            )

        return LoopAnalysisResult(
            is_loop_detected=False,
            loop_type=None,
            confidence=0.0,
            message="No loop detected.",
            suggested_action="PROCEED_NORMAL"
        )

    # -------------------------------------------------------------------
    # Learning LDE: Cross-Session Preemptive Bypass (v1.2.0)
    # -------------------------------------------------------------------

    def check_preemptive(self, error_output: str) -> Optional[LoopAnalysisResult]:
        """
        Check if error matches a known failure pattern from past sessions.
        Returns a LoopAnalysisResult with PREEMPTIVE_KNOWN_PATTERN if matched.
        Returns None if no match or no failure store is configured.
        """
        if self.failure_store is None:
            return None

        match = self.failure_store.match_known_pattern(error_output)
        if match is None:
            return None

        return LoopAnalysisResult(
            is_loop_detected=True,
            loop_type="PREEMPTIVE_KNOWN_PATTERN",
            confidence=0.90,
            message=(
                f"Known failure pattern recognized from past session. "
                f"Error type: {match.error_type}. "
                f"Root cause: {match.root_cause}. "
                f"Previous solution: {match.solution_taken}"
            ),
            suggested_action="APPLY_KNOWN_SOLUTION",
            known_pattern=match,
        )

    def record_resolution(
        self,
        error_output: str,
        error_type: str,
        root_cause: str,
        solution: str,
        language: str = "python",
    ) -> None:
        """
        Record a successfully resolved error into the failure pattern store
        for future preemptive detection.
        """
        if self.failure_store is None:
            return

        self.failure_store.record_failure(
            error_output=error_output,
            error_type=error_type,
            root_cause=root_cause,
            solution=solution,
            language=language,
        )
