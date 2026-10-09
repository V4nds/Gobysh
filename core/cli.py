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

_ALWAYS_CODE_EXTENSIONS = (".py", ".pyw", ".js", ".jsx", ".ts", ".tsx", ".kt", ".kts", ".css", ".html", ".json", ".yaml", ".yml", ".toml")


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
        gate_badge = f" [{sig.gate_type.value} GATE]" if not sig.passed else ""
        print(f"  [{sig.neuron_name}]{gate_badge} {status}{_neuron_location(sig)} - {sig.message}")
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

    # Triage: skip non-code files (documentation/prose) entirely — no neurons.
    if target_path.lower().endswith((".md", ".markdown", ".txt", ".rst")):
        print(f"[GOBY] File {target_path} is documentation / prose (triage SKIP) — verification skipped.")
        if memory:
            abs_path = os.path.abspath(target_path)
            memory.record_file_validation(
                file_path=abs_path,
                passed=True,
                blocked=False,
                gate=None,
                summary="Documentation/prose triage pass",
                signals=[],
                error_message="",
                code_hash="",
            )
        return True

    if not _looks_like_code(code):
        print("[GOBY] Content is prose / not code (triage SKIP) — verification skipped, no neurons executed.")
        if memory:
            abs_path = os.path.abspath(target_path)
            memory.record_file_validation(
                file_path=abs_path,
                passed=True,
                blocked=False,
                gate=None,
                summary="Prose triage pass",
                signals=[],
                error_message="",
                code_hash="",
            )
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
            signals.append(ccr.neuron_architectural_depth(code, target_path, escalate_hard_gate=True))
    elif target_path.endswith((".kt", ".kts")):
        syn = ccr.neuron_kotlin_syntax_check(code)
        signals.append(syn)
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


