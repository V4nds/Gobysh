"""
Conversation Memory for Goby Framework v5.0.
Persists conversation context across AI sessions so that similar problems
don't start from zero every time.

Key features:
- Auto-save: Captures task summary, files modified, errors hit, solution path
- Auto-recall: On new request, searches past conversations by semantic similarity
- Auto-prune: Keeps MAX_ENTRIES most recent, drops oldest
- Persistent: JSON file storage at workspace root (conversation_index.json)

This module is auto-invoked by the agent pipeline:
  Session Start → conversation_memory.recall(user_request)
  Session End   → conversation_memory.save(task_summary, ...)
"""

import hashlib
import json
import os
import re
import threading
import time
import logging
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

from .lde_detector import similarity_ratio


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ConversationEntry:
    """A single conversation record persisted to disk."""
    entry_id: str
    timestamp: str
    user_intent_summary: str       # What the user asked for (abstracted)
    task_type: str                 # fix_bug, create_feature, etc.
    files_modified: List[str]      # Which files were touched
    errors_encountered: List[str]  # Error types hit during this session
    solution_summary: str          # What was done to solve it
    final_status: str              # "SUCCESS", "PARTIAL", "FAILED"
    semantic_fingerprint: str      # Normalized signature for similarity matching
    tags: List[str] = field(default_factory=list)  # Auto-generated topical tags


@dataclass
class RecallResult:
    """Result of a memory recall query."""
    found: bool
    similarity: float
    entry: Optional[ConversationEntry]
    context_hint: str              # Human-readable hint for the agent


# ---------------------------------------------------------------------------
# Conversation Memory Store
# ---------------------------------------------------------------------------

