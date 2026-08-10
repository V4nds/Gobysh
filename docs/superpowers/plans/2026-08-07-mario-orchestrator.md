# Super Mario Bros Arcade & Goby Telemetry HUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an interactive HTML5 Canvas Super Mario Bros 1-1 Arcade Game & Live Goby Multitask Orchestrator Bento-Box HUD Visualizer, fully backed by Python level simulation and 100% passing unit tests (`goby audit`).

**Architecture:** Frontend HTML5 Canvas 60fps retro Mario engine with live Goby DAG telemetry graph HUD, backed by Python `MultitaskOrchestrator` level solver and unit test suite.

**Tech Stack:** HTML5 Canvas, JS (ES6+), Vanilla CSS3, Python 3.12, Goby MultitaskOrchestrator, LDE Engine, StateMemoryManager.

## Global Constraints
- Python unit tests MUST pass with 100% success rate (`python -m unittest discover tests/`).
- Zero bypass of Goby CCR neurons on all written code.
- Modern visual design DNA (Cyberpunk retro dark mode, Bento-box HUD, glassmorphism telemetry panel).

---

### Task 1: Python Mario Level Orchestrator Engine (`demo/mario_orchestrator.py`)

**Files:**
- Create: `demo/mario_orchestrator.py`
- Test: `tests/test_mario_orchestrator.py`

- [ ] **Step 1: Write failing unit test for Mario Orchestrator Engine**

Create `tests/test_mario_orchestrator.py` testing level simulation pipeline execution and obstacle resolution.

- [ ] **Step 2: Run test to verify it fails**

Run `python -m unittest tests/test_mario_orchestrator.py`

- [ ] **Step 3: Implement `demo/mario_orchestrator.py`**

Build `MarioLevelOrchestrator` using `MultitaskOrchestrator`, `StateMemoryManager`, and `LoopDetectionEngine`.

- [ ] **Step 4: Run test to verify it passes**

Run `python -m unittest tests/test_mario_orchestrator.py`

- [ ] **Step 5: Verify full test suite**

Run `python -m unittest discover tests/`

---

### Task 2: Super Mario HTML5 Game Engine & Telemetry Visualizer (`demo/mario_game.js`)

**Files:**
- Create: `demo/mario_game.js`
- Modify: `demo/index.html`

- [ ] **Step 1: Create `demo/mario_game.js` HTML5 Canvas Engine**

Implement 60fps retro Mario physics (running, jumping, Goomba collisions, mystery block pop-ups, coin particles, flagpole finish) and real-time Goby DAG task graph visualization.

- [ ] **Step 2: Update `demo/index.html` with Bento Cyberpunk Layout**

Integrate Mario Game canvas container, live Goby telemetry dashboard, control buttons, and real-time execution log.

- [ ] **Step 3: Test and verify local Web server / Canvas rendering**

Run `python -m http.server 8080 --directory demo` or open `demo/index.html`.

- [ ] **Step 4: Run full Goby audit verification**

Run `python -m core.cli audit`
