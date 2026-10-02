# GOBYSH — ARCHITECTURE CALIBRATION & EVOLUTION SPECIFICATION
## Semantic Adhesion, Deterministic Support, Bounded Execution, and Evidence-Grounded AI Coding

**Document Type:** Engineering Architecture / AI Executor Specification  
**Repository:** `V4nds/Gobysh`  
**Baseline:** Gobysh v5.x architecture as currently implemented  
**Status:** Target architecture for controlled evolution  
**Primary Objective:** Recalibrate Gobysh without destroying existing capabilities, while creating a stronger and materially useful support layer between human intent, AI reasoning, code transformation, and mechanically verifiable evidence.

---

## 0. EXECUTIVE DIRECTIVE

Gobysh must **not** become a replacement reasoning engine for the AI model.

The AI remains responsible for reasoning, planning, selecting approaches, generating code, and deciding among legitimate implementation alternatives.

Gobysh exists outside that intelligence as a **support, control, semantic-adhesion, and evidence layer** whose purpose is to make the AI's actions more faithful to the user's intent and more mechanically accountable to the actual software state.

The core design equation is:

```text
Human Intent
    ↓
Semantic Adhesion
    ↓
Formal Contract / Semantic IR
    ↓
AI Reasoning & Action
    ↓
Code / System Mapping
    ↓
Mechanical Verification
    ↓
Evidence Ledger
    ↓
Finite Execution State
```

The target is not:

```text
"Make the AI smarter than the AI."
```

The target is:

```text
"Make the consequences of AI reasoning more grounded, traceable,
bounded, and faithful to the intent that initiated the task."
```

---

# 1. FUNDAMENTAL DESIGN POSITION

## 1.1 Gobysh is a support layer, not the model's fundamental cognition

The model may reason probabilistically. Gobysh should provide deterministic boundaries around the consequences of that reasoning where deterministic verification is possible.

Therefore:

```text
AI = reasoning / planning / generation
Gobysh = interpretation support / constraints / control / verification / evidence
Toolchain = compiler / parser / test runner / runtime / linter / type checker
```

Gobysh must not attempt to emulate a frontier model's general reasoning ability.

It should instead externalize state that would otherwise exist only inside a model context window.

Examples:

```text
AI belief:
"The user probably does not want the database schema changed."

Gobysh representation:
constraint.database_schema = PRESERVE
```

```text
AI statement:
"The bug is fixed."

Gobysh response:
No claim is accepted until the required verification evidence exists.
```

---

# 2. NON-NEGOTIABLE PRINCIPLE: PRESERVE THE EXISTING SYSTEM

## 2.1 Existing functionality must not be removed merely because a stronger mechanism is added

This is a primary architectural constraint.

**Do not delete, disable, bypass, or silently replace existing Gobysh functions solely because a new semantic layer exists.**

Existing functions are treated as established support mechanisms and should be:

- retained;
- wrapped or orchestrated when appropriate;
- supplied with better semantic context;
- connected to stronger evidence;
- moved only when necessary for architectural clarity;
- preserved through compatibility tests.

The intended evolution is:

```text
Existing Capability
       ↓
Preserve
       ↓
Connect
       ↓
Add semantic context
       ↓
Increase verification strength
```

Not:

```text
Old Capability
       ↓
Delete
       ↓
Rewrite everything
```

## 2.2 Why preservation matters

Gobysh already acts as a set of adhesive points between user, agent, workspace, and lifecycle:

- `IntentResolver` helps reduce ambiguity before action.
- `ConversationMemory` preserves context across sessions.
- `CCR` supplies mechanical checks.
- `StateMemory` remembers unresolved state and validation status.
- `LDE` detects repetitive failure patterns.
- `Hooks` enforce checks at execution lifecycle boundaries.
- `Output Parsers` turn tool output into structured evidence.

Removing these would destroy accumulated glue that makes the system coherent.

The new architecture must therefore **strengthen the bridge already built**, not replace the bridge.

---

# 3. THE ACTUAL PROBLEM TO SOLVE

The primary problem is not simply that AI can generate incorrect code.

The deeper problem is that meaning can drift as information moves through several representations:

```text
Human thought
    ↓
Natural-language sentence
    ↓
AI interpretation
    ↓
Internal plan
    ↓
Tool call
    ↓
Source code
    ↓
Program structure
    ↓
Runtime behavior
    ↓
Claim of completion
```

At every transition there can be semantic drift.

A user may say:

> "Tambahkan login, tapi jangan ubah user table lama."

The intended meaning may contain several distinct constraints:

```text
ADD authentication behavior
PRESERVE existing user table
PRESERVE schema
PRESERVE unrelated behavior
SCOPE changes to authentication flow
```

A model may still produce something that looks linguistically related while violating one of those constraints.

Therefore Gobysh's central value should become:

> **Preserve the identity of the user's intent across representation boundaries.**

This is the meaning of **Semantic Adhesion** in this specification.

---

# 4. SEMANTIC ADHESION — THE CENTRAL CONCEPT

## 4.1 Definition

Semantic Adhesion is the mechanism that keeps the important meaning of an instruction attached to the task while that task moves from natural language into formal specification, AI actions, source-code changes, and verification evidence.

It is not merely semantic similarity.

It contains at least:

