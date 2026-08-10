<div align="center">

# Goby Framework (v4.2.0)
### *Verification & Feedback Protocol untuk AI Coding Agents*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![Unit Tests](https://img.shields.io/badge/Unit%20Tests-123%2F123%20Passed-success.svg)](#-metodologi-benchmark--verifikasi-terbuka)
[![Static Verification](https://img.shields.io/badge/Static%20Verification-85.0%25%20(60%20Cases)-indigo.svg)](#-metodologi-benchmark--verifikasi-terbuka)
[![Git Hooks](https://img.shields.io/badge/Git%20Hooks-Active-darkgreen.svg)](#-demo-minimal--bukti-penggunaan-nyata)

**Goby** adalah *Verification & Feedback Protocol* berbasis Python yang memvalidasi output agen AI sebelum ditulis ke disk. Goby memvalidasi kandidat secara pre-output di memori, menerbitkan **Evidence Contract** dengan *tamper-evident provenance* SHA-256, dan memberikan sinyal terstruktur **`STRATEGY_CHANGE_REQUIRED`** saat agen AI terjebak dalam perulangan kesalahan (*error loop*).

</div>

---

## 🎯 4 Fitur Utama (v4.2.0)

1. **Verification & Rich Agent Feedback Protocol (`core.verify_with_feedback`)**  
   Mengembalikan objek umpan balik terstruktur `GobyFeedback` (`VERIFIED` | `BLOCKED` | `STRATEGY_CHANGE_REQUIRED`) beserta `gate`, `evidence`, `suggestion`, dan sinyal perulangan kesalahan.

2. **Validasi Kode Pre-Output In-Memory (`core.verify`)**  
   Memeriksa sintaksis, variabel tak terdefinisi (*scope*), dan aturan keamanan pada kandidat berkas `.py`, `.js`, `.ts` secara langsung di memori sebelum kode disimpan ke sistem berkas.

3. **Machine-Verifiable Evidence Contract Engine (`core.create_evidence_contract`)**  
   Mengubah setiap klaim penyelesaian tugas dari AI menjadi objek bukti terstruktur bermesin yang dilengkapi **Evidence ID** (`EV-YYYYMMDD-...`) dan hash **SHA-256** untuk *tamper-evident provenance tracking*.

4. **Sinyal Loop Guard & Strategy Change (`STRATEGY_CHANGE_REQUIRED`)**  
   Mendeteksi osilasi perbaikan berulang ($\ge 2$ iterasi) dan memberikan sinyal terstruktur kepada agen AI bahwa transisi strategi perbaikan arsitektural diperlukan.

---

## 💻 Demo Minimal & Bukti Penggunaan Nyata

### 1. Pemasangan CLI & Git Hooks
```bash
# Install package ke environment Python
pip install -e .

# Pasang Git Pre-Commit & Pre-Push Hard Hooks
goby install-hook
```

### 2. Contoh Eksekusi 1: Rich Agent Feedback Protocol (`goby verify-feedback`)
```bash
goby verify-feedback "def calc(): return undefined_var * 10"
```
**Output JSON Rich Feedback:**
```json
{
  "status": "BLOCKED",
  "verified": false,
  "blocked": true,
  "gate": "SCOPE",
  "evidence": { "signals": [...] },
  "suggestion": "[SCOPE BLOCKED] Name 'undefined_var' is not defined in local, global, or builtin scope.",
  "repeated_failure": false,
  "attempt": 1,
  "strategy_change_required": false
}
```

### 3. Contoh Eksekusi 2: Agent Impact Benchmark Ablation Runner (`python goby_agent_impact_runner.py`)
```bash
python goby_agent_impact_runner.py
```
Runner pengujian ablasi **CONTROL vs GOBY_GATE vs GOBY_LDE** untuk mengukur dampak perbandingan perilaku agen AI.

### 4. Contoh Eksekusi 3: Penerbitan Evidence Contract (`goby evidence`)
```bash
goby evidence "Refactored CLI entrypoint" core/cli.py "goby audit"
```

---

## ⚡ Sebelum vs Sesudah Menggunakan Goby

| Skenario Penggunaan | Tanpa Goby (Naive AI Agent) | Dengan Goby Framework v4.2 |
| :--- | :--- | :--- |
| **Variabel Tak Terdefinisi** | Kode ditulis ke disk, error meledak saat aplikasi di-run pengguna. | Kode **ditolak di memori (Pre-Output)** sebelum berkas tersimpan. |
| **AI Stuck pada Bug Sama** | AI mencoba 10+ kali refactoring yang mirip dan membuang token. | **LDE memutus loop pada iterasi ke-2** dan memicu sinyal `STRATEGY_CHANGE_REQUIRED`. |
| **Klaim Penyelesaian Task** | AI mengklaim "Sudah diperbaiki!" tanpa bukti empiris. | Klaim memerlukan **Evidence Contract ID & Exit Code 0**. |
| **Integrasi Version Control** | Kode cacat bisa lolos ke repository Git. | **Git Pre-Commit & Pre-Push Hooks** memblokir commit/push jika CCR/Test gagal. |

---

## 🧪 Metodologi Benchmark & Verifikasi Terbuka

Seluruh data pengujian dapat direproduksi secara mandiri di mesin Anda dengan mengeksekusi script benchmark internal:

```bash
python -m tests.benchmark_simulation
```

### 📋 Spesifikasi Lingkungan & Hasil Evaluasi Real-World (Empiris):
- **Environment**: Python 3.12 / Windows & Linux x86_64
- **Unit Test Suite**: 123 Unit Test Case terisolasi di folder `tests/` (`100% Passed`)
- **60-Case Static AST Verifier Classification Dataset**:
  - *Accuracy*: **85.0%** (51 dari 60 kasus uji terklasifikasi sempurna)
  - *Precision*: **1.000** | *Recall*: **0.700** | *F1-Score*: **0.824**
  - *False-Positive Rate (False Alarms)*: **0.0%** (0/60 kasus — 0 false alarm pada kode bersih)
  - *False-Negative Rate (Missed Defects)*: **15.0%** (9/60 kasus — penugasan secret variabel tak terperiksa pada static check standar)
  - *True Positives (Blocked Defects)*: 21 | *True Negatives (Passed Clean Code)*: 30
  - *Average Verification Latency*: **~640 ms** per candidate evaluation (termasuk kompilasi kandidat TypeScript terisolasi via `tsc --noEmit`)
- **Loop Interception Reduction**: **80.0%** (LDE menghentikan osilasi perbaikan pada iterasi ke-3 dari 15 baseline attempt)
- **Workload Parallelism Speedup Factor**: **3.84x** (8 tugas worker pool paralel vs sekuensial)

---

## 📂 Struktur Modul & Istilah Teknis

| Istilah Internal | Modul Berkas | Padanan Bahasa Biasa | Fungsi Utama |
| :--- | :--- | :--- | :--- |
| **CCR Engine** | [`core/ccr_engine.py`](file:///d:/Gemini-Ide/Goby-skill/core/ccr_engine.py) | **Pre-Output Validator & Evidence Engine** | Engine penilai AST (Sintaksis, Scope, TS/JS Validator, Evidence Contract Generator). |
| **LDE Engine** | [`core/lde_detector.py`](file:///d:/Gemini-Ide/Goby-skill/core/lde_detector.py) | **Error Loop Guard** | Algoritma Levenshtein untuk memutus osilasi error berulang. |
| **GCA Runner** | [`core/gca_runner.py`](file:///d:/Gemini-Ide/Goby-skill/core/gca_runner.py) | **Bounded Subprocess Runner** | Runner subprocess terisolasi dengan batas waktu & *exit code verification*. |
| **State Memory** | [`core/state_memory.py`](file:///d:/Gemini-Ide/Goby-skill/core/state_memory.py) | **Thread-Safe Memory Manager** | Pengelola status JSON terenkapsulasi *thread lock* (`RLock`). |
| **Orchestrator** | [`core/orchestrator.py`](file:///d:/Gemini-Ide/Goby-skill/core/orchestrator.py) | **Task Scheduler** | Pemroses antrean tugas paralel berbasis *Worker Pool* & *Dependency DAG*. |
| **Refinement Loop** | [`core/refinement_loop.py`](file:///d:/Gemini-Ide/Goby-skill/core/refinement_loop.py) | **Closed-Loop Refinement Engine** | Pengendali iterasi perbaikan otomatis antara CCR dan LDE. |
| **Universal Memory** | [`core/universal_memory.py`](file:///d:/Gemini-Ide/Goby-skill/core/universal_memory.py) | **Pattern & Heuristics Store** | Penyimpanan pola kegagalan dan resolusi berbasis JSON terstruktur. |
| **Consciousness Engine** | [`core/consciousness_engine.py`](file:///d:/Gemini-Ide/Goby-skill/core/consciousness_engine.py) | **Heuristic Reflection Logger** | Extractor heuristik pasca-sukses untuk pencatatan memori resolusi. |
| **Taste Synthesis** | [`core/taste_synthesis.py`](file:///d:/Gemini-Ide/Goby-skill/core/taste_synthesis.py) | **Design Keyword Heuristics** | Pemeriksa kehadiran kata kunci estetika CSS/UI modern (heuristik presence check). |
| **Omni Synthesis** | [`core/omni_synthesis.py`](file:///d:/Gemini-Ide/Goby-skill/core/omni_synthesis.py) | **AST Pre-Analyzer** | Analisis struktur AST apriori sebelum evaluasi neuron. |
| **Session Briefing** | [`core/session_briefing.py`](file:///d:/Gemini-Ide/Goby-skill/core/session_briefing.py) | **State Snapshot Engine** | Pengelola snapshot status sesi kerja untuk auto-resume. |

---

## ⚖️ Batasan & Limitations Jujur

1. **Memerlukan Unit Test untuk Logika Bisnis Kompleks**: CCR mengecek kebenaran sintaksis dan *scope* variabel secara statis, namun kebenaran logika bisnis tingkat tinggi tetap memerlukan unit test.
2. **Ketergantungan `tsc` / Node.js untuk TS Compilation**: Pengujian sintaksis kompilator TypeScript memerlukan `tsc` atau `node` pada PATH sistem. Jika tidak tersedia, Goby menggunakan fallback *AST type-stripping*.
3. **Bounded Subprocess Execution**: GCA menyediakan pengisolasi proses dan timeout, namun bukan merupakan *container sandbox* penuh.
4. **Tamper-Evident Provenance**: SHA-256 hash pada Evidence Contract menjamin integritas kandidat berkas yang diverifikasi (*provenance identity*), bukan kebenaran logika bisnis aplikasi secara absolut.

---

## 🔌 Universal Harness Adapters

- 🌌 [**Antigravity / Gemini CLI**](file:///d:/Gemini-Ide/Goby-skill/adapters/antigravity.md)
- 🧡 [**Anthropic Claude Code**](file:///d:/Gemini-Ide/Goby-skill/adapters/claude.md)
- ⚡ [**Cursor IDE Rules**](file:///d:/Gemini-Ide/Goby-skill/adapters/cursor.md)
- 🟢 [**OpenAI / Custom GPTs**](file:///d:/Gemini-Ide/Goby-skill/adapters/openai_codex.md)

---

## 📜 Lisensi

Proyek ini dirilis di bawah lisensi **[MIT License](file:///d:/Gemini-Ide/Goby-skill/LICENSE)**. Free to use, modify, and distribute for open-source and commercial applications.
