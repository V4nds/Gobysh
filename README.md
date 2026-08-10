<div align="center">

# Goby Framework (v4.0.0)
### *Sistem Validasi Kode & Pencegahan Loop Error untuk Agen AI*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![Tests Status](https://img.shields.io/badge/Tests-113%2F113%20Passed-success.svg)](#-pengujian--verifikasi-empiris)
[![Git Hooks](https://img.shields.io/badge/Git%20Hooks-Active-indigo.svg)](#-demo-minimal--bukti-penggunaan-nyata)

**Goby** adalah pustaka Python modular yang memastikan agen AI menulis kode bebas bug melalui validasi pohon sintaksis (AST) sebelum output disajikan, penghentian otomatis perulangan kesalahan (error loop), dan verifikasi terminal empiris berbasis Exit Code.

</div>

---

## 🎯 3 Fitur Utama

1. **Validasi Kode Pre-Output (Pre-Output Validator)**  
   Memeriksa sintaksis, variabel tak terdefinisi (*scope*), dan struktur berkas `.py`, `.js`, `.ts` sebelum kode ditulis ke disk atau disajikan ke pengguna.

2. **Deteksi & Penghentian Error Berulang (Loop Guard)**  
   Mendeteksi ketika agen AI mencoba melakukan perbaikan yang sama berturut-turut ($\ge 2$ kali) dan secara otomatis menghentikan osilasi perbaikan naif.

3. **Verifikasi Terminal Empiris (Empirical Test Runner)**  
   Menolak klaim "tugas selesai" dari agen AI kecuali eksekusi unit test di terminal mengembalikan **Exit Code 0**.

---

## 💻 Demo Minimal & Bukti Penggunaan Nyata

### 1. Pemasangan CLI & Git Hooks (Satu Langkah)
```bash
# Clone dan pasang executable CLI ke environment Python Anda
pip install -e .

# Pasang Git Pre-Commit & Pre-Push Hard Hooks
goby install-hook
```

### 2. Contoh Eksekusi 1: Validasi Kode Sukses
```bash
goby check core/cli.py
```
**Output Terminal (LULUS):**
```text
[GOBY CHECK] Validating file: core/cli.py
  [SYNTAX] PASS (Gate: HARD) - Syntax is valid.
  [SCOPE] PASS (Gate: HARD) - All referenced names are defined within visible scope.
  [TASTE_DESIGN] PASS (Gate: SOFT) - Code is not a UI component, skipping Taste Design check.
[SUCCESS] File passed all CCR hard gates.
```

### 3. Contoh Eksekusi 2: Penolakan Kode Cacat (Failure Case)
Buat berkas uji `broken_sample.py` dengan variabel `undefined_price`:
```python
def calculate_total(quantity):
    return undefined_price * quantity  # 'undefined_price' belum didefinisikan!
```
Jalankan validasi Goby:
```bash
goby check broken_sample.py
```
**Output Terminal (DIBLOKIR / Exit Code 1):**
```text
[GOBY CHECK] Validating file: broken_sample.py
  [SYNTAX] PASS (Gate: HARD) - Syntax is valid.
  [SCOPE] FAIL (Gate: HARD) - Potentially undefined names: undefined_price
  [TASTE_DESIGN] PASS (Gate: SOFT) - Code is not a UI component, skipping Taste Design check.
[BLOCKED] BLOCKED by 1 hard gate(s): SCOPE
```
*Hasil: Git Pre-Commit Hook secara otomatis menolak `git commit` jika ada berkas yang menghasilkan status `[BLOCKED]`.*

---

## ⚡ Sebelum vs Sesudah Menggunakan Goby

| Skenario Penggunaan | Tanpa Goby (Naive AI Agent) | Dengan Goby Framework |
| :--- | :--- | :--- |
| **Variabel Tak Terdefinisi** | Kode ditulis ke disk, error meledak saat aplikasi di-run pengguna. | Kode **ditolak di tingkat AST (Pre-Output)** sebelum berkas disimpan. |
| **AI Stuck pada Bug Sama** | AI mencoba 10+ kali refactoring yang mirip dan membuang ribuan token API. | **LDE menghentikan perulangan pada iterasi ke-2** dan memicu bypass strategi. |
| **Klaim Penyelesaian Task** | AI mengklaim "Sudah diperbaiki!" tanpa bukti eksekusi nyata. | Klaim ditolak sampai `goby audit` mengembalikan **Exit Code 0**. |
| **Integrasi Version Control** | Kode cacat bisa lolos ke repository Git. | **Git Pre-Commit & Pre-Push Hooks** memblokir commit/push jika CCR/Test gagal. |

---

## 🧪 Metodologi Benchmark & Verifikasi Terbuka

Seluruh data pengujian dapat direproduksi secara mandiri di mesin Anda dengan mengeksekusi script benchmark internal:

```bash
python -m tests.benchmark_simulation
```

### 📋 Spesifikasi Lingkungan Pengujian:
- **Environment**: Python 3.12 / Windows & Linux x86_64
- **Dataset Evaluasi**: 113 Unit Test Case terisolasi di folder `tests/`
- **Definisi Metrik**:
  - *Pass Rate*: Persentase tes yang mengembalikan Exit Code 0 tanpa exception.
  - *Loop Abort Count*: Jumlah percobaan perbaikan maksimal sebelum LDE memutus siklus (ditargetkan $\le 2$ iterasi).

---

## 📂 Struktur Modul & Istilah Teknis

Untuk kemudahan navigasi, berikut adalah padanan istilah internal Goby dengan fungsi praktisnya:

| Istilah Internal | Modul Berkas | Padanan Bahasa Biasa | Fungsi Utama |
| :--- | :--- | :--- | :--- |
| **CCR** | [`core/ccr_engine.py`](file:///d:/Gemini-Ide/Goby-skill/core/ccr_engine.py) | **Pre-Output Validator** | Toolkit 9-Neuron penilai AST (Sintaksis, Scope, Keamanan, Infinite Loop). |
| **LDE** | [`core/lde_detector.py`](file:///d:/Gemini-Ide/Goby-skill/core/lde_detector.py) | **Error Loop Guard** | Algoritma jarak Levenshtein untuk menghentikan osilasi error berulang. |
| **GCA** | [`core/gca_runner.py`](file:///d:/Gemini-Ide/Goby-skill/core/gca_runner.py) | **Empirical Test Runner** | Runner subprocess terisolasi pembawa bukti empiris (*Exit Code 0*). |
| **Orchestrator** | [`core/orchestrator.py`](file:///d:/Gemini-Ide/Goby-skill/core/orchestrator.py) | **Task Scheduler** | Pemroses antrean tugas paralel berbasis *Worker Pool* & *Dependency DAG*. |
| **CLI & Hooks** | [`core/cli.py`](file:///d:/Gemini-Ide/Goby-skill/core/cli.py) | **Command Line & Git Enforcer** | Entrypoint terminal OS dan pemasang Git Pre-Commit/Pre-Push Hooks. |

---

## ⚖️ Batasan & Limitations Jujur

Agar ekspektasi pengguna tetap realistis, Goby saat ini **memiliki batasan berikut**:

1. **Belum Dapat Memeriksa Logika Bisnis Tingkat Tinggi Tanpa Unit Test**: CCR mengecek kebenaran sintaksis dan *scope* variabel secara statis, namun kebenaran logika bisnis tetap memerlukan unit test yang ditulis dengan baik.
2. **Ketergantungan Node.js untuk JS/TS**: Pengujian sintaksis JavaScript/TypeScript memerlukan `node` yang terpasang pada PATH sistem. Jika Node.js tidak ada, Goby hanya menjalankan pemeriksaan fallback dasar.
3. **Analisis Scope Terbatas pada Scope Lokal & Builtins**: Parser AST saat ini memeriksa *Load vs Store* pada tingkat modul dan fungsi, namun belum melacak *dynamic monkey-patching* atau *frame injection* eksternal.

---

## 🔌 Universal Harness Adapters

- 🌌 [**Antigravity / Gemini CLI**](file:///d:/Gemini-Ide/Goby-skill/adapters/antigravity.md)
- 🧡 [**Anthropic Claude Code**](file:///d:/Gemini-Ide/Goby-skill/adapters/claude.md)
- ⚡ [**Cursor IDE Rules**](file:///d:/Gemini-Ide/Goby-skill/adapters/cursor.md)
- 🟢 [**OpenAI / Custom GPTs**](file:///d:/Gemini-Ide/Goby-skill/adapters/openai_codex.md)

---

## 📜 Lisensi

Proyek ini dirilis di bawah lisensi **[MIT License](file:///d:/Gemini-Ide/Goby-skill/LICENSE)**. Free to use, modify, and distribute for open-source and commercial applications.