```text
Meaning
Scope
Negation
Constraints
Preservation requirements
Preconditions
Postconditions
Invariants
Target entities
Protected entities
Expected behavior
Acceptance evidence
```

## 4.2 Semantic similarity is not semantic fidelity

Do not use lexical or embedding similarity as proof of correctness.

For example:

```text
User:
"Jangan hapus fungsi lama."

AI result:
"The old function was removed because it is obsolete."
```

The texts are semantically related, but the result is a direct violation.

Therefore the hierarchy is:

```text
Similarity
   ↓
Relevance
   ↓
Semantic Alignment
   ↓
Constraint Compliance
   ↓
Behavioral Compliance
   ↓
Evidence
```

The lower layers must dominate the upper layers whenever they conflict.

---

# 5. CURRENT GOBYSH FUNCTIONS — KEEP AND RECALIBRATE

The current repository already contains the following important components.

## 5.1 `core/intent_resolver.py`

Current role:

```text
User Request
    ↓
IntentTree
    ↓
SemanticContract
```

Current useful capabilities include:

- bilingual Indonesian / English handling;
- task-type extraction;
- confidence and ambiguity tracking;
- clarification generation;
- forbidden targets;
- preserved behavior / targets;
- scope restrictions;
- expected traits;
- action verb extraction.

### Recalibration

Do not remove keyword heuristics. They remain useful as a deterministic first-pass extractor.

However:

> Heuristic extraction must no longer be treated as the final semantic truth.

Target flow:

```text
Keyword / Pattern Extraction
          ↓
Candidate Intent
          ↓
Semantic Normalization
          ↓
Constraint Resolution
          ↓
Formal Contract
```

---

## 5.2 `core/conversation_memory.py`

Current role:

```text
Past sessions
   ↓
Fingerprint / similarity recall
   ↓
Context hint
```

Keep it.

But the current notion of "semantic" recall should be treated accurately: lexical normalization plus similarity is useful retrieval support, not proof of semantic equivalence.

### Recalibration

Conversation memory should eventually distinguish:

```text
Historical context
Known solutions
Past failures
Task similarity
Semantic contract
Repository facts
Final evidence
```

A past successful solution may be reused as a candidate reference, but it must never automatically override the current task's contract.

---

## 5.3 `core/ccr_engine.py`

Current role:

```text
Mechanical validation orchestration
```

It already distinguishes hard and soft checks and supports triage.

Keep this architecture.

### Recalibration

CCR becomes the **Verification Orchestrator** rather than merely a collection of "neurons".

Suggested structure:

```text
CCR
 ├── Context Gate
 ├── Semantic Contract Gate
 ├── Syntax Gate
 ├── Scope Gate
 ├── Cross Reference Gate
 ├── Type Gate
 ├── Dependency / Impact Gate
 ├── Behavioral Gate
 ├── Design Heuristics
 ├── Semantic Alignment
 └── Evidence Aggregator
```

Not every check is available for every project. The triage mechanism remains responsible for selecting applicable checks.

---

## 5.4 `core/state_memory.py`

Current role:

- persistent JSON state;
- thread-safe access;
- validation ledger;
- temporal state;
- interrupted-session recovery.

Keep it.

### Recalibration

State memory should evolve toward an **Execution State + Evidence Ledger**.

The critical distinction becomes:

```text
ERROR MEMORY
      vs
REQUIREMENT / EVIDENCE TRACEABILITY
```

The latter is the more important long-term abstraction.

---

## 5.5 `core/lde_detector.py`

Current role:

- repeated failure detection;
- compiler/runtime loops;
- oscillation detection;
- repeated-error patterns;
- known failure recall.

Keep it.

### Recalibration

LDE should not only detect loops after they have happened.

It should participate in a **Finite Execution State Machine** that limits how the agent can respond to failure.

Instead of relying only on:

```text
"try again"
```

use:

```text
FAILURE
   ↓
CLASSIFY
   ↓
REPAIR ALLOWED?
   ↓
TARGETED REPAIR
   ↓
VERIFY
   ↓
PASS / TERMINAL FAIL / UNKNOWN
```

The existing failure-pattern logic remains useful inside this larger control structure.

---

## 5.6 `core/hooks.py`

Current role:

- PostToolUse validation;
- PreInvocation unresolved-error injection;
- Stop Gate.

Keep it.

### Important hardening

The current Stop Gate contains a permissive exception path that allows the agent to stop when the ledger check itself fails.

That behavior is unsafe for a hard-gate claim.

Target behavior:

```text
Verification unavailable
       ↓
UNKNOWN / BLOCKED
       ↓
No PASS claim
```

A hard gate must fail closed when a reliable verification decision cannot be produced.

Use an explicit recovery path rather than silently allowing completion.

---

# 6. TARGET ARCHITECTURE

The recommended target architecture is additive and modular.

