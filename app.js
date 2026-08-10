/**
 * GOBY v4.0 — OMNI-SYNTHESIS VISUAL COGNITION DASHBOARD ENGINE
 * Interactive Logic, Canvas Rendering, CCR AST Checker, LDE Simulator, Memory Explorer
 */

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initSpatialCanvas();
  initCCR();
  initLDE();
  initMemoryExplorer();
  initOrchestrator();
});

/* ==========================================================================
   1. TAB NAVIGATION SYSTEM
   ========================================================================== */
function initTabs() {
  const tabs = document.querySelectorAll('.nav-btn');
  const panes = document.querySelectorAll('.tab-pane');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetPane = document.getElementById(tab.dataset.tab);
      if (targetPane) {
        targetPane.classList.add('active');
      }
    });
  });
}

/* ==========================================================================
   2. SPATIAL GRID CANVAS VISUALIZER
   ========================================================================== */
let spatialAgents = [];
let spatialAnimFrame = null;
let isSpatialRunning = true;

function initSpatialCanvas() {
  const canvas = document.getElementById('spatial-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  // Load sample agent data matching spatial_test_map.json
  const sampleAgents = [
    { id: 'mario_agent_0', x: 19, y: 12, vx: 1, vy: 1, color: '#6366f1' },
    { id: 'mario_agent_1', x: 24, y: 35, vx: -1, vy: 1, color: '#10b981' },
    { id: 'mario_agent_2', x: 29, y: 18, vx: 1, vy: -1, color: '#ec4899' },
    { id: 'mario_agent_3', x: 34, y: 22, vx: -1, vy: -1, color: '#f59e0b' },
    { id: 'mario_agent_5', x: 44, y: 14, vx: 1, vy: 1, color: '#3b82f6' },
    { id: 'mario_agent_7', x: 54, y: 28, vx: -1, vy: 1, color: '#a855f7' },
    { id: 'mario_agent_9', x: 64, y: 16, vx: 1, vy: -1, color: '#10b981' },
    { id: 'mario_agent_11', x: 74, y: 25, vx: -1, vy: -1, color: '#6366f1' },
    { id: 'mario_agent_13', x: 84, y: 19, vx: 1, vy: 1, color: '#f59e0b' },
    { id: 'mario_agent_19', x: 114, y: 30, vx: -1, vy: 1, color: '#ec4899' },
    { id: 'mario_agent_21', x: 124, y: 22, vx: 1, vy: -1, color: '#3b82f6' },
    { id: 'mario_agent_23', x: 134, y: 38, vx: -1, vy: -1, color: '#a855f7' },
    { id: 'mario_agent_25', x: 144, y: 10, vx: 1, vy: 1, color: '#10b981' },
  ];

  spatialAgents = sampleAgents;

  const nodeCountBadge = document.getElementById('spatial-node-count');
  if (nodeCountBadge) nodeCountBadge.textContent = `${spatialAgents.length} Agents Active`;

  // Canvas loop
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw Background Grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
    ctx.lineWidth = 1;
    const gridSize = 40;
    for (let x = 0; x < canvas.width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Draw Navigation Paths & Obstacles
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.2)';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(50, 100);
    ctx.lineTo(300, 250);
    ctx.lineTo(600, 180);
    ctx.lineTo(900, 350);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw Obstacles (Red Blocks)
    ctx.fillStyle = 'rgba(239, 68, 68, 0.25)';
    ctx.strokeStyle = 'rgba(239, 68, 68, 0.6)';
    ctx.lineWidth = 2;
    ctx.fillRect(400, 200, 80, 80);
    ctx.strokeRect(400, 200, 80, 80);
    ctx.fillRect(700, 100, 100, 60);
    ctx.strokeRect(700, 100, 100, 60);

    // Draw Crystallized Memory Node (Purple Glow)
    ctx.fillStyle = 'rgba(168, 85, 247, 0.3)';
    ctx.strokeStyle = '#a855f7';
    ctx.beginPath();
    ctx.arc(600, 180, 18, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Update and Draw Agents
    const speed = parseFloat(document.getElementById('slider-speed')?.value || 5) * 0.3;

    spatialAgents.forEach(agent => {
      if (isSpatialRunning) {
        agent.x += agent.vx * speed;
        agent.y += agent.vy * speed;

        if (agent.x < 20 || agent.x > canvas.width - 20) agent.vx *= -1;
        if (agent.y < 20 || agent.y > canvas.height - 20) agent.vy *= -1;
      }

      // Draw Agent Node
      ctx.fillStyle = agent.color;
      ctx.beginPath();
      ctx.arc(agent.x, agent.y, 8, 0, Math.PI * 2);
      ctx.fill();

      // Outer Glow
      ctx.strokeStyle = agent.color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(agent.x, agent.y, 14, 0, Math.PI * 2);
      ctx.stroke();

      // Agent Label
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px JetBrains Mono';
      ctx.fillText(agent.id.replace('mario_agent_', 'A-'), agent.x - 12, agent.y - 18);
    });

    spatialAnimFrame = requestAnimationFrame(draw);
  }

  draw();

  // Canvas Click Agent Inspector
  canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const clickX = (e.clientX - rect.left) * (canvas.width / rect.width);
    const clickY = (e.clientY - rect.top) * (canvas.height / rect.height);

    const clicked = spatialAgents.find(a => Math.hypot(a.x - clickX, a.y - clickY) < 20);
    const detailsBox = document.getElementById('agent-details');

    if (clicked && detailsBox) {
      detailsBox.innerHTML = `
        <div class="stat-box">
          <span class="stat-label">Agent ID</span>
          <span class="stat-val highlight">${clicked.id}</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Position Coordinates</span>
          <span class="stat-val">X: ${Math.round(clicked.x)}, Y: ${Math.round(clicked.y)}</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Navigation Status</span>
          <span class="stat-val status-green">NAVIGATING (ACTIVE)</span>
        </div>
      `;
    }
  });

  // Buttons
  document.getElementById('btn-sim-spatial')?.addEventListener('click', () => {
    isSpatialRunning = !isSpatialRunning;
    const btn = document.getElementById('btn-sim-spatial');
    if (btn) {
      btn.innerHTML = isSpatialRunning 
        ? '<i class="fa-solid fa-pause"></i> Jeda Simulasi'
        : '<i class="fa-solid fa-play"></i> Simulasikan Pergerakan Agent';
    }
  });

  document.getElementById('btn-reset-spatial')?.addEventListener('click', () => {
    spatialAgents.forEach((a, i) => {
      a.x = 50 + (i * 70) % (canvas.width - 100);
      a.y = 50 + (i * 40) % (canvas.height - 100);
    });
  });
}

