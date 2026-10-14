"""
State Memory Manager for Goby Framework.
Manages persistent memory, error tracking, state locks, and dynamic context injection.
"""

import json
import os
import threading
import time
import logging
import copy
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path


CODE_EXTENSIONS = (
    ".py", ".pyw", ".js", ".jsx", ".ts", ".tsx",
    ".kt", ".kts", ".rs", ".html", ".css", ".yml", ".yaml",
)
IGNORED_PATTERNS = (
    ".git", "__pycache__", ".venv", "node_modules", ".pytest_cache",
    "build", ".gradle", "dist", "target", ".kilo", ".superpowers",
)


def calculate_workspace_code_hash(workspace_dir: str) -> str:
    """
    Computes a deterministic, cryptographic SHA-256 fingerprint across all active
    code files in the workspace. Used to verify Dynamic Test Evidence Freshness.
    """
    workspace_path = Path(workspace_dir).resolve()
    if not workspace_path.is_dir():
        return hashlib.sha256(b"").hexdigest()

    entries = []
    for root, dirs, files in os.walk(str(workspace_path)):
        dirs[:] = [d for d in dirs if not any(ign in d for ign in IGNORED_PATTERNS)]
        for f in sorted(files):
            if any(f.endswith(ext) for ext in CODE_EXTENSIONS):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, str(workspace_path)).replace("\\", "/")
                try:
                    with open(full_path, "rb") as fp:
                        content_hash = hashlib.sha256(fp.read()).hexdigest()
                    entries.append(f"{rel_path}:{content_hash}")
                except (OSError, PermissionError):
                    pass

    if not entries:
        return hashlib.sha256(b"").hexdigest()

    entries.sort()
    composite_str = "\n".join(entries).encode("utf-8")
    return hashlib.sha256(composite_str).hexdigest()


