"""
Loop Detection Engine (LDE) for Goby Framework.
Detects logic loops, compiler failure cycles, and paradoxical oscillations.
"""

import hashlib
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


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
    loop_type: Optional[str]  # 'COMPILER_LOOP', 'PARADOXICAL_OSCILLATION', 'STATIC_OVER_OPTIMIZATION'
    confidence: float
    message: str
    suggested_action: str


class LoopDetectionEngine:
    """
    Monitors execution history and detects structural or semantic repetitions.
    """

    def __init__(self, threshold_similarity: float = 0.85, max_history_size: int = 10):
        self.threshold_similarity = threshold_similarity
        self.max_history_size = max_history_size
        self.history: List[Tuple[str, str]] = []  # List of (code_hash, output_str)

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
                    message=f"Detected repetitive compiler/runtime error across {count_similar} attempts.",
                    suggested_action="TRIGGER_META_SYSTEMIC_LEAP"
                )

        # 2. Check for Paradoxical Oscillation (Ping-pong between state A and state B)
        if len(outputs) >= 4:
            if similarity_ratio(outputs[-1], outputs[-3]) >= 0.9 and similarity_ratio(outputs[-2], outputs[-4]) >= 0.9:
                if similarity_ratio(outputs[-1], outputs[-2]) < 0.6:
                    return LoopAnalysisResult(
                        is_loop_detected=True,
                        loop_type="PARADOXICAL_OSCILLATION",
                        confidence=0.95,
                        message="Oscillating between two conflicting failure states.",
                        suggested_action="AXIOM_INJECTION_AND_ISOLATION"
                    )

        # 3. Check for Static Over-Optimization (Code changes, but logic/error remains constant)
        if len(hashes) >= 3 and len(set(hashes[-3:])) == 3:  # 3 distinct code attempts
            sims = [similarity_ratio(outputs[-1], outputs[-i]) for i in range(2, min(4, len(outputs) + 1))]
            if all(s >= 0.85 for s in sims):
                return LoopAnalysisResult(
                    is_loop_detected=True,
                    loop_type="STATIC_OVER_OPTIMIZATION",
                    confidence=0.90,
                    message="Code refactored 3+ times without changing underlying runtime failure.",
                    suggested_action="EXPAND_REPRESENTATION_SPACE"
                )

        return LoopAnalysisResult(
            is_loop_detected=False,
            loop_type=None,
            confidence=0.0,
            message="No loop detected.",
            suggested_action="PROCEED_NORMAL"
        )
