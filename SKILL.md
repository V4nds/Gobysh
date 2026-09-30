---
name: goby-universal
description: "Goby v5.0: Aggressive-autonomous AI quality framework. Auto-resolves ambiguous user intent, persists conversation memory across sessions, validates every code output, and enforces modern UI/UX standards. Supports Python, JavaScript, TypeScript, HTML, CSS."
---

# Goby v5.0 — Aggressive-Autonomous AI Quality Engine

## 🚨 ACTIVATION: ALWAYS-ON (NOT OPTIONAL)

Goby activates **automatically** on every task. You do NOT wait for the user to mention Goby.

**TRIGGER CONDITIONS (execute the matching action IMMEDIATELY):**

| When this happens... | You MUST do this... |
|---------------------|---------------------|
| User sends ANY request | Run `goby intent '<request>'` to resolve intent FIRST |
| Intent is ambiguous (ambiguity > 0.5) | Ask clarification questions from intent tree |
| About to start coding | Run `goby recall '<intent>'` to check past context |
| After writing/editing ANY code file | Run `goby check <filepath>` to validate |
| Error persists after 2 attempts | Run `goby recall` to check known fixes, halt naive retries |
| Task is complete | Run `goby gate` + `python -m unittest discover tests/` |
| Both gates pass | Run `goby save '<summary>' <type> [files...]` |

---

## 🧠 Core Pipeline (Deterministic & Linear)

```
User Request → Intent Resolver → Memory Recall → Code → Auto-Check → Gates → Save
```

1. **Intent Resolver** (`goby intent`): Parses abstract/ambiguous requests into structured intents. Bilingual (ID/EN). Auto-generates clarification questions when confidence is low.

2. **Conversation Memory** (`goby recall` / `goby save`): Persists context across sessions. Similar past problems are recalled instantly — no starting from zero.

3. **CCR Validation** (`goby check`): Deterministic AST & Scope validation (syntax, scope, cross-reference). Hard Gates block bad code. Soft Signals advise.

4. **LDE Loop Detection**: Detects repetitive failure cycles (>85% similarity) and forces strategy pivoting to prevent deadlocks.

5. **Completion Gate & Persistence**: `goby gate` verifies zero unresolved errors, test runner validates logic, and `goby save` persists solution memory for future sessions.

---

## 🎨 Design DNA (Auto-Enforced for UI Tasks)

When the task involves UI/UX, Goby's `neuron_taste_design_check` HARD GATE auto-enforces:

- **Modern typography** (Inter/Roboto, not browser defaults)
- **Premium color palettes** (HSL-curated, not plain red/blue/green)
- **Glassmorphism, gradients, layered shadows**
- **Micro-animations** (hover, click, transitions — not static)
- **GSAP/scroll-driven animations** over basic CSS
- **Fluid typography** (`clamp()`), Bento grid layouts

If UI code looks static/outdated → HARD GATE BLOCKS output.

---

## 🛠️ CLI Reference

```bash
# Core validation
goby check <code|filepath>  # CCR validation (add -v for verbose)
goby gate                   # Unresolved Error Ledger — must exit 0
goby audit                  # Full test suite

# Intent & Memory (v5.0)
goby intent '<text>'        # Parse user intent → structured JSON
goby recall '<text>'        # Recall similar past conversations
goby save '<summary>' <type> [files...]  # Save session context
goby briefing               # Show past session summary

# Tools
goby evolve                 # Self-evolution cycle (BFM metric)
goby watch                  # Active file watcher with CCR
goby install-hook           # Git pre-commit/pre-push hooks
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