```text
Gobysh/
├── core/
│   ├── intent/
│   │   ├── resolver.py
│   │   ├── normalizer.py
│   │   └── constraints.py
│   │
│   ├── semantics/
│   │   ├── specification.py
│   │   ├── intermediate_representation.py
│   │   ├── semantic_analyzer.py
│   │   ├── dependency_graph.py
│   │   └── contract_validator.py
│   │
│   ├── translation/
│   │   ├── engine.py
│   │   ├── symbol_mapper.py
│   │   ├── type_mapper.py
│   │   └── adapters/
│   │       ├── python.py
│   │       ├── javascript.py
│   │       └── typescript.py
│   │
│   ├── verification/
│   │   ├── orchestrator.py
│   │   ├── static_analysis.py
│   │   ├── behavioral.py
│   │   ├── semantic_alignment.py
│   │   └── evidence.py
│   │
│   ├── execution/
│   │   ├── bounded_protocol.py
│   │   ├── state_machine.py
│   │   └── finalization.py
│   │
│   ├── ccr_engine.py
│   ├── conversation_memory.py
│   ├── state_memory.py
│   ├── lde_detector.py
│   ├── output_parsers.py
│   └── hooks.py
│
├── tests/
├── benchmarks/
├── docs/
├── AGENTS.md
├── SKILL.md
└── README.md
```

This is a **target structure**, not a mandate to move every file immediately.

Do not create a large rewrite solely to match the tree.

Introduce modules incrementally while preserving compatibility.

---

# 7. SEMANTIC REPRESENTATION / IR

The Semantic IR is the central adhesive object between natural language and code.

## 7.1 Why an intermediate representation exists

Do not rely on direct:

```text
Natural Language → Source Code
```

Instead:

```text
Natural Language
      ↓
Semantic Representation
      ↓
Source / Project Mapping
```

This provides a stable contract regardless of whether the target language is Python, JavaScript, TypeScript, SQL, or another supported language.

## 7.2 Minimum IR fields

```yaml
specification:
  id: unique-task-id
  language: id | en | mixed

intent:
  action: ADD | MODIFY | FIX | REMOVE | EXPLAIN | TEST | CONFIGURE
  target: semantic target
  description: normalized meaning

entities:
  - name: registration_flow
    type: feature

constraints:
  forbidden:
    - user_table
  preserve:
    - existing_schema
    - existing_registration_behavior
  scope:
    - registration_flow

preconditions:
  - email_input_exists

postconditions:
  - invalid_email => account_not_created
  - valid_email => registration_continues

invariants:
  - database_schema_unchanged

protected_symbols:
  - UserModel
  - user_table

acceptance:
  - validation_test_passes
  - schema_hash_unchanged
  - existing_tests_pass
```

The exact serialization format can be JSON, YAML, or an internal Python data structure.

The conceptual schema is more important than the file format.

---

# 8. FORMAL CONTRACT MODEL

Where possible, requests should be expressed through:

```text
Preconditions
Postconditions
Invariants
Constraints
Protected Targets
Required Changes
Evidence Requirements
```

A useful formal notation is:

```text
{P} C {Q}
```

Where:

```text
P = precondition
C = operation / code transition
Q = postcondition
```

Example:

```text
{authenticated(user)}
    access_dashboard(user)
{dashboard_access_granted}
```

And:

```text
{not_authenticated(user)}
    access_dashboard(user)
{dashboard_access_denied}
```

This is not intended to make Gobysh a theorem prover.

The purpose is to give the system a structured vocabulary for expressing constraints that can be checked mechanically when feasible.

---

# 9. CODE-SEMANTIC MAPPING

The new translation layer is not a second AI coding agent.

Its purpose is to map semantic objects to concrete program structures.

## 9.1 Mapping direction

```text
Semantic Entity
      ↓
Repository Entity
      ↓
File
      ↓
Symbol
      ↓
AST / Type / Dependency structure
      ↓
Runtime behavior
```

For example:

```text
"registration flow"
      ↓
AuthController.register
      ↓
app/auth/controller.py
      ↓
register(...)
      ↓
AST nodes / calls / validations
```

This allows Gobysh to answer questions such as:

- Which symbol implements this requirement?
- Which files were actually modified?
- Which protected symbol would be affected by this change?
- Which requirement has no implementation target?
- Which requirement has implementation but no evidence?

## 9.2 Language adapters

Use deterministic language-specific tools when appropriate:

### Python

- `ast`
- symbol / scope inspection
- type checker where available
- pytest / unittest evidence

### JavaScript

- ESTree-compatible parsing
- Babel / parser infrastructure where appropriate
- ESLint where configured
- Jest or project test runner

### TypeScript

- TypeScript Compiler API / compatible parser
- type-checking
- Jest/Vitest/project test runner

### SQL

- parser / dialect-aware analysis
- schema introspection
- migration comparison
- database-level tests when safe

The adapters should map **from a common semantic contract into language-specific program evidence**, not invent a separate semantic philosophy for every language.

---

# 10. CAUSAL / DEPENDENCY GRAPH

A task should not be represented only as files.

It should eventually support a graph such as:

```text
User Requirement
      ↓
Semantic Contract
      ↓
Feature
      ↓
Repository Module
      ↓
File
      ↓
Symbol
      ↓
Dependency
      ↓
Runtime Behavior
      ↓
Test / Evidence
```

This can be called the **Causal Dependency Graph (CDG)**, but it must not be described as formal runtime causality unless that has actually been established.

It is a repository-impact and dependency representation.

The graph is useful for:

- impact analysis;
- protected-target detection;
- change-scope validation;
- requirement-to-code traceability;
- evidence traceability.

---

# 11. EVIDENCE LEDGER

The final system must evolve beyond a file-centric unresolved-error list.

The more powerful abstraction is:

