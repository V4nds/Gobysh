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
from typing import Dict, Any, List, Optional


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
            with self._lock:
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

