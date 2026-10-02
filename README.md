<div align="center">

# 🐟 Gobysh
### *Deterministic Mechanical Harness, Semantic Adhesion & Verification Engine for AI Coding Agents*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![Unit Tests](https://img.shields.io/badge/Unit%20Tests-234%2F234%20Passed-success.svg)](#-bukti-empiris--benchmark-terbuka)
[![Antigravity Lifecycle Hooks](https://img.shields.io/badge/Antigravity%20Hooks-Mechanically%20Active-darkgreen.svg)](#-arsitektur-rantai-kausal-determinis)
[![Bilingual Support](https://img.shields.io/badge/Language-ID%20%7C%20EN%20Bilingual-orange.svg)](#1-cognitive-gateway-intent-resolver--conversation-memory)

<p align="center">
  <b>Gobysh mengubah asisten coding AI (Antigravity, Gemini CLI, Claude Code, Cursor) sebagai mechanical execution harness yang tertanam langsung ke dalam <i>runtime lifecycle loop</i> IDE untuk mengawasi setiap ketukan kode yang dihasilkan AI.</b>
</p>

</div>

## 🛑 Masalah Nyata yang Dipecahkan Gobysh

Asisten coding berbasis Large Language Model (LLM) umumnya memiliki 4 cacat fatal:

1. **Semantic Gap & Perintah Abstrak:** Instruksi manusia (terutama dalam Bahasa Indonesia informal) seringkali ringkas atau ambigu (misal: *"buat fungsi auth tapi jangan sentuh tabel user lama"*). LLM sering mengabaikan larangan implisit ini dan merusak kode yang ada.
2. **Amnesia Antar Sesi Percakapan:** Setiap kali pengguna memulai obrolan baru, agen melupakan seluruh konteks, mengulang eksperimen buntu yang sama, dan membuang-buang token.
3. **Patching Dangkal (*Superficial Fixes*):** Ketika menghadapi bug, AI cenderung menghapus assertion, membungkus logika rusak dengan silent `try/except: pass`, atau menambahkan fallback kosong alih-alih membereskan akar masalah (*root cause*).
4. **Klaim Palsu Penyelesaian (*False Completion*):** Agen dengan percaya diri menyatakan *"Pekerjaan selesai dan telah diperbaiki!"* padahal file masih memiliki error kompilasi atau variabel tidak terdefinisi.

---

## 🏛️ Arsitektur Rantai Kausal Determinis

Gobysh bekerja sebagai sistem tertutup (*closed-loop deterministic chain*) yang mengunci kebebasan acak LLM di dalam batas-batas kompilator, kontrak semantik, dan graf kausal repositori:

```mermaid
flowchart TD
    UserInput["Perintah Pengguna (Abstrak / Bilingual ID-EN)"] --> IntentRes["IntentResolver (core/intent_resolver.py)\n- Ekstraksi Niat & Batas Larangan\n- Penerbitan SemanticContract"]
    
    IntentRes --> SemIR["Formal Semantic Core (core/semantics/)\n- SemanticIR (Pure YAML/JSON)\n- ConstraintModel (Deteksi Kontradiksi)"]
    SemIR --> ContractVal["ContractValidator (core/semantics/contract_validator.py)\n- PreservationContract (Proteksi Kode Lama)\n- ScopeNormalizer (Glob & OS Path Boundaries)\n- NegationHandler (Deep Bilingual Negation Parser)"]
    
    ContractVal --> CodeMap["Semantic Code Mapping (core/translation/)\n- RepositoryScanner (AST Python & Regex JS/TS)\n- DependencyGraph (CDG Blast Radius Tracker)\n- CodeSemanticMapper (Resolusi Simbol Konkret)"]
    
    CodeMap --> MemRecall["ConversationMemory (core/conversation_memory.py)\n- Lexical Overlap Indexing\n- Recall Solusi Sesi Lampau"]
    MemRecall --> AIAgent["AI Coding Agent (Generator)"]
    
    AIAgent -->|"Tulis/Edit Berkas"| ToolCall["write_to_file / replace_file_content"]
    
    subgraph MechanicalHarness ["Harness Mekanikal IDE (.agents/hooks.json & core/hooks.py)"]
        ToolCall -->|"PostToolUse Hook"| CCRCheck["Cognitive Control Room (CCR)\n1. Syntax Check (AST)\n2. Scope Check (Undefined Vars)\n3. Taste Design (Modern UI)\n4. Semantic Alignment (Faithfulness/Similarity)"]
        CCRCheck -->|"Catat Status"| Ledger["Unresolved Error Ledger (cognitive_map.json)"]
        
        Ledger -->|"Ada Error"| PreInvoc["PreInvocation Hook\nInjeksi Warning Langsung ke Prompt Model"]
        PreInvoc -.-> AIAgent
        
        AIAgent -->|"Mencoba Berhenti (model_stop)"| StopHook{"Stop Gate Hook\nApakah Ledger Bersih?"}
        StopHook -- "TIDAK (Error > 0)" --> BlockStop["BLOKIR PENGHENTIAN (decision: continue)\nModel Dipaksa Memperbaiki"]
        BlockStop -.-> AIAgent
        StopHook -- "YA (0 Error)" --> GatePass["goby gate = 0\nSesi Diizinkan Selesai"]
    end
    
    GatePass --> GitPush["Git Pre-Push Hook (goby audit)\n234 Unit Tests Lulus -> PUSH KE REPO"]
```

---

## ⚡ 4 Lapisan Utama Gobysh v5.1

### 1. Cognitive Gateway: Intent Resolver & Conversation Memory
- **Bilingual Intent Resolver ([core/intent_resolver.py](file:///d:/Gemini-Ide/Goby-skill/core/intent_resolver.py)):**  
  Menerjemahkan instruksi pengguna bahasa Indonesia dan Inggris menjadi pohon niat (`IntentTree`). Jika tingkat ambiguitas $> 0.5$, Gobysh memicu pertanyaan klarifikasi alih-alih membiarkan AI menebak.
- **Persistent Conversation Memory ([core/conversation_memory.py](file:///d:/Gemini-Ide/Goby-skill/core/conversation_memory.py)):**  
  Penyimpanan berbasis indeks leksikal ($O(1)$ lookup) yang mengingat apa yang telah diselesaikan pada sesi sebelumnya. Tidak ada lagi percakapan yang harus dimulai dari nol.

### 2. Formal Semantic Core & Multi-Clause Contract Validation ([core/semantics/](file:///d:/Gemini-Ide/Goby-skill/core/semantics/))
- **Formal Semantic Specification & IR:**  
  Menstandarkan kebutuhan menjadi entitas formal (`Requirement`, `SemanticEntity`, `SemanticIR`) yang dapat diserialisasi ke format JSON dan YAML deterministik murni tanpa dependensi library eksternal.
- **Deterministic Contradiction Detection:**  
  Model batasan (`ConstraintModel`) yang secara otomatis mendeteksi konflik klausul (misal: perintah *menghapus* file yang masuk ke daftar *strict scope* atau *forbidden targets*).
- **Preservation Contract ([core/semantics/preservation.py](file:///d:/Gemini-Ide/Goby-skill/core/semantics/preservation.py)):**  
  Kontrak first-class yang secara eksplisit melindungi sistem lama dari perombakan destruktif tak diinginkan.
- **Deep Bilingual Negation Handler ([core/semantics/negation.py](file:///d:/Gemini-Ide/Goby-skill/core/semantics/negation.py)):**  
  Menganalisis negasi kompleks dalam bahasa Indonesia dan Inggris (*"jangan pernah sentuh"*, *"tanpa mengubah method"*, *"dilarang modifikasi"*).
- **Multi-Clause Scope Normalizer ([core/semantics/scope.py](file:///d:/Gemini-Ide/Goby-skill/core/semantics/scope.py)):**  
  Normalisasi path lintas sistem operasi (POSIX & Windows) serta validasi boundary berbasis pola glob.

### 3. Semantic Code Mapping & Causal Dependency Graph ([core/translation/](file:///d:/Gemini-Ide/Goby-skill/core/translation/))
- **Repository AST Scanner ([core/translation/scanner.py](file:///d:/Gemini-Ide/Goby-skill/core/translation/scanner.py)):**  
  Memindai seluruh repositori untuk mengekstrak class, function, method, docstring, parameter, dan relasi import menggunakan `ast` bawaan Python serta tokenizer regex aman untuk JavaScript dan TypeScript.
- **Causal Dependency Graph ([core/semantics/dependency_graph.py](file:///d:/Gemini-Ide/Goby-skill/core/semantics/dependency_graph.py)):**  
  Melacak hubungan dependensi upstream dan downstream antar berkas. Menghitung *blast radius* secara otomatis dan memblokir modifikasi jika mempengaruhi *protected symbols*.
- **Code-Semantic Mapper ([core/translation/engine.py](file:///d:/Gemini-Ide/Goby-skill/core/translation/engine.py)):**  
  Menjembatani intent bahasa manusia langsung ke simbol dan berkas target di repositori (`MappingReport`).

### 4. Deterministic Verification: Cognitive Control Room (CCR) & Hooks
- **AST Syntax & Scope Neurons ([core/ccr_engine.py](file:///d:/Gemini-Ide/Goby-skill/core/ccr_engine.py)):**  
  Memeriksa sintaksis kode Python, JavaScript, dan TypeScript. Mendeteksi variabel tak terdefinisi (*undefined names*) sebelum berkas sempat disentuh oleh interpreter.
- **Indonesian Semantic Alignment ([core/neurons/semantics.py](file:///d:/Gemini-Ide/Goby-skill/core/neurons/semantics.py)):**  
  Mengukur *Faithfulness*, *Context Relevance*, dan *Semantic Answer Similarity* dwi-bahasa (ID/EN).
- **Modern Taste & Design Heuristics ([core/neurons/taste.py](file:///d:/Gemini-Ide/Goby-skill/core/neurons/taste.py)):**  
  Hard Gate untuk frontend yang menolak desain HTML/CSS jadul (memaksa palet modern HSL, tipografi Inter/Roboto, micro-animations, dan tata letak dinamis).
- **Lifecycle Hooks ([.agents/hooks.json](file:///d:/Gemini-Ide/Goby-skill/.agents/hooks.json)):**  
  Intersepsi `PostToolUse`, injeksi `PreInvocation`, dan penguncian terminasi `Stop`.
- **Dual Git Hooks (`.git/hooks/`):**  
  *Pre-Commit* via CCR dan *Pre-Push* wajib lulus seluruh pengujian unittest.

---

## 📊 Perbandingan Nyata: Agen Naif vs Agen dengan Gobysh

| Skenario Nyata | Agen AI Standar (Tanpa Gobysh) | Agen AI dengan Gobysh v5.1 |
|---|---|---|
| **Instruksi Ambigu & Kompleks** | AI berhalusinasi dan menulis kode yang salah tebak. | **IntentResolver + SemanticIR** mengunci spesifikasi dan menolak asumsi liar. |
| **Larangan Negatif Implisit** | AI merusak modul lain karena tidak menyadari larangan implisit. | **NegationHandler + ConstraintModel** mendeteksi kontradiksi klausul di awal. |
| **Dampak Perubahan Repositori** | AI mengubah satu fungsi dan merusak 5 modul downstream. | **DependencyGraph + CodeSemanticMapper** menghitung *blast radius* sebelum coding. |
| **Sesi Baru di Hari Berikutnya** | Mengulang kesalahan yang sama, amnesia penuh. | **ConversationMemory** langsung me-recall solusi lampau dalam hitungan milidetik. |
| **Variabel Tak Terdefinisi** | Kode ditulis ke disk, crash saat dijalankan user. | **Scope Neuron** memblokir kode di memori sebelum file sempat disimpan. |
| **AI Menyerah / Mengaku Selesai** | AI berkata "Semua sudah selesai" walau ada error. | **Stop Hook** memblokir terminasi dan memaksa agen tetap bekerja hingga lolos gate. |
| **Error Loop Berulang** | AI mencoba perbaikan identik 10x dan membuang token. | **LDE Engine** memotong loop pada iterasi ke-2 (`STRATEGY_CHANGE_REQUIRED`). |
| **Kesesuaian Bahasa Indonesia** | Hilang konteks karena perbedaan leksikal ID-EN. | **Semantic Alignment Neuron** mengukur kecocokan makna dwi-bahasa. |

---

## 🚀 Panduan Memulai Cepat (Quickstart)

### 1. Instalasi Lingkungan
```bash
# Clone repository
git clone https://github.com/V4nds/Gobysh.git
cd Gobysh

# Pasang mode editable
pip install -e .

# Pasang Git Hooks dan Antigravity Lifecycle Hooks secara otomatis
goby install-hook
```

### 2. Memeriksa Status Framework
```bash
goby status
```
*Output:*
```
==========================================================
       GOBY META-COGNITIVE FRAMEWORK STATUS (v5.0.0)
==========================================================
Git Pre-Commit Hook: INSTALLED (Active)
Git Pre-Push Hook:   INSTALLED (Active)
Antigravity Hooks:   INSTALLED (Active: PostToolUse, PreInvocation, Stop)
Unresolved File Errors: 0
Conversation Memory: 9 entries, 37 unique files
==========================================================
```

### 3. Validasi Kode & Gate Pemeriksaan
```bash
# Validasi file tunggal
goby check core/hooks.py

# Validasi dengan kontrak semantik bahasa Indonesia
goby check "def hitung(a, b): return a + b" --intent "buat fungsi hitung"

# Cek apakah workspace bersih dari error (Kunci Gate 1)
goby gate

# Jalankan seluruh pengujian audit (Kunci Gate 2)
goby audit
```

### 4. Pemetaan Repositori & Intent Resolution
```bash
# Petakan intent / query langsung ke simbol dan blast radius repositori
goby map "authentication logic" --repo core

# Uji pemahaman intent dengan pemindaian repositori otomatis
goby intent "bikin endpoint registrasi tapi jangan sentuh tabel user" --repo .

# Cari tahu apakah tugas serupa pernah dikerjakan sebelumnya
goby recall "endpoint registrasi pengguna"

# Simpan riwayat keberhasilan sesi
goby save "Selesai migrasi endpoint auth" create_feature core/auth.py
```

---

## 📁 Struktur Bersih Repositori

```
Gobysh/
├── .agents/                    # Konfigurasi Antigravity Lifecycle Hooks (hooks.json)
├── benchmarks/                 # Runner uji ablasi & benchmark dampak agen
│   ├── __init__.py
│   └── goby_agent_impact_runner.py
├── core/                       # Inti Mesin Gobysh v5.1
│   ├── ccr_engine.py           # Cognitive Control Room (Syntax, Scope, Taste)
│   ├── conversation_memory.py  # Penyimpanan & recall memori percakapan
│   ├── hooks.py                # Handler lifecycle hooks (PostToolUse, PreInvocation, Stop)
│   ├── intent_resolver.py      # Bilingual Intent Resolver & Semantic Contract
│   ├── lde_detector.py         # Loop Detection Engine (Levenshtein)
│   ├── state_memory.py         # Ledger kesalahan tak terselesaikan (Thread-safe)
│   ├── semantics/              # Formal Semantic Layer
│   │   ├── specification.py    # Requirement & SemanticSpecification models
│   │   ├── constraints.py      # Deterministic ConstraintModel & contradiction detector
│   │   ├── intermediate_representation.py # SemanticIR & SemanticEntity (Pure YAML/JSON)
│   │   ├── preservation.py     # PreservationContract model
│   │   ├── scope.py            # ScopeNormalizer & boundary checker
│   │   ├── negation.py         # NegationHandler (Deep bilingual ID/EN negation parsing)
│   │   ├── contract_validator.py # Multi-clause ContractValidator
│   │   └── dependency_graph.py # Causal Dependency Graph (CDG) & blast radius tracker
│   ├── translation/            # Code Mapping Layer (AST & Dependency Blast Radius)
│   │   ├── symbol_mapper.py    # Symbol, FileSymbolMap & SymbolMap models
│   │   ├── scanner.py          # RepositoryScanner (Python AST & JS/TS Regex Parser)
│   │   └── engine.py           # CodeSemanticMapper & MappingReport
│   └── neurons/                # Neuron modular CCR (Semantik ID/EN, Syntax, Scope, Taste)
├── demo/                       # Showcase Web UI interaktif
├── docs/                       # Dokumentasi arsitektur & panduan
│   ├── superpowers/plans/      # Rencana eksekusi subagent SDD (Stages 1-3)
│   └── adapters/               # Panduan integrasi IDE/CLI pihak ketiga:
│       ├── antigravity.md      # Google Antigravity & Gemini IDE
│       ├── claude.md           # Anthropic Claude Code
│       ├── cursor.md           # Cursor IDE Rules
│       └── openai_codex.md     # OpenAI GPT-4o / Codex
├── tests/                      # Rangkaian 234 unit test komprehensif
├── AGENTS.md                   # Protokol Operasional Wajib bagi AI Agent
├── GOBYSH_ARCHITECTURE_CALIBRATION_SPEC.md # Dokumen Spesifikasi Target Kalibrasi
├── pyproject.toml              # Konfigurasi paket Python standar
├── README.md                   # Dokumentasi publik resmi
└── SKILL.md                    # Antigravity Skill Definition
```

---

## 🧪 Bukti Empiris & Benchmark Terbuka

Seluruh klaim Gobysh didukung oleh pengujian empiris terbuka yang dapat direproduksi langsung:

```bash
python -m unittest discover tests/
```

- **Total Pengujian**: **234 Unit Tests** terisolasi di direktori `tests/`
- **Tingkat Kelulusan**: **100% OK** (Exit Code 0 dalam ~15.9 detik)
- **Cakupan Pengujian**:
  - Formal Semantic Core & IR serialization (`tests/test_semantic_core.py`)
  - Multi-clause Contract Validation & scope boundary checks (`tests/test_contract_validation.py`)
  - Repository AST Scanner, Symbol Mapping & Dependency Graph (`tests/test_semantic_mapping.py`)
  - Intent Tree parsing, Semantic Contract & Code Mapping (`tests/test_intent_resolver.py`)
  - Cross-session memory recall, save, persistence & concurrency (`tests/test_conversation_memory.py`, `tests/test_session_briefing.py`)
  - Semantic Alignment Neuron (Faithfulness, Relevance, Similarity)
  - Antigravity Lifecycle Hooks (PostToolUse, PreInvocation, Stop)
  - AST Scope analysis & undefined variable intercept
  - Levenshtein loop detection & strategy change state machines
  - Spatial stress tests & 20-thread concurrent memory locking

---

## 📜 Lisensi & Kontribusi

Proyek ini dirilis di bawah naungan lisensi **[MIT License](file:///d:/Gemini-Ide/Goby-skill/LICENSE)**. Bebas digunakan, dimodifikasi, dan diintegrasikan baik untuk penelitian akademis maupun aplikasi industri komersial.

Dikembangkan dengan dedikasi untuk mengubah masa depan *Autonomous AI Engineering* menjadi disiplin yang terbukti, deterministik, dan dapat dipercaya.