```text
Requirement
    ↓
Mapped Entity
    ↓
Changed Symbol
    ↓
Verification
    ↓
Evidence
    ↓
Final Status
```

Example:

```json
{
  "requirement_id": "REQ-001",
  "statement": "Do not modify existing user schema",
  "protected_targets": ["user_table", "UserModel"],
  "mapped_files": ["db/models.py"],
  "verification": "schema_hash_comparison",
  "evidence": {
    "before": "abc123",
    "after": "abc123"
  },
  "status": "PASS"
}
```

The ledger must support at least four final evidence states:

```text
PASS
FAIL
BLOCKED
UNKNOWN
```

`UNKNOWN` is critical.

If verification cannot establish the result, the system must not turn uncertainty into PASS.

---

# 12. BOUNDED EXECUTION PROTOCOL

The user's requirement for clear boundaries and no endless iteration must become a first-class execution protocol.

## 12.1 Finite state machine

Recommended conceptual states:

```text
RECEIVED
   ↓
INTENT_RESOLVED
   ↓
CONTRACT_FROZEN
   ↓
READY
   ↓
GENERATING
   ↓
VERIFYING
   ├── PASS → FINALIZING → TERMINAL_SUCCESS
   ├── FAIL → REPAIR_ELIGIBLE
   ├── BLOCKED → TERMINAL_BLOCKED
   └── UNKNOWN → TERMINAL_UNKNOWN

REPAIR_ELIGIBLE
   ↓
TARGETED_REPAIR
   ↓
VERIFYING
   ├── PASS → FINALIZING → TERMINAL_SUCCESS
   ├── FAIL → TERMINAL_FAILURE
   ├── BLOCKED → TERMINAL_BLOCKED
   └── UNKNOWN → TERMINAL_UNKNOWN
```

## 12.2 Default repair budget

The default bounded protocol should allow:

```text
1 initial candidate
+
1 targeted repair
=
2 total implementation attempts
```

This does not mean "always two attempts".

It means **never unlimited repair by default**.

## 12.3 When repair is forbidden

Do not permit another repair merely because:

- the model wants to try something else;
- the same error message was paraphrased;
- the same transformation has already failed;
- verification is unavailable;
- the failure originates from missing user information.

Instead:

```text
Missing context → ask user / terminate as blocked
Repeated failure → escalate representation / terminate
Unknown verification → UNKNOWN
```

## 12.4 Stop is a valid result

The system must not equate "continued activity" with success.

Stopping safely can be the correct outcome.

```text
PASS
FAIL
BLOCKED
UNKNOWN
```

All four are legitimate terminal states.

---

# 13. ROLE OF LDE AFTER CALIBRATION

LDE becomes one component of bounded execution, not the entire stopping mechanism.

Its responsibilities:

1. detect repeated failure;
2. detect oscillation;
3. detect ineffective modifications;
4. detect known failure patterns;
5. suggest strategy escalation;
6. prevent mechanical repetition.

Do not claim that LDE's named heuristics constitute formal applications of the mathematical theories referenced by their labels.

Names such as "P vs NP Trap" or "Cantor Lateral Bypass" may remain internal labels if useful, but documentation must describe their actual implementation rather than implying formal mathematical proof or theorem usage.

---

# 14. ROLE OF MEMORY AFTER CALIBRATION

Memory must answer three different questions:

```text
What happened before?
What does the current repository mean?
What has been proven in the current task?
```

These are not the same thing.

Recommended distinction:

```text
Historical Memory
    ↓
Recall candidates

Repository Semantic State
    ↓
Current facts

Execution Evidence
    ↓
Current proof / verification
```

Historical memory is advisory.

Current verification evidence is authoritative.

---

# 15. ROLE OF HOOKS AFTER CALIBRATION

Hooks should remain the physical enforcement layer.

```text
AI intention
   ↓
AI tool invocation
   ↓
Hook boundary
   ↓
Goby semantic / verification layer
   ↓
Allow / Block / Record / Inject
```

Recommended lifecycle responsibilities:

### PreInvocation

- restore relevant semantic contract;
- inject unresolved requirements / failures;
- expose bounded execution state;
- prevent the model from treating stale context as current truth.

### PostToolUse

- identify actual modified files;
- map them to semantic targets;
- run applicable verification;
- update evidence ledger;
- update execution state.

### Stop

- allow termination only when required completion gates are satisfied;
- otherwise return a deterministic reason;
- if verifier itself fails, return UNKNOWN/BLOCKED rather than allow a false PASS.

---

# 16. PRESERVATION AS A FIRST-CLASS CONCEPT

The instruction "don't remove existing functionality" should become more than a sentence in a prompt.

Represent it formally.

Example:

```yaml
preservation:
  required: true
  protected_symbols:
    - old_auth_function
    - user_table
    - public_api
  protected_behaviors:
    - existing_login_flow
    - existing_registration_flow
```

Verification may include:

```text
symbol existence check
API signature check
schema comparison
snapshot comparison
existing test suite
behavioral regression tests
```

The preservation contract should be generated from user intent whenever explicit preservation language exists.

---

# 17. CONTEXT + SEMANTIC GATING

Intent clarity and repository context should be evaluated before implementation.

Recommended order:

```text
1. Intent extraction
2. Context assessment
3. Semantic normalization
4. Contract construction
5. Contradiction detection
6. Scope determination
7. Code mapping
8. AI generation
```

