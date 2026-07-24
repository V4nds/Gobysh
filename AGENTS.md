# AGENTS.md — System Protocol for Autonomous AI Agents

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

Before declaring any work complete, run:
```bash
python -m unittest discover tests/
```
Ensure all tests pass with clean status (Exit Code 0).
