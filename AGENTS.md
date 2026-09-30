# AGENTS.md — Goby v5.0 Aggressive-Autonomous Protocol

> [!CAUTION]
> # 🚨 THIS IS NOT OPTIONAL — IT IS YOUR OPERATING SYSTEM 🚨
> **Every step below is MANDATORY. Skipping ANY step is a protocol violation.**
> This is not a reference doc. This is a **step-by-step execution pipeline** you follow on EVERY task.

---

## ⚡ STEP 1: INTENT RESOLUTION (Before ANY work)

**WHEN:** You receive ANY user request  
**DO:** Run intent resolution FIRST. Never start coding before understanding intent.

```bash
goby intent '<user_request_text>'
```

**IF** `clarification_needed: true` → Ask the user the suggested questions BEFORE writing code.  
**IF** `ambiguity_score > 0.5` → Explicitly state your interpretation and ask for confirmation.  
**NEVER** guess what the user wants when their request is abstract or ambiguous.

---

## 🧠 STEP 2: MEMORY RECALL (Before starting work)

**WHEN:** Intent is resolved and clear  
**DO:** Check if similar work was done before.

```bash
goby recall '<intent_summary>'
```

**IF** similar past context found → Use it as a starting point. Don't repeat past mistakes.  
**IF** no context found → Proceed normally, but flag this as a new knowledge area.

---

## 🔍 STEP 3: VIEW BEFORE WRITE (Empirical ground truth)

**WHEN:** You are about to modify any file  
**DO:** Always `view_file` the target file FIRST to see the actual current state.

- Do NOT guess variable definitions, schema fields, or method signatures.
- Do NOT assume file contents from memory or context window.
- Every code edit must be grounded in what the file actually contains RIGHT NOW.

---

## ✍️ STEP 4: WRITE CODE (With quality gates)

**WHEN:** You write or modify code  
**DO:** Follow these constraints:

1. **No Superficial Patches:** Never wrap logic in silent `try/except` blocks, return empty fallback objects, or delete failing assertions. Fix the true root cause.
2. **Decompose Complex Tasks:** Break into independent sub-tasks. Don't rush to write messy monolithic code.
3. **Preserve Existing Behavior:** Don't break things that already work. Check imports, function signatures, and test assertions.

---

## ✅ STEP 5: POST-WRITE VALIDATION (Mechanically Automated)

**WHEN:** After EVERY file write/edit  
**DO:** Goby is mechanically hooked into Antigravity (`.agents/hooks.json`):
- **`PostToolUse`** automatically intercepts file writes/edits, verifies code with CCR, and updates the Unresolved Error Ledger (`cognitive_map.json`).
- **`PreInvocation`** injects active ledger warnings directly into the prompt before the model speaks.
- **`Stop`** mechanically blocks the agent loop from finishing if any unresolved errors remain.

You can also run manually anytime:
```bash
goby check <filepath>
```

**IF** CCR Hard Gate FAILS → Fix the issue immediately. Do NOT proceed.  
**IF** error persists across 2 attempts → Halt naive refactoring. Run `goby evolve` or query Universal Memory. Expand the problem representation. Do not blindly retry the same approach.

---

## 🏁 STEP 6: COMPLETION GATES (Before declaring done)

**WHEN:** You believe the task is complete  
**DO:** Run BOTH gates. Both MUST return Exit Code 0.

```bash
# Gate 1: Zero unresolved file errors
goby gate

# Gate 2: All tests pass
python -m unittest discover tests/
```

**IF** either gate fails → You are NOT done. Fix and retry.  
**NEVER** claim completion without both gates passing.

---

## 💾 STEP 7: SAVE CONTEXT (After completion)

**WHEN:** Task is verified complete (both gates pass)  
**DO:** Save the session context for future recall.

```bash
goby save '<what_was_done>' <task_type> [modified_files...]
```

This ensures the next session can recall what was done and avoid repeating the same exploration.

---

## 🔄 ERROR ESCALATION PROTOCOL

| Condition | Action |
|-----------|--------|
| 1st failure | Fix directly based on error message |
| 2nd failure on same issue | HALT naive refactoring. Run `goby evolve`. Check Universal Memory. Try a fundamentally different approach. |
| Error matches known pattern | Apply the stored solution from memory (`goby recall`) |
| Ambiguous user request | Ask clarification questions (`goby intent`). Do NOT guess. |