Do not allow the model to begin a complex implementation when the task cannot be represented with sufficient clarity.

However, do not block trivial tasks merely because an elaborate context package is unavailable.

This is where the existing CCR triage mechanism remains useful.

---

# 18. CONTRADICTION DETECTION

The semantic layer must detect incompatible requirements before code changes.

Examples:

```text
"Refactor everything"
+
"Do not change any existing code"
```

or:

```text
"Remove the old API"
+
"Backward compatibility with the old API is mandatory"
```

These cannot be silently reconciled.

Expected result:

```text
CONTRADICTION_DETECTED
→ user clarification required
```

Do not let the model decide invisibly which requirement wins.

---

# 19. SEMANTIC TRANSLATION TRACEABILITY

Every important requirement should eventually be traceable.

Minimum trace format:

```text
REQ-001
  ↓
Semantic entity
  ↓
Repository entity
  ↓
File
  ↓
Symbol / AST region
  ↓
Change
  ↓
Verification
  ↓
Evidence
```

If a requirement cannot be mapped to a code target, that is not necessarily an error, but it must be explicitly represented:

```text
UNMAPPED_REQUIREMENT
```

Likewise, code changes with no corresponding semantic requirement should be inspectable as:

```text
UNJUSTIFIED_CHANGE
```

This is substantially stronger than simple text similarity.

---

# 20. FRESHNESS / ANTI-GIMMICK CRITERION

Gobysh must not add a feature merely because it sounds novel.

A proposed feature must pass the following questions.

## 20.1 Does the model already do this?

If yes, ask whether Gobysh adds an **external guarantee, traceability, boundedness, or evidence mechanism**.

If it adds none, reject the feature or move it to optional convenience tooling.

## 20.2 Does the feature remain useful if the model gets substantially better?

This is a critical architectural test.

Bad dependency:

```text
Gobysh value = model is weak
```

Better dependency:

```text
Gobysh value = consequences remain externally constrained and verifiable
```

As models improve, Gobysh should remain relevant because stronger models can execute more powerful tasks that also require stronger state, dependency, and verification control.

## 20.3 Can the improvement be benchmarked?

Prefer measurable properties such as:

```text
Intent preservation rate
Constraint violation rate
Regression rate
False completion rate
Unbounded retry count
Unknown verification rate
Requirement-to-evidence coverage
Unjustified change rate
Translation traceability
```

Do not use subjective claims such as "the AI feels smarter" as a primary metric.

---

# 21. DETERMINISM: WHAT GOBYSH CAN AND CANNOT CLAIM

Gobysh should claim deterministic behavior only for operations that are actually deterministic under fixed inputs and toolchain conditions.

Good claim:

```text
Same specification + same repository state + same verifier configuration
=> same verification decision
```

Bad claim:

```text
Gobysh makes the entire AI reasoning process deterministic.
```

The latter is not realistic.

The intended architecture is:

```text
Probabilistic reasoning
        ↓
Deterministic constraints
        ↓
Deterministic verification where possible
        ↓
Explicit uncertainty where not possible
```

---

# 22. HARD / SOFT / UNKNOWN GATE MODEL

Use three semantic verification classes.

## HARD

Machine-verifiable condition whose failure blocks completion.

Examples:

- syntax failure;
- protected symbol deleted;
- required invariant violated;
- required test failure;
- forbidden target modified.

## SOFT

Advisory signal that informs but does not by itself block completion unless explicitly configured.

Examples:

- style heuristics;
- information density;
- design taste;
- contextual relevance.

## UNKNOWN

The system cannot reliably establish PASS or FAIL.

Unknown must never be coerced into PASS.

---

# 23. UI / DESIGN HEURISTICS

Existing design-quality checks may remain.

However, design taste should not be confused with objective semantic correctness.

Examples of heuristic criteria:

```text
modern typography
spacing
layout consistency
motion quality
visual hierarchy
responsive structure
```

These are generally SOFT unless the project explicitly promotes them to HARD acceptance requirements.

Do not allow aesthetic preference to override explicit product requirements.

---

# 24. OPTIMAL FINE-TUNED WORKFLOW

This is the recommended end-to-end workflow for the AI executor.

## PHASE A — UNDERSTAND

```text
Receive request
   ↓
Run intent extraction
   ↓
Detect language
   ↓
Detect ambiguity / uncertainty
   ↓
Retrieve relevant memory
   ↓
Assess available repository context
```

Output:

```text
Intent Candidate
Context Assessment
Recall Context
```

---

## PHASE B — NORMALIZE

```text
Intent Candidate
      ↓
Semantic normalization
      ↓
Negation extraction
      ↓
Constraint extraction
      ↓
Preservation extraction
      ↓
Scope extraction
      ↓
Requirement decomposition
```

Output:

```text
Semantic Contract
```

---

## PHASE C — VALIDATE THE CONTRACT

Before code changes:

```text
Check contradiction
Check missing critical information
Check protected targets
Check requested scope
Check acceptance conditions
```

Possible outputs:

```text
READY
NEEDS_CLARIFICATION
CONTRADICTORY
BLOCKED
```

Do not enter code generation when the contract is structurally invalid.

---

## PHASE D — FREEZE THE CONTRACT

Once the contract is accepted for execution:

