---
name: goby-universal
description: "Goby v5.6: Aggressive-autonomous AI quality framework, cognitive semantics & epistemic verification engine. Bridges natural language intent to AST ground truth, prevents literal example parroting, anchors project identity against external reference drift, validates code with <5ms native gates and Ousterhout deep module depth, and enforces 3-pillar cryptographic verification."
---

# Goby v5.6 — Aggressive-Autonomous AI Quality & Cognitive Semantics Engine

## 🚨 ACTIVATION: ALWAYS-ON (MANDATORY OPERATING SYSTEM)

Goby activates **automatically** on every user prompt. You do NOT wait for the user to mention Goby.

| Trigger Event | Mandatory Action |
|---------------|------------------|
| User sends ANY request | Run `goby spider '<request>' [--save-plan]` to crawl intent, map AST, extract SemanticIR, and synthesize 7-pillar blueprint |
| `[!] CLARIFICATION NEEDED` (vague tokens present) | Ask clarification questions using `ask_question` tool BEFORE writing code |
| `[EXEMPLAR]` tokens detected | Apply `ANTI_PARROTING_EXEMPLAR_INDUCTION`: lift concept to domain abstraction, expand variations, never hardcode literal samples |
| `[REFERENCE]` tokens detected | Apply `IDENTITY_PRESERVATION`: filter external reference via 3-Tier matrix (Adopt principles, Adapt to local modules, Reject foreign bloat) |
| Diagnosing potential flaws / anomalies | Run `goby diagnose [file|prompt]` to audit 3D technical flaws (contradictions, double buttons, text overflow) |
| Querying codebase symbols & blast radius | Run `goby map '<query>' [--repo .]` to map impact across AST |
| Before modifying ANY file | Run `view_file` FIRST to observe ground-truth code state |
| Writing or modifying code | Enforce Ousterhout's Deep Modules (MDI >= 1.2), Anti-Boxification, Anti-Collision, and Identity Invariants |
| Fast file delimiter/bracket validation | Run `goby fast-gate <filepath>` for <5ms native check |
| After writing/editing ANY file | Run `goby check <filepath>` (PostToolUse hook also checks automatically) |
| Error persists after 2 attempts | Run `goby recall` to check known fixes, halt naive retries, trigger dialectical escalation |
| Task completion claim | Run `goby audit` (dynamic tests + SHA-256 code hash) + `goby gate` (3-Pillar Epistemic Exit Gate must exit 0) |
| Both gates pass | Run `goby save '<summary>' <type> [files...]` to persist session memory |

---

## 🧠 Core Architecture: 4 Cognitive Semantic Pillars

### 1. Tripartite Semantic Bridge & Formal SemanticIR
- **Bidirectional Grounding:** Translates natural language (Indonesian, English, mixed colloquial) $\leftrightarrow$ Semantic Intent Ontologies $\leftrightarrow$ Ground-truth AST symbols & files.
- **Formal SemanticIR:** Prompt Spider constructs a formal `SemanticIR` (`Specification`, `Requirements`, `Constraints`, `PreservationContract`) and verifies it using `ContractValidator` to catch multi-clause contradictions before coding starts.
- **Action Ontologies:** Accurately classifies actions (`create_feature`, `fix_bug`, `refactor`, `design_ui`, `audit_review`, `calibrate`, `delete`).

### 2. Exemplar Induction Engine (`ANTI_PARROTING_EXEMPLAR_INDUCTION`)
- **Concept Lifting:** When a user mentions 2-3 examples (e.g. *"misal tombol sudut, penggaris, atau busur"*), Goby identifies the underlying domain concept (`geometric_measurement_tools`) rather than copying the exact samples.
- **Variation Expansion:** Synthesizes rich contextual variations and injects a mandatory blueprint rule:
  ```markdown
  - RULE: ANTI_PARROTING_EXEMPLAR_INDUCTION: Token [A, B] adalah sampel ilustratif.
    Wajib rancang abstraksi polimorfik/generik, dilarang meniru/hardcode 2-3 contoh secara harfiah.
  ```