class StateMemoryManager:
    """
    Manages persistent JSON state with file locking and thread safety.
    """

    def __init__(self, memory_file_path: str = "cognitive_map.json"):
        self.memory_file_path = os.path.abspath(memory_file_path)
        self._lock = threading.RLock()
        self._cached_state = None
        self._ensure_memory_file()

    def _ensure_memory_file(self) -> None:
        """Ensures cognitive map file exists with valid structure."""
        with self._lock:
            if not os.path.exists(self.memory_file_path):
                default_state = {
                    "version": "1.0.0",
                    "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "active_context": {
                        "task_id": None,
                        "error_count": 0,
                        "current_state": "IDLE"
                    },
                    "concepts": {
                        "godel_bypass": {
                            "path": "SKILL.md",
                            "activation_weight": 1.0
                        }
                    },
                    "error_history": [],
                    "temporal_state": {}
                }
                self.save_state(default_state)

    def load_state(self) -> Dict[str, Any]:
        """Loads and returns the JSON state in a thread-safe manner."""
        with self._lock:
            if self._cached_state is not None:
                return copy.deepcopy(self._cached_state)
            if not os.path.exists(self.memory_file_path):
                self._ensure_memory_file()

            try:
                with open(self.memory_file_path, "r", encoding="utf-8") as f:
                    self._cached_state = json.load(f)
                    return copy.deepcopy(self._cached_state)
            except (json.JSONDecodeError, OSError) as e:
                logging.warning(f"Failed to load state memory from {self.memory_file_path}: {e}")
                self._cached_state = {
                    "version": "1.0.0",
                    "error": "Corrupted memory state re-initialized",
                    "error_history": [],
                    "temporal_state": {}
                }
                return copy.deepcopy(self._cached_state)

    def save_state(self, state_data: Dict[str, Any]) -> bool:
        """Saves JSON state in a thread-safe manner."""
        with self._lock:
            # Work on a copy to prevent mutation during serialization
            state_copy = copy.deepcopy(state_data)
            state_copy["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            tmp_path = f"{self.memory_file_path}.{threading.get_ident()}.tmp"
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(state_copy, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logging.warning(f"Failed to serialize state memory to {self.memory_file_path}: {e}")
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
                return False

            for _attempt in range(5):
                try:
                    os.replace(tmp_path, self.memory_file_path)
                    self._cached_state = copy.deepcopy(state_copy)
                    return True
                except (PermissionError, OSError):
                    pass
                time.sleep(0.005)

            logging.warning(f"Failed to save state memory after multiple retries to {self.memory_file_path}")
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            return False

    def record_error(self, error_type: str, details: str, code_context: Optional[str] = None) -> Dict[str, Any]:
        """Records an error event into persistent state memory."""
        with self._lock:
            state = self.load_state()
            error_entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "type": error_type,
                "details": details,
                "code_context": code_context
            }

            if "error_history" not in state:
                state["error_history"] = []
            state["error_history"].append(error_entry)

            # Increment error count in active context
            active_ctx = state.get("active_context", {})
            active_ctx["error_count"] = active_ctx.get("error_count", 0) + 1
            state["active_context"] = active_ctx

            self.save_state(state)
            return error_entry

    def set_temporal_variable(self, key: str, value: Any) -> None:
        """Sets a dynamic temporal variable in the state (Representation Expansion)."""
        with self._lock:
            state = self.load_state()
            if "temporal_state" not in state:
                state["temporal_state"] = {}
            state["temporal_state"][key] = value
            self.save_state(state)

    # -----------------------------------------------------------------------
    # Unresolved File Error Ledger (Closed-Loop Awareness)
    # -----------------------------------------------------------------------

    def record_file_validation(
        self,
        file_path: str,
        passed: bool,
        blocked: bool = False,
        gate: Optional[str] = None,
        summary: str = "",
        signals: Optional[List[Dict[str, Any]]] = None,
        error_message: str = "",
        code_hash: str = "",
    ) -> None:
        """
        Records the latest validation result for a file into the persistent
        ledger. A file that fails validation stays in the ledger (unresolved)
        until a later validation of the same file passes.
        """
        with self._lock:
            state = self.load_state()
            ledger = state.setdefault("file_validation", {})
            abs_path = os.path.abspath(file_path)
            ledger[abs_path] = {
                "file": abs_path,
                "passed": bool(passed),
                "blocked": bool(blocked),
                "gate": gate,
                "summary": summary,
                "signals": signals or [],
                "message": error_message,
                "code_hash": code_hash,
                "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            self.save_state(state)

    def get_unresolved_errors(self) -> List[Dict[str, Any]]:
        """
        Returns all files in the ledger whose last validation failed.
        These are the errors the agent MUST resolve before claiming completion.
        """
        with self._lock:
            state = self.load_state()
            ledger = state.get("file_validation", {})
            return [entry for entry in ledger.values() if not entry.get("passed")]

    def clear_validation_ledger(self) -> None:
        """Wipes the file validation ledger (used for cleanup / re-baseline)."""
        with self._lock:
            state = self.load_state()
            state["file_validation"] = {}
            self.save_state(state)

    def get_temporal_variable(self, key: str, default: Any = None) -> Any:
        """Gets a dynamic temporal variable from state."""
        with self._lock:
            state = self.load_state()
            return state.get("temporal_state", {}).get(key, default)

    def clear_session_errors(self) -> None:
        """Clears active session error counter."""
        with self._lock:
            state = self.load_state()
            if "active_context" in state:
                state["active_context"]["error_count"] = 0
                state["active_context"]["current_state"] = "IDLE"
            self.save_state(state)

    def recover_interrupted_session(self) -> Dict[str, Any]:
        """
        Recovers state after an abrupt application crash or unexpected exit.
        Returns the active context and last known checkpoint.
        """
        with self._lock:
            state = self.load_state()
            active_ctx = state.get("active_context", {})
            
            # If application crashed while running a task
            if active_ctx.get("current_state") == "RUNNING":
                active_ctx["current_state"] = "INTERRUPTED_RECOVERED"
                active_ctx["recovery_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                state["active_context"] = active_ctx
                self.save_state(state)
                
            return {
                "recovered_state": active_ctx.get("current_state"),
                "last_task_id": active_ctx.get("task_id"),
                "error_count": active_ctx.get("error_count", 0),
                "temporal_variables": state.get("temporal_state", {})
            }

    # -----------------------------------------------------------------------
    # Dynamic Test Evidence & Epistemic Obligation Ledger (Goby v5.5)
    # -----------------------------------------------------------------------

    def record_test_execution(
        self,
        command: str,
        exit_code: int,
        duration_seconds: float = 0.0,
        output_summary: str = "",
        workspace_hash: str = "",
    ) -> Dict[str, Any]:
        """
        Records a test runner execution with cryptographic workspace fingerprint.
        Establishes ground truth verification evidence.
        """
        with self._lock:
            state = self.load_state()
            evidence_ledger = state.setdefault("evidence_ledger", {})
            history = evidence_ledger.setdefault("test_executions", [])

            timestamp_str = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
            short_hash = workspace_hash[:8] if workspace_hash else "00000000"
            evidence_id = f"EV-{timestamp_str}-{short_hash}"

            record = {
                "evidence_id": evidence_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "command": command,
                "exit_code": int(exit_code),
                "duration_seconds": round(float(duration_seconds), 3),
                "output_summary": output_summary[:500] if output_summary else "",
                "workspace_hash": workspace_hash,
                "status": "PASS" if exit_code == 0 else "FAIL",
            }
            history.append(record)
            evidence_ledger["last_test"] = record
            self.save_state(state)
            return record

    def get_last_test_execution(self) -> Optional[Dict[str, Any]]:
        """Returns the most recent test execution record, if any."""
        with self._lock:
            state = self.load_state()
            return state.get("evidence_ledger", {}).get("last_test")

    def record_obligation(
        self,
        claim: str,
        source: str = "user_prompt",
        target_files: Optional[List[str]] = None,
        required_authority: str = "dynamic_test",
    ) -> str:
        """
        Registers a formal task obligation (extracted from user prompt or Prompt Spider).
        Obligations must be resolved with empirical evidence before session exit.
        """
        with self._lock:
            state = self.load_state()
            ledger = state.setdefault("obligation_ledger", {})

            # Deterministic ID based on claim string
            h = hashlib.sha256(claim.encode("utf-8")).hexdigest()[:8]
            ob_id = f"ob_{h}"

            # If obligation already exists, don't overwrite if already verified
            if ob_id in ledger and ledger[ob_id].get("status") == "VERIFIED":
                return ob_id

            ledger[ob_id] = {
                "obligation_id": ob_id,
                "claim": claim,
                "source": source,
                "target_files": target_files or [],
                "required_authority": required_authority,
                "status": "PENDING",
                "evidence_id": None,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "resolved_at": None,
            }
            self.save_state(state)
            return ob_id

    def resolve_obligation(
        self,
        obligation_id: str,
        evidence_id: Optional[str] = None,
        status: str = "VERIFIED",
    ) -> bool:
        """
        Marks an obligation as VERIFIED (or FAILED) with an associated evidence_id.
        """
        with self._lock:
            state = self.load_state()
            ledger = state.get("obligation_ledger", {})
            if obligation_id in ledger:
                ledger[obligation_id]["status"] = status
                ledger[obligation_id]["evidence_id"] = evidence_id
                ledger[obligation_id]["resolved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                self.save_state(state)
                return True
            return False

    def get_unresolved_obligations(self) -> List[Dict[str, Any]]:
        """
        Returns all obligations currently in PENDING, UNKNOWN, or FAILED status.
        """
        with self._lock:
            state = self.load_state()
            ledger = state.get("obligation_ledger", {})
            return [ob for ob in ledger.values() if ob.get("status") != "VERIFIED"]

    def get_all_obligations(self) -> List[Dict[str, Any]]:
        """Returns all recorded obligations in the ledger."""
        with self._lock:
            state = self.load_state()
            ledger = state.get("obligation_ledger", {})
            return list(ledger.values())

    def evaluate_exit_gate(self, workspace_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluates the comprehensive 3-Pillar Epistemic Exit Gate:
        1. Static Code Health: Zero unresolved file errors in CCR validation ledger.
        2. Dynamic Test Freshness: Cryptographic workspace hash matches last passing test execution.
        3. Task Obligations: Zero pending or unknown obligations from Prompt Spider / user intent.
        """
        with self._lock:
            # Pillar 1: Static Code Health
            unresolved_errors = self.get_unresolved_errors()
            static_passed = len(unresolved_errors) == 0

            # Pillar 3: Task Obligations & Residual Unknowns (evaluated first to inform freshness)
            open_obligations = self.get_unresolved_obligations()
            obligations_passed = len(open_obligations) == 0

            # Pillar 2: Dynamic Test Freshness
            if workspace_dir:
                target_ws = os.path.abspath(workspace_dir)
            else:
                target_ws = os.path.dirname(os.path.abspath(self.memory_file_path))
                if not target_ws or target_ws == os.path.abspath("."):
                    target_ws = os.getcwd()

            current_whash = calculate_workspace_code_hash(target_ws)
            last_test = self.get_last_test_execution()

            if not last_test:
                # If no test has been recorded in this ledger
                if open_obligations:
                    freshness = "MISSING"
                    dynamic_passed = False
                else:
                    freshness = "UNRECORDED"
                    dynamic_passed = True
            else:
                if last_test.get("workspace_hash") == current_whash:
                    if last_test.get("exit_code") == 0:
                        freshness = "FRESH"
                        dynamic_passed = True
                    else:
                        freshness = "FAILED"
                        dynamic_passed = False
                else:
                    freshness = "STALE"
                    dynamic_passed = False

            # Overall verdict
            overall_passed = static_passed and dynamic_passed and obligations_passed
            verdict = "PASS" if overall_passed else "BLOCKED"

            block_reasons = []
            if not static_passed:
                block_reasons.append(
                    f"Static Code Health: {len(unresolved_errors)} unresolved CCR file error(s)."
                )
            if not dynamic_passed:
                if freshness == "STALE":
                    block_reasons.append(
                        "Dynamic Test Freshness: Workspace code modified after last test execution (STALE evidence). "
                        "Run `goby audit` or test command to refresh verification."
                    )
                elif freshness == "MISSING":
                    block_reasons.append(
                        "Dynamic Test Freshness: Task obligations exist but no test verification has been executed. "
                        "Run `goby audit` or test suite before completing task."
                    )
                elif freshness == "FAILED":
                    block_reasons.append(
                        f"Dynamic Test Freshness: Last test execution failed with exit code {last_test.get('exit_code')}."
                    )
            if not obligations_passed:
                block_reasons.append(
                    f"Task Obligations: {len(open_obligations)} unresolved obligation(s) pending empirical verification."
                )

            return {
                "passed": overall_passed,
                "verdict": verdict,
                "pillars": {
                    "static_integrity": {
                        "passed": static_passed,
                        "unresolved": unresolved_errors,
                    },
                    "dynamic_evidence": {
                        "passed": dynamic_passed,
                        "freshness": freshness,
                        "last_test": last_test,
                        "current_workspace_hash": current_whash,
                    },
                    "obligations": {
                        "passed": obligations_passed,
                        "open_obligations": open_obligations,
                    },
                },
                "block_reasons": block_reasons,
            }

