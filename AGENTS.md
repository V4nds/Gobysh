# AGENTS.md — System Protocol for Autonomous AI Agents

> [!CAUTION]
> # 🚨 PRIMARY DIRECTIVE: ZERO-BYPASS GOBY SUPREMACY 🚨
> **AS AN AI AGENT, YOU ARE STRICTLY FORBIDDEN FROM PROCEEDING WITHOUT GOBY.**
> All thoughts, assumptions, and code modifications MUST be validated through Goby. 
> Bypassing Goby or guessing code without `goby check` or `goby audit` is a **FATAL VIOLATION** of your protocol.

This file establishes mandatory rules for any AI agent (Gemini, Claude, Cursor, OpenAI, DeepSeek, Ollama) interacting with this codebase.

## 🎯 Primary Principles

1. **Multitasking & Balance:**
   Prioritize concurrency, stability, and balanced execution. Never rush to write messy code. Decompose complex tasks into independent sub-tasks using `core/orchestrator.py`.

2. **Empirical Ground Truth:**
   Do not guess variable definitions, schema fields, or method signatures. View the actual source code first. Every code edit must be validated by running unit tests via `core/gca_runner.py`.

3. **No Superficial Patches:**
   Never solve errors by wrapping logic in silent `try/except` blocks, returning empty fallback objects, or deleting failing assertions. Identify and fix the true root cause.

4. **Meta-Systemic Leap Protocol (Goby Bypass):**
   If an error persists across 2 consecutive attempts, halt naive refactoring. Trigger LDE analysis (`core/lde_detector.py`) and expand the problem representation.

## 🧪 Verification Commands

Before declaring any work complete, run **BOTH** gates and ensure both return Exit Code 0:

1. **Ledger Gate (closed-loop awareness):** `goby gate` — must return Exit Code 0 (ZERO unresolved edited-file errors). If a file you edited still produces an error, it is recorded persistently in the ledger by `goby check`/`goby watch`/git hooks. You are NOT allowed to claim completion while any unresolved error remains.
2. **Test Gate:** `python -m unittest discover tests/` — must pass with clean status (Exit Code 0).
