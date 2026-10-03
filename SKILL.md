---
name: goby-universal
description: "Goby v5.1: Aggressive-autonomous AI quality framework. Auto-resolves ambiguous user intent, repository AST & dependency graph code mapping, persists conversation memory across sessions, validates every code output, and enforces modern UI/UX standards. Supports Python, JavaScript, TypeScript, Kotlin, HTML, CSS."
---

# Goby v5.1 — Aggressive-Autonomous AI Quality Engine

## 🚨 ACTIVATION: ALWAYS-ON (NOT OPTIONAL)

Goby activates **automatically** on every task. You do NOT wait for the user to mention Goby.

**TRIGGER CONDITIONS (execute the matching action IMMEDIATELY):**

| When this happens... | You MUST do this... |
|---------------------|---------------------|
| User sends ANY request | Run `goby intent '<request>' [--repo .]` to resolve intent FIRST |
| Intent is ambiguous (ambiguity > 0.5) | Ask clarification questions from intent tree |
| Querying codebase symbols & blast radius | Run `goby map '<query>' [--repo .]` to map impact |
| About to start coding | Run `goby recall '<intent>'` to check past context |
| After writing/editing ANY code file | Run `goby check <filepath>` to validate |
| Error persists after 2 attempts | Run `goby recall` to check known fixes, halt naive retries |
| Task is complete | Run `goby gate` + `./gradlew.bat test` (or `python -m unittest discover tests/`) |
| Both gates pass | Run `goby save '<summary>' <type> [files...]` |

---

## 🧠 Core Pipeline (Deterministic & Linear)

```
User Request → Intent Resolver (+ Code Map) → Memory Recall → Code → Auto-Check → Gates → Save
```

1. **Intent Resolver & Semantic Core** (`goby intent`): Parses abstract/ambiguous requests into structured intents and formal `SemanticIR`. Bilingual (ID/EN). Auto-generates clarification questions when confidence is low.

2. **Repository AST Scanner & Dependency Graph** (`goby map`): Scans Python, JS/TS, and Kotlin source files. Maps intent to concrete classes, functions, and files, and calculates upstream/downstream causal blast radius.

3. **Conversation Memory** (`goby recall` / `goby save`): Persists context across sessions. Similar past problems are recalled instantly — no starting from zero.

4. **CCR Validation** (`goby check`): Deterministic AST, Bracket & Scope validation (syntax, scope, cross-reference). Hard Gates block bad code. Soft Signals advise. Supports Python, JavaScript, TypeScript, and Kotlin.

5. **LDE Loop Detection**: Detects repetitive failure cycles (>85% similarity) and forces strategy pivoting to prevent deadlocks.

6. **Completion Gate & Persistence**: `goby gate` verifies zero unresolved errors, test runner validates logic, and `goby save` persists solution memory for future sessions.

---

## 🎨 Design Guardrails & Visual Density (v5.2)

Goby bertindak sebagai **Pengaman (Guardrail) & Manajemen Konteks**, bukan mandor gaya preskriptif:
- **Anti-Boxification (Visual Density Governor):** Mencegah over-encapsulation di mana teks, angka telemetri, dan simbol dipaksa masuk ke nested card boxes. Mendukung layout CSS native yang bersih, semantic HTML (`<output>`, `<meter>`, `<dl>`), dan HUD contextual.
- **Anti-Collision Engine (ComponentCapabilityRegistry):** Mencegah duplikasi fitur (*double fitur bocor*) di mana kontrol yang sama dibuat berulang di permukaan layout berbeda.
- **Respect User Design Tokens:** Mengutamakan konsistensi token/gaya proyek pengguna, bukan memaksakan keyword template klise.


---

## 🛠️ CLI Reference

```bash
# Core validation
goby check <code|filepath>  # CCR validation (add -v for verbose, --intent '<text>' for alignment)
goby verify '<code_string>' # Genuine pre-output in-memory verification
goby evidence '<claim>' '<file>' # Generate machine-verifiable evidence contract
goby gate                   # Unresolved Error Ledger — must exit 0
goby audit                  # Full test suite

# Intent, Semantic IR & Repository Code Mapping (v5.1)
goby intent '<text>' [--repo <path>]  # Parse user intent + repository code mapping
goby map '<query>' [--repo <path>]    # Map intent/query to repository symbols & blast radius
goby recall '<text>'                  # Recall similar past conversations
goby save '<summary>' <type> [files...] # Save session context
goby briefing                         # Show past session summary

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