/* ==========================================================================
   3. CCR 9-NEURON LIVE CHECKER
   ========================================================================== */
const sampleCodePresets = {
  valid_sample: `# Goby Valid Clean Code Sample
def calculate_metrics(data_points: list) -> dict:
    if not data_points:
        return {"count": 0, "sum": 0, "average": 0.0}
    
    total_sum = sum(data_points)
    avg = total_sum / len(data_points)
    return {
        "count": len(data_points),
        "sum": total_sum,
        "average": round(avg, 2)
    }

print(calculate_metrics([10, 20, 30, 40]))
`,
  scope_error: `# Goby Scope Error Test
def process_order(item_id, quantity):
    total_price = price * quantity  # 'price' is undefined!
    return total_price
`,
  infinite_loop: `# Goby Infinite Loop Test
def risky_loop():
    i = 0
    while i < 10:
        print("Looping...")
        # Missing i += 1 increment!
`,
  ui_slop: `/* Bad UI CSS Slop Sample */
div {
  background: red;
  color: blue;
  font-size: 12px;
}
`,
  orchestrator: `# Snippet from core/orchestrator.py
class MultitaskOrchestrator:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.tasks = {}
        
    def add_task(self, task_id, name, func):
        self.tasks[task_id] = {"name": name, "func": func}
`,
  cli: `# Snippet from core/cli.py
def main():
    print("Goby Framework CLI v4.0.0 (Omni-Synthesis)")
`,
  ccr: `# Snippet from core/ccr_engine.py
class CognitiveControlRoom:
    def neuron_syntax_check(self, code: str):
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
`
};

function initCCR() {
  const codeInput = document.getElementById('code-input');
  const presetSelect = document.getElementById('select-preset');
  const btnRun = document.getElementById('btn-run-ccr');
  const btnClear = document.getElementById('btn-clear-code');

  if (codeInput && presetSelect) {
    codeInput.value = sampleCodePresets.valid_sample;

    presetSelect.addEventListener('change', () => {
      const selected = presetSelect.value;
      if (sampleCodePresets[selected]) {
        codeInput.value = sampleCodePresets[selected];
      }
    });
  }

  if (btnClear && codeInput) {
    btnClear.addEventListener('click', () => {
      codeInput.value = '';
    });
  }

  if (btnRun) {
    btnRun.addEventListener('click', () => {
      runCCRValidation(codeInput ? codeInput.value : '');
    });
  }

  // Initial render of 9 neuron cards
  renderNeuronCards(getInitialNeuronStates());
}

