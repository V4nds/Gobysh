---
name: goby-universal
description: "Goby v5.4: Aggressive-autonomous AI quality framework with Rust native acceleration. Auto-resolves ambiguous user intent, repository AST & dependency graph code mapping, persists conversation memory across sessions, validates every code output with ultra-fast delimiter gates (<5ms), and enforces modern UI/UX standards. Supports Python, JavaScript, TypeScript, Kotlin, Rust, HTML, CSS."
---

# Goby v5.4 — Aggressive-Autonomous AI Quality Engine

## 🚨 ACTIVATION: ALWAYS-ON (NOT OPTIONAL)

Goby activates **automatically** on every task. You do NOT wait for the user to mention Goby.

**TRIGGER CONDITIONS (execute the matching action IMMEDIATELY):**

| When this happens... | You MUST do this... |
|---------------------|---------------------|
| User sends ANY request | Run `goby spider '<request>' [--save-plan]` to crawl intent & synthesize blueprint |
| Intent is ambiguous (vague tokens present) | Ask clarification questions using `ask_question` tool |
| Diagnosing potential flaws / anomalies | Run `goby diagnose [file|prompt]` to audit 3D technical flaws |
| Querying codebase symbols & blast radius | Run `goby map '<query>' [--repo .]` to map impact |
| Fast file delimiter/bracket validation | Run `goby fast-gate <filepath>` for <5ms native check |
| About to start coding | Run `goby recall '<intent>'` to check past context |
| After writing/editing ANY code file | Run `goby check <filepath>` to validate |
| Error persists after 2 attempts | Run `goby recall` to check known fixes, halt naive retries |
| Task is complete | Run `goby gate` + `python -m unittest discover tests/` |
| Both gates pass | Run `goby save '<summary>' <type> [files...]` |

---

## 🧠 Core Pipeline (Deterministic & Linear)

```
User Request → Prompt Spider (Flaw Audit & 7-Pillars) → Memory Recall → Code → Auto-Check → Gates → Save
```

1. **Prompt Spider & Tripartite Semantic Bridge** (`goby spider`): Crawls raw user requests, tags tokens into 5 categories (`claim`, `owner`, `file`, `approval`, `vague`), resolves ID-EN-AST semantics, audits flaws across 3 dimensions, and synthesizes 7-Pillar Empirical Blueprints with mechanical contract binding.

2. **Technical Flaw & Anomaly Detector** (`goby diagnose`): Audits user prompt contradictions, project topology (double buttons / capability collision), and UI layout traps (text overflow outside container).

3. **Repository AST Scanner & Dependency Graph** (`goby map`): Scans Python, JS/TS, and Kotlin source files. Maps intent to concrete classes, functions, and files, and calculates upstream/downstream causal blast radius.

4. **Conversation Memory** (`goby recall` / `goby save`): Persists context across sessions. Similar past problems are recalled instantly — no starting from zero.

5. **CCR Validation & Depth Engine** (`goby check` / `goby deepen`): Deterministic AST, Scope, and Architectural Depth validation (Ousterhout's MDI). Hard Gates block bad code or shallow wrappers. Soft Signals advise.

6. **LDE Loop Detection**: Detects repetitive failure cycles (>85% similarity) and forces strategy pivoting to prevent deadlocks.

7. **Completion Gate & Persistence**: `goby gate` verifies zero unresolved errors, test runner validates logic, and `goby save` persists solution memory for future sessions.

---

## 🎨 Design Guardrails & Visual Density (v5.3)

Goby bertindak sebagai **Pengaman (Guardrail) & Manajemen Konteks**, bukan mandor gaya preskriptif:
- **Anti-Boxification (Visual Density Governor):** Mencegah over-encapsulation di mana teks dan simbol dipaksa masuk ke nested card boxes. Mendukung layout CSS native yang elastis tanpa fixed height trap yang membuat teks tumpah keluar kotak.
- **Anti-Collision Engine (ComponentCapabilityRegistry):** Mencegah duplikasi fitur (*double button / fitur bocor*) di mana kontrol yang sama dibuat berulang di permukaan layout berbeda.
- **Respect User Design Tokens:** Mengutamakan konsistensi token/gaya proyek pengguna, bukan memaksakan keyword template klise.

---

## 🛠️ CLI Reference

```bash
# Core validation & Diagnostics
goby check <code|filepath>  # CCR validation (add -v for verbose, --intent '<text>' for alignment)
goby verify '<code_string>' # Genuine pre-output in-memory verification
goby fast-gate <filepath>   # Ultra-fast native delimiter & structural gate (<5ms)
goby native <subcommand>    # Direct interface to goby_core Rust native accelerator (scan|check|version)
goby deepen [file|dir]      # Architectural depth & leverage analysis (Ousterhout's MDI)
goby diagnose [file|prompt] # Audit 3D technical flaws (prompt contradictions, double buttons, text overflow)
goby gate                   # Unresolved Error Ledger — must exit 0
goby audit                  # Full test suite

# Prompt Spider, Intent & Repository Mapping (v5.3)
goby spider '<prompt>' [--save-plan] [--json] # Crawl prompt, tag tokens, and synthesize 7-pillar blueprint
goby intent '<text>' [--repo <path>]          # Parse user intent + repository code mapping
goby map '<query>' [--repo <path>]            # Map intent/query to repository symbols & blast radius
goby recall '<text>'                          # Recall similar past conversations
goby save '<summary>' <type> [files...]       # Save session context
goby briefing                                 # Show past session summary

# Tools & Infrastructure
goby evolve                 # Self-evolution cycle (BFM metric)
goby watch                  # Active file watcher with CCR
goby install-hook           # Git pre-commit/pre-push hooks & Antigravity hooks
goby status                 # Framework status dashboard
```

---

## ⚡ Operational Rules

1. **Evidence Over Assertion:** Never claim done without `goby gate` Exit Code 0.
2. **Ask Before Guess:** If user intent is unclear, ask — don't hallucinate requirements.
3. **Memory First:** Check past context before starting from scratch.
4. **Auto-Check Always:** Every file write triggers `goby check`. No exceptions.
5. **No Superficial Patches:** Fix root causes, not symptoms.
6. **2-Strike Escalation:** 2 failed attempts → halt, escalate strategy (LDE/evolve).

