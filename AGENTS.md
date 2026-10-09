# AGENTS.md — Goby v5.3 Context Architecture, Dialectical Protocol & Architectural Depth

> [!CAUTION]
> # 🚨 THIS IS NOT OPTIONAL — IT IS YOUR OPERATING SYSTEM 🚨
> **Every step below is MANDATORY. Skipping ANY step is a protocol violation.**
> This is not a reference doc. This is a **step-by-step execution pipeline** you follow on EVERY task.

---

## ⚡ STEP 1: HUMAN INTENT INGESTION & DIALECTICAL MANDATE (Before ANY work)

**WHEN:** You receive ANY user request  
**DO:** Run intent resolution FIRST to perceive the human's projection. Never start coding before understanding intent.

```bash
goby intent '<user_request_text>'
```

**IF** `clarification_needed: true` → Ask the user the suggested questions BEFORE writing code.  
**IF** `ambiguity_score > 0.5` → Explicitly state your interpretation and ask for confirmation.  
**NEVER** guess what the user wants when their request is abstract or ambiguous.

Output `goby intent` generates the **Dialectical Mandate for AI Cognition**: the architectural guardrails, tradeoffs, and blindspots that your upcoming thinking must rigorously address.

---

## 🧠 STEP 2: BOUNDLESS REASONING & PROPOSAL AUDIT (Antigravity Thinking)

**WHEN:** Intent is resolved and clear  
**DO:** Check past memory and formulate your solution proposal using the model's full reasoning, logic, and data processing power.

```bash
goby recall '<intent_summary>'
```

### ⚔️ DIALECTICAL AUDIT (Anti-Sycophancy Rule on AI Proposal)
- Pada fase ideation, perumusan plan, atau desain arsitektur, **DILARANG MENJADI YES-MAN**.
- Sycophancy adalah kesalahan AI ketika sekadar mengiyakan permintaan tanpa pertimbangan arsitektur.
- Proposisi rencana Anda **WAJIB**:
  1. Menjawab *trade-offs* dan *blindspots* yang tercantum pada Dialectical Mandate.
  2. Menyajikan minimal 1 kritik konstruktif atau alternatif dengan *higher leverage* (counter-vector).
  3. Jangan tergesa-gesa mengiyakan solusi klise/boilerplate tanpa menguji *Single Source of Truth* dan *Architectural Depth*.
- Anda dapat menguji keabsahan rencana Anda sendiri via CLI:
  ```bash
  goby spar '<ai_proposal_summary>' --intent '<user_request_text>'
  ```

---

## 🔍 STEP 3: VIEW BEFORE WRITE (Empirical ground truth)

**WHEN:** You are about to modify any file  
**DO:** Always `view_file` the target file FIRST to see the actual current state.

- Do NOT guess variable definitions, schema fields, or method signatures.
- Do NOT assume file contents from memory or context window.
- Every code edit must be grounded in what the file actually contains RIGHT NOW.

---

## ✍️ STEP 4: WRITE CODE (With quality & depth gates)

**WHEN:** You write or modify code  
**DO:** Follow these constraints:

1. **No Superficial Patches:** Never wrap logic in silent `try/except` blocks, return empty fallback objects, or delete failing assertions. Fix the true root cause.
2. **Decompose Complex Tasks:** Break into independent sub-tasks. Don't rush to write messy monolithic code.
3. **Preserve Existing Behavior:** Don't break things that already work. Check imports, function signatures, and test assertions.
4. **Anti-Boxification (Visual Density Governor):** Jangan memaksakan semua nilai, simbol, dan teks penjelasan masuk ke dalam frame box/card klise. Gunakan layout CSS native, semantic HTML (`<output>`, `<meter>`, `<dl>`), atau HUD kontekstual.
5. **Anti-Collision (Single Source of Truth):** Pastikan kapabilitas/kontrol tidak diduplikasi di tempat lain (*double fitur bocor*). Verifikasi topologi komponen (`ComponentCapabilityRegistry`) sebelum membuat kontrol baru.
6. **Architectural Depth & Conditional Hard Gate Escalation (Ousterhout's Law):**
   - Desain *Deep Modules* (antarmuka publik ringkas yang menyembunyikan logika kompleks internal). Hindari modul dangkal / *shallow pass-through wrappers*.
   - **Conditional Hard Gate Escalation:** Jika sebuah modul terdeteksi *extreme shallow* ($MDI < 1.0$ dan $\ge 2$ pass-through delegators), gate otomatis ter-eskalasi dari `SOFT` menjadi **`HARD GATE`**. `goby check` akan exit code 1 dan masuk ke Unresolved Error Ledger.
   - Verifikasi kedalaman kode Anda via `goby deepen <filepath>`.


---

## ✅ STEP 5: POST-WRITE VALIDATION & AGGRESSIVE TELEMETRY (Mechanically Automated)

**WHEN:** After EVERY file write/edit  
**DO:** Goby is mechanically hooked into Antigravity (`.agents/hooks.json`):
- **`PostToolUse`** automatically intercepts file writes/edits, verifies code with CCR, injects **Aggressive Telemetry** ($MDI$ score, gate verdicts) to `stderr`, and updates the Unresolved Error Ledger (`cognitive_map.json`).
- **`PreInvocation`** injects active ledger warnings and architectural mandates directly into the prompt before the model speaks.
- **`Stop`** mechanically blocks the agent loop from finishing if any unresolved errors remain.

You can also run manually anytime:
```bash
goby check <filepath>
```

**IF** CCR Hard Gate FAILS (termasuk escalated Architectural Depth) → Fix the issue immediately. Do NOT proceed.  
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