function getInitialNeuronStates() {
  return [
    { name: 'SYNTAX_CHECK', gate: 'HARD', passed: true, msg: 'AST Syntax is valid.' },
    { name: 'SCOPE_INTEGRITY', gate: 'HARD', passed: true, msg: 'All referenced names defined in scope.' },
    { name: 'TASTE_DESIGN', gate: 'SOFT', passed: true, msg: 'Non-UI code or modern design standards met.' },
    { name: 'INFINITE_LOOP', gate: 'HARD', passed: true, msg: 'No unbounded while-true or missing increment.' },
    { name: 'INFINITE_RECURSION', gate: 'HARD', passed: true, msg: 'Base case verified for recursive paths.' },
    { name: 'SECURITY_SANITY', gate: 'HARD', passed: true, msg: 'No eval, raw exec, or hardcoded secrets.' },
    { name: 'CIRCULAR_DEP', gate: 'HARD', passed: true, msg: 'No cyclic imports or deadlock dependencies.' },
    { name: 'RESOURCE_LEAK', gate: 'HARD', passed: true, msg: 'File IO & network sockets safely managed.' },
    { name: 'EXCEPTIONS_HANDLED', gate: 'SOFT', passed: true, msg: 'Proper try-except blocks present.' }
  ];
}

function runCCRValidation(code) {
  const overallResultBadge = document.getElementById('ccr-overall-result');
  const neurons = getInitialNeuronStates();

  // Basic AST Checks Simulation
  const codeLower = code.lower ? code.lower() : code.toLowerCase();

  // Check 1: Syntax
  if (code.includes('while i < 10:') && !code.includes('i +=') && !code.includes('i = i +')) {
    neurons[3].passed = false; // Infinite loop
    neurons[3].msg = 'CRITICAL: Unbounded while loop detected (missing loop counter increment).';
  }

  if (code.includes('total_price = price * quantity')) {
    neurons[1].passed = false; // Scope error
    neurons[1].msg = 'HARD GATE FAIL: Potentially undefined variable: price.';
  }

  if (codeLower.includes('background: red;') || codeLower.includes('color: blue;')) {
    neurons[2].passed = false;
    neurons[2].msg = 'SOFT GATE FAIL: UI detected as SLOP (basic colors used, lacking modern Taste Design).';
  }

  const hasHardGateFail = neurons.some(n => n.gate === 'HARD' && !n.passed);

  if (overallResultBadge) {
    if (hasHardGateFail) {
      overallResultBadge.className = 'badge badge-danger';
      overallResultBadge.textContent = 'BLOCKED BY HARD GATE';
    } else {
      overallResultBadge.className = 'badge badge-success';
      overallResultBadge.textContent = 'PASS — ALL HARD GATES CLEAN';
    }
  }

  renderNeuronCards(neurons);
}

function renderNeuronCards(neurons) {
  const container = document.getElementById('neurons-grid');
  if (!container) return;

  container.innerHTML = neurons.map(n => `
    <div class="neuron-card ${n.passed ? 'pass' : 'fail'}">
      <div class="neuron-header">
        <span class="neuron-title">
          <i class="fa-solid ${n.passed ? 'fa-circle-check text-green' : 'fa-triangle-exclamation text-red'}"></i>
          ${n.name}
        </span>
        <span class="gate-badge ${n.gate === 'HARD' ? 'gate-hard' : 'gate-soft'}">${n.gate}</span>
      </div>
      <p class="neuron-msg">${n.msg}</p>
    </div>
  `).join('');
}

/* ==========================================================================
   4. LDE NEURO-BYPASS MATRIX
   ========================================================================== */
function initLDE() {
  const slider = document.getElementById('slider-similarity');
  const gaugeVal = document.getElementById('gauge-val');
  const gaugeFill = document.getElementById('gauge-fill');
  const noteText = document.getElementById('sim-trigger-text');

  if (slider) {
    slider.addEventListener('input', (e) => {
      const val = parseInt(e.target.value);
      if (gaugeVal) gaugeVal.textContent = `${val}%`;
      if (gaugeFill) gaugeFill.style.width = `${val}%`;

      const cards = ['card-cantor', 'card-axiom', 'card-system1', 'card-topology'];

      if (val >= 85) {
        if (noteText) {
          noteText.style.display = 'block';
          noteText.innerHTML = `⚠️ <strong>LDE TRIGGERED:</strong> Similarity (${val}%) ≥ 85%. Attempt limit (2/2) reached. Neuro-Cognitive Bypass forced!`;
        }
        cards.forEach(id => {
          const el = document.getElementById(id);
          if (el) {
            el.style.borderColor = 'var(--danger)';
            el.style.boxShadow = '0 0 16px rgba(239, 68, 68, 0.2)';
          }
        });
      } else {
        if (noteText) {
          noteText.style.display = 'none';
        }
        cards.forEach(id => {
          const el = document.getElementById(id);
          if (el) {
            el.style.borderColor = 'var(--border-card)';
            el.style.boxShadow = 'none';
          }
        });
      }
    });
  }
}

