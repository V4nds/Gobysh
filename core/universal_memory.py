"""
Universal Memory Store for Goby Consciousness Engine.
Upgrades FailurePatternStore into Epistemic Universal Memory.
Instead of just fuzzy matching strings, it stores abstract problem signatures,
enabling cross-domain heuristic problem solving (Aha! moments).
"""

import hashlib
import json
import os
import re
import threading
import time
import logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from .lde_detector import similarity_ratio


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class UniversalMemoryPattern:
    """Abstract cognitive footprint of a solved problem."""
    memory_id: str
    semantic_signature: str       # Abstracted representation of the problem space
    error_type: str
    original_context: str
    abstract_root_cause: str      # E.g., "Recursive infinite depth" instead of "RecursionError line 42"
    universal_heuristic: str      # The general principle used to solve it (e.g. "Introduce state tracking")
    language: str
    timestamp: str
    success_count: int = 0


# ---------------------------------------------------------------------------
# Universal Memory Store
# ---------------------------------------------------------------------------

class UniversalMemoryStore:
    """
    Persistent Epistemic Consciousness Store.
    This module transforms raw failure outputs into universal abstract patterns.
    """

    MAX_PATTERNS = 200

    def __init__(self, memory_file_path: str = "universal_consciousness.json"):
        self.memory_file_path = os.path.abspath(memory_file_path)
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Ensure the consciousness file exists."""
        if not os.path.exists(self.memory_file_path):
            self._save_patterns([])

    def _extract_semantic_signature(self, error_output: str, error_type: str) -> str:
        """
        Abstract the error output into a semantic signature.
        Strips highly specific context to capture the 'soul' of the problem.
        """
        # Remove literal numbers, addresses, specific variable names (heuristically)
        sig = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', error_output)
        sig = re.sub(r'\d+', 'N', sig)
        sig = re.sub(r'line N', 'LINE_REF', sig, flags=re.IGNORECASE)
        sig = re.sub(r"'.*?'", 'STR_LITERAL', sig)
        sig = re.sub(r'".*?"', 'STR_LITERAL', sig)
        sig = re.sub(r'\s+', ' ', sig).strip()
        # Combine with error type to form a conceptual block
        return f"{error_type}::[{sig}]"

    def _compute_hash(self, semantic_signature: str) -> str:
        """Compute deterministic hash for a semantic signature."""
        return hashlib.sha256(semantic_signature.encode("utf-8")).hexdigest()[:16]

    def _load_patterns(self) -> List[Dict[str, Any]]:
        with self._lock:
            try:
                with open(self.memory_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("memories", [])
            except (json.JSONDecodeError, OSError, KeyError) as e:
                logging.warning(f"Failed to load universal memory from {self.memory_file_path}: {e}")
                return []

    def _save_patterns(self, patterns: List[Dict[str, Any]]) -> None:
        with self._lock:
            tmp_path = self.memory_file_path + ".tmp"
            data = {
                "version": "3.0.0",
                "consciousness_level": "Epistemic",
                "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "memory_count": len(patterns),
                "memories": patterns,
            }
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(tmp_path, self.memory_file_path)
            except Exception as e:
                logging.warning(f"Failed to save universal memory to {self.memory_file_path}: {e}")
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    def crystallize_memory(
        self,
        error_output: str,
        error_type: str,
        abstract_root_cause: str,
        universal_heuristic: str,
        language: str = "agnostic",
    ) -> UniversalMemoryPattern:
        """
        Crystallize a successful problem-solving journey into a universal memory.
        This is called by the Consciousness Engine after a successful validation.
        """
        semantic_sig = self._extract_semantic_signature(error_output, error_type)
        memory_id = self._compute_hash(semantic_sig)

        memory = UniversalMemoryPattern(
            memory_id=memory_id,
            semantic_signature=semantic_sig,
            error_type=error_type,
            original_context=error_output[:200] + "...", # keep snippet for human readability
            abstract_root_cause=abstract_root_cause,
            universal_heuristic=universal_heuristic,
            language=language,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            success_count=0,
        )

        patterns = self._load_patterns()

        for i, p in enumerate(patterns):
            if p.get("memory_id") == memory_id:
                patterns[i] = asdict(memory)
                self._save_patterns(patterns)
                return memory

        patterns.append(asdict(memory))
        if len(patterns) > self.MAX_PATTERNS:
            patterns = patterns[-self.MAX_PATTERNS:]

        self._save_patterns(patterns)
        return memory

    def recall_intuition(
        self, error_output: str, error_type: str, threshold: float = 0.75
    ) -> Optional[UniversalMemoryPattern]:
        """
        Trigger 'System 1 Intuition'. Searches for a conceptually similar problem
        and returns the abstract heuristic to bypass the issue.
        """
        current_sig = self._extract_semantic_signature(error_output, error_type)
        patterns = self._load_patterns()

        best_match: Optional[Dict[str, Any]] = None
        best_similarity: float = 0.0

        for pattern in patterns:
            stored_sig = pattern.get("semantic_signature", "")
            sim = similarity_ratio(current_sig, stored_sig)
            if sim >= threshold and sim > best_similarity:
                best_similarity = sim
                best_match = pattern

        if best_match is None:
            return None

        best_match["success_count"] = best_match.get("success_count", 0) + 1
        self._save_patterns(patterns)

        return UniversalMemoryPattern(
            memory_id=best_match.get("memory_id", ""),
            semantic_signature=best_match.get("semantic_signature", ""),
            error_type=best_match.get("error_type", ""),
            original_context=best_match.get("original_context", ""),
            abstract_root_cause=best_match.get("abstract_root_cause", ""),
            universal_heuristic=best_match.get("universal_heuristic", ""),
            language=best_match.get("language", ""),
            timestamp=best_match.get("timestamp", ""),
            success_count=best_match.get("success_count", 0),
        )

    def get_all_memories(self) -> List[UniversalMemoryPattern]:
        patterns = self._load_patterns()
        return [UniversalMemoryPattern(**p) for p in patterns]

    def clear_consciousness(self) -> None:
        self._save_patterns([])

    def recall_apriori_knowledge(self, code_snippet: str) -> Optional[str]:
        """
        Omni-Synthesis Apriori Index.
        Scans code against universal patterns before execution to deliver zero-bypass direct guidance.
        """
        patterns = self._load_patterns()
        for p in patterns:
            heuristic = p.get("universal_heuristic", "")
            root_cause = p.get("abstract_root_cause", "")
            if "recursion" in root_cause.lower() and ("solve(" in code_snippet or "def " in code_snippet):
                return heuristic
        return None

    # -----------------------------------------------------------------
    # Backward-compatible FailurePatternStore facade (v1.x compatibility)
    # Eliminates the need for a separate failure_memory.py for new code.
    # -----------------------------------------------------------------

    def record_failure_compat(
        self,
        error_output: str,
        error_type: str,
        root_cause: str,
        solution: str,
        language: str = "python",
    ) -> UniversalMemoryPattern:
        """Legacy-compatible entry point matching FailurePatternStore.record_failure()."""
        return self.crystallize_memory(
            error_output=error_output,
            error_type=error_type,
            abstract_root_cause=root_cause,
            universal_heuristic=solution,
            language=language,
        )

    def match_known_pattern_compat(
        self, error_output: str, threshold: float = 0.80
    ) -> Optional[UniversalMemoryPattern]:
        """Legacy-compatible entry point matching FailurePatternStore.match_known_pattern()."""
        # Infer error_type from output heuristically
        error_type = "UnknownError"
        for token in ["RecursionError", "ImportError", "ModuleNotFoundError", "Timeout", "MemoryError", "SyntaxError"]:
            if token in error_output:
                error_type = token
                break
        return self.recall_intuition(error_output, error_type, threshold)