```text
CONTRACT_FROZEN = true
```

This is important.

The AI may reason about implementation strategies, but it must not silently rewrite the user's requirements merely because a later implementation becomes inconvenient.

If the contract itself must change:

```text
new interpretation
    ↓
contract revision
    ↓
re-validation
```

This is a semantic transition, not an invisible implementation detail.

---

## PHASE E — MAP SEMANTICS TO CODE

```text
Contract
   ↓
Repository analysis
   ↓
Relevant files
   ↓
Symbols
   ↓
Dependencies
   ↓
Protected regions
```

Create an explicit change scope.

Example:

```yaml
scope:
  allowed:
    - app/auth/controller.py
    - app/auth/validators.py
  protected:
    - app/db/models.py
    - app/public_api.py
```

---

## PHASE F — AI REASONING / IMPLEMENTATION

Now the AI does what it is good at:

- select architecture;
- design code;
- write implementation;
- reason about tradeoffs;
- generate tests.

Gobysh does not need to micromanage every internal thought.

It monitors the consequences.

---

## PHASE G — POST-ACTION VERIFICATION

Immediately after the relevant tool operation:

```text
Actual file changes
      ↓
Semantic scope check
      ↓
Syntax
      ↓
Scope
      ↓
References
      ↓
Types
      ↓
Behavior
      ↓
Tests
      ↓
Contract compliance
```

Record every result as evidence.

---

## PHASE H — FAILURE HANDLING

If verification fails:

```text
FAIL
 ↓
Classify failure
 ↓
Check known pattern / memory
 ↓
Check LDE history
 ↓
Determine whether targeted repair is valid
```

Only then allow a repair.

Never default to:

```text
FAIL → TRY AGAIN
```

Use:

```text
FAIL → DIAGNOSE → REPAIR_ELIGIBILITY → TARGETED_REPAIR
```

---

## PHASE I — SECOND VERIFICATION

After the single targeted repair budget is consumed:

```text
VERIFY AGAIN
```

Possible outcomes:

```text
PASS
FAIL
BLOCKED
UNKNOWN
```

No automatic third attempt in the default bounded protocol.

---

## PHASE J — FINALIZATION

The system may declare success only when:

```text
Contract satisfied
+
Required hard gates pass
+
Required tests pass
+
No unresolved critical ledger entries
+
Evidence exists for required acceptance conditions
```

Then:

```text
FINALIZE
 ↓
SAVE RELEVANT CONTEXT
 ↓
TERMINAL_SUCCESS
```

---

# 25. FINALIZATION MUST BE EVIDENCE-BASED

The phrase:

> "Selesai, sudah diperbaiki."

must not itself count as evidence.

Instead:

```text
Claim
 ↓
Requirement
 ↓
Verification
 ↓
Evidence
 ↓
Status
```

If evidence is missing:

```text
UNKNOWN
```

The system should be mechanically incapable of transforming a missing verification result into a PASS completion state.

---

# 26. REQUIREMENT-TO-EVIDENCE COVERAGE

A useful final metric is:

```text
coverage = verified_requirements / required_requirements
```

For hard completion:

```text
coverage = 100%
```

unless a requirement is explicitly marked not applicable or deferred by the user.

The implementation should record the reason for non-applicability rather than silently dropping the requirement.

---

# 27. PRESERVE + DELTA MODEL

To make preservation concrete, compare:

```text
Repository BEFORE
        ↓
Requested DELTA
        ↓
Repository AFTER
```

The verifier should ask:

```text
What changed?
What should have changed?
What should not have changed?
```

This produces a powerful invariant:

```text
Actual Delta ⊆ Allowed Delta
```

Where mechanically enforceable.

A stronger form is:

```text
Protected Delta = 0
```

for explicitly immutable targets.

---

# 28. UNJUSTIFIED CHANGE DETECTION

A future semantic verifier should identify changes that cannot be associated with any active requirement or necessary dependency effect.

Example:

```text
User requested:
add email validation
```

AI modified:

```text
validator.py
registration.py
user_model.py
billing.py
landing_page.css
```

Even if the resulting code passes tests, the system should surface:

```text
UNJUSTIFIED_CHANGE
```

for changes lacking semantic traceability.

This is not an automatic rejection in every case; some transitive changes may be legitimate.

But the system should make the discrepancy observable.

---

# 29. BACKWARD COMPATIBILITY REQUIREMENTS

Before changing existing Gobysh modules:

```text
Inspect current implementation
 ↓
Understand current API
 ↓
Create characterization tests
 ↓
Add new behavior
 ↓
Run old tests
 ↓
Run new tests
```

Do not rewrite based on assumptions.

Do not infer current file structure from documentation alone.

The repository itself is the ground truth.

---

# 30. IMPLEMENTATION STRATEGY — DO NOT REWRITE EVERYTHING

The recommended implementation order is additive.

## Stage 1 — Formal semantic core

Add:

```text
Semantic Specification
Semantic IR
Constraint model
Requirement model
```

Connect them to the existing `IntentResolver`.

## Stage 2 — Contract validation

Add:

```text
negation handling
contradiction detection
preservation semantics
scope normalization
```

## Stage 3 — Semantic code mapping

Add:

```text
repository scanner
symbol map
file-to-symbol map
dependency graph
```

## Stage 4 — Evidence ledger