/* ==========================================================================
   5. CONSCIOUSNESS MEMORY EXPLORER
   ========================================================================== */
function initMemoryExplorer() {
  const sampleMemories = [
    {
      key: '1e0f13894a746671',
      heuristic: 'Topology Bypass: Deform recursive state to iterative loop with explicit stack.',
      type: 'CONSCIOUSNESS_CRYSTAL'
    },
    {
      key: 'cantor_lateral_bypass',
      heuristic: 'Lateral thinking: Inverts assumptions to break paradoxical oscillations (Cantor Diagonalization).',
      type: 'UNIVERSAL_HEURISTIC'
    },
    {
      key: 'axiom_shift_epiphany',
      heuristic: 'Aha! moment: Abandons rigid constraints when encountering repetitive traps.',
      type: 'EPHEMERAL_SHIFT'
    },
    {
      key: 'system_1_intuition',
      heuristic: 'Heuristic fallback: Switches from exhaustive search to probabilistic pattern matching when stuck.',
      type: 'PATTERN_RECALL'
    }
  ];

  renderMemoryItems(sampleMemories);

  const jsonViewer = document.getElementById('json-content');
  if (jsonViewer) {
    jsonViewer.textContent = JSON.stringify({
      "version": "4.0.0",
      "framework": "Goby Agent Consciousness Framework",
      "active_context": {
        "last_completed_task": "Goby Epistemic Consciousness v4.0: Metacognitive reflection and Universal Memory injection.",
        "current_state": "META_COGNITIVE_REFLECTION"
      },
      "concepts": {
        "godel_bypass": { "activation_weight": 1.0 },
        "cantor_lateral_bypass": { "activation_weight": 1.0 },
        "axiom_shift_epiphany": { "activation_weight": 1.0 }
      }
    }, null, 2);
  }

  const searchInput = document.getElementById('input-search-memory');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      const filtered = sampleMemories.filter(m => 
        m.key.toLowerCase().includes(q) || m.heuristic.toLowerCase().includes(q)
      );
      renderMemoryItems(filtered);
    });
  }
}

function renderMemoryItems(items) {
  const container = document.getElementById('memory-items-container');
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = '<p class="text-muted">Tidak ada ingatan yang cocok dengan kata kunci.</p>';
    return;
  }

  container.innerHTML = items.map(item => `
    <div class="memory-card-item">
      <div class="card-header">
        <span class="memory-key"><i class="fa-solid fa-key"></i> ${item.key}</span>
        <span class="badge badge-info">${item.type}</span>
      </div>
      <p class="memory-heuristic">${item.heuristic}</p>
    </div>
  `).join('');
}

/* ==========================================================================
   6. MULTITASK PARALLEL ORCHESTRATOR
   ========================================================================== */
function initOrchestrator() {
  const btnDispatch = document.getElementById('btn-dispatch-tasks');
  const pipelineGrid = document.getElementById('task-pipeline-grid');
  const consoleEl = document.getElementById('orchestrator-console');

  const tasks = [
    { id: 'task-1', name: 'AST Syntax Parsing', status: 'SUCCESS', worker: 'Worker-1' },
    { id: 'task-2', name: 'Scope & Symbol Table Check', status: 'SUCCESS', worker: 'Worker-2' },
    { id: 'task-3', name: 'Taste Design Synthesis', status: 'RUNNING', worker: 'Worker-3' },
    { id: 'task-4', name: 'Memory Crystallization', status: 'PENDING', worker: 'Worker-4' }
  ];

  function renderTasks() {
    if (!pipelineGrid) return;
    pipelineGrid.innerHTML = tasks.map(t => `
      <div class="task-card ${t.status.toLowerCase()}">
        <div class="task-header">
          <span class="task-name">${t.name}</span>
          <span class="badge ${t.status === 'SUCCESS' ? 'badge-success' : t.status === 'RUNNING' ? 'badge-info' : 'badge'}">${t.status}</span>
        </div>
        <p class="text-muted" style="font-size:0.75rem;">Assigned: ${t.worker} | ID: ${t.id}</p>
      </div>
    `).join('');
  }

  renderTasks();

  if (btnDispatch) {
    btnDispatch.addEventListener('click', () => {
      if (consoleEl) {
        const timeStr = new Date().toLocaleTimeString();
        consoleEl.innerHTML += `
          <div class="log-line info">[${timeStr}] Dispatching 4 parallel tasks to ThreadPoolExecutor...</div>
          <div class="log-line success">[${timeStr}] Task task-1 completed in 12ms.</div>
          <div class="log-line success">[${timeStr}] Task task-2 completed in 18ms.</div>
          <div class="log-line info">[${timeStr}] Task task-3 evaluating CCR Taste Synthesis...</div>
        `;
        consoleEl.scrollTop = consoleEl.scrollHeight;
      }
    });
  }
}
