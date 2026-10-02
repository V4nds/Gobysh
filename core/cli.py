"""
CLI Entrypoint for Goby Framework v5.0.0.
Run using: goby audit | goby benchmark | goby check <code|filepath> | goby install-hook | goby watch | goby status | goby intent | goby recall | goby save
"""

import hashlib
import os
import re
import sys
import time
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional
from .ccr_engine import CognitiveControlRoom
from .state_memory import StateMemoryManager


# ---------------------------------------------------------------------------
# Triage & unified output helpers (single source of truth for `goby check`/`verify`)
# ---------------------------------------------------------------------------

_CODE_MARKERS = (
    "def ", "class ", "import ", "from ", "return ", "if ", "elif ", "else:",
    "for ", "while ", "lambda", "try:", "except", "with ", "async ", "yield",
    "global ", "raise ", "assert ", "function ", "const ", "let ", "var ", "=>",
    "console.", "window.", "document.", "print(", "int(", "str(", "list(",
)

_ALWAYS_CODE_EXTENSIONS = (".py", ".pyw", ".js", ".jsx", ".ts", ".tsx", ".css", ".html", ".json", ".yaml", ".yml", ".toml")


def _looks_like_code(content: str) -> bool:
    """Heuristic triage: is the content code or prose/documentation?"""
    stripped = content.strip()
    if not stripped:
        return False

    if any(marker in stripped for marker in _CODE_MARKERS):
        return True

    if any(ch in stripped for ch in "{};"):
        return True

    # Assignment pattern: identifier = value  (e.g. "x = 10")
    if re.search(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*[^=]", stripped, re.MULTILINE):
        return True

    # Block header line ending with ':' (Python)
    if any(
        line.rstrip().endswith(":") and not line.strip().startswith(("#", "//"))
        for line in content.splitlines()
    ):
        return True

    return False


def _neuron_location(sig) -> str:
    line = None
    if sig.evidence and isinstance(sig.evidence, dict):
        line = sig.evidence.get("line") or sig.evidence.get("first_line")
    if line:
        return f" (line {line})"
    return ""


def _report_signals(ccr, signals, verbose: bool = False) -> bool:
    """Print one consistent, non-contradictory verdict for a set of signals."""
    res = ccr.evaluate_signals(signals)

    def render(sig):
        status = "PASS" if sig.passed else "FAIL"
        print(f"  [{sig.neuron_name}] {status}{_neuron_location(sig)} - {sig.message}")
        if not sig.passed and sig.suggestion:
            print(f"     Hint: {sig.suggestion}")

    if verbose:
        for sig in signals:
            render(sig)
    else:
        for sig in signals:
            if not sig.passed:
                render(sig)

    if res["blocked"]:
        print(f"[BLOCKED] {res['summary']}")
        return False

    print("[PASS] All gates passed.")
    return True


def install_git_hooks():
    git_dir = Path(".git")
    if not git_dir.exists():
        print("[ERROR] .git directory not found. Must run from root of a git repository.")
        sys.exit(1)

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Pre-commit hook script
    pre_commit_script = r"""#!/bin/sh
# Goby Zero-Bypass Pre-Commit Quality Gate
echo "[Goby Gate] Validating staged files..."

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|ts)$')

if [ -z "$STAGED_FILES" ]; then
    echo "[Goby Gate] No Python/JS/TS files staged."
    exit 0
fi

FAILED=0
for FILE in $STAGED_FILES; do
    if [ -f "$FILE" ]; then
        echo "[Goby Check] Validating $FILE..."
        goby check "$FILE"
        if [ $? -ne 0 ]; then
            echo "[Goby Gate] REJECTED: $FILE failed CCR Hard Gate validation."
            FAILED=1
        fi
    fi
done

if [ $FAILED -ne 0 ]; then
    echo "=========================================================="
    echo "[ERROR] GOBY HARD GATE FAILURE: COMMIT REJECTED"
    echo "Fix CCR errors or run 'goby check <file>' before committing."
    echo "=========================================================="
    exit 1
fi

echo "[Goby Gate] All staged files passed CCR Hard Gates."
exit 0
"""

    pre_push_script = """#!/bin/sh
# Goby Zero-Bypass Pre-Push Audit Gate
echo "[Goby Audit Gate] Running empirical test suite before push..."
goby audit
if [ $? -ne 0 ]; then
    echo "=========================================================="
    echo "[ERROR] GOBY AUDIT FAILURE: PUSH REJECTED"
    echo "Ensure all unit tests pass before pushing."
    echo "=========================================================="
    exit 1
fi
echo "[Goby Audit Gate] Audit passed. Proceeding with push."
exit 0
"""

    pre_commit_path = hooks_dir / "pre-commit"
    pre_push_path = hooks_dir / "pre-push"

    with open(pre_commit_path, "w", encoding="utf-8") as f:
        f.write(pre_commit_script)

    with open(pre_push_path, "w", encoding="utf-8") as f:
        f.write(pre_push_script)

    # Make executable on Unix/Mac if applicable
    try:
        os.chmod(pre_commit_path, 0o755)
        os.chmod(pre_push_path, 0o755)
    except Exception:
        pass

    print("[SUCCESS] Goby Git Pre-Commit & Pre-Push Hooks installed successfully into .git/hooks/")
    print("  -> .git/hooks/pre-commit (CCR file check)")
    print("  -> .git/hooks/pre-push   (Full audit suite)")

    # Install Antigravity lifecycle hooks
    try:
        from .hooks import install_lifecycle_hooks
        res = install_lifecycle_hooks()
        print("[SUCCESS] Goby Antigravity Lifecycle Hooks installed into .agents/hooks.json")
        print("  -> PostToolUse: Intercepts file writes & auto-validates CCR")
        print("  -> PreInvocation: Injects active error ledger warnings into model prompt")
        print("  -> Stop: Mechanically blocks completion if ledger has unresolved errors")
    except Exception as e:
        print(f"[WARNING] Could not install .agents/hooks.json: {e}")


def run_watch_loop(memory: StateMemoryManager = None):
    print("[GOBY WATCH] Starting Active CCR Workspace Watcher...")
    print("Monitoring .py, .js, .ts file modifications... (Press Ctrl+C to stop)")
    ccr = CognitiveControlRoom()

    file_mtimes = {}

    def scan_files():
        for root, _, files in os.walk("."):
            if ".git" in root or ".venv" in root or "__pycache__" in root or ".kilo" in root:
                continue
            for file in files:
                if file.endswith((".py", ".js", ".ts")):
                    filepath = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(filepath)
                        if filepath in file_mtimes and file_mtimes[filepath] != mtime:
                            file_mtimes[filepath] = mtime
                            validate_filepath(filepath, ccr, memory=memory)
                        elif filepath not in file_mtimes:
                            file_mtimes[filepath] = mtime
                    except Exception:
                        pass

    try:
        while True:
            scan_files()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[GOBY WATCH] Active Watcher stopped.")


def validate_filepath(target_path: str, ccr: CognitiveControlRoom, memory: StateMemoryManager = None, verbose: bool = False, contract: Any = None) -> bool:
    print(f"[GOBY CHECK] Validating file: {target_path}")
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        print(f"[ERROR] Could not read file {target_path}: {e}")
        return False

    # Triage: skip non-code content (prose/documentation) entirely — no neurons.
    if not _looks_like_code(code):
        print("[GOBY] Content is prose / not code (triage SKIP) — verification skipped, no neurons executed.")
        return True

    signals = []
    if target_path.endswith((".js", ".ts", ".jsx", ".tsx")):
        syn = ccr.neuron_js_syntax_check(code)
        signals.append(syn)
        signals.append(ccr.neuron_taste_design_check(code))
    elif target_path.endswith((".css", ".html")):
        signals.append(ccr.neuron_taste_design_check(code))
    elif target_path.endswith((".py", ".pyw")):
        syn = ccr.neuron_syntax_check(code)
        signals.append(syn)
        if syn.passed:
            signals.append(ccr.neuron_scope_check(code))
            signals.append(ccr.neuron_taste_design_check(code))
    else:
        # Default: if it's code, attempt syntax check
        syn = ccr.neuron_syntax_check(code)
        signals.append(syn)

    if contract is not None:
        signals.append(ccr.neuron_semantic_alignment(code, contract=contract))

    res = ccr.evaluate_signals(signals)
    passed = _report_signals(ccr, signals, verbose=verbose)

    if memory:
        failed = next((s for s in signals if not s.passed), None)
        memory.record_file_validation(
            file_path=target_path,
            passed=not res["blocked"],
            blocked=res["blocked"],
            gate=failed.neuron_name if failed else None,
            summary=res["summary"],
            signals=[
                {"neuron": s.neuron_name, "passed": s.passed, "gate": s.gate_type.value, "message": s.message}
                for s in signals
            ],
            error_message=failed.message if failed else "",
            code_hash=hashlib.sha256(code.encode("utf-8")).hexdigest()[:16],
        )

    return passed


def show_status():
    print("==========================================================")
    print("       GOBY META-COGNITIVE FRAMEWORK STATUS (v5.0.0)")
    print("==========================================================")
    print(f"Working Directory: {os.getcwd()}")

    git_hooks_installed = Path(".git/hooks/pre-commit").exists() and Path(".git/hooks/pre-push").exists()
    print(f"Git Pre-Commit Hook: {'INSTALLED (Active)' if git_hooks_installed else 'NOT INSTALLED (Run: goby install-hook)'}")
    print(f"Git Pre-Push Hook:   {'INSTALLED (Active)' if git_hooks_installed else 'NOT INSTALLED (Run: goby install-hook)'}")

    lifecycle_hooks_installed = Path(".agents/hooks.json").exists()
    print(f"Antigravity Hooks:   {'INSTALLED (Active: PostToolUse, PreInvocation, Stop)' if lifecycle_hooks_installed else 'NOT INSTALLED (Run: goby install-hook)'}")

    # Memory files status
    mem_file = Path("universal_consciousness.json")
    print(f"Universal Memory:    {'PRESENT (' + str(mem_file.stat().st_size) + ' bytes)' if mem_file.exists() else 'NOT INITIALIZED'}")

    fail_file = Path("failure_patterns.json")
    print(f"Failure Memory:      {'PRESENT (' + str(fail_file.stat().st_size) + ' bytes)' if fail_file.exists() else 'NOT INITIALIZED'}")

    # Unresolved file error ledger
    try:
        ledger_mgr = StateMemoryManager("cognitive_map.json")
        unresolved = ledger_mgr.get_unresolved_errors()
    except Exception:
        unresolved = []
    print(f"Unresolved File Errors: {len(unresolved)}")
    for entry in unresolved[:10]:
        print(f"  - {entry['file']} [{entry['gate']}] {entry['message']}")
    if unresolved:
        print("  -> Run `goby check <file>` until passing, then `goby gate` must exit 0.")

    # Conversation Memory stats
    conv_file = Path("conversation_index.json")
    if conv_file.exists():
        try:
            from .conversation_memory import ConversationMemoryStore
            conv_store = ConversationMemoryStore("conversation_index.json")
            stats = conv_store.get_summary_stats()
            print(f"Conversation Memory: {stats['total']} entries, {stats['unique_files']} unique files")
        except Exception:
            print(f"Conversation Memory: PRESENT ({conv_file.stat().st_size} bytes)")
    else:
        print("Conversation Memory: NOT INITIALIZED")

    print("==========================================================")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Goby Framework CLI v5.0.0 (Aggressive-Autonomous AI Quality Engine)")
        print("Usage:")
        print("  goby audit         Run full test suite verification")
        print("  goby benchmark     Run empirical benchmark simulation")
        print("  goby evolve        Run autonomous self-evolution cycle (BFM metric)")
        print("  goby check <code|filepath> Validate python/JS snippet or file via CCR (add -v for verbose, --intent '<text>' for semantic alignment)")
        print("  goby verify <code_string>   Genuine Pre-Output In-Memory Code Verification (add -v for verbose, --intent '<text>' for semantic alignment)")
        print("  goby evidence <claim> <file> Generate Machine-Verifiable Evidence Contract")
        print("  goby install-hook  Install Git hooks and Antigravity lifecycle hooks (.agents/hooks.json)")
        print("  goby hooks [status|install] Manage Antigravity lifecycle hooks")
        print("  goby watch         Run active workspace CCR watcher")
        print("  goby status        Show framework installation & memory status")
        print("  goby gate          Check Unresolved Error Ledger (must exit 0 before claiming done)")
        print("  goby intent <text> Parse user intent -> structured JSON (bilingual)")
        print("  goby recall <text> Recall similar past conversations from memory")
        print("  goby save '<summary>' <type> Save current session context to conversation memory")
        print("  goby briefing      Show auto-generated session briefing from memory")
        sys.exit(0)

    cmd = args[0].lower()

    if cmd == "status":
        show_status()
        sys.exit(0)

    elif cmd == "verify":
        verbose = "-v" in args or "--verbose" in args
        intent_text = None
        filtered_args = []
        skip_next = False
        for i, a in enumerate(args[1:], 1):
            if skip_next:
                skip_next = False
                continue
            if a == "--intent":
                if i < len(args) - 1:
                    intent_text = args[i + 1]
                    skip_next = True
                continue
            if a not in ("-v", "--verbose"):
                filtered_args.append(a)

        contract = None
        if intent_text:
            from .intent_resolver import IntentResolver
            contract = IntentResolver().resolve(intent_text).semantic_contract

        if not filtered_args:
            print("Error: Please provide code string to verify. Example: goby verify 'x = 10'")
            sys.exit(1)
        code = filtered_args[0]
        ccr = CognitiveControlRoom()

        if not _looks_like_code(code):
            print("[GOBY] Input is prose / not code (triage SKIP) — verification skipped, no neurons executed.")
            sys.exit(0)

        signals = []
        syn = ccr.neuron_syntax_check(code)
        signals.append(syn)
        if syn.passed:
            signals.append(ccr.neuron_scope_check(code))
            signals.append(ccr.neuron_taste_design_check(code))
        if contract is not None:
            signals.append(ccr.neuron_semantic_alignment(code, contract=contract))

        print("[GOBY VERIFY] Verifying candidate...")
        sys.exit(0 if _report_signals(ccr, signals, verbose=verbose) else 1)

    elif cmd == "verify-feedback":
        if len(args) < 2:
            print("Error: Please provide code string. Example: goby verify-feedback 'x = 10'")
            sys.exit(1)
        code = args[1]
        err_ctx = args[2] if len(args) > 2 else None
        ccr = CognitiveControlRoom()
        fb = ccr.verify_candidate_with_feedback(code, error_context=err_ctx)
        import json
        print(json.dumps(fb.to_dict(), indent=2))
        sys.exit(0 if fb.verified else 1)

    elif cmd == "evidence":
        if len(args) < 3:
            print("Error: Usage: goby evidence '<claim>' '<file|code>' [optional_test_command]")
            sys.exit(1)
        claim = args[1]
        target = args[2]
        test_cmd = args[3] if len(args) > 3 else None
        ccr = CognitiveControlRoom()
        contract = ccr.create_evidence_contract(claim, target, test_command=test_cmd)
        import json
        print(json.dumps(contract, indent=2))
        sys.exit(0 if contract["status"] == "VERIFIED" else 1)

    elif cmd == "install-hook":
        install_git_hooks()
        sys.exit(0)

    elif cmd == "hooks":
        from .hooks import cli_entry
        subaction = args[1] if len(args) > 1 else "status"
        cli_entry(subaction)
        sys.exit(0)

    elif cmd == "watch":
        memory = StateMemoryManager("cognitive_map.json")
        run_watch_loop(memory=memory)
        sys.exit(0)

    elif cmd == "gate":
        memory = StateMemoryManager("cognitive_map.json")
        unresolved = memory.get_unresolved_errors()
        if not unresolved:
            print("[GOBY GATE] Ledger clean: 0 unresolved file errors. Workspace ready.")
            sys.exit(0)
        print(f"[GOBY GATE] {len(unresolved)} unresolved file error(s):")
        for entry in unresolved:
            print(f"  - {entry['file']} [{entry['gate']}] {entry['message']}")
            print(f"    Last checked: {entry.get('checked_at', 'N/A')} | Hash: {entry.get('code_hash', '')}")
        print("[GOBY GATE] BLOCKED. Fix each file, then run `goby check <file>` until it passes.")
        sys.exit(1)

    elif cmd == "evolve":
        print("[EVOLUTION] Running Goby v4.2.0 Omni-Synthesis Evolution Benchmark...")
        from .evolution_loop import SelfEvolutionEngine
        engine = SelfEvolutionEngine()
        result = engine.run_evolution_cycle()
        print(f"  -> Total Benchmarks: {result['total_benchmarks']}")
        print(f"  -> Caught Apriori:   {result['caught_apriori']}")
        print(f"  -> Bypasses Needed:  {result['bypasses_needed']}")
        print(f"  -> BFM Metric:       {result['bypass_frequency_metric']}")
        print(f"  -> Status:           {result['status']}")
        sys.exit(0 if result['status'] == "ZERO_BYPASS_ACHIEVED" else 1)

    elif cmd == "audit":
        print("[AUDIT] Running Goby Empirical Verification Audit...")
        suite = unittest.defaultTestLoader.discover("tests")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    elif cmd == "benchmark":
        print("[BENCHMARK] Running Goby Benchmark Simulation...")
        from tests import benchmark_simulation
        benchmark_simulation.main()
        sys.exit(0)

    elif cmd == "check":
        verbose = "-v" in args or "--verbose" in args
        intent_text = None
        filtered_args = []
        skip_next = False
        for i, a in enumerate(args[1:], 1):
            if skip_next:
                skip_next = False
                continue
            if a == "--intent":
                if i < len(args) - 1:
                    intent_text = args[i + 1]
                    skip_next = True
                continue
            if a not in ("-v", "--verbose"):
                filtered_args.append(a)

        contract = None
        if intent_text:
            from .intent_resolver import IntentResolver
            contract = IntentResolver().resolve(intent_text).semantic_contract

        if not filtered_args:
            print("Error: Please provide code string or filepath to check. Example: goby check 'x = 1' or goby check main.py")
            sys.exit(1)
        target = filtered_args[0]
        ccr = CognitiveControlRoom()

        if os.path.isfile(target):
            memory = StateMemoryManager("cognitive_map.json")
            passed = validate_filepath(target, ccr, memory=memory, verbose=verbose, contract=contract)
            sys.exit(0 if passed else 1)

        code = target
        if not _looks_like_code(code):
            print("[GOBY] Input is prose / not code (triage SKIP) — verification skipped, no neurons executed.")
            sys.exit(0)

        signals = []
        syn = ccr.neuron_syntax_check(code)
        signals.append(syn)
        if syn.passed:
            signals.append(ccr.neuron_scope_check(code))
            signals.append(ccr.neuron_taste_design_check(code))
        if contract is not None:
            signals.append(ccr.neuron_semantic_alignment(code, contract=contract))

        print("[GOBY CHECK] Verifying candidate...")
        sys.exit(0 if _report_signals(ccr, signals, verbose=verbose) else 1)

    elif cmd == "intent":
        if len(args) < 2:
            print("Error: Please provide user text. Example: goby intent 'perbaiki error di app.js'")
            sys.exit(1)
        user_text = " ".join(args[1:])
        from .intent_resolver import IntentResolver
        resolver = IntentResolver()
        intent_tree = resolver.resolve(user_text)
        import json
        print(json.dumps(intent_tree.to_dict(), indent=2, ensure_ascii=False))
        if intent_tree.semantic_contract.contradictions:
            print("\n[GOBY INTENT] [!] Contradictions detected:")
            for c in intent_tree.semantic_contract.contradictions:
                print(f"  -> {c}")
        if intent_tree.clarification_needed:
            print("\n[GOBY INTENT] [!] Clarification needed:")
            for q in intent_tree.clarification_questions:
                print(f"  -> {q}")
            sys.exit(1)
        sys.exit(0)

    elif cmd == "recall":
        if len(args) < 2:
            print("Error: Please provide search text. Example: goby recall 'fix error in app.js'")
            sys.exit(1)
        search_text = " ".join(args[1:])
        from .conversation_memory import ConversationMemoryStore
        store = ConversationMemoryStore("conversation_index.json")
        results = store.recall(search_text)
        if results and results[0].found:
            print(f"[GOBY RECALL] Found {len([r for r in results if r.found])} similar past conversation(s):")
            for r in results:
                if r.found:
                    print(f"  [{r.similarity:.0%} match] {r.context_hint}")
        else:
            print("[GOBY RECALL] No similar past conversations found. Starting fresh.")
        sys.exit(0)

    elif cmd == "save":
        if len(args) < 3:
            print("Error: Usage: goby save '<summary>' <task_type> [files...]")
            print("  task_type: fix_bug | create_feature | refactor | design_ui | test | configure")
            sys.exit(1)
        summary = args[1]
        task_type = args[2]
        files = args[3:] if len(args) > 3 else []
        from .conversation_memory import ConversationMemoryStore
        store = ConversationMemoryStore("conversation_index.json")
        entry = store.save(
            user_intent_summary=summary,
            task_type=task_type,
            files_modified=files,
            final_status="SUCCESS",
        )
        print(f"[GOBY SAVE] Session context saved: {entry.entry_id}")
        print(f"  Summary: {summary}")
        print(f"  Type: {task_type}")
        if files:
            print(f"  Files: {', '.join(files)}")
        sys.exit(0)

    elif cmd == "briefing":
        from .conversation_memory import ConversationMemoryStore
        store = ConversationMemoryStore("conversation_index.json")
        stats = store.get_summary_stats()
        entries = store.get_all_entries()
        print("==========================================================")
        print("       GOBY SESSION BRIEFING (Auto-Generated)")
        print("==========================================================")
        print(f"Total Past Conversations: {stats['total']}")
        if stats['by_type']:
            print(f"By Type: {stats['by_type']}")
        if stats['by_status']:
            print(f"By Status: {stats['by_status']}")
        if entries:
            print("\nRecent Sessions (last 5):")
            for e in entries[-5:]:
                status_icon = "[OK]" if e.final_status == "SUCCESS" else "[!]"
                print(f"  {status_icon} [{e.timestamp}] {e.user_intent_summary}")
                if e.files_modified:
                    print(f"     Files: {', '.join(e.files_modified[:3])}")
        print("==========================================================")
        sys.exit(0)

    else:
        print(f"Unknown command: '{cmd}'. Run 'goby --help' for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()