Extend `StateMemory` to associate:

```text
requirement → target → verification → evidence
```

without removing its existing error ledger API.

## Stage 5 — Bounded execution state machine

Integrate LDE into explicit finite state transitions.

## Stage 6 — Harden lifecycle hooks

Make hard completion gates fail closed on verifier failure.

## Stage 7 — Language adapters

Start with the languages already supported by Gobysh.

## Stage 8 — Benchmarking

Measure actual improvement against baseline Gobysh and against a control condition without Gobysh.

---

# 31. TESTING STRATEGY

Testing must verify both old and new behavior.

## 31.1 Regression tests

Every existing passing test remains valuable.

## 31.2 Semantic tests

Test:

- negation extraction;
- preservation extraction;
- forbidden targets;
- scope extraction;
- ambiguity;
- contradiction detection;
- contract serialization;
- contract comparison.

## 31.3 Translation tests

Test:

```text
semantic entity → correct file
semantic entity → correct symbol
protected symbol → correctly recognized
requirement → correct implementation target
```

## 31.4 Verification tests

Test:

- syntax failure;
- undefined references;
- missing symbols;
- forbidden modifications;
- behavior regression;
- required tests not run;
- verifier unavailable;
- UNKNOWN propagation.

## 31.5 Bounded execution tests

Test:

```text
initial pass
initial fail + repair pass
initial fail + repair fail
initial fail + UNKNOWN
contradiction
blocked execution
```

No path should produce an unbounded repair cycle.

## 31.6 Hook tests

Test:

- PostToolUse validation;
- PreInvocation injection;
- Stop Gate allow;
- Stop Gate block;
- verifier exception → UNKNOWN/BLOCKED rather than false allow.

---

# 32. BENCHMARK DESIGN

Do not benchmark only on raw test pass rate.

A stronger evaluation matrix includes:

| Metric | Baseline | Target Meaning |
|---|---:|---|
| Intent preservation | measure | higher is better |
| Constraint violation rate | measure | lower is better |
| Protected-target modification | measure | ideally zero |
| Regression rate | measure | lower is better |
| False completion | measure | ideally zero |
| Average repair attempts | measure | bounded |
| Infinite / repeated retries | measure | zero |
| Requirement→evidence coverage | measure | 100% for hard-complete tasks |
| Unjustified changes | measure | lower is better |
| Unknown handling | measure | explicit, never hidden as PASS |

The benchmark should compare at least:

```text
AI without Gobysh
AI + existing Gobysh
AI + calibrated Gobysh
```

The point is to demonstrate incremental value rather than merely demonstrate that the new architecture is more complex.

---

# 33. ANTI-OVERENGINEERING RULE

More code is not automatically more support.

Every new subsystem must answer:

```text
What failure mode does this prevent?
What evidence does it create?
What ambiguity does it remove?
What boundary does it enforce?
What benchmark can demonstrate its value?
```

If these answers are weak, do not add the subsystem merely for architectural appearance.

---

# 34. AI EXECUTOR OPERATING RULES

The AI that implements this specification must follow these rules.

## Rule 1 — Inspect before changing

Never modify a current Gobysh file based only on a previous description.

Read the current file.

## Rule 2 — Preserve existing APIs and behavior

Do not remove working behavior unless there is an explicit migration requirement.

## Rule 3 — Add before replacing

Prefer extension, adapters, wrappers, and composition over destructive rewrites.

## Rule 4 — Freeze the semantic contract

Do not silently change the user's requirements to fit an implementation.

## Rule 5 — Never confuse similarity with correctness

Similarity is advisory.

Contract and evidence are authoritative.

## Rule 6 — Do not hide UNKNOWN

Verification failure is not PASS.

## Rule 7 — Repair must be bounded

No infinite retries.

## Rule 8 — Preserve the bridge

All existing Gobysh glue mechanisms remain valuable unless explicitly proven obsolete by benchmark evidence.

## Rule 9 — Do not add gimmicks

Every new capability must address a real gap and be benchmarkable.

## Rule 10 — Do not claim work that was not verified

Completion claims require evidence.

---

# 35. TARGET ARCHITECTURAL CONTRACT

The final intended relationship is:

```text
                HUMAN
                  │
                  ▼
        ┌───────────────────┐
        │ Intent Resolution │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ Semantic Adhesion │
        │ Meaning           │
        │ Negation          │
        │ Constraints       │
        │ Preservation      │
        │ Scope             │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ Semantic Contract │
        │ / Semantic IR     │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │    AI AGENT       │
        │ Reason / Plan     │
        │ Generate / Edit   │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ Code-Semantic Map │
        │ File / Symbol     │
        │ Type / Dependency │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │  CCR / Verifier   │
        │ Syntax / Scope    │
        │ Behavior / Tests  │
        │ Contract / Delta  │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │  Evidence Ledger  │
        │ Req → Code → Test │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ Finite State Gate │
        │ PASS              │
        │ FAIL              │
        │ BLOCKED           │
        │ UNKNOWN           │
        └───────────────────┘
```

Existing modules remain embedded in this architecture.

---

# 36. THE DEEPEST DESIGN PRINCIPLE

Gobysh should not ask:

> "How do we make the model do more thinking?"

It should ask:

> "How do we make the meaning that enters the system remain attached to the action that leaves it?"

