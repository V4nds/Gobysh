"""
Antigravity Lifecycle Hooks for Goby Framework v5.0.0.
Provides mechanical, aggressive-autonomous execution integration:
- PostToolUse: Automatically intercepts file writes/edits, verifies code via CCR,
  and records status to Unresolved Error Ledger (cognitive_map.json).
- PreInvocation: Injects active ledger warnings directly into agent's context window.
- Stop: Mechanically blocks the agent from finishing if unresolved errors exist.
"""

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
_current_dir = Path(__file__).resolve().parent
_project_root = _current_dir.parent
for _p in [str(_project_root), str(_current_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


CODE_EXTENSIONS = (".py", ".js", ".ts", ".jsx", ".tsx", ".css", ".html", ".kt", ".kts")
IGNORED_PATTERNS = (".venv", ".git", "__pycache__", ".kilo", "node_modules", ".pytest_cache", "build", ".gradle")


def normalize_file_path(path_str: str, base_dir: Optional[str] = None) -> Optional[str]:
    """Clean up quotes, resolve path, and ensure it exists."""
    if not path_str:
        return None
    cleaned = path_str.strip('"\' \t\r\n')
    if not cleaned:
        return None
    p = Path(cleaned)
    if not p.is_absolute() and base_dir:
        p = Path(base_dir) / p
    try:
        resolved = p.resolve()
        if resolved.is_file():
            return str(resolved)
    except Exception:
        pass
    return None


def extract_modified_files(payload: Dict[str, Any]) -> List[str]:
    """
    Extracts modified code files from:
    1. Tool call args in transcriptPath (TargetFile parameter)
    2. Git status porcelain for unstaged/staged modified code files
    """
    candidates = set()
    workspace = None
    workspace_paths = payload.get("workspacePaths") or []
    if workspace_paths and os.path.isdir(workspace_paths[0]):
        workspace = workspace_paths[0]
    else:
        workspace = str(_project_root)

    # 1. Transcript extraction
    transcript_path = payload.get("transcriptPath")
    if transcript_path and os.path.isfile(transcript_path):
        try:
            with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            for line in reversed(lines[-25:]):
                try:
                    entry = json.loads(line)
                    for call in entry.get("tool_calls", []):
                        args = call.get("args", {})
                        if isinstance(args, dict):
                            target = args.get("TargetFile")
                            if target:
                                norm = normalize_file_path(str(target), base_dir=workspace)
                                if norm:
                                    candidates.add(norm)
                except Exception:
                    continue
        except Exception:
            pass

    # 2. Git status extraction
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if len(line) > 3:
                    rel = line[3:].strip()
                    if " -> " in rel:
                        rel = rel.split(" -> ")[-1].strip()
                    norm = normalize_file_path(rel, base_dir=workspace)
                    if norm:
                        candidates.add(norm)
    except Exception:
        pass

    # Filter candidates
    valid_files = []
    for f in candidates:
        if any(ign in f for ign in IGNORED_PATTERNS):
            continue
        if any(f.endswith(ext) for ext in CODE_EXTENSIONS):
            valid_files.append(f)

    return sorted(valid_files)


def handle_post_tool_use(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    PostToolUse hook handler.
    Validates any modified code files via CCR, injects aggressive telemetry to stderr,
    and updates cognitive_map.json ledger.
    Returns {} as required by Antigravity PostToolUse spec.
    """
    from .ccr_engine import CognitiveControlRoom
    from .state_memory import StateMemoryManager
    from .cli import validate_filepath

    workspace_paths = payload.get("workspacePaths") or []
    workspace = workspace_paths[0] if workspace_paths and os.path.isdir(workspace_paths[0]) else str(_project_root)

    old_cwd = os.getcwd()
    try:
        os.chdir(workspace)
        ccr = CognitiveControlRoom()
        memory = StateMemoryManager("cognitive_map.json")

        files = extract_modified_files(payload)
        for filepath in files:
            rel = os.path.relpath(filepath, workspace)
            try:
                passed = validate_filepath(filepath, ccr, memory=memory, verbose=False)

                # Extract Architectural Depth Telemetry for Python files
                mdi_telemetry = ""
                if filepath.endswith((".py", ".pyw")):
                    try:
                        from .semantics.depth_engine import DepthEngine
                        with open(filepath, "r", encoding="utf-8") as f:
                            code_str = f.read()
                        m = DepthEngine().analyze_source(code_str, filepath)
                        mdi_telemetry = f" | MDI: {m.mdi_score:.2f} [{m.classification}]"
                    except Exception:
                        pass

                if passed:
                    sys.stderr.write(f"[GOBY TELEMETRY ✅] {rel}{mdi_telemetry} passed all CCR Gates.\n")
                else:
                    unresolved = memory.get_unresolved_errors()
                    err = next((e for e in unresolved if os.path.abspath(e.get("file", "")) == os.path.abspath(filepath)), None)
                    gate_name = err.get("gate", "CCR") if err else "CCR"
                    msg = err.get("message", "Validation failed") if err else "Validation failed"
                    sys.stderr.write(f"[GOBY 🚨 HARD GATE BLOCKED] {rel}{mdi_telemetry} failed [{gate_name}]: {msg}\n")
            except Exception as e:
                sys.stderr.write(f"[GOBY TELEMETRY ERROR] Validation error for {rel}: {e}\n")
    finally:
        os.chdir(old_cwd)

    return {}


def handle_pre_invocation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    PreInvocation hook handler.
    Checks the 3-Pillar Epistemic Exit Gate status in cognitive_map.json.
    If any pillar is blocked, injects an aggressive warning message into the agent's context window.
    """
    from .state_memory import StateMemoryManager

    workspace_paths = payload.get("workspacePaths") or []
    workspace = workspace_paths[0] if workspace_paths and os.path.isdir(workspace_paths[0]) else str(_project_root)

    memory_path = os.path.join(workspace, "cognitive_map.json")
    if not os.path.isfile(memory_path):
        return {}

    try:
        memory = StateMemoryManager(memory_path)
        verdict = memory.evaluate_exit_gate(workspace_dir=workspace)
        if verdict["passed"]:
            return {}

        p1 = verdict["pillars"]["static_integrity"]
        p2 = verdict["pillars"]["dynamic_evidence"]
        p3 = verdict["pillars"]["obligations"]

        items = []
        if not p1["passed"]:
            items.append(f"  [1/3] Static Code Health: [BLOCKED] ({len(p1['unresolved'])} unresolved errors):")
            for e in p1["unresolved"][:5]:
                fname = os.path.basename(e.get("file", "unknown"))
                gate = e.get("gate", "CCR")
                msg = e.get("message", "Validation failed")
                items.append(f"        - {fname} [{gate}]: {msg}")

        if not p2["passed"]:
            items.append(f"  [2/3] Dynamic Test Freshness: [{p2['freshness']}]")

        if not p3["passed"]:
            items.append(f"  [3/3] Task Obligation Ledger: [BLOCKED] ({len(p3['open_obligations'])} open):")
            for ob in p3["open_obligations"][:5]:
                items.append(f"        - [{ob.get('status', 'PENDING')}] {ob.get('obligation_id', '')}: {ob.get('claim', '')}")

        warning_text = (
            f"🚨 [GOBY AGGRESSIVE TELEMETRY & HARD GATE ALERT]\n"
            f"The Epistemic Exit Gate is currently [BLOCKED]:\n"
            + "\n".join(items) + "\n\n"
            "⚡ MANDATORY DIALECTICAL ACTION:\n"
            "1. You CANNOT declare completion (goby gate & Antigravity Stop hook are mechanically ARMED).\n"
            "2. If caused by [ARCHITECTURAL_DEPTH]: Collapse shallow wrappers into deep modules (Ousterhout's Law).\n"
            "3. Run `goby audit` or test suite to verify claims and prove dynamic freshness before ending turn."
        )

        return {
            "injectSteps": [
                {
                    "ephemeralMessage": warning_text
                }
            ]
        }
    except Exception as e:
        sys.stderr.write(f"[Goby Hook] PreInvocation check failed: {e}\n")
        return {}


def handle_stop_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stop hook handler.
    Blocks the agent from stopping if any of the 3 Epistemic Exit Gate pillars fail
    (Static code errors, Stale/missing test freshness, or Unresolved task obligations).
    """
    from .state_memory import StateMemoryManager

    workspace_paths = payload.get("workspacePaths") or []
    workspace = workspace_paths[0] if workspace_paths and os.path.isdir(workspace_paths[0]) else str(_project_root)

    memory_path = os.path.join(workspace, "cognitive_map.json")
    if not os.path.isfile(memory_path):
        return {"decision": "allow"}

    try:
        memory = StateMemoryManager(memory_path)
        verdict = memory.evaluate_exit_gate(workspace_dir=workspace)
        if verdict["passed"]:
            return {"decision": "allow"}

        p1 = verdict["pillars"]["static_integrity"]
        p2 = verdict["pillars"]["dynamic_evidence"]
        p3 = verdict["pillars"]["obligations"]

        lines = [
            "🚨 [GOBY 3-PILLAR EXIT GATE BLOCKED] Cannot finish session due to incomplete verification:",
            f"  [1/3] Static Code Health:     {'[PASS]' if p1['passed'] else '[BLOCKED]'} ({len(p1['unresolved'])} unresolved errors)",
        ]
        for e in p1["unresolved"][:5]:
            fname = os.path.basename(e.get("file", "unknown"))
            gate = e.get("gate", "CCR")
            msg = e.get("message", "Validation failed")
            lines.append(f"        - {fname} [{gate}]: {msg}")

        last_ev = p2.get("last_test")
        ev_id = f" ({last_ev.get('evidence_id')})" if last_ev else ""
        lines.append(f"  [2/3] Dynamic Test Freshness: [{p2['freshness']}]{ev_id}")

        lines.append(f"  [3/3] Task Obligation Ledger: {'[PASS]' if p3['passed'] else '[BLOCKED]'} ({len(p3['open_obligations'])} open)")
        for ob in p3["open_obligations"][:5]:
            lines.append(f"        - [{ob.get('status', 'PENDING')}] {ob.get('obligation_id', '')}: {ob.get('claim', '')}")

        lines.append("\nBlock Reasons:")
        for r in verdict["block_reasons"]:
            lines.append(f"  - {r}")

        lines.append("\n⚡ MANDATORY ACTION:")
        lines.append("  -> Fix code issues and run `goby audit` (or your test suite) to establish fresh verification before completing.")

        block_reason = "\n".join(lines)

        return {
            "decision": "continue",
            "reason": block_reason
        }
    except Exception as e:
        sys.stderr.write(f"[Goby Hook] Stop gate check failed: {e}\n")
        return {"decision": "allow"}


def get_hooks_config() -> Dict[str, Any]:
    """Returns the standardized .agents/hooks.json configuration dictionary."""
    is_windows = os.name == "nt"
    if is_windows:
        post_cmd = "goby hooks post-tool"
        pre_cmd = "goby hooks pre-invocation"
        stop_cmd = "goby hooks stop-gate"
    else:
        post_cmd = "goby hooks post-tool"
        pre_cmd = "goby hooks pre-invocation"
        stop_cmd = "goby hooks stop-gate"

    return {
        "goby-lifecycle": {
            "PostToolUse": [
                {
                    "matcher": "write_to_file|replace_file_content|multi_replace_file_content",
                    "hooks": [
                        {
                            "type": "command",
                            "command": post_cmd,
                            "timeout": 15
                        }
                    ]
                }
            ],
            "PreInvocation": [
                {
                    "type": "command",
                    "command": pre_cmd,
                    "timeout": 10
                }
            ],
            "Stop": [
                {
                    "type": "command",
                    "command": stop_cmd,
                    "timeout": 10
                }
            ]
        }
    }


def install_lifecycle_hooks(target_dir: Optional[str] = None) -> Dict[str, Any]:
    """Installs .agents/hooks.json in the target directory (default: workspace root)."""
    base = Path(target_dir or os.getcwd()).resolve()
    agents_dir = base / ".agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    hooks_file = agents_dir / "hooks.json"

    config = get_hooks_config()
    with open(hooks_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    return {
        "installed": True,
        "path": str(hooks_file),
        "events": ["PostToolUse", "PreInvocation", "Stop"]
    }


def cli_entry(action: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> None:
    """CLI dispatcher for Antigravity hook events."""
    if not action:
        if len(sys.argv) > 1:
            action = sys.argv[1].lower()
        else:
            action = "status"

    if payload is None:
        payload = {}
        if action not in ("status", "install") and not sys.stdin.isatty():
            try:
                raw = sys.stdin.read().strip()
                if raw:
                    payload = json.loads(raw)
            except Exception as e:
                sys.stderr.write(f"[Goby Hook] Failed to parse stdin JSON: {e}\n")

    if action in ("post-tool", "posttooluse"):
        res = handle_post_tool_use(payload)
        sys.stdout.write(json.dumps(res))
    elif action in ("pre-invocation", "preinvocation"):
        res = handle_pre_invocation(payload)
        sys.stdout.write(json.dumps(res))
    elif action in ("stop-gate", "stop"):
        res = handle_stop_gate(payload)
        sys.stdout.write(json.dumps(res))
    elif action == "install":
        res = install_lifecycle_hooks()
        sys.stdout.write(json.dumps(res, indent=2))
    elif action == "status":
        hooks_file = Path(os.getcwd()) / ".agents" / "hooks.json"
        if not hooks_file.exists():
            hooks_file = _project_root / ".agents" / "hooks.json"
        status = {
            "installed": hooks_file.exists(),
            "path": str(hooks_file) if hooks_file.exists() else None,
            "version": "5.4.0"
        }
        sys.stdout.write(json.dumps(status, indent=2))
    else:
        sys.stderr.write(f"Unknown hook action: {action}\n")
        sys.stdout.write(json.dumps({}))


if __name__ == "__main__":
    cli_entry()
