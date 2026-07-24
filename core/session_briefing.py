"""
Session Briefing & Auto-Resume Engine for Goby Framework.
Eliminates context loss, prevents AI hallucination upon session restart,
and automatically generates human-readable session briefings.
"""

import json
import os
import time
from typing import Dict, Any, Optional
from .state_memory import StateMemoryManager


class SessionBriefingEngine:
    """
    Handles automatic session snapshots, human-readable briefings,
    and zero-hallucination auto-resume protocols.
    """

    def __init__(self, workspace_dir: Optional[str] = None, memory_mgr: Optional[StateMemoryManager] = None):
        self.workspace_dir = workspace_dir or os.getcwd()
        self.briefing_file = os.path.join(self.workspace_dir, "SESSION_BRIEFING.md")
        self.memory_mgr = memory_mgr or StateMemoryManager(
            memory_file_path=os.path.join(self.workspace_dir, "cognitive_map.json")
        )

    def create_snapshot(self, last_completed_task: str, current_in_progress: str, next_action: str) -> str:
        """
        Creates a structured session snapshot and writes SESSION_BRIEFING.md.
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S local", time.localtime())
        
        # Save structured state
        state = self.memory_mgr.load_state()
        state["active_context"] = {
            "last_completed_task": last_completed_task,
            "current_in_progress": current_in_progress,
            "next_action": next_action,
            "current_state": "PAUSED_SAVED",
            "snapshot_timestamp": timestamp
        }
        self.memory_mgr.save_state(state)

        # Generate human-readable Markdown briefing
        briefing_content = f"""# 📍 Goby Session Briefing & Progress Snapshot
*Auto-Generated Snapshot Timestamp: {timestamp}*

---

### 🟢 Completed Before Pause/Shutdown:
- **{last_completed_task}**

### 🔄 In-Progress State:
- **{current_in_progress}**

### 🎯 Next Immediate Action Ready:
- **{next_action}**

---
> 💡 *Note: Goby has locked this state. You do NOT need to re-explain context upon restart.*
"""
        with open(self.briefing_file, "w", encoding="utf-8") as f:
            f.write(briefing_content)

        return self.briefing_file

    def auto_resume_briefing(self) -> Dict[str, Any]:
        """
        Called upon restarting session. Ingests last snapshot and returns exact briefing status.
        """
        state = self.memory_mgr.load_state()
        active_ctx = state.get("active_context", {})

        has_briefing_file = os.path.exists(self.briefing_file)

        return {
            "has_saved_snapshot": bool(active_ctx.get("snapshot_timestamp")),
            "last_completed_task": active_ctx.get("last_completed_task", "N/A"),
            "current_in_progress": active_ctx.get("current_in_progress", "N/A"),
            "next_action": active_ctx.get("next_action", "N/A"),
            "snapshot_timestamp": active_ctx.get("snapshot_timestamp", "N/A"),
            "briefing_file_path": self.briefing_file if has_briefing_file else None,
            "resume_status": "READY_TO_CONTINUE"
        }