def generate_architecture_report(
    metrics_list: List[Any],
    output_path: Optional[str] = None
) -> str:
    """
    Generates a self-contained visual HTML report of codebase architectural depth
    and deepening opportunities, honoring Matt Pocock's improve-codebase-architecture design.
    """
    import tempfile
    if not output_path:
        ts = time.strftime("%Y%m%d-%H%M%S")
        output_path = os.path.join(tempfile.gettempdir(), f"architecture-review-{ts}.html")

    deep_count = sum(1 for m in metrics_list if m.classification == "DEEP")
    balanced_count = sum(1 for m in metrics_list if m.classification == "BALANCED")
    shallow_count = sum(1 for m in metrics_list if m.classification == "SHALLOW")
    avg_mdi = round(sum(m.mdi_score for m in metrics_list) / max(1, len(metrics_list)), 2)

    cards_html = []
    for m in metrics_list:
        badge_color = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" if m.classification == "DEEP" else (
            "bg-amber-500/10 text-amber-400 border-amber-500/20" if m.classification == "BALANCED" else
            "bg-rose-500/10 text-rose-400 border-rose-500/20"
        )
        recommendation_badge = "Deep / Optimal" if m.classification == "DEEP" else (
            "Worth Exploring" if m.classification == "BALANCED" else "Strong Refactoring Opportunity"
        )

        anti_patterns_html = ""
        if m.anti_patterns:
            items = "".join(f"<li class='text-xs text-rose-300 font-mono'>• [{ap.get('type')}] {ap.get('details')}</li>" for ap in m.anti_patterns)
            anti_patterns_html = f"""
            <div class="mt-3 p-3 rounded bg-rose-950/20 border border-rose-900/30">
                <span class="text-xs font-semibold text-rose-400 uppercase tracking-wider">Detected Architectural Friction:</span>
                <ul class="mt-1 space-y-1">{items}</ul>
            </div>
            """

        clean_mod = re.sub(r'[^a-zA-Z0-9_]', '_', m.module_name)
        before_diagram = f"""graph TD
    Client["Caller / Client"] -->|Surface: {m.surface_area}| {clean_mod}["{m.module_name}"]
    {clean_mod} -.->|Pass-through| Inner["Dependencies"]
"""
        after_diagram = f"""graph TD
    Client["Caller / Client"] -->|Compact Interface| {clean_mod}["{m.module_name} (Deep Seam)"]
    subgraph Encapsulated ["Hidden Domain Logic"]
        Logic["Rich Business Invariants"]
        Storage["Private Cache / State"]
    end
    {clean_mod} --> Logic
    Logic --> Storage
"""

        card = f"""
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-sm">
            <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                    <h3 class="text-lg font-bold text-slate-100 font-mono">{m.file_path}</h3>
                    <span class="text-xs text-slate-400">Module: {m.module_name}</span>
                </div>
                <div class="flex items-center gap-3">
                    <span class="px-3 py-1 rounded-full text-xs font-semibold border {badge_color}">
                        {m.classification} (MDI: {m.mdi_score})
                    </span>
                    <span class="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {recommendation_badge}
                    </span>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div class="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
                    <h4 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Metrics Anatomy</h4>
                    <div class="space-y-1.5 text-xs text-slate-300">
                        <div class="flex justify-between"><span>Interface Surface (S_int):</span><span class="font-mono text-cyan-400">{m.surface_area}</span></div>
                        <div class="flex justify-between"><span>Implementation Volume (V_impl):</span><span class="font-mono text-indigo-400">{m.implementation_volume}</span></div>
                        <div class="flex justify-between"><span>Public Methods:</span><span class="font-mono">{m.details.get('public_methods', 0)}</span></div>
                        <div class="flex justify-between"><span>Internal Statements:</span><span class="font-mono">{m.details.get('total_statements', 0)}</span></div>
                        <div class="flex justify-between"><span>Cyclomatic Complexity:</span><span class="font-mono">{m.details.get('cyclomatic_complexity', 1)}</span></div>
                    </div>
                    {anti_patterns_html}
                </div>

                <div class="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
                    <h4 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Seam Visualization (Before / After)</h4>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[10px]">
                        <div>
                            <span class="text-slate-400 block mb-1 text-center font-semibold">Current State</span>
                            <pre class="mermaid">{before_diagram}</pre>
                        </div>
                        <div>
                            <span class="text-emerald-400 block mb-1 text-center font-semibold">Deepened Target</span>
                            <pre class="mermaid">{after_diagram}</pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
        cards_html.append(card)

    cards_joined = "\n".join(cards_html)

    html_content = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Goby Architecture Review — Deep Modules Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen py-10 px-4 sm:px-8 font-sans">
    <div class="max-w-6xl mx-auto space-y-8">
        <header class="border-b border-slate-800 pb-6">
            <div class="flex items-center gap-3 mb-2">
                <span class="px-2.5 py-0.5 rounded text-xs font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">GOBY v5.3</span>
                <span class="text-xs text-slate-400">Dialectical Synthesis Engine</span>
            </div>
            <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400">
                Goby Architecture Review — Deep Modules Report
            </h1>
            <p class="text-sm text-slate-400 mt-2">
                Mechanical architectural telemetry based on John Ousterhout's <em>A Philosophy of Software Design</em>.
                Measures leverage (V_impl / S_int), seam clarity, and anti-patterns.
            </p>
            <div class="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-6">
                <div class="bg-slate-900 border border-slate-800 p-3 rounded-lg text-center">
                    <div class="text-xl font-bold text-slate-100 font-mono">{len(metrics_list)}</div>
                    <div class="text-xs text-slate-400">Modules Scanned</div>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-3 rounded-lg text-center">
                    <div class="text-xl font-bold text-cyan-400 font-mono">{avg_mdi}</div>
                    <div class="text-xs text-slate-400">Average MDI</div>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-3 rounded-lg text-center">
                    <div class="text-xl font-bold text-emerald-400 font-mono">{deep_count}</div>
                    <div class="text-xs text-slate-400">Deep Modules</div>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-3 rounded-lg text-center">
                    <div class="text-xl font-bold text-amber-400 font-mono">{balanced_count}</div>
                    <div class="text-xs text-slate-400">Balanced</div>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-3 rounded-lg text-center">
                    <div class="text-xl font-bold text-rose-400 font-mono">{shallow_count}</div>
                    <div class="text-xs text-slate-400">Shallow (Friction)</div>
                </div>
            </div>
        </header>

        <main class="space-y-6">
            <h2 class="text-lg font-bold text-slate-200">Module Deepening Telemetry</h2>
            {cards_joined}
        </main>

        <footer class="pt-8 border-t border-slate-900 text-center text-xs text-slate-500">
            Generated autonomously by Goby Meta-Cognitive Quality Framework • Ground of Being Preserved
        </footer>
    </div>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path


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
        print("  goby intent <text> [--repo <path>] Parse user intent -> structured JSON (bilingual)")
        print("  goby spar '<ai_proposal>' [--intent '<text>'] Audit AI cognitive thinking/proposal against dialectical mandate")
        print("  goby map <query> [--repo <path>]   Map intent/query to repository symbols and blast radius")
        print("  goby deepen [file|dir] [--report] [--verbose] Analyze architectural depth & leverage (Ousterhout's Deep Modules)")
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
        repo_arg = None
        user_words = []
        i = 1
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_arg = args[i + 1]
                i += 2
            else:
                user_words.append(args[i])
                i += 1
        user_text = " ".join(user_words)
        from .intent_resolver import IntentResolver
        resolver = IntentResolver()
        intent_tree = resolver.resolve(user_text, repo_root=repo_arg)
        import json
        print(json.dumps(intent_tree.to_dict(), indent=2, ensure_ascii=False))
        if intent_tree.semantic_contract.contradictions:
            print("\n[GOBY INTENT] [!] Contradictions detected:")
            for c in intent_tree.semantic_contract.contradictions:
                print(f"  -> {c}")
        if intent_tree.dialectical_contract and intent_tree.dialectical_contract.is_sycophantic:
            print("\n[GOBY INTENT] [DIALECTICAL MANDATE - COGNITIVE GUARDRAILS FOR AI]:")
            for a in intent_tree.dialectical_contract.naive_assumptions:
                print(f"  [AI Mandate]       {a}")
            for t in intent_tree.dialectical_contract.tradeoffs_identified:
                print(f"  [Trade-off/Risk]   {t}")
            if intent_tree.dialectical_contract.counter_vector:
                print(f"  [Counter-Vector]   {intent_tree.dialectical_contract.counter_vector}")
        if intent_tree.clarification_needed:
            print("\n[GOBY INTENT] [!] Clarification needed:")
            for q in intent_tree.clarification_questions:
                print(f"  -> {q}")
            sys.exit(1)
        sys.exit(0)

    elif cmd == "spar":
        if len(args) < 2:
            print("Error: Usage: goby spar '<ai_proposal_text>' [--intent '<user_intent_text>']")
            sys.exit(1)
        intent_text = None
        proposal_words = []
        i = 1
        while i < len(args):
            if args[i] == "--intent" and i + 1 < len(args):
                intent_text = args[i + 1]
                i += 2
            else:
                proposal_words.append(args[i])
                i += 1
        proposal_text = " ".join(proposal_words)
        from .intent_resolver import IntentResolver
        resolver = IntentResolver()
        dia_contract = None
        if intent_text:
            tree = resolver.resolve(intent_text)
            dia_contract = tree.dialectical_contract
        audit_res = resolver.audit_ai_proposition(proposal_text, dialectical_contract=dia_contract)
        print("==========================================================")
        print("       GOBY COGNITIVE AUDIT — AI PROPOSITION EVALUATION")
        print("==========================================================")
        print(f"Status:         {'[PASSED]' if audit_res['passed'] else '[SYCOPHANTIC BLOCKED]'}")
        print(f"Recommendation: {audit_res['recommendation']}")
        if audit_res['violations']:
            print("\nViolations:")
            for v in audit_res['violations']:
                print(f"  ! {v}")
        print("==========================================================")
        sys.exit(0 if audit_res['passed'] else 1)

    elif cmd == "map":
        if len(args) < 2:
            print("Error: Please provide query. Example: goby map 'authentication logic' [--repo .]")
            sys.exit(1)
        repo_arg = "."
        query_words = []
        i = 1
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_arg = args[i + 1]
                i += 2
            else:
                query_words.append(args[i])
                i += 1
        query_text = " ".join(query_words)
        from .translation import RepositoryScanner, CodeSemanticMapper
        from .semantics import DependencyGraph
        sym_map = RepositoryScanner.scan_directory(repo_arg)
        dg = DependencyGraph.build_from_symbol_map(sym_map)
        mapper = CodeSemanticMapper(sym_map, dg)
        report = mapper.map_query(query_text)
        import json
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
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

    elif cmd == "deepen":
        from .semantics.depth_engine import DepthEngine
        engine = DepthEngine()
        is_report = "--report" in args
        verbose = "-v" in args or "--verbose" in args
        target_path = "."
        for a in args[1:]:
            if a not in ("--report", "-v", "--verbose"):
                target_path = a
                break

        if os.path.isfile(target_path):
            metrics_list = [engine.analyze_file(target_path)]
        elif os.path.isdir(target_path):
            metrics_list = engine.analyze_directory(target_path)
        else:
            print(f"Error: Target path not found: {target_path}")
            sys.exit(1)

        if not metrics_list:
            print(f"[GOBY ARCHITECTURE] No Python files found in: {target_path}")
            sys.exit(0)

        if is_report:
            report_file = generate_architecture_report(metrics_list)
            print("==========================================================")
            print("       GOBY ARCHITECTURAL DEPTH — VISUAL REPORT")
            print("==========================================================")
            print(f"HTML Report generated: {report_file}")
            print(f"Total modules analyzed: {len(metrics_list)}")
            deep_n = sum(1 for m in metrics_list if m.classification == "DEEP")
            balanced_n = sum(1 for m in metrics_list if m.classification == "BALANCED")
            shallow_n = sum(1 for m in metrics_list if m.classification == "SHALLOW")
            print(f"Classification: {deep_n} DEEP, {balanced_n} BALANCED, {shallow_n} SHALLOW")
            print("Opening report in browser...")
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(report_file)}")
            print("==========================================================")
            sys.exit(0)

        print("==========================================================")
        print("       GOBY ARCHITECTURAL DEPTH TELEMETRY (v5.3)")
        print("==========================================================")
        print(f"Target: {target_path} ({len(metrics_list)} module(s))\n")
        for m in metrics_list:
            badge = "[DEEP]" if m.classification == "DEEP" else ("[BALANCED]" if m.classification == "BALANCED" else "[SHALLOW]")
            print(f"  {badge:<10} MDI: {m.mdi_score:<5.2f} (S_int: {m.surface_area:<4.1f} | V_impl: {m.implementation_volume:<5.1f}) -> {m.file_path}")
            if verbose or m.classification == "SHALLOW":
                for ap in m.anti_patterns:
                    print(f"     ! [{ap.get('type')}] {ap.get('details')}")
        print("==========================================================")
        sys.exit(0)

    else:
        print(f"Unknown command: '{cmd}'. Run 'goby --help' for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()

