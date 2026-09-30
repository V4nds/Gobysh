<div align="center">

# Goby Framework (v5.0.0)
### *Aggressive-Autonomous AI Quality & Verification Engine*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![Unit Tests](https://img.shields.io/badge/Unit%20Tests-203%2F203%20Passed-success.svg)](#-metodologi-benchmark--verifikasi-terbuka)
[![Antigravity Hooks](https://img.shields.io/badge/Antigravity%20Hooks-Active%20Harness-darkgreen.svg)](#-antigravity-mechanical-lifecycle-hooks)
[![Static Verification](https://img.shields.io/badge/Static%20Verification-85.0%25%20(60%20Cases)-indigo.svg)](#-metodologi-benchmark--verifikasi-terbuka)

**Goby** adalah framework penjamin mutu AI coding agresif-otonom berbasis Python. Goby menjembatani instruksi abstrak/ambigu pengguna, memvalidasi output kode secara pre-output di memori, mencatat status ke *Unresolved Error Ledger*, dan mengunci agen coding AI dalam harness mekanikal otonom (**Lifecycle Hooks**) agar tidak dapat berhenti jika ada kode rusak atau gagal gate.

</div>

---

## 🎯 6 Pilar Arsitektur (v5.0.0)

1. **Mechanical Lifecycle Hooks (`.agents/hooks.json` & `core/hooks.py`)**  
   Terintegrasi langsung ke event loop Antigravity IDE:
   - `PostToolUse`: Memvalidasi setiap file yang ditulis/diedit (`write_to_file`, `replace_file_content`) secara otomatis via CCR dan memperbarui error ledger.
   - `PreInvocation`: Menginjeksi peringatan aktif ledger ke dalam prompt sebelum model merespons.
   - `Stop`: Memblokir secara mekanis penghentian sesi (`decision: continue`) jika masih ada error tertunggak.

2. **Intent Resolver & Semantic Contract (`core/intent_resolver.py`)**  
   Mengurai perintah abstrak atau ambigu pengguna menjadi struktur deterministik (`IntentTree`). Mendukung bahasa Indonesia dan Inggris secara bilingual, serta menerbitkan `SemanticContract` berisi target simbol yang wajib dilindungi atau dilarang dimodifikasi.

3. **Persistent Conversation Memory (`core/conversation_memory.py`)**  
   Menyimpan indeks leksikal dan konteks sesi sebelumnya. Saat pengguna menanyakan hal serupa, Goby me-recall solusi terdahulu sehingga agen tidak mengulang eksplorasi dari nol.

4. **Indonesian Semantic Alignment Engine (`core/neurons/semantics.py`)**  
   Neuron CCR khusus untuk mengukur keselarasan makna:
   - *Faithfulness*: Memastikan kode tidak melanggar larangan atau menghapus simbol terlarang.
   - *Context Relevance*: Mengukur relevansi perubahan terhadap niat pengguna.
   - *Semantic Answer Similarity*: Menjamin kesesuaian semantik bilingual ID/EN.

5. **Cognitive Control Room (CCR) & AST Scope Gate (`core/ccr_engine.py`)**  
   Pemeriksaan sintaksis, variabel tak terdefinisi (*scope*), dan desain modern (`taste_design_check`) secara pre-output sebelum kode disimpan ke disk.

6. **Loop Detection Engine (LDE) & Strategy Change Guard (`core/lde_detector.py`)**  
   Mendeteksi osilasi perbaikan berulang ($\ge 2$ iterasi) dan memaksa agen beralih strategi perbaikan arsitektural (`STRATEGY_CHANGE_REQUIRED`).

---

## 💻 Panduan Penggunaan & CLI Reference

### 1. Pemasangan CLI, Git Hooks & Lifecycle Hooks
```bash
# Install package ke environment Python
pip install -e .

# Pasang Git Pre-Commit/Pre-Push Hooks DAN Antigravity Lifecycle Hooks (.agents/hooks.json)
goby install-hook

# Periksa status seluruh harness & memory
goby status
```

### 2. Validasi & Gate Verifikasi
```bash
# Validasi file atau cuplikan kode via CCR
goby check core/hooks.py
goby check "def add(a, b): return a + b" --intent "buat fungsi tambah"

# Gerbang penyelesaian (Must exit code 0)
goby gate

# Jalankan seluruh rangkaian test suite
goby audit
```

### 3. Intent Resolution & Memory Recall
```bash
# Resolusi niat pengguna abstrak/bilingual
goby intent "bikin fungsi login tapi jangan sentuh database"

# Recall konteks sesi serupa dari memori
goby recall "implementasi caching redis"

# Simpan konteks sesi selesai ke memori
goby save "Selesai implementasi hooks dan memory" FEATURE core/hooks.py
```

### 4. Menjalankan Agent Impact Benchmark Ablation Runner
```bash
python benchmarks/goby_agent_impact_runner.py
```

---

## ⚡ Sebelum vs Sesudah Menggunakan Goby v5.0

| Skenario Penggunaan | Tanpa Goby (Naive AI Agent) | Dengan Goby Framework v5.0 |
| :--- | :--- | :--- |
| **Instruksi Pengguna Ambigu** | AI menebak dan berhalusinasi solusi yang salah. | **IntentResolver** mengurai kontrak semantik dan menanyakan klarifikasi jika ambiguitas $> 0.5$. |
| **Amnesia Antar Sesi** | Setiap chat baru mulai dari nol dan mengulang kesalahan sama. | **ConversationMemory** me-recall konteks dan solusi lampau secara deterministik. |
| **Pengecekan Kode** | Hanya diperiksa jika pengguna meminta atau model ingat. | **Mechanical Hook (`PostToolUse`)** otomatis memicu audit CCR di level OS/IDE pada tiap file write. |
| **AI Mengaku "Selesai" Padahal Error** | AI mengklaim tugas selesai walau kode rusak. | **Mechanical Hook (`Stop`)** memblokir terminasi sesi hingga ledger bersih (Exit 0). |
| **Osilasi Loop Error** | AI terjebak mencoba perbaikan naif berulang-ulang. | **LDE** memutus loop pada iterasi ke-2 dan memicu perubahan strategi. |

---

## 📂 Struktur Repositori & Modul

```
.
├── .agents/                    # Antigravity Lifecycle Hooks configuration (hooks.json)
├── benchmarks/                 # Benchmark simulation & agent impact ablation runner
├── core/                       # Goby Framework Core Engine
│   ├── ccr_engine.py           # Cognitive Control Room (AST, Scope, Taste)
│   ├── conversation_memory.py  # Cross-session conversation memory store
│   ├── hooks.py                # Antigravity Lifecycle hooks handler
│   ├── intent_resolver.py      # Bilingual intent resolver & semantic contract
│   ├── lde_detector.py         # Loop Detection Engine (Levenshtein)
│   ├── state_memory.py         # Thread-safe Unresolved Error Ledger
│   └── neurons/                # Modular CCR neurons (semantics, etc.)
├── demo/                       # Interactive web UI demo (index.html, app.js, index.css)
├── docs/                       # Dokumentasi arsitektur, briefing & adapters
│   └── adapters/               # Panduan adapter (Antigravity, Claude, Cursor, OpenAI)
├── tests/                      # Full unit test suite (203 passing tests)
├── AGENTS.md                   # SOP Protokol Otonom-Agresif
├── pyproject.toml              # Build & dependency metadata
├── README.md                   # Dokumentasi utama proyek
└── SKILL.md                    # Antigravity Skill definition
```

---

## 🧪 Metodologi Benchmark & Verifikasi Terbuka

Seluruh data pengujian dapat direproduksi secara mandiri di mesin Anda:

```bash
python -m unittest discover tests/
```

### 📋 Spesifikasi Evaluasi Real-World (Empiris):
- **Environment**: Python 3.12 / Windows & Linux x86_64
- **Unit Test Suite**: **203 Unit Test Cases** terisolasi di folder `tests/` (`100% Passed` dalam ~15.1 detik)
- **60-Case Static AST Verifier Classification Dataset**:
  - *Accuracy*: **80.0%** (48 dari 60 kasus uji terklasifikasi sempurna)
  - *Precision*: **0.875** | *Recall*: **0.700** | *F1-Score*: **0.778**
  - *False-Positive Rate*: **5.0%** (3/60 kasus)
  - *False-Negative Rate*: **15.0%** (9/60 kasus)
- **Mechanical Hook Response**: **~30-90 ms** per tool call intercept.

---

## 🔌 Universal Harness Adapters

- 🌌 [**Antigravity / Gemini CLI**](file:///d:/Gemini-Ide/Goby-skill/docs/adapters/antigravity.md)
- 🧡 [**Anthropic Claude Code**](file:///d:/Gemini-Ide/Goby-skill/docs/adapters/claude.md)
- ⚡ [**Cursor IDE Rules**](file:///d:/Gemini-Ide/Goby-skill/docs/adapters/cursor.md)
- 🟢 [**OpenAI / Custom GPTs**](file:///d:/Gemini-Ide/Goby-skill/docs/adapters/openai_codex.md)

---

## 📜 Lisensi

Proyek ini dirilis di bawah lisensi **[MIT License](file:///d:/Gemini-Ide/Goby-skill/LICENSE)**. Free to use, modify, and distribute for open-source and commercial applications.
