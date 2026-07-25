"""
Failure Pattern Store for Goby Framework.
Provides persistent cross-session memory of error patterns and their solutions.
When a similar error is encountered in a future session, the store can suggest
a known bypass — enabling preemptive resolution without re-experiencing the loop.
"""

import hashlib
import json
import os
import re
import threading
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from .lde_detector import similarity_ratio


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class FailureFingerprint:
    """Fingerprint of a known failure pattern with its solution."""
    error_hash: str
    error_type: str
    normalized_output: str
    root_cause: str
    solution_taken: str
    language: str
    timestamp: str
    success_count: int = 0


# ---------------------------------------------------------------------------
# Failure Pattern Store
# ---------------------------------------------------------------------------

class FailurePatternStore:
    """
    Persistent store for failure patterns learned across sessions.
    Uses JSON file storage and Levenshtein similarity for pattern matching.

    This transforms LDE from reactive ("detect loop after 3 failures")
    to predictive ("recognize error from past sessions, bypass immediately").
    """

    MAX_PATTERNS = 100  # Auto-prune oldest when exceeded

    def __init__(self, memory_file_path: str = "failure_patterns.json"):
        self.memory_file_path = os.path.abspath(memory_file_path)
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Ensure the patterns file exists."""
        if not os.path.exists(self.memory_file_path):
            self._save_patterns([])

    def _normalize_error(self, error_output: str) -> str:
        """Normalize error output for consistent fingerprinting."""
        output = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', error_output)
        output = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?', 'TIMESTAMP', output)
        output = re.sub(r'line \d+', 'line N', output, flags=re.IGNORECASE)
        output = re.sub(r':\d+:\d+', ':N:N', output)
        output = re.sub(r'\s+', ' ', output).strip()
        return output

    def _compute_hash(self, normalized_output: str) -> str:
        """Compute deterministic hash for a normalized error string."""
        return hashlib.sha256(normalized_output.encode("utf-8")).hexdigest()[:16]

    def _load_patterns(self) -> List[Dict[str, Any]]:
        """Load patterns from disk."""
        with self._lock:
            try:
                with open(self.memory_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("patterns", [])
            except (json.JSONDecodeError, OSError, KeyError):
                return []

    def _save_patterns(self, patterns: List[Dict[str, Any]]) -> None:
        """Save patterns to disk atomically."""
        with self._lock:
            tmp_path = self.memory_file_path + ".tmp"
            data = {
                "version": "1.0.0",
                "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "pattern_count": len(patterns),
                "patterns": patterns,
            }
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(tmp_path, self.memory_file_path)
            except Exception:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    def record_failure(
        self,
        error_output: str,
        error_type: str,
        root_cause: str,
        solution: str,
        language: str,
    ) -> FailureFingerprint:
        """
        Record a new failure pattern into persistent storage.
        Auto-prunes oldest patterns if MAX_PATTERNS is exceeded.
        """
        normalized = self._normalize_error(error_output)
        error_hash = self._compute_hash(normalized)

        fingerprint = FailureFingerprint(
            error_hash=error_hash,
            error_type=error_type,
            normalized_output=normalized,
            root_cause=root_cause,
            solution_taken=solution,
            language=language,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            success_count=0,
        )

        patterns = self._load_patterns()

        # Check for duplicate (same hash) — update instead of duplicate
        for i, p in enumerate(patterns):
            if p.get("error_hash") == error_hash:
                patterns[i] = asdict(fingerprint)
                self._save_patterns(patterns)
                return fingerprint

        patterns.append(asdict(fingerprint))

        # Auto-prune: keep only the most recent patterns
        if len(patterns) > self.MAX_PATTERNS:
            patterns = patterns[-self.MAX_PATTERNS:]

        self._save_patterns(patterns)
        return fingerprint

    def match_known_pattern(
        self, error_output: str, threshold: float = 0.80
    ) -> Optional[FailureFingerprint]:
        """
        Search for a known failure pattern matching the given error output.
        Uses Levenshtein similarity ratio for fuzzy matching.
        Returns the best match above threshold, or None.
        """
        normalized = self._normalize_error(error_output)
        patterns = self._load_patterns()

        best_match: Optional[Dict[str, Any]] = None
        best_similarity: float = 0.0

        for pattern in patterns:
            stored_output = pattern.get("normalized_output", "")
            sim = similarity_ratio(normalized, stored_output)
            if sim >= threshold and sim > best_similarity:
                best_similarity = sim
                best_match = pattern

        if best_match is None:
            return None

        # Increment success_count to track how useful this pattern is
        best_match["success_count"] = best_match.get("success_count", 0) + 1
        self._save_patterns(patterns)

        return FailureFingerprint(
            error_hash=best_match.get("error_hash", ""),
            error_type=best_match.get("error_type", ""),
            normalized_output=best_match.get("normalized_output", ""),
            root_cause=best_match.get("root_cause", ""),
            solution_taken=best_match.get("solution_taken", ""),
            language=best_match.get("language", ""),
            timestamp=best_match.get("timestamp", ""),
            success_count=best_match.get("success_count", 0),
        )

    def get_all_patterns(self) -> List[FailureFingerprint]:
        """Return all stored failure patterns."""
        patterns = self._load_patterns()
        return [
            FailureFingerprint(
                error_hash=p.get("error_hash", ""),
                error_type=p.get("error_type", ""),
                normalized_output=p.get("normalized_output", ""),
                root_cause=p.get("root_cause", ""),
                solution_taken=p.get("solution_taken", ""),
                language=p.get("language", ""),
                timestamp=p.get("timestamp", ""),
                success_count=p.get("success_count", 0),
            )
            for p in patterns
        ]

    def clear_patterns(self) -> None:
        """Remove all stored failure patterns."""
        self._save_patterns([])