That gives the system a stronger identity than a collection of validators.

The chain is:

```text
Intent
  → preserved meaning
  → explicit constraints
  → bounded action
  → mapped implementation
  → mechanically checked outcome
  → evidence-backed completion
```

This is the architectural core that should remain stable even when the underlying AI models change.

---

# 37. DEFINITION OF SUCCESS FOR THIS EVOLUTION

This recalibration is successful when all of the following are true:

1. Existing Gobysh capabilities remain operational.
2. Existing tests continue to pass unless intentionally revised for a documented reason.
3. User negations and preservation constraints survive into a formal semantic contract.
4. The AI can reason freely inside the allowed implementation space without Gobysh pretending to replace it.
5. Actual code changes can be mapped back to semantic requirements.
6. Required behavior has explicit evidence.
7. Protected targets can be checked mechanically where technically possible.
8. Repeated failure cannot create an unbounded retry loop.
9. Verification uncertainty becomes UNKNOWN/BLOCKED rather than PASS.
10. Completion cannot be claimed merely from the model's own textual assertion.
11. Improvements can be demonstrated with measurable benchmarks.
12. The system remains useful even as the underlying AI model becomes substantially more capable.

---

# 38. FINAL EXECUTION DIRECTIVE FOR THE IMPLEMENTING AI

Before modifying Gobysh, the implementing AI must internalize the following:

```text
DO NOT REWRITE GOBYSH FROM SCRATCH.

DO NOT REMOVE EXISTING FEATURES JUST TO INTRODUCE NEW ONES.

DO NOT TREAT CURRENT HEURISTICS AS FINAL SEMANTIC TRUTH.

DO NOT BUILD A SECOND GENERAL-PURPOSE AI REASONER.

DO BUILD A STRONGER SEMANTIC CONTRACT LAYER.

DO BUILD A COMMON INTERMEDIATE REPRESENTATION.

DO BUILD TRACEABLE MAPPING FROM REQUIREMENT TO CODE.

DO TURN VERIFICATION INTO EVIDENCE, NOT ASSERTION.

DO MAKE EXECUTION FINITE AND BOUNDED.

DO PRESERVE EXISTING MEMORY, CCR, LDE, STATE, PARSERS, AND HOOKS.

DO HARDEN THEIR ROLES THROUGH BETTER ORCHESTRATION.

DO REPRESENT UNKNOWN EXPLICITLY.

DO MEASURE WHETHER EVERY NEW CAPABILITY ACTUALLY ADDS VALUE.
```

The objective is not to make Gobysh look larger.

The objective is to make the **existing bridge stronger** and the **semantic distance between user intent and verified software outcome smaller**.

---

# APPENDIX A — EXAMPLE END-TO-END CASE

User request:

> "Tambahkan validasi email sebelum registrasi, tapi jangan ubah database atau fungsi lama."

## A1. Intent

```yaml
action: ADD
feature: email_validation
```

## A2. Constraints

```yaml
forbidden:
  - database_schema
  - existing_functions
```

## A3. Postcondition

```text
invalid email → registration rejected
valid email → registration continues
```

## A4. Preservation

```text
existing functions must still exist
existing database schema unchanged
```

## A5. Mapping

```text
registration flow
  ↓
registration controller
  ↓
validator
```

## A6. AI implementation

The AI selects its implementation strategy.

## A7. Verification

```text
syntax PASS
scope PASS
protected symbols PASS
schema unchanged PASS
invalid email test PASS
existing tests PASS
```

## A8. Evidence

```text
REQ-001 → validator → test_email_invalid → PASS
REQ-002 → schema → before_hash == after_hash → PASS
REQ-003 → existing_function → symbol check → PASS
```

## A9. Final state

```text
TERMINAL_SUCCESS
```

If the database hash cannot be established because the database is unavailable:

```text
UNKNOWN / BLOCKED
```

not PASS.

---

# APPENDIX B — CHANGE REVIEW CHECKLIST FOR THE IMPLEMENTING AI

Before committing architecture changes:

```text
[ ] Existing modules inspected
[ ] Existing tests preserved
[ ] No unnecessary deletion
[ ] IntentResolver remains usable
[ ] ConversationMemory remains usable
[ ] CCR remains usable
[ ] StateMemory remains usable
[ ] LDE remains usable
[ ] Hooks remain usable
[ ] Output parsers remain usable
[ ] New semantic contract introduced cleanly
[ ] Semantic IR has explicit schema
[ ] Requirement-to-code traceability implemented or staged
[ ] UNKNOWN state represented
[ ] Bounded execution represented
[ ] Stop gate does not fail open for hard completion claims
[ ] New behavior benchmarkable
[ ] Documentation matches actual code
[ ] No unsupported mathematical claims
[ ] No false completion claims
```

---

# APPENDIX C — BASELINE REFERENCES

Repository:

- `https://github.com/V4nds/Gobysh`

Key current files reviewed as baseline for this specification:

- `README.md`
- `AGENTS.md`
- `SKILL.md`
- `core/intent_resolver.py`
- `core/ccr_engine.py`
- `core/state_memory.py`
- `core/lde_detector.py`
- `core/conversation_memory.py`
- `core/hooks.py`

This specification is an **evolution target**, not a claim that the target architecture already exists in the repository.

---

# END OF SPECIFICATION