class ConversationMemoryStore:
    """
    Persistent conversation memory with semantic recall.

    Usage:
        mem = ConversationMemoryStore()

        # At session start — recall relevant past context
        recall = mem.recall("perbaiki error di app.js")
        if recall.found:
            print(f"Found similar past session: {recall.context_hint}")

        # At session end — save what was done
        mem.save(
            user_intent_summary="Fix TypeError in app.js event handler",
            task_type="fix_bug",
            files_modified=["app.js"],
            errors_encountered=["TypeError"],
            solution_summary="Added null check before accessing event.target",
            final_status="SUCCESS",
        )
    """

    MAX_ENTRIES = 50
    RECALL_THRESHOLD = 0.55  # Minimum similarity for a useful recall

    def __init__(self, memory_file_path: str = "conversation_index.json"):
        self.memory_file_path = os.path.abspath(memory_file_path)
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Ensure the conversation index file exists."""
        if not os.path.exists(self.memory_file_path):
            self._save_entries([])

    def _create_fingerprint(self, text: str) -> str:
        """
        Create a semantic fingerprint from text.
        Strips specifics (numbers, paths, quotes) to capture the 'essence'.
        """
        sig = text.lower().strip()
        # Remove specific file paths
        sig = re.sub(r'[\w/\\.-]+\.\w+', 'FILE_REF', sig)
        # Remove numbers
        sig = re.sub(r'\d+', 'N', sig)
        # Remove quoted strings
        sig = re.sub(r"'.*?'", 'STR', sig)
        sig = re.sub(r'".*?"', 'STR', sig)
        # Normalize whitespace
        sig = re.sub(r'\s+', ' ', sig).strip()
        return sig

    def _compute_id(self, fingerprint: str, timestamp: str) -> str:
        """Compute a unique entry ID."""
        raw = f"{fingerprint}::{timestamp}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]

    def _extract_tags(self, intent_summary: str, task_type: str, files: List[str]) -> List[str]:
        """Auto-generate topical tags from the conversation data."""
        tags = [task_type]

        # Extract file extensions as tags
        for f in files:
            ext = os.path.splitext(f)[1].lstrip(".")
            if ext:
                tags.append(ext)

        # Extract technology keywords
        text_lower = intent_summary.lower()
        tech_keywords = [
            "react", "vue", "angular", "python", "javascript", "typescript",
            "css", "html", "api", "database", "test", "deploy", "docker",
            "git", "npm", "pip",
        ]
        for kw in tech_keywords:
            if kw in text_lower:
                tags.append(kw)

        return list(set(tags))  # Deduplicate

    def _load_entries(self) -> List[Dict[str, Any]]:
        """Load entries from disk."""
        with self._lock:
            try:
                with open(self.memory_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("conversations", [])
            except (json.JSONDecodeError, OSError) as e:
                logging.warning(f"Failed to load conversation memory from {self.memory_file_path}: {e}")
                return []

    def _save_entries(self, entries: List[Dict[str, Any]]) -> None:
        """Save entries to disk atomically."""
        with self._lock:
            tmp_path = self.memory_file_path + ".tmp"
            data = {
                "version": "1.0.0",
                "goby_version": "5.0.0",
                "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "entry_count": len(entries),
                "conversations": entries,
            }
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(tmp_path, self.memory_file_path)
            except Exception as e:
                logging.warning(f"Failed to save conversation memory to {self.memory_file_path}: {e}")
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

    # -------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------

    def save(
        self,
        user_intent_summary: str,
        task_type: str,
        files_modified: Optional[List[str]] = None,
        errors_encountered: Optional[List[str]] = None,
        solution_summary: str = "",
        final_status: str = "SUCCESS",
    ) -> ConversationEntry:
        """
        Save a conversation record at the end of a session.
        Auto-prunes oldest entries if MAX_ENTRIES exceeded.
        """
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        fingerprint = self._create_fingerprint(user_intent_summary)
        entry_id = self._compute_id(fingerprint, timestamp)

        entry = ConversationEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            user_intent_summary=user_intent_summary,
            task_type=task_type,
            files_modified=files_modified or [],
            errors_encountered=errors_encountered or [],
            solution_summary=solution_summary,
            final_status=final_status,
            semantic_fingerprint=fingerprint,
            tags=self._extract_tags(user_intent_summary, task_type, files_modified or []),
        )

        entries = self._load_entries()
        entries.append(asdict(entry))

        # Auto-prune: keep only the most recent entries
        if len(entries) > self.MAX_ENTRIES:
            entries = entries[-self.MAX_ENTRIES:]

        self._save_entries(entries)
        return entry

    def recall(
        self,
        user_input: str,
        threshold: Optional[float] = None,
        max_results: int = 3,
    ) -> List[RecallResult]:
        """
        Search past conversations for similar context.
        Returns a list of RecallResults sorted by similarity (highest first).
        """
        effective_threshold = threshold if threshold is not None else self.RECALL_THRESHOLD
        current_fingerprint = self._create_fingerprint(user_input)
        entries = self._load_entries()

        scored: List[tuple] = []
        for entry_dict in entries:
            stored_fp = entry_dict.get("semantic_fingerprint", "")
            sim = similarity_ratio(current_fingerprint, stored_fp)
            if sim >= effective_threshold:
                scored.append((sim, entry_dict))

        # Sort by similarity descending
        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sim, entry_dict in scored[:max_results]:
            entry = ConversationEntry(
                entry_id=entry_dict.get("entry_id", ""),
                timestamp=entry_dict.get("timestamp", ""),
                user_intent_summary=entry_dict.get("user_intent_summary", ""),
                task_type=entry_dict.get("task_type", ""),
                files_modified=entry_dict.get("files_modified", []),
                errors_encountered=entry_dict.get("errors_encountered", []),
                solution_summary=entry_dict.get("solution_summary", ""),
                final_status=entry_dict.get("final_status", ""),
                semantic_fingerprint=entry_dict.get("semantic_fingerprint", ""),
                tags=entry_dict.get("tags", []),
            )

            # Build context hint
            hint_parts = [f"Past session ({entry.timestamp}): {entry.user_intent_summary}"]
            if entry.solution_summary:
                hint_parts.append(f"Solution: {entry.solution_summary}")
            if entry.files_modified:
                hint_parts.append(f"Files: {', '.join(entry.files_modified[:5])}")
            if entry.errors_encountered:
                hint_parts.append(f"Errors hit: {', '.join(entry.errors_encountered[:3])}")

            results.append(RecallResult(
                found=True,
                similarity=round(sim, 3),
                entry=entry,
                context_hint=" | ".join(hint_parts),
            ))

        if not results:
            results.append(RecallResult(
                found=False,
                similarity=0.0,
                entry=None,
                context_hint="No similar past conversation found. Starting fresh.",
            ))

        return results

    def get_all_entries(self) -> List[ConversationEntry]:
        """Return all stored conversation entries."""
        entries = self._load_entries()
        return [
            ConversationEntry(
                entry_id=e.get("entry_id", ""),
                timestamp=e.get("timestamp", ""),
                user_intent_summary=e.get("user_intent_summary", ""),
                task_type=e.get("task_type", ""),
                files_modified=e.get("files_modified", []),
                errors_encountered=e.get("errors_encountered", []),
                solution_summary=e.get("solution_summary", ""),
                final_status=e.get("final_status", ""),
                semantic_fingerprint=e.get("semantic_fingerprint", ""),
                tags=e.get("tags", []),
            )
            for e in entries
        ]

    def clear_memory(self) -> None:
        """Wipe all conversation memory."""
        self._save_entries([])

    def get_summary_stats(self) -> Dict[str, Any]:
        """Return summary statistics of the conversation memory."""
        entries = self._load_entries()
        if not entries:
            return {"total": 0, "by_type": {}, "by_status": {}, "unique_files": 0}

        by_type: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        all_files: set = set()

        for e in entries:
            tt = e.get("task_type", "unknown")
            by_type[tt] = by_type.get(tt, 0) + 1
            fs = e.get("final_status", "unknown")
            by_status[fs] = by_status.get(fs, 0) + 1
            all_files.update(e.get("files_modified", []))

        return {
            "total": len(entries),
            "by_type": by_type,
            "by_status": by_status,
            "unique_files": len(all_files),
        }