### 3. Project Identity Anchor & 3-Tier Selective Synthesis (`IDENTITY_PRESERVATION`)
- **Ground-of-Being Invariants:** Grounded in `pyproject.toml` and `README.md`. Prevents the AI from corrupting the repository orientation when external references or URLs are provided.
- **3-Tier Reference Matrix (`goby anchor --ref <url|name>`):**
  - **Tier 1 (Adopt):** Architectural principles, quality bars, and formal contract discipline.
  - **Tier 2 (Adapt):** Translate and adapt into existing Goby idiomatic modules (`StateMemory`, `CCR`, `PromptSpider`).
  - **Tier 3 (Reject):** Strictly reject foreign domain runtimes, alien binary dependencies, or off-topic bloat.
- **CCR Guardrail (`neuron_identity_drift`):** HARD GATE blocking project renaming, deletion of core public API re-exports, or un-adapted foreign monolithic dumps.

### 4. 3-Pillar Epistemic Verification & Antigravity Lifecycle Hard-Stops
- **Pillar 1: Static Code Health:** 0 unresolved CCR errors on the cognitive map ledger.
- **Pillar 2: Dynamic Test Freshness:** Cryptographic SHA-256 workspace fingerprint. Any file edits after the test pass mark evidence as `STALE`, blocking completion.
- **Pillar 3: Task Obligation Ledger:** Prompt claims are tracked as formal obligations in `cognitive_map.json` and must be verified by test execution (`goby audit`).
- **Antigravity Hard-Stop:** `.agents/hooks.json` mechanically rejects IDE stop requests if any pillar fails.

---

## 🎨 Design & Layout Governors

- **Anti-Boxification (Visual Density Governor):** Avoids cramping information into fixed-height, nested card boxes where text overflows or clips. Promotes native, fluid CSS layouts, semantic HTML (`<output>`, `<meter>`, `<dl>`), and contextual HUDs.
- **Anti-Collision Engine (ComponentCapabilityRegistry):** Ensures controls and features are not accidentally duplicated across different surfaces (Toolbar vs Canvas vs Sidebar).
- **Architectural Depth (DepthEngine):** Module Depth Index ($MDI \ge 1.2$). Shallow pass-through wrappers escalate automatically to HARD GATE failures.

---

## 🛠️ CLI Reference

```bash
# Core validation & Diagnostics
goby check <code|filepath>  # CCR validation (add -v for verbose, --intent '<text>' for alignment)
goby verify '<code_string>' # Genuine pre-output in-memory verification
goby fast-gate <filepath>   # Ultra-fast native delimiter & structural gate (<5ms)
goby native <subcommand>    # Direct interface to goby_core Rust native accelerator (scan|check|version)
goby deepen [file|dir]      # Architectural depth & leverage analysis (Ousterhout's MDI)
goby anchor [--ref <url>]   # Display Ground-of-Being project identity & 3-tier reference policy
goby diagnose [file|prompt] # Audit 3D technical flaws (contradictions, double buttons, text overflow)
goby gate                   # 3-Pillar Epistemic Exit Gate — must exit 0
goby audit                  # Run full test suite, compute SHA-256 fingerprint, resolve obligations

# Prompt Spider, Intent & Repository Mapping (v5.6)
goby spider '<prompt>' [--save-plan] [--json] # Crawl prompt, tag tokens, construct SemanticIR, and synthesize blueprint
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

## ⚡ Non-Negotiable Engineering Rules

1. **Evidence Over Assertion:** Never claim done without `goby gate` Exit Code 0.
2. **View Before Write:** Always `view_file` real ground-truth code before editing.
3. **Deep Modules Only:** Build small, expressive interfaces that hide rich internal logic.
4. **Auto-Check Always:** Every file write triggers CCR validation.
5. **No Superficial Patches:** Fix root causes; never silence errors with empty try/except.
6. **2-Strike Escalation:** 2 failed attempts on the same issue $\rightarrow$ halt, run `goby evolve`, pivot fundamentally.
